#!/usr/bin/env python3
"""Inspect raw source clips before planning an edit; with --measure, also measure the picture and sound.

Planning a timeline without knowing what the footage is produces plans that cannot be cut. This reads the
real properties of each file (duration, size, rotation, fps, audio, HDR) and emits a shot-log skeleton.
--measure decodes samples of every clip and measures what the edit depends on:

  light     mean / 10th / 90th percentile luma of the keyframes (signalstats), 0-255
  colour    the average RGB of the keyframes and the cast it implies (warm/cool, green/magenta)
  noise     PSNR between a frame and a lightly denoised copy: < 44 dB grainy, < 40 dB very noisy
  motion    vid.stab's frame-to-frame shift on the first 12 s: `move` (the camera travels: walk, pan)
            and `jitter` (shake around that path); needs ffmpeg built with libvidstab
  speech    loud, varied sound in the camera's own audio: probably someone talking on camera

and recommends corrections (prepare_footage.py applies them) plus a summary that playbook.py suggest
uses to guess the kind of video. The thresholds are heuristics (references/image-processing.md): look at
the contact sheet before trusting them, and confirm suspected speech with align_captions.py.

Usage:
    python inspect_footage.py <folder-or-files...> [--log] [--measure] [--json [FILE]]

    --log      emit a blank shot-log table to paste into the edit plan
    --measure  measure light, colour, noise, motion and speech (a few seconds per clip)
    --json     machine-readable output to stdout, or to FILE (analysis.json)

Requires ffmpeg and ffprobe on PATH.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv", ".hevc", ".3gp"}


def probe(path: Path) -> dict:
    cmd = [
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", str(path),
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60).stdout
    except subprocess.CalledProcessError as e:
        return {"error": (e.stderr or "ffprobe failed").strip().splitlines()[-1][:120]}
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return {"error": str(e)[:120]}

    data = json.loads(out)
    v = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    a = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    if not v:
        return {"error": "no video stream"}

    w, h = int(v.get("width", 0)), int(v.get("height", 0))
    # Phones write rotation metadata rather than rotating pixels, so a clip that reads as
    # landscape here may actually play vertical. Check before concluding it needs reframing.
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = abs(int(sd["rotation"])) % 180
    if rot == 90:
        w, h = h, w

    fps = 0.0
    raw_fps = v.get("avg_frame_rate") or v.get("r_frame_rate") or "0/1"
    try:
        num, den = raw_fps.split("/")
        fps = round(float(num) / float(den), 2) if float(den) else 0.0
    except (ValueError, ZeroDivisionError):
        pass

    dur = float(data.get("format", {}).get("duration") or v.get("duration") or 0)
    hdr = v.get("color_transfer") in ("arib-std-b67", "smpte2084") or v.get("color_primaries") == "bt2020"

    return {
        "duration_s": round(dur, 2),
        "width": w,
        "height": h,
        "orientation": "vertical" if h > w else ("square" if h == w else "LANDSCAPE"),
        "fps": fps,
        "has_audio": a is not None,
        "vcodec": v.get("codec_name", "?"),
        "size_mb": round(path.stat().st_size / 1_048_576, 1),
        "rotated": rot == 90,
        "hdr": hdr,
        "transfer": v.get("color_transfer", ""),
    }


# ----------------------------------------------------------------------------- measurement
# HLG / PQ footage (iPhone HDR) must be tone-mapped before anything is measured or graded. `mobius`
# keeps the mid-tones and compresses only the highlights: on an HLG copy of a real clip it gave mean
# luma 125 and saturation 11.6 against the SDR original's 128 and 11.6, where `hable` gave 90 and 7.7.
TONEMAP = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,"
           "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
DARK, BRIGHT = 0.33, 0.72          # mean luma (0-1 of the video range) outside which exposure is corrected
CAST = 0.06                        # colour cast (share of grey) above which white balance is corrected
JITTER = 4.0                       # shake, px per frame at 480 px wide, above which a clip is stabilised
MOVING = 2.5                       # camera travel, px per frame at 480 px wide, above which motion is "high"
NOISY, VERY_NOISY = 44.0, 40.0     # PSNR (dB) vs a denoised copy: below = grainy / very noisy


def ffmpeg_out(args: list[str], binary: bool = False):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", *args], capture_output=True, text=not binary)
    return r.stdout


def has_filter(name: str) -> bool:
    out = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    return any(line.split()[1:2] == [name] for line in out.splitlines() if len(line.split()) > 1)


def keyframe_light(path: Path, pre: str) -> dict:
    out = ffmpeg_out(["-skip_frame", "nokey", "-i", str(path), "-an", "-vf",
                      f"{pre}format=yuv420p,scale=320:-2,signalstats,metadata=mode=print:file=-", "-f", "null", "-"])
    def series(key):
        return [float(x) for x in re.findall(rf"signalstats\.{key}=([\d.]+)", out)] or [0.0]
    return {k: round(statistics.mean(series(k.upper())), 1) for k in ("yavg", "ylow", "yhigh", "satavg")}


def neutral_rgb(path: Path, pre: str) -> tuple[list[float], float]:
    """Average RGB of the keyframes' near-neutral pixels (walls, concrete, white cloth: low saturation,
    neither black nor clipped) and their share of the frame. Plain grey-world averages every pixel, so a
    large green object or a red wall reads as a colour cast; the neutral pixels are what white balance is about."""
    raw = ffmpeg_out(["-skip_frame", "nokey", "-i", str(path), "-an", "-vf", f"{pre}scale=96:-2,format=rgb24",
                      "-frames:v", "8", "-f", "rawvideo", "-"], binary=True)
    total, picked = 0, [0.0, 0.0, 0.0, 0]
    for i in range(0, len(raw) - 2, 3):
        r, g, b = raw[i], raw[i + 1], raw[i + 2]
        hi, lo = max(r, g, b), min(r, g, b)
        total += 1
        if 50 <= hi <= 245 and hi - lo <= 0.2 * hi:
            picked[0] += r; picked[1] += g; picked[2] += b; picked[3] += 1
    if picked[3] < 0.05 * max(1, total):
        return [0.0, 0.0, 0.0], 0.0
    return [round(picked[c] / picked[3], 1) for c in range(3)], round(picked[3] / total, 3)


def frame_noise(path: Path, pre: str, duration: float) -> float:
    """PSNR between three frames (at 25/50/75%) and a lightly denoised copy, at 1080 px wide. Fine texture
    (concrete, fabric, leaves) also lowers it, so it only counts with low light (see measure)."""
    vals = []
    for f in (0.25, 0.5, 0.75):
        out = ffmpeg_out(["-ss", f"{duration * f:.2f}", "-i", str(path), "-an", "-frames:v", "3", "-filter_complex",
                          f"[0:v]{pre}scale=1080:-2,format=yuv420p,split[a][b];[b]hqdn3d=6:4:0:0[c];[a][c]psnr=stats_file=-",
                          "-f", "null", "-"])
        # hqdn3d barely filters the first frame it sees, so its PSNR is skipped
        vals += [float(y) for n, y in re.findall(r"n:(\d+).*?psnr_y:([\d.]+)", out) if int(n) > 1]
    return round(statistics.mean(vals), 1) if vals else 99.0


def camera_motion(path: Path) -> dict | None:
    """Median vid.stab local-motion vector per frame (480 px wide, first 12 s): mean travel and the
    shake around a 9-frame moving average."""
    with tempfile.TemporaryDirectory() as tmp:
        trf = Path(tmp) / "m.trf"
        ffmpeg_out(["-t", "12", "-i", str(path), "-an", "-vf",
                    f"scale=480:-2,vidstabdetect=result={trf.as_posix()}:shakiness=5:accuracy=9:show=0:fileformat=ascii",
                    "-f", "null", "-"])
        if not trf.is_file():
            return None
        xs, ys = [], []
        for line in trf.read_text(errors="replace").splitlines():
            if not line.startswith("Frame"):
                continue
            lms = re.findall(r"\(LM (-?\d+) (-?\d+) ", line)
            xs.append(statistics.median(int(a) for a, _ in lms) if lms else 0.0)
            ys.append(statistics.median(int(b) for _, b in lms) if lms else 0.0)
    if len(xs) < 5:
        return None
    avg = lambda v, i: statistics.mean(v[max(0, i - 4):i + 5])
    move = statistics.mean(math.hypot(x, y) for x, y in zip(xs, ys))
    jitter = statistics.mean(abs(xs[i] - avg(xs, i)) + abs(ys[i] - avg(ys, i)) for i in range(len(xs)))
    return {"move": round(move, 2), "jitter": round(jitter, 2), "level": "high" if move >= MOVING else "low"}


def speech_likely(path: Path) -> bool:
    """Loud and varied camera audio (90th percentile of 100 ms windows above -32 dBFS and 18 dB over the
    10th): a voice close to the mic. Wind and crowds can fool it; confirm with align_captions.py."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from process_audio import pct, windows
    lv = windows(path)
    return pct(lv, 0.9) > -32 and pct(lv, 0.9) - pct(lv, 0.1) > 18


