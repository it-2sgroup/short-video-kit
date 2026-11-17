#!/usr/bin/env python3
"""Locate and remove baked-in channel tags / watermarks from a video clip using ffmpeg delogo.

Workflow:
  1. Generate a coordinate grid frame to measure the exact tag box (x, y, w, h):
       python scripts/delogo_clip.py CLIP --grid grid.png [--time 0.5]
  2. Remove the tag(s) (and optionally deep-remix with hflip/zoom/speed/grain):
       python scripts/delogo_clip.py CLIP --box 740,1265,290,60 --out clean.mp4 [--hflip] [--zoom 1.13] [--speed 1.10] [--grain 3] [--no-audio]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_box(spec: str) -> tuple[int, int, int, int]:
    parts = [p.strip() for p in spec.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError(f"expected x,y,w,h (got {spec!r})")
    try:
        x, y, w, h = (int(p) for p in parts)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"non-integer coordinate in {spec!r}") from e
    if w <= 0 or h <= 0 or x < 0 or y < 0:
        raise argparse.ArgumentTypeError(f"invalid box dimensions in {spec!r}")
    return x, y, w, h


def probe_size(src: Path) -> tuple[int, int]:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(src)],
        capture_output=True, text=True,
    )
    try:
        w, h = (int(v) for v in r.stdout.strip().split(","))
        return w, h
    except ValueError:
        return 1080, 1920


def make_grid(src: Path, out: Path, t: float) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    w, h = probe_size(src)
    # 100x50 coordinate grid via ffmpeg drawgrid; add numeric labels when a system font is found
    vf_parts = ["drawgrid=w=100:h=50:t=1:c=red@0.8"]
    font = next((p for p in (
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/System/Library/Fonts/Helvetica.ttc"),
    ) if p.is_file()), None)
    if font is not None:
        ff_font = str(font).replace("\\", "/").replace(":", "\\:")
        for x in range(0, w, 100):
            vf_parts.append(f"drawtext=fontfile='{ff_font}':text='{x}':x={x + 3}:y=4:fontsize=18:fontcolor=yellow:box=1:boxcolor=black@0.5")
        for y in range(50, h, 100):
            vf_parts.append(f"drawtext=fontfile='{ff_font}':text='{y}':x=4:y={y + 3}:fontsize=18:fontcolor=yellow:box=1:boxcolor=black@0.5")
    r = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", str(src), "-vframes", "1", "-vf", ",".join(vf_parts), str(out)],
        capture_output=True, text=True,
    )
    if r.returncode != 0 or not out.exists():
        sys.exit(f"ffmpeg failed to write grid at {t}s: {r.stderr.strip()}")
    print(f"wrote grid frame: {out}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Locate and remove baked-in channel tags/watermarks via ffmpeg delogo.")
    ap.add_argument("clip", help="input video clip")
    ap.add_argument("--grid", help="write a 100x50px coordinate grid PNG at --time to measure box coordinates")
    ap.add_argument("--time", type=float, default=0.5, help="timestamp (s) for --grid or --check-out (default 0.5)")
    ap.add_argument("--box", action="append", type=parse_box, default=[], help="x,y,w,h box to remove with delogo (repeatable)")
    ap.add_argument("--out", help="output video path")
    ap.add_argument("--from", dest="t0", type=float, help="optional start time (s)")
    ap.add_argument("--to", dest="t1", type=float, help="optional end time (s)")
    ap.add_argument("--hflip", action="store_true", help="horizontally flip the clip before delogo (measure --grid on flipped output if needed)")
    ap.add_argument("--zoom", type=float, default=1.0, help="center-crop zoom factor (e.g. 1.13 crops 88.5%% and scales back)")
    ap.add_argument("--speed", type=float, default=1.0, help="video speed multiplier (e.g. 1.10)")
    ap.add_argument("--grain", type=float, default=0.0, help="subtle noise strength (e.g. 3)")
    ap.add_argument("--no-audio", action="store_true", help="strip original audio (-an)")
    ap.add_argument("--check-out", help="optional PNG path to save a verification frame from --out at --time")
    ap.add_argument("--crf", type=int, default=18)
    a = ap.parse_args()

    src = Path(a.clip)
    if not src.is_file():
        sys.exit(f"not found: {src}")

    if a.grid:
        return make_grid(src, Path(a.grid), a.time)

    if not a.out:
        sys.exit("give --out (or --grid to inspect coordinates)")
    if not a.box and not a.hflip and a.zoom == 1.0 and a.speed == 1.0 and a.grain == 0.0:
        sys.exit("give at least one --box x,y,w,h (or remix flags)")

    filters: list[str] = []
    if a.hflip:
        filters.append("hflip")
    if a.zoom > 1.0:
        frac = 1.0 / a.zoom
        filters.append(f"crop=iw*{frac:.4f}:ih*{frac:.4f},scale=1080:1920:flags=lanczos")
    for x, y, w, h in a.box:
        filters.append(f"delogo=x={x}:y={y}:w={w}:h={h}")
    if a.grain > 0:
        filters.append(f"noise=alls={a.grain}:allf=t")
    if a.speed != 1.0:
        filters.append(f"setpts=PTS/{a.speed:.4f}")

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-v", "error"]
    if a.t0 is not None:
        cmd += ["-ss", str(a.t0)]
    if a.t1 is not None:
        cmd += ["-to", str(a.t1)]
    cmd += ["-i", str(src)]
    if filters:
        cmd += ["-vf", ",".join(filters)]
    cmd += ["-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", str(a.crf), "-pix_fmt", "yuv420p"]
    if a.no_audio:
        cmd.append("-an")
    else:
        cmd += ["-c:a", "aac", "-b:a", "192k"]
    cmd.append(str(out))

    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"ffmpeg failed: {r.stderr.strip()}")
    print(f"wrote {out}")

    if a.check_out:
        chk = Path(a.check_out)
        chk.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", str(a.time), "-i", str(out), "-vframes", "1", str(chk)],
            check=True,
        )
        print(f"wrote check frame: {chk}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
