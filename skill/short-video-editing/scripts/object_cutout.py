#!/usr/bin/env python3
"""Cut ONE object (a building, a gate, a vehicle, a product) out of one frame into a transparent PNG for the `objectDrop` overlay.

    python scripts/object_cutout.py CLIP --at 5.2 --grid grid.png                      # 1. a still with a coordinate grid: look at it
    python scripts/object_cutout.py CLIP --at 5.2 --poly "0.31,0.40 0.69,0.40 0.72,0.66 0.28,0.66" \
        --out render/public/objects/CLIP_A_gate.png --preview check.png                 # 2. outline it by hand (fractions of the frame)
    python scripts/object_cutout.py CLIP --at 5.2 --model u2net.onnx --box 0.2,0.3,0.8,0.7 --out ...   # or let a model draw the outline

It prints the plan cell to paste into the Overlays table:  `src=objects/CLIP_A_gate.png; at=0.5,0.66; width=412; aspect=0.74`
(`at` = the object's bottom-centre as fractions of the 1080x1920 frame, `width` in px, `aspect` = height / width), measured on the frame the NEXT
shot starts with, so that the dropped picture and the real object in that shot sit on the same spot. CLIP may also be a still image.

Two ways to get the outline, and what each costs:
  --poly   an outline you give (3 or more x,y points, fractions of the frame, or pixels when a number is above 1.5). No model, no download, no
           licence question; the edge is anti-aliased 2x2 and feathered. The right choice for a building or a gate with straight edges.
  --model  a salient-object ONNX model (the U^2-Net family, or an IS-Net `isnet-*.onnx`: the input size is read from the model) run on the
           frame, or only on --box (x0,y0,x1,y1 as fractions: much better when the frame holds more than the object). onnxruntime comes with
           faster-whisper in the kit's venv. NO model is shipped or downloaded by the kit: the person model `u2net_human_seg.onnx` is trained on
           people and fails on buildings. Whoever supplies a model checks ITS weights licence before an ad ships (the rembg page says model
           weights carry their own licences; the IS-Net page states none for `isnet-general-use`; RMBG-2.0 needs a paid agreement). Looked for in
           $SVK_MODEL_DIR, $WHISPER_MODEL_DIR, ~/.cache/short-video-kit/models and ~/.local/share/short-video-kit/models, or give a path.
           Normalisation by file name: `isnet` -> mean 0.485,0.456,0.406 std 1 (rembg's setting); anything else -> the U^2-Net setting (std 0.229...).

--size WxH   the render frame (default 1080x1920): the clip frame is scaled to cover it and centre-cropped, as the template shows a clip.
--shrink N   pull the edge in N pixels (default 1): drops the background colour a soft edge leaves on the cutout.
--feather R  blur the edge by R px (default 1.2).
--preview P  write the whole frame with everything but the object painted magenta: look at the edge before using the PNG.
The camera: the plan's camera move at the cut changes where the object sits on screen; measure the frame as the viewer sees it, or leave the
new scene's camera on `hold` for its first 0.4 s.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _venv import ensure_venv  # noqa: E402

ensure_venv("numpy")
import numpy as np  # noqa: E402

MODEL_DIRS = [os.environ.get("SVK_MODEL_DIR", ""), os.environ.get("WHISPER_MODEL_DIR", ""),
              str(Path.home() / ".cache/short-video-kit/models"), str(Path.home() / ".local/share/short-video-kit/models")]


def ffmpeg_rgb(src: Path, t: float, vf: str, w: int, h: int) -> np.ndarray:
    cmd = ["ffmpeg", "-hide_banner", "-v", "error", "-ss", f"{t:.4f}", "-i", str(src), "-frames:v", "1", "-vf", vf,
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode or len(r.stdout) != w * h * 3:
        sys.exit(f"cannot read a frame at {t:.3f}s of {src}: {r.stderr.decode(errors='ignore')[:200]}")
    return np.frombuffer(r.stdout, np.uint8).reshape(h, w, 3)


def write_png(path: Path, arr: np.ndarray) -> None:
    h, w, c = arr.shape
    path.parent.mkdir(parents=True, exist_ok=True)
    fmt = {3: "rgb24", 4: "rgba"}[c]
    r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", fmt, "-s", f"{w}x{h}", "-i", "-", str(path)],
                       input=np.ascontiguousarray(arr).tobytes(), capture_output=True)
    if r.returncode:
        sys.exit(f"cannot write {path}: {r.stderr.decode(errors='ignore')[:200]}")


def points(text: str, w: int, h: int) -> list[tuple[float, float]]:
    pts = []
    for tok in text.replace(";", " ").split():
        try:
            x, y = (float(v) for v in tok.split(","))
        except ValueError:
            sys.exit(f'--poly: "{tok}" is not x,y')
        pts.append((x * w if x <= 1.5 else x, y * h if y <= 1.5 else y))
    if len(pts) < 3:
        sys.exit("--poly needs at least 3 points")
    return pts


def polygon_mask(pts: list[tuple[float, float]], w: int, h: int) -> np.ndarray:
    """Even-odd fill at 2x2 supersampling inside the polygon's own box: coverage 0..1 per pixel."""
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, x1 = max(0, int(min(xs)) - 2), min(w, int(max(xs)) + 3)
    y0, y1 = max(0, int(min(ys)) - 2), min(h, int(max(ys)) + 3)
    out = np.zeros((h, w), np.float32)
    if x1 <= x0 or y1 <= y0:
        return out
    X = (np.arange((x1 - x0) * 2) + 0.5) / 2 + x0
    Y = ((np.arange((y1 - y0) * 2) + 0.5) / 2 + y0)[:, None]
    inside = np.zeros((Y.shape[0], X.shape[0]), bool)
    for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
        if ay == by:
            continue
        crosses = (ay > Y) != (by > Y)
        xint = ax + (Y - ay) * (bx - ax) / (by - ay)
        inside ^= crosses & (X[None, :] < xint)
    cov = inside.reshape(y1 - y0, 2, x1 - x0, 2).mean(axis=(1, 3))
    out[y0:y1, x0:x1] = cov
    return out


