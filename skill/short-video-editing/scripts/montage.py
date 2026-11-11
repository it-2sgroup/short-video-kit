#!/usr/bin/env python3
"""Tile any images into one labelled sheet, so a whole effect (or a before/after pair) can be judged in a single look.

`contact_sheet.py` makes a sheet from VIDEOS (the middle of every scene, every cut). This one tiles IMAGES you already have:
the stills `stills.mjs` renders, a dense run of frames pulled from a reference video, two versions of one frame side by side.

    python scripts/montage.py "out/d1_*.jpg" --cols 4 --width 360 --out out/sheet.jpg
    python scripts/montage.py a.png b.png --cols 2 --out compare.png --labels "sample,mine"

Labels: --labels "a,b,c" in order, else the number in the file name (`d1_012.50.jpg` -> 12.50: the second the still was
taken at), else the position. Frames are scaled to --width and padded to the tallest, so a 16:9 and a 9:16 image can share a sheet.
Needs only ffmpeg (the label font is looked for in the usual Windows, macOS and Linux places; no font = no labels).
Images are ordered by the number in their name (not as text), so `2.5` comes before `12.0`.
"""
from __future__ import annotations

import argparse
import glob
import re
import subprocess
import sys
from pathlib import Path

FONTS = [r"C:/Windows/Fonts/arialbd.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"]


def font() -> str | None:
    for f in FONTS:
        if Path(f).is_file():
            return f.replace(":", r"\:")   # ffmpeg filter syntax: the drive colon must be escaped
    return None


def number_in(name: str) -> float | None:
    m = re.search(r"[_-](\d+(?:\.\d+)?)\.\w+$", name)
    return float(m.group(1)) if m else None


def probe_size(f: str) -> tuple[int, int]:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", f],
                       capture_output=True, text=True)
    try:
        w, h = r.stdout.strip().split("x")
        return int(w), int(h)
    except ValueError:
        sys.exit(f"cannot read {f}: {r.stderr.strip()[:200]}")


def tile(files: list[str], out: str, cols: int = 4, width: int = 360, labels: list[str] | None = None) -> str:
    """Write the sheet; returns a one-line description. Exits with the ffmpeg error when it fails."""
    files = sorted(files, key=lambda f: (number_in(Path(f).name) is None, number_in(Path(f).name) or 0, f))
    missing = [f for f in files if not Path(f).is_file()]
    if missing:
        sys.exit("not found: " + ", ".join(missing[:5]))
    if not files:
        sys.exit("no images")
    labels = labels or []
    ft = font()
    sizes = [probe_size(f) for f in files]
    th = max(round(width * h / w / 2) * 2 for w, h in sizes)
    cmd = ["ffmpeg", "-hide_banner", "-v", "error", "-y"]
    for f in files:
        cmd += ["-i", f]
    fc, tags = [], []
    for i, f in enumerate(files):
        n = number_in(Path(f).name)
        label = labels[i] if i < len(labels) else (f"{n:g}" if n is not None else str(i + 1))
        label = re.sub(r"[^\w .:+\-]", "", label)
        chain = f"[{i}:v]scale={width}:{th}:force_original_aspect_ratio=decrease,pad={width}:{th}:(ow-iw)/2:(oh-ih)/2:color=black"
        if ft:
            chain += f",drawtext=fontfile='{ft}':text='{label}':x=6:y=6:fontsize=26:fontcolor=yellow:box=1:boxcolor=black@0.65"
        fc.append(chain + f"[v{i}]")
        tags.append(f"[v{i}]")
    n = len(files)
    layout = "|".join(f"{(i % cols) * width}_{(i // cols) * th}" for i in range(n))
    fc.append("".join(tags) + (f"xstack=inputs={n}:layout={layout}[o]" if n > 1 else "null[o]"))
    cmd += ["-filter_complex", ";".join(fc), "-map", "[o]", "-frames:v", "1", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr[-600:])
    return f"wrote {out} ({n} images, {min(cols, n)} per row{'' if ft else ', no labels: no font found'})"


def main() -> int:
    ap = argparse.ArgumentParser(description="Tile images into one labelled sheet.")
    ap.add_argument("files", nargs="+", help="image paths or quoted globs")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--width", type=int, default=360, help="width of one tile in pixels")
    ap.add_argument("--labels", help="comma-separated labels, in file order (default: the number in each file name)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    files = sorted({f for pat in a.files for f in (glob.glob(pat) or [pat])})
    print(tile(files, a.out, a.cols, a.width, [x.strip() for x in a.labels.split(",")] if a.labels else None))
    return 0


if __name__ == "__main__":
    sys.exit(main())