def measure(path: Path, info: dict, stab: bool) -> dict:
    pre = TONEMAP + "," if info.get("hdr") else ""
    light = keyframe_light(path, pre)
    (r, g, b), neutral = neutral_rgb(path, pre)
    grey = max(1.0, (r + g + b) / 3)
    warm, green = ((r - b) / grey, (g - (r + b) / 2) / grey) if neutral else (0.0, 0.0)
    m = (light["yavg"] - 16) / 219
    noise = frame_noise(path, pre, info["duration_s"])
    motion = camera_motion(path) if stab else None
    speech = info["has_audio"] and speech_likely(path)
    rec = []
    if info.get("hdr"):
        rec.append("tonemap")
    if m < DARK or m > BRIGHT or (info.get("hdr") and m < DARK + 0.09):  # tone-mapped HDR runs a little dark
        rec.append("exposure")
    if neutral and max(abs(warm), abs(green)) > CAST:
        rec.append("white-balance")
    if motion and motion["jitter"] > JITTER:
        rec.append("stabilize")
    if noise < VERY_NOISY or (noise < NOISY and m < DARK + 0.05):  # grain shows in the dark, texture in daylight
        rec.append("denoise")
    return {"light": {**light, "level": round(m, 3)}, "rgb": [r, g, b], "neutral_share": neutral,
            "cast": {"warm": round(warm, 3), "green": round(green, 3)}, "noise_psnr": noise,
            "motion": motion["level"] if motion else "unknown", "move": motion,
            "speech": bool(speech), "slowmo": info["fps"] >= 50, "recommend": rec}


