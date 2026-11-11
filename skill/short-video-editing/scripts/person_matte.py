#!/usr/bin/env python3
"""Cut a person out of a few frames: white "silhouette" PNGs (alpha = the person) for flash and pop effects.

The opening flash of many social videos fills the speaker's outline with white for a frame, three times in a row, and
then the video starts. This writes one RGBA PNG per frame (white where the person is, transparent elsewhere) from a clip,
using a person-segmentation ONNX model (U^2-Net human segmentation, Apache-2.0, 168 MB, kept OUTSIDE the repo). It is looked for in
$SVK_MODEL_DIR, $WHISPER_MODEL_DIR, ~/.cache/short-video-kit/models and ~/.local/share/short-video-kit/models (--model names a file);
`./setup.sh --person-model` downloads it (ASK THE USER FIRST: 168 MB). onnxruntime comes with faster-whisper in the kit's venv.

    python scripts/person_matte.py clip.mp4 --at 5.22 --frames 0,2,4 --fps 30 --out render/public/mattes/C5074 [--size 1080x1920]
    python scripts/person_matte.py --faces "C5074@5.22,C5074@7.0,C5079@1.9" --clips render/public/clips   # where the head is

--faces    beauty-light mode: for each CLIP@SECONDS print the head as {"x","y","r"} (fractions of the frame; r = half the head width as a
           fraction of the frame width), measured on the person matte: the head is the part above the shoulders. Written to --faces-out JSON.

--at       clip time (s) of the planned cut: the frame the scene starts on (the pictures must match the flashes exactly)
--frames   frame offsets from --at, at --fps, one PNG each: out_0.png, out_2.png, out_4.png
Model: u2net_human_seg.onnx from https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net_human_seg.onnx
The matte is soft-edged (a 1.5 px blur) and slightly grown so the white fill hides the person's own edge pixels.
Not a production-grade matte (hair is approximate): it is made for a flash that lasts one frame.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _venv import ensure_venv  # noqa: E402

ensure_venv("numpy", "onnxruntime")
import numpy as np  # noqa: E402

MODEL_DIRS = [os.environ.get("SVK_MODEL_DIR", ""), os.environ.get("WHISPER_MODEL_DIR", ""),
              str(Path.home() / ".cache/short-video-kit/models"), str(Path.home() / ".local/share/short-video-kit/models")]
MODEL_FILE = "u2net_human_seg.onnx"
MEAN, STD = np.array([0.485, 0.456, 0.406], np.float32), np.array([0.229, 0.224, 0.225], np.float32)


def find_model(explicit: str | None) -> Path:
    cands = [Path(explicit)] if explicit else [Path(d) / MODEL_FILE for d in MODEL_DIRS if d]
    for c in cands:
        if c.is_file():
            return c
    sys.exit(f"model not found ({MODEL_FILE}); looked in {', '.join(map(str, cands))}. Download it with ./setup.sh --person-model "
             "(ask the user first: 168 MB from https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net_human_seg.onnx)")


def grab(video: Path, t: float, size: int = 320) -> np.ndarray:
    cmd = ["ffmpeg", "-hide_banner", "-v", "error", "-ss", f"{t:.4f}", "-i", str(video), "-frames:v", "1",
           "-vf", f"scale={size}:{size}:flags=bilinear", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode or len(r.stdout) != size * size * 3:
        sys.exit(f"cannot read a frame at {t:.3f}s of {video}: {r.stderr.decode(errors='ignore')[:200]}")
    return np.frombuffer(r.stdout, np.uint8).reshape(size, size, 3)


def matte(session, frame: np.ndarray) -> np.ndarray:
    x = (frame.astype(np.float32) / 255.0 - MEAN) / STD
    x = x.transpose(2, 0, 1)[None].astype(np.float32)
    d = session.run(None, {session.get_inputs()[0].name: x})[0][0, 0]
    d = (d - d.min()) / max(1e-6, d.max() - d.min())
    return (d * 255).astype(np.uint8)


def write_png(mask: np.ndarray, out: Path, w: int, h: int) -> None:
    """Upscale the 320x320 mask, firm up its edge, and write white RGBA with it as alpha (all in ffmpeg)."""
    cmd = ["ffmpeg", "-hide_banner", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{mask.shape[1]}x{mask.shape[0]}", "-i", "-",
           "-f", "lavfi", "-i", f"color=c=white:s={w}x{h},format=rgba",
           "-filter_complex", f"[0:v]scale={w}:{h}:flags=bicubic,gblur=sigma=2,curves=all='0/0 0.28/0 0.5/0.9 1/1',gblur=sigma=1.5,format=gray[m];[1:v][m]alphamerge",
           "-frames:v", "1", str(out)]
    r = subprocess.run(cmd, input=mask.tobytes(), capture_output=True)
    if r.returncode:
        sys.exit(f"ffmpeg failed writing {out}: {r.stderr.decode(errors='ignore')[:300]}")


def head_of(m: np.ndarray) -> dict | None:
    """Head centre and half-width from a person matte (fractions of the frame). The head is the stretch from the top of the person down to
    where the outline suddenly widens (the shoulders); long hair widens it slowly, so the cut is at 1.7x the width near the top."""
    on = m > 127
    rows = np.where(on.any(1))[0]
    if len(rows) < 12:
        return None
    top, bot = rows[0], rows[-1]
    h = max(1, bot - top)
    widths = on.sum(1).astype(float)
    ref_rows = slice(top + max(2, int(0.02 * h)), top + max(4, int(0.09 * h)))
    ref = np.median(widths[ref_rows][widths[ref_rows] > 0]) if (widths[ref_rows] > 0).any() else widths[top + 3]
    y = top + max(4, int(0.05 * h))
    while y < bot and widths[y] < 1.7 * max(ref, 3) and y < top + 0.45 * h:
        y += 1
    head_h = max(6, y - top)
    cols = np.where(on[top:top + head_h].any(0))[0]
    head_w = np.percentile(widths[top:top + head_h][widths[top:top + head_h] > 0], 90)
    cx = (cols.min() + cols.max()) / 2 if len(cols) else on[top].argmax()
    n = m.shape[0]
    return {"x": round(float(cx) / n, 4), "y": round(float(top + head_h * 0.52) / n, 4), "r": round(float(min(head_w, head_h * 1.1)) / 2 / n, 4)}


def faces_mode(a) -> int:
    import json

    import onnxruntime as ort

    session = ort.InferenceSession(str(find_model(a.model)), providers=["CPUExecutionProvider"])
    out = {}
    for item in a.faces.split(","):
        clip, _, t = item.strip().partition("@")
        path = next((p for p in (Path(a.clips or ".") / f"{clip}{ext}" for ext in (".mp4", ".MP4", ".mov", ".MOV")) if p.is_file()), None)
        if path is None:
            sys.exit(f"clip {clip} not found in {a.clips or '.'}")
        f = head_of(matte(session, grab(path, float(t))))
        out[item.strip()] = f
        print(f"{item.strip():16} {f}")
    if a.faces_out:
        Path(a.faces_out).write_text(json.dumps(out, indent=1), encoding="utf-8")
        print(f"wrote {a.faces_out}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="White silhouette PNGs of a person, for flash effects, and head positions for a beauty light.")
    ap.add_argument("video", type=Path, nargs="?")
    ap.add_argument("--faces", help="CLIP@SECONDS,CLIP@SECONDS,...: print the head position of the person in each")
    ap.add_argument("--clips", help="with --faces: the folder of clips")
    ap.add_argument("--faces-out", help="with --faces: write the result as JSON")
    ap.add_argument("--at", type=float, help="clip time (s) of the frame the scene starts on")
    ap.add_argument("--frames", default="0,2,4", help="frame offsets from --at (default 0,2,4: three one-frame flashes)")
    ap.add_argument("--fps", type=float, default=30.0)
    ap.add_argument("--out", help="output prefix: PREFIX_<offset>.png")
    ap.add_argument("--size", default="1080x1920", help="PNG size (the frame size the effect is drawn at)")
    ap.add_argument("--model", help="path to u2net_human_seg.onnx")
    a = ap.parse_args()
    if a.faces:
        return faces_mode(a)
    if a.video is None or a.at is None or not a.out:
        ap.error("video, --at and --out are required (or use --faces)")
    import onnxruntime as ort

    w, h = (int(v) for v in a.size.lower().split("x"))
    session = ort.InferenceSession(str(find_model(a.model)), providers=["CPUExecutionProvider"])
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    for off in (int(v) for v in a.frames.split(",")):
        t = a.at + off / a.fps
        m = matte(session, grab(a.video, t))
        path = out.parent / f"{out.name}_{off}.png"
        write_png(m, path, w, h)
        print(f"{path}  (clip {t:.3f}s, person covers {100 * (m > 127).mean():.0f}% of the frame)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
