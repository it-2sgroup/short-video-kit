#!/usr/bin/env python3
"""Tile any images into one labelled sheet, so a whole effect (or a before/after pair) can be judged in a single look.

`contact_sheet.py` makes a sheet from VIDEOS (the middle of every scene, every cut). This one tiles IMAGES you already have:
the stills `stills.mjs` renders, a dense run of frames pulled from a reference video, two versions of one frame side by side.

    python scripts/montage.py "out/still_*.jpg" --cols 4 --width 360 --out out/sheet.jpg
    python scripts/montage.py a.png b.png --cols 2 --out compare.png --labels "sample,mine"

Labels: --labels "a,b,c" in order, else the number in the file name (`still_012.50.jpg` -> 12.50: the second the still was
taken at), else the position. Frames are scaled to --width and padded to the tallest, so a 16:9 and a 9:16 image can share a sheet.
Needs only ffmpeg. Labels need the `drawtext` filter (ffmpeg built with libfreetype) and a font in the usual Windows, macOS or Linux
places; without either the tiles are written UNLABELLED and an index is printed instead (tile number, read left to right and top to
bottom -> label), so the tool works on every build. Images are ordered by the number in their name (not as text), so `2.5` comes
before `12.0`.
"""
from __future__ import annotations

import argparse
import glob
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

FONTS = [r"C:/Windows/Fonts/arialbd.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"]


@lru_cache(maxsize=None)
def has_filter(name: str) -> bool:
    """Is this ffmpeg built with filter `name`? (`ffmpeg -filters`, asked once per process.)"""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True)
    return any(len(p) > 1 and p[1] == name for p in (ln.split() for ln in r.stdout.splitlines()))


def font() -> str | None:
    """A font file drawtext can use, or None when there is no font OR this ffmpeg has no drawtext filter (no libfreetype)."""
    if not has_filter("drawtext"):
        return None
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


def plan(files: list[str], labels: list[str] | None = None) -> list[tuple[str, str]]:
    """(file, label) in sheet order: by the number in the file name, labels given in that order or else the number or the position."""
    files = sorted(files, key=lambda f: (number_in(Path(f).name) is None, number_in(Path(f).name) or 0, f))
    labels = labels or []
    out = []
    for i, f in enumerate(files):
        n = number_in(Path(f).name)
        out.append((f, labels[i] if i < len(labels) else (f"{n:g}" if n is not None else str(i + 1))))
    return out


def index_text(tiles: list[tuple[str, str]], cols: int) -> str:
    """The tile index for a sheet without labels: `1 (row 1 col 1) = 0.5`, one per line."""
    return "\n".join(f"  {i + 1:2}  row {i // cols + 1} col {i % cols + 1}  = {lab}" for i, (_, lab) in enumerate(tiles))


def tile(files: list[str], out: str, cols: int = 4, width: int = 360, labels: list[str] | None = None) -> str:
    """Write the sheet; returns a description (with the tile index when the build cannot draw labels). Exits with the ffmpeg error on failure."""
    missing = [f for f in files if not Path(f).is_file()]
    if missing:
        sys.exit("not found: " + ", ".join(missing[:5]))
    if not files:
        sys.exit("no images")
    tiles = plan(files, labels)
    files = [f for f, _ in tiles]
    ft = font()
    sizes = [probe_size(f) for f in files]
    th = max(round(width * h / w / 2) * 2 for w, h in sizes)
    cmd = ["ffmpeg", "-hide_banner", "-v", "error", "-y"]
    for f in files:
        cmd += ["-i", f]
    fc, tags = [], []
    for i, (f, label) in enumerate(tiles):
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
    head = f"wrote {out} ({n} images, {min(cols, n)} per row"
    if ft:
        return head + ")"
    why = "this ffmpeg has no drawtext filter" if not has_filter("drawtext") else "no font found"
    return f"{head}, no labels: {why}). Tile index, left to right, top to bottom:\n{index_text(tiles, cols)}"


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
