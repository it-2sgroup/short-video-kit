#!/usr/bin/env python3
"""Measure a REFERENCE video (a client's sample, a competitor-style clip you were asked to match) before planning a copy of it.

Reading a sample by eye misses what happens between two looks: a flash on frames 0, 2 and 4, a cut every 0.4 s, a sound on each
cut. This script reads every frame once (small, in memory) and every sample of the audio, and writes the facts a plan needs:

    python scripts/analyze_reference.py sample.mp4 --out ref/ [--dense 0-3,10.2-12 --step 2]

  report.md / report.json   - the facts below, as a table and as data
  scenes.png (+ scenes_2.png) - one frame just after every cut, labelled with its time
  dense_<a>-<b>.png         - every --step-th frame of each --dense range (default: the first 3 s, every 2nd frame): flashes,
                              letters that jump up, a transition's in-between frames. ONE LOOK AT THESE is worth a minute of guessing.

What it measures (numbers, not opinions):
  cuts          frame-to-frame change above --cut (hard cuts), with the length of every shot, the median and the shortest
  motion runs   stretches where the picture keeps changing for 4+ frames without a cut: transitions, wipes, swirls, animated text.
                Their length in frames is the transition's duration.
  flashes       a one-frame brightening that falls back within 6 frames (a white flash, a silhouette fill, a glint)
  colours       the colour of the frame edge and centre just after each cut, named (a red checker behind a card shows as red edge,
                other centre); the run of edge colours tells where the background changes
  loudness      integrated LUFS, loudness range, true peak (ffmpeg ebur128): the target to master to
  spectrograms  spectrum_<a>-<b>.png, 15 s each: a click or pop is a thin vertical streak, a whoosh a slanted band, a riser a rising
                one, a note a horizontal line. Read them against scenes.png to see which sound sits on which cut. (Detecting sounds
                automatically under a voice does not work: tested against a mix whose 68 cues are known, a detector found 5 of them.)

What it cannot do: say WHAT a graphic is, read text, or hear a sound's character (say so in the report you give: "not listened"). Look at the sheets and list the techniques you
see; this report gives their frame-exact timing and counts. Needs numpy (the kit's venv: SVK_PYTHON) and ffmpeg.
"""
from __future__ import annotations

import argparse
import colorsys
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _venv import ensure_venv  # noqa: E402

ensure_venv()
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import montage  # noqa: E402  (same folder)


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, **kw)


def probe(path: Path) -> dict:
    r = run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,avg_frame_rate,sample_rate,pix_fmt,color_range:format=duration",
             "-of", "json", str(path)], text=True)
    if r.returncode:
        sys.exit(f"ffprobe failed: {r.stderr.strip()[:300]}")
    j = json.loads(r.stdout)
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), None)
    au = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    if not v:
        sys.exit("no video stream")
    n, d = (v["avg_frame_rate"].split("/") + ["1"])[:2]
    return {"width": v["width"], "height": v["height"], "fps": round(float(n) / float(d or 1), 3), "duration": float(j["format"]["duration"]),
            "codec": v["codec_name"], "pix_fmt": v.get("pix_fmt"), "range": v.get("color_range"), "audio": au["codec_name"] if au else None}


