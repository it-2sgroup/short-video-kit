#!/usr/bin/env python3
"""Contact sheets: look at a rendered video, or at a folder of raw clips, without playing anything.

    # a rendered video: the middle of every scene plus every cut (transition centre)
    python scripts/contact_sheet.py out/kb7.mp4 --project kb7.json --out sheet.png
    # a rendered video at explicit seconds
    python scripts/contact_sheet.py out/kb7.mp4 --times 0.5,2.6,5.5 --out sheet.png
    # raw footage: one row per clip, evenly spaced frames, to build the shot log
    python scripts/contact_sheet.py /path/to/clips --out clips.png

--cols    frames per row (default 7 for a video, 8 for a folder)
--width   frame width in pixels (default 360 for a video, 200 for a folder)
--rows    folder mode: clips per sheet (default 6); more clips continue in clips_2.png, clips_3.png...
--every   folder mode: aim for one frame per this many seconds, at most --cols (default 4)

Prints which frame sits where (rows read left to right, top to bottom). Needs ffmpeg and ffprobe.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

VIDEO_EXT = {".mov", ".mp4", ".m4v", ".mkv"}


def run(*cmd: str) -> None:
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *cmd], check=True)


def duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def grab(video: Path, t: float, width: int, dest: Path) -> None:
    run("-ss", f"{max(t, 0):.3f}", "-i", str(video), "-frames:v", "1", "-vf", f"scale={width}:-2", str(dest))


def tile(frames_glob: str, cols: int, rows: int, out: Path) -> None:
    run("-framerate", "1", "-i", frames_glob, "-vf", f"tile={cols}x{rows}:padding=4:color=black",
        "-frames:v", "1", str(out))


def project_marks(project: Path) -> list[tuple[float, str]]:
    scenes = json.loads(project.read_text(encoding="utf-8"))["scenes"]
    marks: list[tuple[float, str]] = []
    for i, s in enumerate(scenes, 1):
        if i > 1:
            marks.append((s["start"], f"cut {i - 1}->{i}"))
        marks.append((round((s["start"] + s["end"]) / 2, 2), f"scene {i}"))
    return marks


def sheet_of_video(a: argparse.Namespace) -> None:
    cols, width = a.cols or 7, a.width or 360
    marks = project_marks(a.project) if a.project else [(float(t), "") for t in a.times.split(",")]
    marks.sort(key=lambda m: m[0])
    with tempfile.TemporaryDirectory() as tmp:
        for i, (t, _) in enumerate(marks, 1):
            grab(a.source, t - 0.02, width, Path(tmp) / f"f{i:03d}.png")
        a.out.parent.mkdir(parents=True, exist_ok=True)
        tile(f"{tmp}/f%03d.png", cols, -(-len(marks) // cols), a.out)
    print(f"wrote {a.out}: {len(marks)} frames, {cols} per row")
    for i, (t, label) in enumerate(marks, 1):
        print(f"  {i:2}  row {(i - 1) // cols + 1} col {(i - 1) % cols + 1}  {t:6.2f}s  {label}")


def sheets_of_clips(a: argparse.Namespace) -> None:
    cols, width, per_sheet = a.cols or 8, a.width or 200, a.rows
    clips = sorted(p for p in a.source.rglob("*") if p.suffix.lower() in VIDEO_EXT)
    if not clips:
        sys.exit(f"no video files under {a.source}")
    with tempfile.TemporaryDirectory() as tmp:
        rows: list[tuple[Path, float, list[float]]] = []
        for ci, clip in enumerate(clips):
            dur = duration(clip)
            n = min(cols, max(2, round(dur / a.every)))
            times = [round(0.3 + (dur - 0.6) * k / (n - 1), 1) for k in range(n)]
            for k, t in enumerate(times):
                grab(clip, t, width, Path(tmp) / f"c{ci:03d}_{k:02d}.png")
            tile(f"{tmp}/c{ci:03d}_%02d.png", cols, 1, Path(tmp) / f"row{ci:03d}.png")
            rows.append((clip, dur, times))
        a.out.parent.mkdir(parents=True, exist_ok=True)
        for s, first in enumerate(range(0, len(rows), per_sheet), 1):
            chunk = list(range(first, min(first + per_sheet, len(rows))))
            out = a.out if len(rows) <= per_sheet else a.out.with_name(f"{a.out.stem}_{s}{a.out.suffix}")
            if len(chunk) == 1:
                (Path(tmp) / f"row{chunk[0]:03d}.png").replace(out)
            else:
                ins = [x for ci in chunk for x in ("-i", str(Path(tmp) / f"row{ci:03d}.png"))]
                run(*ins, "-filter_complex", f"vstack=inputs={len(chunk)}", "-frames:v", "1", str(out))
            print(f"wrote {out}: {len(chunk)} clip(s), one per row")
            for r, ci in enumerate(chunk, 1):
                clip, dur, times = rows[ci]
                print(f"  row {r}  {clip.stem}  {dur:5.1f}s  frames at " + ", ".join(f"{t:g}" for t in times))


def main() -> int:
    ap = argparse.ArgumentParser(description="Contact sheet of a rendered video or a folder of raw clips.")
    ap.add_argument("source", type=Path, help="a video file, or a folder of clips")
    ap.add_argument("--project", type=Path, help="project.json: scene middles + cuts")
    ap.add_argument("--times", help="comma-separated seconds")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--cols", type=int)
    ap.add_argument("--width", type=int)
    ap.add_argument("--rows", type=int, default=6)
    ap.add_argument("--every", type=float, default=4.0)
    a = ap.parse_args()
    if a.source.is_dir():
        sheets_of_clips(a)
    elif a.project or a.times:
        sheet_of_video(a)
    else:
        ap.error("for a video file give --project or --times; for a folder of clips just pass the folder")
    return 0


if __name__ == "__main__":
    sys.exit(main())
