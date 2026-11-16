#!/usr/bin/env python3
"""Write a clip (or a stretch of it) played backwards, for a scene that must run in reverse.

Remotion plays a video forwards only, so a reverse scene needs a reversed file. This cuts the stretch with ffmpeg and reverses it
(`trim`, `reverse`, and `areverse` when the sound is kept):

    python scripts/reverse_clip.py CLIP --from 3.2 --to 7.0 --out public/clips/CLIP_REV.mp4 [--audio] [--crf 16]

Use the new file as the scene's Source with In = 0 (the plan's In reads from the start of the reversed stretch); the picture at its start is the
picture the original had at `--to`. ffmpeg's `reverse` holds every frame of the stretch in memory, so the stretch is limited to what fits in about 3 GB
(a 2880-tall 30 fps proxy: roughly 12 s): cut a long reversed move in pieces, or reverse the proxy at a smaller size. Reversed footage reads as
"reverse" only when the motion shows direction (a person walking, a pour, a door, a train moving): a static shot looks the same both ways.
Reversing flips the camera's own move too: a push-in becomes a pull-out. Sound is dropped unless `--audio`; a reversed voice or music is rarely wanted.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

LIMIT = 3.0e9  # bytes of raw frames ffmpeg may hold


def probe(path: Path) -> tuple[int, int, float]:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate", "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    try:
        w, h, rate = r.stdout.strip().split(",")
        a, b = rate.split("/")
        return int(w), int(h), float(a) / float(b)
    except ValueError:
        sys.exit(f"cannot read {path}: is it a video?")


def main() -> int:
    ap = argparse.ArgumentParser(description="Write a stretch of a clip played backwards.")
    ap.add_argument("clip")
    ap.add_argument("--from", dest="t0", type=float, default=0.0, help="start of the stretch in seconds (default 0)")
    ap.add_argument("--to", dest="t1", type=float, required=True, help="end of the stretch in seconds")
    ap.add_argument("--out", required=True)
    ap.add_argument("--audio", action="store_true", help="keep the sound, reversed too")
    ap.add_argument("--crf", type=int, default=16)
    a = ap.parse_args()
    src = Path(a.clip)
    if not src.is_file():
        sys.exit(f"no such file: {src}")
    if a.t1 <= a.t0:
        sys.exit("--to must be after --from")
    w, h, fps = probe(src)
    need = (a.t1 - a.t0) * fps * w * h * 1.5
    if need > LIMIT:
        sys.exit(f"{a.t1 - a.t0:.1f} s of {w}x{h} at {fps:g} fps is {need / 1e9:.1f} GB of raw frames, over the {LIMIT / 1e9:g} GB limit: reverse a shorter stretch "
                 f"(about {LIMIT / (fps * w * h * 1.5):.0f} s fits), or a smaller proxy.")
    vf = f"trim=start={a.t0}:end={a.t1},setpts=PTS-STARTPTS,reverse"
    cmd = ["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", str(src), "-vf", vf]
    if a.audio:
        cmd += ["-af", f"atrim=start={a.t0}:end={a.t1},asetpts=PTS-STARTPTS,areverse", "-c:a", "aac"]
    else:
        cmd += ["-an"]
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd += ["-c:v", "libx264", "-crf", str(a.crf), "-pix_fmt", "yuv420p", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode or not out.is_file():
        sys.exit(f"ffmpeg failed:\n{r.stderr[-600:]}")
    print(f"wrote {out}: {a.t1 - a.t0:.2f} s reversed (original {a.t0:g}-{a.t1:g} s). Plan: Source = {out.stem.upper()}, In = 0.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