def summarize(clips: list[dict]) -> dict:
    total = sum(c["duration_s"] for c in clips) or 1
    talk = sum(c["duration_s"] for c in clips if c.get("speech"))
    moving = sum(c["duration_s"] for c in clips if c.get("motion") == "high")
    return {"clips": len(clips), "seconds": round(total, 1),
            "speech": "on-camera" if talk / total >= 0.4 else "none",
            "motion": "high" if moving / total >= 0.5 else "low",
            "hdr": sum(1 for c in clips if c.get("hdr")),
            "fps60": sum(1 for c in clips if c.get("slowmo"))}


def collect(targets: list[str]) -> list[Path]:
    files: list[Path] = []
    for t in targets:
        p = Path(t)
        if p.is_dir():
            files += [f for f in sorted(p.iterdir()) if f.suffix.lower() in VIDEO_EXT]
        elif p.is_file():
            files.append(p)
        else:
            print(f"Skipped (not found): {t}", file=sys.stderr)
    return files


def main() -> int:
    ap = argparse.ArgumentParser(description="Inspect raw clips before planning an edit.")
    ap.add_argument("targets", nargs="+", help="Folder(s) or video file(s)")
    ap.add_argument("--json", nargs="?", const="-", help="JSON to stdout, or to this file (analysis.json)")
    ap.add_argument("--log", action="store_true", help="Emit a blank shot-log table")
    ap.add_argument("--measure", action="store_true", help="measure light, colour, noise, motion and speech")
    args = ap.parse_args()

    if not shutil.which("ffprobe"):
        print("ffprobe not found on PATH. It ships with ffmpeg.", file=sys.stderr)
        return 1

    files = collect(args.targets)
    if not files:
        print("No video files found.", file=sys.stderr)
        return 1

    stab = args.measure and has_filter("vidstabdetect")
    if args.measure and not stab:
        print("note: this ffmpeg has no libvidstab: shake and motion are not measured", file=sys.stderr)
    results = []
    for f in files:
        info = probe(f)
        info["file"] = f.name
        info["stem"] = f.stem.upper()
        info["path"] = str(f.resolve())
        if args.measure and "error" not in info:
            print(f"measuring {f.name}", file=sys.stderr)
            info.update(measure(f, info, stab))
        results.append(info)
    ok = [r for r in results if "error" not in r]
    doc = {"clips": results, "summary": summarize(ok) if args.measure else {}}

    if args.json:
        text = json.dumps(doc, ensure_ascii=False, indent=1)
        if args.json == "-":
            print(text)
            return 0
        Path(args.json).write_text(text, encoding="utf-8")
        print(f"wrote {args.json}", file=sys.stderr)

    bad = [r for r in results if "error" in r]

    print(f"{len(files)} clip(s)\n")
    print(f"{'File':<34}{'Dur':>8}{'Resolution':>12}{'FPS':>7}{'Audio':>7}  Orientation")
    print("-" * 84)
    for r in ok:
        res = f"{r['width']}x{r['height']}"
        audio = "yes" if r["has_audio"] else "NO"
        print(
            f"{r['file'][:33]:<34}"
            f"{r['duration_s']:>7.1f}s"
            f"{res:>12}"
            f"{r['fps']:>7.0f}"
            f"{audio:>7}"
            f"  {r['orientation']}"
            + ("  (rotation metadata)" if r.get("rotated") else "")
        )
    for r in bad:
        print(f"{r['file'][:33]:<34}  ERROR: {r['error']}")
    if args.measure and ok:
        print(f"\n{'File':<34}{'Light':>7}{'Warm':>7}{'Green':>7}{'Noise':>7}{'Move':>7}{'Shake':>7}  Speech  Recommend")
        print("-" * 104)
        for r in ok:
            mv = r.get("move") or {}
            print(f"{r['file'][:33]:<34}{r['light']['level']:>7.2f}{r['cast']['warm']:>+7.2f}{r['cast']['green']:>+7.2f}"
                  f"{r['noise_psnr']:>7.1f}{mv.get('move', float('nan')):>7.1f}{mv.get('jitter', float('nan')):>7.1f}"
                  f"  {'yes' if r['speech'] else 'no':6}  {', '.join(r['recommend']) or '-'}")
        sm = summarize(ok)
        print(f"\nSummary: speech {sm['speech']}, camera motion {sm['motion']}, {sm['hdr']} HDR clip(s), "
              f"{sm['fps60']} clip(s) at 50+ fps (slow motion possible: prepare_footage.py --slowmo). Next: playbook.py suggest --analysis")

    if ok:
        total = sum(r["duration_s"] for r in ok)
        print(f"\nTotal source: {total:.1f}s across {len(ok)} clip(s)")

        # Flag the things that will break a plan if discovered late.
        notes = []
        land = [r["file"] for r in ok if r["orientation"] == "LANDSCAPE"]
        if land:
            notes.append(
                f"{len(land)} clip(s) are landscape — they need reframing or a blurred-fill "
                f"backdrop for a 1080x1920 frame: {', '.join(land[:3])}"
            )
        silent = [r["file"] for r in ok if not r["has_audio"]]
        if silent:
            notes.append(
                f"{len(silent)} clip(s) have no audio track — no diegetic sound to use, so the "
                f"demo will lean entirely on voiceover: {', '.join(silent[:3])}"
            )
        fpsset = {r["fps"] for r in ok if r["fps"]}
        if len(fpsset) > 1:
            notes.append(f"Mixed frame rates ({sorted(fpsset)}) — conform before cutting.")
        sizes = {(r["width"], r["height"]) for r in ok}
        if len(sizes) > 1:
            notes.append(f"Mixed resolutions ({len(sizes)} different) — conform before cutting.")
        hdr = [r["file"] for r in ok if r.get("hdr")]
        if hdr:
            notes.append(f"{len(hdr)} clip(s) are HDR ({ok[0].get('transfer') or 'HLG/PQ'}): render from tone-mapped "
                         f"proxies (prepare_footage.py), never the originals: {', '.join(hdr[:3])}")
        if total < 45:
            notes.append(
                f"Only {total:.0f}s of source for a 30-40s cut. That leaves almost no room to "
                "choose moments; expect to reuse shots via punch-ins, or shoot pickups."
            )
        if notes:
            print("\nWorth knowing before planning:")
            for n in notes:
                print(f"  ! {n}")

    if args.log:
        print("\n## Shot log\n")
        print("| Clip | In | Out | What happens | Usable for |")
        print("|------|----|----|--------------|------------|")
        for r in ok:
            print(f"| {r['file']} | 0.0 | {r['duration_s']} | [describe] | [the playbook's beats: HOOK, DEMO, LIVING, STEP...] |")
        print(
            "\nSplit a clip into several rows where several usable moments sit inside it. "
            "The In/Out columns are source timecodes; the edit plan's Start/End are timeline "
            "positions. They are not the same thing."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