def read_frames(path: Path, fps: float, w: int, h: int) -> np.ndarray:
    """Every frame as a small RGB array [n, h, w, 3] (uint8): about 20 KB per frame."""
    r = run(["ffmpeg", "-hide_banner", "-v", "error", "-i", str(path), "-vf", f"fps={fps},scale={w}:{h}:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    if r.returncode:
        sys.exit(f"ffmpeg failed: {r.stderr.decode(errors='ignore')[-300:]}")
    a = np.frombuffer(r.stdout, np.uint8)
    n = len(a) // (w * h * 3)
    return a[: n * w * h * 3].reshape(n, h, w, 3)


def loudness(path: Path) -> dict | None:
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"], text=True)
    tail = r.stderr.split("Summary:")[-1] if "Summary:" in r.stderr else ""
    def num(label: str) -> float | None:
        m = re.search(rf"{label}:\s+(-?[\d.]+)", tail)
        return float(m.group(1)) if m else None
    i, lra, peak = num("I"), num("LRA"), num("Peak")
    return {"lufs": i, "lra": lra, "true_peak_db": peak} if i is not None else None


def colour_name(rgb: np.ndarray) -> str:
    r, g, b = (float(x) / 255 for x in rgb)
    hh, s, v = colorsys.rgb_to_hsv(r, g, b)
    if v < 0.16:
        return "black"
    if s < 0.14:
        return "white" if v > 0.86 else ("light grey" if v > 0.6 else ("grey" if v > 0.35 else "dark grey"))
    hue = hh * 360
    name = ("red" if hue < 14 or hue >= 346 else "orange" if hue < 40 else "yellow" if hue < 68 else "green" if hue < 165
            else "cyan" if hue < 200 else "blue" if hue < 255 else "purple" if hue < 290 else "magenta" if hue < 330 else "pink")
    return ("dark " if v < 0.4 else "light " if s < 0.4 and v > 0.8 else "") + name


def hard_cuts(diff: np.ndarray, thr: float) -> list[int]:
    """Frame indices where the picture jumps: a big change that its neighbours do not share (a slide is a RUN of medium changes)."""
    out = []
    for i in range(1, len(diff)):
        if diff[i] >= thr and diff[i] >= 1.6 * max(diff[i - 1] if i > 1 else 0, diff[i + 1] if i + 1 < len(diff) else 0):
            out.append(i + 1)   # diff[i] compares frame i with i+1: the new shot starts at i+1
    return out


def motion_runs(diff: np.ndarray, cuts: list[int], lo: float, min_len: int = 4) -> list[tuple[int, int]]:
    """Runs of >= min_len frames each changing by more than `lo` with no hard cut inside: transitions and animated graphics."""
    cutset = set(cuts)
    runs, start = [], None
    for i, d in enumerate(diff):
        moving = d >= lo and (i + 1) not in cutset
        if moving and start is None:
            start = i
        if (not moving or i == len(diff) - 1) and start is not None:
            end = i if not moving else i + 1
            if end - start >= min_len:
                runs.append((start, end))
            start = None
    return runs


def flashes(luma: np.ndarray, rise: float = 18.0, back: int = 6) -> list[int]:
    out = []
    for i in range(1, len(luma) - 1):
        if luma[i] - luma[i - 1] >= rise and luma[i + 1 : i + 1 + back].min() < luma[i] - rise * 0.6:
            out.append(i)
    return out


def spectrograms(video: Path, dur: float, out: Path, chunk: float = 15.0) -> list[str]:
    names = []
    t = 0.0
    while t < dur - 0.2:
        name = f"spectrum_{t:g}-{min(dur, t + chunk):g}.png"
        r = run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-ss", f"{t:.2f}", "-t", f"{chunk:.2f}", "-i", str(video), "-vn", "-ac", "1", "-lavfi",
                 "showspectrumpic=s=1500x300:legend=0:fscale=log:color=intensity", str(out / name)])
        if r.returncode == 0:
            names.append(name)
        t += chunk
    return names


def extract_frames(video: Path, times: list[float], tmp: Path, prefix: str) -> list[str]:
    out = []
    for t in times:
        f = tmp / f"{prefix}_{t:.3f}.jpg"
        run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-ss", f"{max(0.0, t):.3f}", "-i", str(video), "-frames:v", "1", "-q:v", "3", str(f)])
        if f.exists():
            out.append(str(f))
    return out


def sheet(files: list[str], out: Path, cols: int, width: int) -> None:
    if files:
        montage.tile(files, str(out), cols, width)


