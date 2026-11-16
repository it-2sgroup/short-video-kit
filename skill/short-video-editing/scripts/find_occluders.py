#!/usr/bin/env python3
"""Find the moments in raw clips where something passes the lens and covers the picture: the places to hide a cut.

A "mask transition" or "shape transition" (references/transition-pack.md) is a hard cut made at the moment a foreground object (a sleeve, a
shoulder, a handrail, a pillar, a hand) fills the frame: the old shot ends under it and the new shot starts as it leaves. You cannot plan that
from a script; you have to find the frames. This script scans clips and lists them:

    python scripts/find_occluders.py CLIPS_DIR_OR_FILE [--min-cover 0.6] [--rise 0.35] [--json out.json]

A frame is "covered" by the share of its cells (an 8 x 6 grid) that are flat: a near-uniform or defocused region has almost no gradient, while the
background that was there before (a street, a market) is textured. A candidate is a stretch where that share climbs from below `--rise` to at least
`--min-cover` within 0.5 s. Per candidate: clip, `start` (the cover begins to grow), `peak` (the best frame to cut on), `end` (the picture is clear again),
the peak cover, and whether the covering mass is dark, bright or mid-grey. Cut the old shot at `peak` and start the new shot from the frame where
ITS own foreground leaves (look at it: the new shot should also begin with a covered frame, or with a fast move).

Measured at 160 x 90 grey, every frame. Not judged here: whether the thing that covers the lens looks good, or whether the two shots have a similar
cover (always look at the candidate on a contact sheet). A wall, the sky or a blurred wide shot can score high all the time: they never rise, so they
are skipped, but a clip that is flat from its first frame has no candidate.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _venv import ensure_venv  # noqa: E402

ensure_venv("numpy")
import numpy as np  # noqa: E402

EXT = {".mp4", ".mov", ".m4v", ".mkv", ".mxf", ".avi"}
W, H = 160, 90
GX, GY = 8, 6


def fps_of(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    try:
        a, b = r.stdout.strip().split("/")
        return float(a) / float(b)
    except (ValueError, ZeroDivisionError):
        return 30.0


def frames(path: Path) -> np.ndarray:
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-an", "-vf", f"scale={W}:{H}:flags=area,format=gray", "-fps_mode", "passthrough", "-f", "rawvideo", "-"], capture_output=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(-1, H, W).astype(np.float32)


def cover_series(f: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per frame: the share of flat cells, and the mean luma of the flat cells (0..1)."""
    gx = np.abs(np.diff(f, axis=2))[:, :-1, :]
    gy = np.abs(np.diff(f, axis=1))[:, :, :-1]
    g = gx + gy  # (n, H-1, W-1)
    ch, cw = (H - 1) // GY, (W - 1) // GX
    cells = g[:, : ch * GY, : cw * GX].reshape(len(f), GY, ch, GX, cw).mean(axis=(2, 4))  # (n, GY, GX)
    luma = f[:, : ch * GY, : cw * GX].reshape(len(f), GY, ch, GX, cw).mean(axis=(2, 4)) / 255.0
    ref = max(float(np.percentile(cells, 75)), 1.0)  # what "textured" means in this clip
    flat = cells < ref * 0.18
    share = flat.mean(axis=(1, 2))
    lum = np.where(flat.sum(axis=(1, 2)) > 0, (luma * flat).sum(axis=(1, 2)) / np.maximum(flat.sum(axis=(1, 2)), 1), 0.0)
    return share, lum


def candidates(share: np.ndarray, lum: np.ndarray, fps: float, min_cover: float, rise: float) -> list[dict]:
    out: list[dict] = []
    n = len(share)
    win = max(2, int(0.5 * fps))
    i = 0
    while i < n:
        if share[i] >= min_cover:
            j = i
            while j + 1 < n and share[j + 1] >= min_cover * 0.8:
                j += 1
            lo = int(max(0, i - win))
            if share[lo:i + 1].min() <= rise:  # it climbed from a textured picture: something came in
                k = i + int(np.argmax(share[i:j + 1]))
                s = i
                while s > lo and share[s - 1] > rise:
                    s -= 1
                e = j
                while e + 1 < n and share[e + 1] > rise:
                    e += 1
                m = float(lum[k])
                out.append({"start": round(s / fps, 3), "peak": round(k / fps, 3), "end": round(e / fps, 3), "cover": round(float(share[k]), 2),
                            "tone": "dark" if m < 0.3 else "bright" if m > 0.65 else "mid"})
            i = j + 1
        else:
            i += 1
    return out


def clips_in(p: Path) -> list[Path]:
    return [p] if p.is_file() else sorted(f for f in p.rglob("*") if f.suffix.lower() in EXT)


def main() -> int:
    ap = argparse.ArgumentParser(description="List the moments where a foreground object covers the lens: places to hide a cut (mask / shape transitions).")
    ap.add_argument("path", help="a clip or a folder of clips")
    ap.add_argument("--min-cover", type=float, default=0.6, help="share of flat cells that counts as covered (default 0.6)")
    ap.add_argument("--rise", type=float, default=0.35, help="the share the picture must have been below within 0.5 s before (default 0.35)")
    ap.add_argument("--min-len", type=float, default=0.1, help="shortest stretch in seconds (default 0.1: one to three black or white frames are flashes, not objects)")
    ap.add_argument("--json", help="write the candidates here")
    a = ap.parse_args()
    files = clips_in(Path(a.path))
    if not files:
        print(f"no clips under {a.path}", file=sys.stderr)
        return 2
    result: list[dict] = []
    for f in files:
        fr = frames(f)
        if len(fr) < 8:
            print(f"{f.name}: could not read frames", file=sys.stderr)
            continue
        fps = fps_of(f)
        share, lum = cover_series(fr)
        found = [c for c in candidates(share, lum, fps, a.min_cover, a.rise) if c["end"] - c["start"] >= a.min_len]
        for c in found:
            c["clip"] = f.name
            result.append(c)
        print(f"{f.name}: {len(found)} candidate(s)" + "".join(f"\n  peak {c['peak']:.2f} s  ({c['start']:.2f} to {c['end']:.2f})  cover {c['cover']:.2f}  {c['tone']}" for c in found))
    if a.json:
        Path(a.json).write_text(json.dumps(result, indent=1), encoding="utf8")
        print(f"wrote {a.json}")
    print("Look at each candidate on a contact sheet before cutting on it: a flat wall or a lens cap also scores.")
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