def resize(a: np.ndarray, h: int, w: int) -> np.ndarray:
    """Separable bilinear resize of a float 2-D array."""
    ys = np.linspace(0, a.shape[0] - 1, h)
    xs = np.linspace(0, a.shape[1] - 1, w)
    tmp = np.stack([np.interp(xs, np.arange(a.shape[1]), row) for row in a])
    return np.stack([np.interp(ys, np.arange(a.shape[0]), tmp[:, j]) for j in range(w)], axis=1).astype(np.float32)


def blur(a: np.ndarray, r: float) -> np.ndarray:
    if r <= 0:
        return a
    k = int(max(1, round(r * 2)))
    ker = np.exp(-0.5 * (np.arange(-k, k + 1) / max(r, 1e-3)) ** 2)
    ker /= ker.sum()
    pad = np.pad(a, k, mode="edge")
    pad = np.apply_along_axis(lambda v: np.convolve(v, ker, mode="valid"), 1, pad)
    return np.apply_along_axis(lambda v: np.convolve(v, ker, mode="valid"), 0, pad)[: a.shape[0], : a.shape[1]].astype(np.float32)


def shrink(a: np.ndarray, n: int) -> np.ndarray:
    for _ in range(max(0, n)):
        p = np.pad(a, 1, mode="edge")
        a = np.minimum.reduce([p[1:-1, 1:-1], p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]])
    return a


def find_model(name: str) -> Path:
    p = Path(name)
    cands = [p] if p.parent != Path(".") or p.is_absolute() else [Path(d) / name for d in MODEL_DIRS if d] + [p]
    for c in cands:
        if c.is_file():
            return c
    sys.exit(f"model not found: {name} (looked in {', '.join(map(str, cands))}). The kit ships and downloads no object model; give --model a path to an ONNX "
             "salient-object model, or outline the object by hand with --poly. Check the model's weights licence before an ad ships.")


def model_mask(src: Path, t: float, model: Path, box: tuple[float, float, float, float] | None, w: int, h: int, base: str) -> np.ndarray:
    ensure_venv("onnxruntime")
    import onnxruntime as ort  # noqa: PLC0415

    sess = ort.InferenceSession(str(model), providers=["CPUExecutionProvider"])
    inp = sess.get_inputs()[0]
    shape = inp.shape
    side = int(shape[2]) if len(shape) == 4 and isinstance(shape[2], int) else (1024 if "isnet" in model.name.lower() else 320)
    isnet = "isnet" in model.name.lower()
    mean = np.array([0.485, 0.456, 0.406], np.float32)
    std = np.array([1.0, 1.0, 1.0] if isnet else [0.229, 0.224, 0.225], np.float32)
    bx0, by0, bx1, by1 = box if box else (0.0, 0.0, 1.0, 1.0)
    cx0, cy0 = int(bx0 * w), int(by0 * h)
    cw, ch = max(8, int(bx1 * w) - cx0), max(8, int(by1 * h) - cy0)
    crop = ffmpeg_rgb(src, t, f"{base},crop={cw}:{ch}:{cx0}:{cy0},scale={side}:{side}:flags=bilinear", side, side)
    x = (crop.astype(np.float32) / max(1.0, float(crop.max())) - mean) / std
    out = sess.run(None, {inp.name: x.transpose(2, 0, 1)[None].astype(np.float32)})[0]
    m = np.asarray(out, np.float32).reshape(out.shape[-2], out.shape[-1])
    m = (m - m.min()) / max(1e-6, float(m.max() - m.min()))
    m = np.clip((m - 0.35) / 0.3, 0.0, 1.0)  # the soft score to a firm edge
    full = np.zeros((h, w), np.float32)
    full[cy0:cy0 + ch, cx0:cx0 + cw] = resize(m, ch, cw)
    return full