def main() -> int:
    ap = argparse.ArgumentParser(description="Measure a reference video: cuts, transitions, flashes, colours, loudness, spectrograms.")
    ap.add_argument("video", type=Path)
    ap.add_argument("--out", type=Path, default=Path("ref"))
    ap.add_argument("--cut", type=float, default=0.10, help="hard-cut threshold: mean change of a frame, 0..1 (default 0.10)")
    ap.add_argument("--motion", type=float, default=0.025, help="per-frame change that counts as movement for a transition run (default 0.025)")
    ap.add_argument("--dense", default="0-3", help="seconds ranges to pull every --step-th frame from, e.g. 0-3,10.2-12 (default 0-3)")
    ap.add_argument("--step", type=int, default=2, help="every n-th frame in the dense sheets (default 2)")
    a = ap.parse_args()
    if not a.video.is_file():
        sys.exit(f"not found: {a.video}")
    a.out.mkdir(parents=True, exist_ok=True)

    info = probe(a.video)
    fps, dur = info["fps"], info["duration"]
    w = 64
    h = max(2, round(w * info["height"] / info["width"] / 2) * 2)
    print(f"{a.video.name}: {info['width']}x{info['height']} {fps} fps, {dur:.2f} s, {info['codec']} {info['pix_fmt']} {info['range'] or ''}, audio {info['audio'] or 'none'}")
    fr = read_frames(a.video, fps, w, h)
    n = len(fr)
    f32 = fr.astype(np.float32)
    diff = np.abs(f32[1:] - f32[:-1]).mean(axis=(1, 2, 3)) / 255
    luma = (f32 @ np.array([0.2126, 0.7152, 0.0722], np.float32)).mean(axis=(1, 2))

    cuts = hard_cuts(diff, a.cut)
    starts = [0] + cuts
    shots = [(round(s / fps, 3), round((starts[i + 1] if i + 1 < len(starts) else n) / fps, 3)) for i, s in enumerate(starts)]
    lens = np.array([e - s for s, e in shots])
    runs = motion_runs(diff, cuts, a.motion)
    fl = flashes(luma)

    # colours just after each cut: the edge band (12% of the frame) and the centre
    bh, bw = max(1, h // 8), max(1, w // 8)
    colours = []
    for s in starts:
        k = min(n - 1, s + 2)
        im = fr[k]
        edge = np.concatenate([im[:bh].reshape(-1, 3), im[-bh:].reshape(-1, 3), im[:, :bw].reshape(-1, 3), im[:, -bw:].reshape(-1, 3)])
        colours.append((colour_name(np.median(edge, axis=0)), colour_name(np.median(im[h // 3 : 2 * h // 3, w // 3 : 2 * w // 3].reshape(-1, 3), axis=0))))

    # audio
    loud = loudness(a.video) if info["audio"] else None
    spectra = spectrograms(a.video, dur, a.out) if info["audio"] else []

    # pictures
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        scene_t = [min(dur - 0.05, s / fps + 0.1) for s in starts]
        for k in range(0, len(scene_t), 40):
            files = extract_frames(a.video, scene_t[k : k + 40], tmp, f"s{k // 40}")
            sheet(files, a.out / ("scenes.png" if k == 0 else f"scenes_{k // 40 + 1}.png"), 8, 180)
        dense_written = []
        for rng in [r for r in a.dense.split(",") if r.strip()]:
            lo, _, hi = rng.partition("-")
            t0, t1 = float(lo), float(hi or float(lo) + 3)
            times = list(np.arange(t0, min(t1, dur), a.step / fps))[:48]
            files = extract_frames(a.video, [float(t) for t in times], tmp, "d")
            name = f"dense_{t0:g}-{t1:g}.png"
            sheet(files, a.out / name, 8, 160)
            dense_written.append(name)

    report = {
        "video": a.video.name, **info, "frames": n,
        "shots": [{"start": s, "end": e, "length": round(e - s, 3), "edge": colours[i][0], "centre": colours[i][1]} for i, (s, e) in enumerate(shots)],
        "shot_length": {"count": len(lens), "median": round(float(np.median(lens)), 2), "shortest": round(float(lens.min()), 2), "longest": round(float(lens.max()), 2),
                        "cuts_per_minute": round(len(cuts) / dur * 60, 1)},
        "motion_runs": [{"start": round(s / fps, 3), "frames": e - s, "seconds": round((e - s) / fps, 2)} for s, e in runs],
        "flashes": [round(i / fps, 3) for i in fl],
        "loudness": loud,
        "sheets": ["scenes.png", *dense_written, *spectra],
    }
    (a.out / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")

    md = [f"# Reference: {a.video.name}", "",
          f"{info['width']}x{info['height']}, {fps} fps, {dur:.1f} s, {n} frames. Audio: {info['audio'] or 'none'}.", "",
          "## Shots", "", f"{len(lens)} shots, {report['shot_length']['cuts_per_minute']} cuts/min; median {report['shot_length']['median']} s, "
          f"shortest {report['shot_length']['shortest']} s, longest {report['shot_length']['longest']} s.", "",
          "| # | start | end | length | edge colour | centre colour |", "|---|---|---|---|---|---|"]
    md += [f"| {i + 1} | {s['start']:.2f} | {s['end']:.2f} | {s['length']:.2f} | {s['edge']} | {s['centre']} |" for i, s in enumerate(report["shots"])]
    md += ["", "## Motion runs (transitions, wipes, animated graphics: 4+ frames of continuous change)", ""]
    md += [f"- {r['start']:.2f} s: {r['frames']} frames ({r['seconds']} s)" for r in report["motion_runs"]] or ["- none"]
    md += ["", "## Flashes (a one-frame brightening that falls back)", "", ", ".join(f"{t:.2f} s" for t in report["flashes"]) or "none"]
    md += ["", "## Sound", ""]
    if loud:
        md.append(f"Integrated {loud['lufs']} LUFS, range {loud['lra']} LU, true peak {loud['true_peak_db']} dBFS.")
    md.append("Sound effects are not detected automatically (a voice hides them): read the spectrum_*.png sheets, where a click is a vertical streak "
              "and a whoosh a slanted band, against the cut times above, and say that nobody listened.")
    md += ["", "## Sheets to look at", ""] + [f"- `{s}`" for s in report["sheets"]]
    md += ["", "Numbers give timing; the sheets give the technique. List what you SEE in each dense sheet (flash, text pile, transition kind) next to these times."]
    (a.out / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"{len(lens)} shots (median {report['shot_length']['median']} s, shortest {report['shot_length']['shortest']} s), {len(runs)} motion runs, "
          f"{len(fl)} flashes"
          + (f", {loud['lufs']} LUFS / {loud['true_peak_db']} dBTP" if loud else ""))
    print(f"wrote {a.out / 'report.md'}, report.json and {', '.join(report['sheets'])}: LOOK at the sheets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
