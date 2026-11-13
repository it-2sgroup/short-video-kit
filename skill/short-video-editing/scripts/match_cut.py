#!/usr/bin/env python3
"""Match cut: Camera cells that make scene B open on the same screen point and size as scene A's last frame.

    python scripts/match_cut.py --a CLIP_A@7.90 --b CLIP_B@0.20                       # the subject is a person (matte)
    python scripts/match_cut.py --a CLIP_A@7.90 --b CLIP_B@0.20 --box-a 0.30,0.40,0.20,0.30 --box-b 0.55,0.20,0.15,0.24
    python scripts/match_cut.py --a a.png@0 --b b.png@0 --detect bright               # white object on a dark ground (tests)

CLIP@SECONDS is the clip and the time of the frame: A's LAST frame, B's FIRST. The subject is measured in both: the person matte
(person_matte.py, the model u2net_human_seg.onnx), or the bright blob (--detect bright), or a box you give (--box-a/--box-b, x,y,w,h as
fractions of the frame). Each gives the subject's bounding box: size = its height, centre = the middle of the box, and a lean
(the angle of its long axis from the vertical, clockwise positive).

The maths (camera of references/camera-moves.md: zoom z about the footage point `at`, screen = 0.5 + (p - at) * z):
    z2 = z1 * s1 / s2                              B's zoom, so the subject is as big on screen as at the end of A
    at2 = c2 - (p1 - 0.5) / z2, p1 = 0.5 + (c1 - at1) * z1     B's centre, so its subject sits where A's ended
    roll2 = (lean1 + roll1) - lean2                B's lean, clamped to +-3 deg (a bigger roll reads as a tilt, not as a match)
`at` is clamped so the frame edge stays covered (the renderer does the same), and the zoom stays within [1, --max-zoom 1.5]: past 1.5 the
proxy is soft (references/camera-moves.md). When the exact match is out of reach the script says WHICH limit stopped it, the error left
over, and what to change instead (zoom A's end, or pick another B frame). A's own end state is --zoom-a / --at-a (default: no move).

Prints the Camera cell for B (`keys 0=Z@X,Y roll R ; 0.4=... ; 1=--then`) ready for the edit plan, and how close the match gets. A tool cannot
see taste: look at the two frames side by side (montage.py) and at the cut in motion before keeping it.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _venv import ensure_venv  # noqa: E402

ensure_venv()
import numpy as np  # noqa: E402

CANVAS_W, CANVAS_H = 1080, 1920


def parse_ref(s: str) -> tuple[Path, float]:
    path, _, t = s.rpartition("@")
    if not path:
        path, t = s, "0"
    return Path(path), float(t)


def box_from(mask: np.ndarray) -> dict | None:
    """Bounding box (fractions of the frame), centre, size = height, and the lean of the long axis from the vertical (clockwise +, degrees)."""
    ys, xs = np.where(mask)
    if len(xs) < 20:
        return None
    hh, ww = mask.shape
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    cov = np.cov(np.vstack([xs - xs.mean(), ys - ys.mean()]))
    vals, vecs = np.linalg.eigh(cov)
    major = vecs[:, int(np.argmax(vals))]
    lean = math.degrees(math.atan2(major[0], major[1] if major[1] != 0 else 1e-9))
    lean = (lean + 90) % 180 - 90                      # a line has no direction: fold to -90..90 from the vertical
    elong = float(np.sqrt(vals.max() / max(vals.min(), 1e-9)))
    return {"x": round(x0 / ww, 4), "y": round(y0 / hh, 4), "w": round((x1 - x0) / ww, 4), "h": round((y1 - y0) / hh, 4),
            "lean": round(lean, 1) if elong > 1.6 else None}     # a round blob has no usable axis


def grab(path: Path, t: float, size: int = 320) -> np.ndarray:
    """One frame as size x size RGB (squashed: boxes are fractions of the frame, so the aspect does not matter). A still takes no -ss."""
    import subprocess
    seek = [] if path.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".bmp") else ["-ss", f"{t:.4f}"]
    r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", *seek, "-i", str(path), "-frames:v", "1", "-vf", f"scale={size}:{size}:flags=bilinear",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    if r.returncode or len(r.stdout) != size * size * 3:
        sys.exit(f"cannot read a frame at {t:.3f}s of {path}: {r.stderr.decode(errors='ignore')[:200]}")
    return np.frombuffer(r.stdout, np.uint8).reshape(size, size, 3)


def detect(ref: tuple[Path, float], how: str, model: str | None) -> dict | None:
    import person_matte as pm
    path, t = ref
    frame = grab(path, t)
    if how == "bright":
        return box_from(frame.astype(np.float32).mean(axis=2) > 128)
    import onnxruntime as ort
    session = ort.InferenceSession(str(pm.find_model(model)), providers=["CPUExecutionProvider"])
    return box_from(pm.matte(session, frame) > 127)


def solve(A: dict, B: dict, z1: float, at1: tuple[float, float], roll1: float, max_zoom: float, use_roll: bool) -> dict:
    """The framing of B and what is left over. Boxes are dicts of x, y, w, h (fractions); sizes are heights."""
    cx = lambda b: (b["x"] + b["w"] / 2, b["y"] + b["h"] / 2)   # noqa: E731
    (c1x, c1y), (c2x, c2y) = cx(A), cx(B)
    s1, s2 = A["h"], B["h"]
    p1 = (0.5 + (c1x - at1[0]) * z1, 0.5 + (c1y - at1[1]) * z1)           # where A's subject sits on screen at its last frame
    want = z1 * s1 / s2
    z2 = min(max(want, 1.0), max_zoom)
    limits = []
    if want > max_zoom:
        limits.append(f"B's subject is {want / max_zoom:.2f}x too small for a x{max_zoom:g} zoom (it would need x{want:.2f})")
    if want < 1.0:
        limits.append(f"B's subject is already {1 / want:.2f}x bigger than A's at its end: the camera cannot zoom out below x1")
    lo, hi = 0.5 / z2, 1 - 0.5 / z2
    at2 = (c2x - (p1[0] - 0.5) / z2, c2y - (p1[1] - 0.5) / z2)
    at2c = (min(max(at2[0], lo), hi), min(max(at2[1], lo), hi))
    if abs(at2c[0] - at2[0]) > 1e-4 or abs(at2c[1] - at2[1]) > 1e-4:
        limits.append("the centre point had to stay inside the frame (the edge must stay covered), so B's subject cannot reach A's screen point")
    got = (0.5 + (c2x - at2c[0]) * z2, 0.5 + (c2y - at2c[1]) * z2)
    roll2, roll_note = 0.0, None
    if use_roll and A["lean"] is not None and B["lean"] is not None:
        r = (A["lean"] + roll1) - B["lean"]
        roll2 = max(-3.0, min(3.0, r))
        roll_note = f"lean A {A['lean']:+.1f}, B {B['lean']:+.1f}" + (f"; the {r:+.1f} deg needed was clamped to {roll2:+.1f}" if roll2 != r else "")
    return {"zoom": round(z2, 3), "at": [round(at2c[0], 3), round(at2c[1], 3)], "roll": round(roll2, 1) if roll2 else 0.0,
            "wanted_zoom": round(want, 3), "size_error_pct": round((s2 * z2 / (s1 * z1) - 1) * 100, 1),
            "position_error_px": [round((got[0] - p1[0]) * CANVAS_W), round((got[1] - p1[1]) * CANVAS_H)],
            "screen_A": [round(p1[0], 3), round(p1[1], 3)], "limits": limits, "roll_note": roll_note,
            "a_end_zoom_for_exact_match": round(max(1.0, s2 / s1 * 1.0), 3) if want < 1.0 else None}


def main() -> int:
    ap = argparse.ArgumentParser(description="Camera cells so scene B opens on the same screen point and size as scene A's last frame.")
    ap.add_argument("--a", required=True, help="CLIP@SECONDS: A's last frame")
    ap.add_argument("--b", required=True, help="CLIP@SECONDS: B's first frame")
    ap.add_argument("--box-a", help="x,y,w,h of A's subject (fractions): skips detection")
    ap.add_argument("--box-b", help="x,y,w,h of B's subject (fractions): skips detection")
    ap.add_argument("--detect", choices=["person", "bright"], default="person", help="person = the matte (needs the model: ./setup.sh --person-model); bright = pixels above mid-grey")
    ap.add_argument("--model", help="path to u2net_human_seg.onnx")
    ap.add_argument("--zoom-a", type=float, default=1.0, help="A's zoom at its last frame (default 1: no move)")
    ap.add_argument("--at-a", default="0.5,0.5", help="A's camera centre at its last frame, X,Y (default 0.5,0.5)")
    ap.add_argument("--roll-a", type=float, default=0.0)
    ap.add_argument("--max-zoom", type=float, default=1.5, help="footage limit (default 1.5: references/camera-moves.md)")
    ap.add_argument("--no-roll", action="store_true", help="never propose a roll")
    ap.add_argument("--then", type=float, default=1.0, help="B's zoom at the end of the scene, after the match holds (default 1.0)")
    ap.add_argument("--json", type=Path, help="also write the result here")
    a = ap.parse_args()

    def box(arg: str | None, ref: str, tag: str) -> dict:
        if arg:
            x, y, w, h = (float(v) for v in arg.split(","))
            return {"x": x, "y": y, "w": w, "h": h, "lean": None}
        path, t = parse_ref(ref)
        if not path.is_file():
            sys.exit(f"not found: {path}")
        b = detect((path, t), a.detect, a.model)
        if b is None:
            sys.exit(f"no subject found in {tag} ({path.name} at {t:g} s) with --detect {a.detect}: give --box-{tag.lower()} x,y,w,h")
        return b

    A, B = box(a.box_a, a.a, "A"), box(a.box_b, a.b, "B")
    at1 = tuple(float(v) for v in a.at_a.split(","))
    res = solve(A, B, a.zoom_a, at1, a.roll_a, a.max_zoom, not a.no_roll)
    print(f"A subject: box x{A['x']:.3f} y{A['y']:.3f} w{A['w']:.3f} h{A['h']:.3f}; on screen at ({res['screen_A'][0]:.3f}, {res['screen_A'][1]:.3f}) with zoom {a.zoom_a:g}")
    print(f"B subject: box x{B['x']:.3f} y{B['y']:.3f} w{B['w']:.3f} h{B['h']:.3f}")
    z, (x, y), r = res["zoom"], res["at"], res["roll"]
    roll = f" roll {r:g}" if r else ""
    print(f"\nB Camera: keys 0={z:g}@{x:g},{y:g}{roll} ; 0.4={z:g}@{x:g},{y:g}{roll} ; 1={a.then:g}@0.5,0.5 soft")
    print(f"          (the framing holds for the first 40 % of the scene, then relaxes to x{a.then:g}; for no relaxation: hold {z:g} focus {x:g},{y:g})")
    print(f"match: size error {res['size_error_pct']:+.1f} %, position error {res['position_error_px'][0]:+d}, {res['position_error_px'][1]:+d} px on a {CANVAS_W}x{CANVAS_H} frame"
          + (f"; {res['roll_note']}" if res["roll_note"] else ""))
    if res["limits"]:
        print("NOT EXACT: " + "; ".join(res["limits"]))
        if res["a_end_zoom_for_exact_match"]:
            print(f"  instead: end A at zoom {res['a_end_zoom_for_exact_match']:g} (a push-in on A's last second) and open B at x1, or pick a B frame where the subject is smaller")
        elif res["wanted_zoom"] > a.max_zoom:
            print("  instead: pick a B frame where the subject is bigger, end A on a wider framing (pull back its last second), or accept a size jump")
    else:
        print("exact within the footage limit.")
    if a.json:
        a.json.write_text(json.dumps({"A": A, "B": B, **res}, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