def main() -> int:
    ap = argparse.ArgumentParser(description="Cut one object out of one frame into a transparent PNG (for objectDrop).")
    ap.add_argument("clip", type=Path, help="a video or a still image")
    ap.add_argument("--at", type=float, default=0.0, help="clip time (s) of the frame; the frame the next shot starts on")
    ap.add_argument("--out", type=Path, help="the PNG to write, normally under render/public/objects/")
    ap.add_argument("--poly", help='outline: "x,y x,y x,y ..." (fractions of the frame, or pixels)')
    ap.add_argument("--model", help="an ONNX salient-object model (path, or a file name looked for in the model folders)")
    ap.add_argument("--box", help="x0,y0,x1,y1 (fractions): run the model only inside this box")
    ap.add_argument("--size", default="1080x1920", help="render frame WxH (default 1080x1920)")
    ap.add_argument("--shrink", type=int, default=1)
    ap.add_argument("--feather", type=float, default=1.2)
    ap.add_argument("--grid", type=Path, help="write the frame with a coordinate grid (a line every 0.1 across, every 0.05 down; thick = 0.5) and stop")
    ap.add_argument("--preview", type=Path, help="write the frame with the background painted magenta")
    a = ap.parse_args()

    if not a.clip.is_file():
        sys.exit(f"not found: {a.clip}")
    try:
        w, h = (int(v) for v in a.size.lower().split("x"))
    except ValueError:
        sys.exit("--size is WxH, e.g. 1080x1920")
    base = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"
    rgb = ffmpeg_rgb(a.clip, a.at, base, w, h)

    if a.grid:
        g = a.grid
        r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-i", "-",
                            "-vf", f"drawgrid=w=iw/10:h=ih/20:t=2:c=red@0.6,drawgrid=w=iw/2:h=ih/2:t=5:c=white@0.9", "-frames:v", "1", str(g)],
                           input=rgb.tobytes(), capture_output=True)
        if r.returncode:
            sys.exit(f"cannot write {g}: {r.stderr.decode(errors='ignore')[:200]}")
        print(f"grid: {g}  ({w}x{h}; red lines every 0.1 of the width and 0.05 of the height, white lines at 0.5)")
        return 0

    if not a.out:
        sys.exit("--out is required (or use --grid to look first)")
    if bool(a.poly) == bool(a.model):
        sys.exit("give exactly one of --poly (an outline by hand) or --model (a salient-object ONNX model)")
    if a.poly:
        mask = polygon_mask(points(a.poly, w, h), w, h)
    else:
        box = tuple(float(v) for v in a.box.split(",")) if a.box else None
        if box and len(box) != 4:
            sys.exit("--box is x0,y0,x1,y1")
        mask = model_mask(a.clip, a.at, find_model(a.model), box, w, h, base)

    mask = blur(shrink(mask, a.shrink), a.feather)
    solid = mask > 0.03
    share = solid.mean()
    if share < 0.002:
        sys.exit(f"the outline covers {share:.2%} of the frame: nothing to cut (check the points with --grid)")
    if share > 0.8:
        print(f"WARNING: the outline covers {share:.0%} of the frame: that is a background, not an object", file=sys.stderr)
    ys, xs = np.where(mask > 0.03)
    # padded on three sides; the bottom edge of the PNG is the object's feet, which is where the overlay anchors it
    x0, x1, y0, y1 = max(0, xs.min() - 2), min(w, xs.max() + 3), max(0, ys.min() - 2), min(h, ys.max() + 1)
    rgba = np.dstack([rgb, np.round(np.clip(mask, 0, 1) * 255).astype(np.uint8)])[y0:y1, x0:x1]
    write_png(a.out, rgba)
    if a.preview:
        m = np.clip(mask, 0, 1)[..., None]
        write_png(a.preview, np.round(rgb * m + np.array([255, 0, 255]) * (1 - m)).astype(np.uint8))

    bw, bh = int(x1 - x0), int(y1 - y0)
    parts = a.out.parts
    rel = "/".join(parts[parts.index("public") + 1:]) if "public" in parts else a.out.name
    at = ((x0 + x1) / 2 / w, y1 / h)
    print(f"wrote {a.out}  ({bw}x{bh}px, {share:.1%} of the frame)")
    print(f"plan cell:  src={rel}; at={at[0]:.3f},{at[1]:.3f}; width={bw}; aspect={bh / bw:.3f}")
    print("start the overlay at (cut time - fall/fps): the next shot must begin on the frame the object touches down.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
