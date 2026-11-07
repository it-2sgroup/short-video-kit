#!/usr/bin/env python3
"""Make the render proxies: tone-map, correct and grade every clip, so the whole video shares one look.

    python scripts/prepare_footage.py RAW_CLIPS render/public/clips --playbook real-estate
    python scripts/prepare_footage.py RAW_CLIPS OUT --analysis analysis.json --grade natural --height 1920
    python scripts/prepare_footage.py RAW_CLIPS OUT --fix "IMG_0332:rotate=-1.5,stabilize=on" --fix "IMG_0400:lens=-0.12:0.03"

Per clip, in this order (references/image-processing.md explains each step and its thresholds):

  1. tone-map    HLG / PQ (iPhone HDR) to SDR bt709, or the colours come out washed and grey
  2. frame       scale and centre-crop to 9:16 at --height (2880 default: camera moves to ~1.5x stay sharp)
  3. denoise     hqdn3d, light or stronger, when the measurement says grain (dark and noisy)
  4. stabilise   vid.stab two-pass (smoothing 15, optimal zoom so no border shows) when the clip shakes
  5. lens        lenscorrection k1,k2: only by --fix (phones correct their lenses in camera)
  6. level       rotate by --fix degrees and zoom just enough to hide the corners
  7. fps         30; with --slowmo, 60 for sources of 50+ fps (0.5x slow motion stays smooth; twice the
                 encoding time, so only when the plan slows something down)
  8. white bal.  RGB gains from the clip's near-neutral pixels, times the grade's wbStrength
  9. exposure    a gamma towards mid-grey when the clip is too dark or too bright
 10. grade       the playbook's look from assets/grades.json (8-10 are baked into one 3D LUT: one RGB pass)
 11. sharpen     a light unsharp mask after the downscale

`correction: shared` in the playbook (product demos, tutorials, promos) computes white balance and
exposure ONCE from all clips together: a BEFORE and an AFTER must never be corrected differently.
`per-clip` (property, food, montages) corrects each clip on its own. Measurements come from
--analysis (inspect_footage.py --measure --json) or are taken now. Existing proxies are kept unless
--force. Writes corrections.json beside the proxies: what was done to which clip.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import inspect_footage as insp  # noqa: E402
import playbook as playbooks  # noqa: E402

VIDEO_EXT = {".mov", ".mp4", ".m4v", ".mkv"}
TARGET_LEVEL = 0.45  # mean luma (0-1 of the video range) a too-dark or too-bright clip is moved towards


def parse_fix(specs: list[str]) -> dict:
    """--fix "STEM:rotate=-1.5,lens=-0.12:0.03,stabilize=on,denoise=off,wb=off,exposure=off" """
    out = {}
    for spec in specs:
        stem, _, body = spec.partition(":")
        opts = {}
        for kv in filter(None, body.split(",")):
            k, _, v = kv.partition("=")
            opts[k.strip()] = v.strip()
        out[Path(stem).stem.upper()] = opts
    return out


def wb_gains(rgb: list[float], strength: float) -> tuple[float, float, float] | None:
    r, g, b = rgb
    if min(r, g, b) <= 0:
        return None
    grey = (r + g + b) / 3
    gains = [min(1.18, max(0.85, (grey / c) ** strength)) for c in (r, g, b)]
    lum = 0.2126 * gains[0] + 0.7152 * gains[1] + 0.0722 * gains[2]  # keep brightness where it was
    return tuple(round(x / lum, 4) for x in gains)


def gamma_for(level: float) -> float:
    if not 0.02 < level < 0.98:
        return 1.0
    target = TARGET_LEVEL if level < TARGET_LEVEL else 0.62
    return round(min(1.5, max(0.75, math.log(level) / math.log(target))), 3)


def build_chain(m: dict, fix: dict, grade: dict, gains, gamma, w: int, h: int, stab_trf: Path | None) -> tuple[str, list[str]]:
    rec, done, f = m.get("recommend", []), [], []
    if m.get("hdr"):
        f.append(insp.TONEMAP); done.append("tone-mapped HDR")
    f.append(f"scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,crop={w}:{h}")
    if fix.get("denoise", "auto") == "on" or ("denoise" in rec and fix.get("denoise") != "off"):
        strong = m.get("noise_psnr", 99) < insp.VERY_NOISY
        f.append("hqdn3d=4:3:6:4.5" if strong else "hqdn3d=2:1.5:3:2.25"); done.append("denoised" + (" (strong)" if strong else ""))
    if stab_trf:
        # The scale=iw:ih copy is not decoration: an RGB filter (curves, colortemperature, vibrance) right after
        # vidstabtransform segfaults ffmpeg 7.0 (measured); a re-allocated frame in between does not.
        f.append(f"vidstabtransform=input={stab_trf.as_posix()}:smoothing=15:optzoom=1:zoomspeed=0.25:interpol=bicubic,scale=iw:ih")
        done.append("stabilised")
    if fix.get("lens"):
        k1, _, k2 = fix["lens"].partition(":")
        f.append(f"lenscorrection=k1={float(k1)}:k2={float(k2 or 0)}"); done.append(f"lens k1={k1} k2={k2 or 0}")
    if fix.get("rotate"):
        a = math.radians(float(fix["rotate"]))
        z = math.cos(abs(a)) + math.sin(abs(a)) * h / w  # zoom that hides the corners of a rotated 9:16 frame
        f.append(f"rotate={a:.5f}:c=black,scale=ceil(iw*{z:.4f}/2)*2:ceil(ih*{z:.4f}/2)*2,crop={w}:{h}")
        done.append(f"levelled {fix['rotate']}°")
    f.append(f"fps={m['proxy_fps']}")
    colour = []  # white balance, exposure and the grade: baked into one 3D LUT (see colour_lut)
    if gains and fix.get("wb") != "off":
        colour.append(f"colorchannelmixer=rr={gains[0]}:gg={gains[1]}:bb={gains[2]}")
        done.append(f"white balance R{gains[0]:.3f} G{gains[1]:.3f} B{gains[2]:.3f}")
    if gamma != 1.0 and fix.get("exposure") != "off":
        colour.append(f"eq=gamma={gamma}"); done.append(f"exposure gamma {gamma}")
    if grade["chain"]:
        colour.append(grade["chain"])
    return ",".join(f), ",".join(colour), done


def colour_lut(chain: str, out: Path) -> None:
    """Run the colour chain once over an identity Hald CLUT (64^3 colours). Applying that one image with
    `haldclut` costs a single RGB pass instead of one per filter: on 4K60 footage the full chain took
    113 s for 6 s, the LUT path a fraction, and the two pictures differ by 46 dB PSNR (invisible)."""
    run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-f", "lavfi", "-i", "haldclutsrc=level=8", "-frames:v", "1",
         "-vf", chain, "-pix_fmt", "rgb24", str(out)])


def run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"ffmpeg failed (exit {r.returncode}):\n{' '.join(cmd)}\n{r.stderr[-1200:]}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Correct, grade and proxy raw clips for the render.")
    ap.add_argument("src", type=Path, help="folder of raw clips (or one clip)")
    ap.add_argument("dest", type=Path, help="proxy folder, normally <render project>/public/clips")
    ap.add_argument("--playbook", help="playbook id[:variant]: its grade and correction mode")
    ap.add_argument("--grade", help="override the grade (assets/grades.json)")
    ap.add_argument("--analysis", type=Path, help="analysis.json from inspect_footage.py --measure --json")
    ap.add_argument("--height", type=int, default=2880, choices=[1920, 2880, 3840])
    ap.add_argument("--no-correct", action="store_true", help="tone-map and frame only: no denoise, stabilise, WB or exposure")
    ap.add_argument("--fix", action="append", default=[], help='per-clip overrides, e.g. "IMG_0332:rotate=-1.5,stabilize=on"')
    ap.add_argument("--slowmo", action="store_true", help="keep 60 fps for 50+ fps sources (for 0.5x slow motion)")
    ap.add_argument("--force", action="store_true", help="rebuild proxies that already exist")
    a = ap.parse_args()

    pb = playbooks.load(a.playbook) if a.playbook else None
    grades = json.loads((SKILL / "assets" / "grades.json").read_text(encoding="utf-8"))["grades"]
    gname = a.grade or (pb["grade"] if pb else "natural")
    if gname not in grades:
        sys.exit(f"unknown grade '{gname}' (known: {', '.join(grades)})")
    grade, shared = grades[gname], (pb["correction"] == "shared") if pb else False
    fixes = parse_fix(a.fix)

    clips = sorted(p for p in ([a.src] if a.src.is_file() else a.src.rglob("*")) if p.suffix.lower() in VIDEO_EXT)
    if not clips:
        sys.exit(f"no video files in {a.src}")
    known = {c["stem"]: c for c in json.loads(a.analysis.read_text(encoding="utf-8"))["clips"]} if a.analysis else {}
    stab = insp.has_filter("vidstabdetect")
    measures = {}
    for p in clips:
        stem = p.stem.upper()
        m = known.get(stem)
        if not m or "recommend" not in m:
            print(f"measuring {p.name}")
            m = insp.probe(p)
            m.update(insp.measure(p, m, stab))
        if a.no_correct:
            m = {**m, "recommend": [r for r in m.get("recommend", []) if r == "tonemap"]}
        m["proxy_fps"] = 60 if a.slowmo and m.get("fps", 0) >= 50 else 30
        measures[stem] = m

    w = a.height * 9 // 16
    # Shared mode: one white balance and one exposure for every clip (duration-weighted means).
    if shared and not a.no_correct:
        pool = [m for m in measures.values() if m.get("neutral_share")]
        weight = sum(m["duration_s"] for m in pool) or 1
        mean_rgb = [sum(m["rgb"][c] * m["duration_s"] for m in pool) / weight for c in range(3)] if pool else None
        level = sum(m["light"]["level"] * m["duration_s"] for m in measures.values()) / (sum(m["duration_s"] for m in measures.values()) or 1)
        any_wb = any("white-balance" in m["recommend"] for m in measures.values())
        any_ex = any("exposure" in m["recommend"] for m in measures.values())
        common = (wb_gains(mean_rgb, grade["wbStrength"]) if mean_rgb and any_wb else None,
                  gamma_for(level) if any_ex else 1.0)

    a.dest.mkdir(parents=True, exist_ok=True)
    prev = a.dest / "corrections.json"
    kept = json.loads(prev.read_text(encoding="utf-8")).get("clips", {}) if prev.is_file() else {}
    log = {"grade": gname, "correction": "shared" if shared else "per-clip", "height": a.height, "clips": kept}
    for p in clips:
        stem, m = p.stem.upper(), measures[p.stem.upper()]
        out = a.dest / f"{stem}.mp4"
        if out.exists() and not a.force:
            print(f"keep  {out.name} (exists; --force rebuilds)")
            continue
        fix = fixes.get(stem, {})
        rec = m.get("recommend", [])
        if a.no_correct:
            gains, gamma = None, 1.0
        elif shared:
            gains, gamma = common
        else:
            gains = wb_gains(m["rgb"], grade["wbStrength"]) if "white-balance" in rec else None
            gamma = gamma_for(m["light"]["level"]) if "exposure" in rec else 1.0
        with tempfile.TemporaryDirectory() as tmp:
            trf = None
            want_stab = fix.get("stabilize") == "on" or ("stabilize" in rec and fix.get("stabilize") != "off" and not a.no_correct)
            if want_stab and stab:
                trf = Path(tmp) / "t.trf"
                pre = (insp.TONEMAP + "," if m.get("hdr") else "") + f"scale={w}:{a.height}:force_original_aspect_ratio=increase,crop={w}:{a.height}"
                run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", str(p), "-an", "-vf",
                     f"{pre},vidstabdetect=result={trf.as_posix()}:shakiness=6:accuracy=12", "-f", "null", "-"])
            elif want_stab:
                print(f"  ! {p.name}: shake measured but this ffmpeg has no libvidstab; not stabilised")
            chain, colour, done = build_chain(m, fix if not a.no_correct else {}, grade, gains, gamma, w, a.height, trf)
            print(f"proxy {p.name} -> {out.name}: " + (", ".join(done) or "no correction") + f"; grade {gname}")
            post = "unsharp=5:5:0.5:5:5:0.0,format=yuv420p"
            if colour:
                lut = Path(tmp) / "lut.png"
                colour_lut(colour, lut)
                inputs, graph = ["-i", str(p), "-i", str(lut)], f"[0:v]{chain}[v];[v][1:v]haldclut=interp=tetrahedral,{post}[out]"
            else:
                inputs, graph = ["-i", str(p)], f"[0:v]{chain},{post}[out]"
            part = Path(tmp) / out.name  # written aside and moved: a failed encode never leaves a proxy to be "kept"
            run(["ffmpeg", "-hide_banner", "-v", "error", "-y", *inputs, "-filter_complex", graph, "-map", "[out]", "-an",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(part)])
            shutil.move(str(part), out)
        log["clips"][stem] = {"source": str(p), "fps": m["proxy_fps"], "applied": done, "measured": {
            k: m.get(k) for k in ("light", "cast", "noise_psnr", "move", "speech", "hdr")}}
    (a.dest / "corrections.json").write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(clips)} clip(s) in {a.dest}; corrections.json written. Look at the result: contact_sheet.py {a.dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
