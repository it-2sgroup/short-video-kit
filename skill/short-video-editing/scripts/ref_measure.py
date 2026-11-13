#!/usr/bin/env python3
"""Measurements behind `analyze_reference.py`: transition family, camera path, speed, grade fingerprint, beat alignment, sound hints, silhouette hints.

Not a command: `analyze_reference.py` imports it. Everything here is numpy + ffmpeg (+ libvidstab, already checked by doctor.py):
no OCR, no model, no download. What each function returns, its thresholds and its known failure cases are written in
`references/reference-analysis.md`; the thresholds sit in the constants below so a change is one edit and one re-run of the
synthetic checks. A result that depends on a guess carries `needs_look: true`: the number says WHEN and HOW MUCH, the name of the
technique is Claude's reading of the evidence sheet.
"""
from __future__ import annotations

import math
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np

W709 = np.array([0.2126, 0.7152, 0.0722], np.float32)

# ---- thresholds (see references/reference-analysis.md for what each one separates) -------------------------------------------------
SAME_SCENE = 0.80      # correlation of 12x21 block luma of A and B above which a "transition" is movement inside one shot
CROSSFADE = 0.06       # blend residual under which the in-between frames are a mix of A and B
DISSOLVE_COH = 0.85    # neighbouring pixels agreeing on A-or-B below this = random-looking mask
WIPE_BIN = 0.10        # every pixel still exactly A or B under this = a hard-edged mask
SLIDE_BIN = 0.15       # ... after allowing each layer its own displacement (seams and resampling leave a little): a slide, cover or reveal
NOISE_BLEND = 0.20     # a random or pixel mask, seen at 96 px, looks like a partial mix: blend residual between CROSSFADE and this
WIPE_COH = 0.97        # hard-edged masks are spatially coherent
SHIFT_FRAC = 0.08      # a layer displaced by more than this share of the frame (median over the run) is sliding
MOVE_MIN = 0.03        # a camera move below 3 % zoom or 3 % of the frame width is "static"
FREEZE_DIFF = 0.0015   # mean frame change (0..1 at 64 px) under which two frames count as identical
MIN_VECTORS = 12       # vid.stab vectors a frame needs before its fit is believed
MIN_INLIERS = 0.5      # share of those vectors that agree with the fit


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, **kw)


def _luma(x: np.ndarray) -> np.ndarray:
    return x @ W709


def _blocks(l: np.ndarray, by: int = 21, bx: int = 12) -> np.ndarray:
    h, w = l.shape
    h2, w2 = h // by * by, w // bx * bx
    return l[:h2, :w2].reshape(by, h2 // by, bx, w2 // bx).mean(axis=(1, 3))


def _corr(a: np.ndarray, b: np.ndarray) -> float:
    a, b = a.ravel() - a.mean(), b.ravel() - b.mean()
    d = float(np.sqrt((a @ a) * (b @ b)))
    return float(a @ b / d) if d > 1e-6 else 1.0


def _line_costs(m: np.ndarray, a: np.ndarray) -> np.ndarray:
    """cost[d + L - 1, k] = mean abs difference of line k of `m` against line k - d of `a` (lines = rows of the 2-D arrays);
    255 where that line does not exist. d is the displacement of `a` inside `m`."""
    n = m.shape[0]
    cost = np.full((2 * n - 1, n), 255.0, np.float32)
    for d in range(-(n - 1), n):
        k0, k1 = max(0, d), min(n, n + d)
        cost[d + n - 1, k0:k1] = np.abs(m[k0:k1] - a[k0 - d:k1 - d]).mean(axis=1)
    return cost


def _pan_match(a: np.ndarray, b: np.ndarray, ab: float) -> float:
    """0..1: how well `b` is just `a` displaced along one axis (up to 40 % of the frame): 1 = a pure camera pan, 0 = unrelated pictures."""
    best = 1.0
    for aa, bb in ((a, b), (a.T, b.T)):
        n = aa.shape[0]
        cost = _line_costs(aa, bb)
        for i in range(int(0.6 * n), int(1.4 * n)):
            ok = cost[i] < 255
            if ok.sum() >= 0.6 * n:
                best = min(best, float(cost[i][ok].mean()) / ab)
    return float(np.clip(1 - best, 0, 1))


def _slide_fit(m: np.ndarray, a: np.ndarray, b: np.ndarray, ab: float) -> tuple[float, float, float, int]:
    """Best explanation of luma frame `m` as A displaced along one axis next to B displaced along the same axis.
    Returns (displacement of A, of B, residual / ab, axis) with displacements as a share of that axis (0 = x, 1 = y)."""
    best = (0.0, 0.0, 9.0, 0)
    for axis in (0, 1):
        mm, aa, bb = (m, a, b) if axis == 1 else (m.T, a.T, b.T)       # lines are rows: axis 1 = displacement along y
        n = mm.shape[0]
        cA, cB = _line_costs(mm, aa), _line_costs(mm, bb)
        cand = lambda c: sorted({n - 1, *np.argsort(-(c < 0.35 * ab).sum(axis=1))[:6].tolist()})   # noqa: E731
        for i in cand(cA):
            for j in cand(cB):
                res = float(np.minimum(cA[i], cB[j]).mean()) / ab + 0.002 * (abs(i - (n - 1)) + abs(j - (n - 1))) / n
                if res < best[2]:
                    best = ((i - (n - 1)) / n, (j - (n - 1)) / n, res, axis)
    return best


def _dir(dx: float, dy: float) -> str:
    return ("right" if dx > 0 else "left") if abs(dx) >= abs(dy) else ("down" if dy > 0 else "up")


# =====================================================================================================================================
# M1  transitions
# =====================================================================================================================================
def transition_features(fr: np.ndarray, s: int, e: int, lo: int = 0, hi: int | None = None, pad: int = 2) -> dict:
    """Features of the picture changing over frames s..e. A = the frame `pad` before s, B = the frame `pad` after e (inside lo..hi, the
    frames that belong to the same shot): the first frames of a soft change are too small to be detected. `fr` is uint8 [n,h,w,3]."""
    n = len(fr)
    hi = n - 1 if hi is None else hi
    f = lambda i: fr[min(max(i, 0), n - 1)].astype(np.float32)   # noqa: E731
    A, B = f(max(lo, s - pad)), f(min(hi, e + pad))
    h, w = A.shape[:2]
    ab = float(np.abs(A - B).mean()) + 1e-6
    lA, lB = _luma(A), _luma(B)
    abl = float(np.abs(lA - lB).mean()) + 1e-6
    inter = list(range(s, e + 1))
    lum = np.array([_luma(f(i)).mean() for i in inter]) if inter else np.array([min(lA.mean(), lB.mean())])
    k = int(0.2 * len(inter))
    mid = (inter[k: len(inter) - k] or inter)[:7]
    drift = max(float(np.abs(f(max(lo, s - pad - 3)) - A).mean()), float(np.abs(f(min(hi, e + pad + 3)) - B).mean())) / ab
    d = (A - B).ravel()
    dd = float(d @ d) + 1e-6
    blend, binr, bins, coh, cov, cen, sa, sb = [], [], [], [], [], [], [], []
    for i in mid:
        M = f(i)
        al = float(np.clip(((M - B).ravel() @ d) / dd, 0, 1))
        blend.append(float(np.abs(M - (al * A + (1 - al) * B)).mean()) / ab)
        dA, dB = np.abs(M - A).mean(axis=2), np.abs(M - B).mean(axis=2)
        binr.append(float(np.minimum(dA, dB).mean()) / ab)
        m = dB < dA
        coh.append(float(((m[:, 1:] == m[:, :-1]).mean() + (m[1:] == m[:-1]).mean()) / 2))
        c = float(m.mean())
        cov.append(c)
        if 0.05 < c < 0.95:
            ys, xs = np.nonzero(m)
            cen.append((float(xs.mean()) / w, float(ys.mean()) / h))
        da, db, res, ax = _slide_fit(_luma(M), lA, lB, abl)
        sa.append((da, 0.0) if ax == 0 else (0.0, da))
        sb.append((db, 0.0) if ax == 0 else (0.0, db))
        bins.append(res)
    sa, sb = np.array(sa, float).reshape(-1, 2), np.array(sb, float).reshape(-1, 2)
    cen_move = (cen[-1][0] - cen[0][0], cen[-1][1] - cen[0][1]) if len(cen) >= 2 else None
    return {
        "ab": round(ab / 255, 3), "same_scene": round(max(_corr(_blocks(lA), _blocks(lB)), 1.0 if (pm := _pan_match(lA, lB, abl)) >= 0.5 else 0.0), 2), "pan_match": round(pm, 2), "drift": round(drift, 2),
        "lum_a": round(float(lA.mean()), 1), "lum_b": round(float(lB.mean()), 1),
        "lum_min": round(float(lum.min()), 1), "lum_max": round(float(lum.max()), 1),
        "blend_res": round(float(np.median(blend)), 3), "bin_res": round(float(np.median(binr)), 3),
        "bin_res_shifted": round(float(np.median(bins)), 3), "coherence": round(float(np.median(coh)), 3),
        "coverage": [round(cov[0], 2), round(cov[-1], 2)],
        "mask_move": [round(cen_move[0], 2), round(cen_move[1], 2)] if cen_move else None,
        "shift_a": [round(float(np.median(sa[:, 0])), 3), round(float(np.median(sa[:, 1])), 3)],
        "shift_b": [round(float(np.median(sb[:, 0])), 3), round(float(np.median(sb[:, 1])), 3)], "mid_frames": len(mid),
    }


def classify_run(ft: dict) -> dict:
    """Family from the features. Order matters: the cheapest, most certain tests first."""
    drift_conf = float(np.clip(1 - 3 * ft["drift"], 0, 1))
    fam, direction, margin, note = "unknown", None, 0.3, ""
    la, lb = ft["lum_a"], ft["lum_b"]
    lo_ab, hi_ab = min(la, lb), max(la, lb)
    sax, say = ft["shift_a"]
    sbx, sby = ft["shift_b"]
    sa, sb = max(abs(sax), abs(say)), max(abs(sbx), abs(sby))
    if ft["lum_min"] <= max(20.0, 0.25 * lo_ab) and lo_ab - ft["lum_min"] >= 25:
        fam, margin = "dip-to-black", min(1.0, (lo_ab - ft["lum_min"]) / 80)
    elif ft["lum_max"] >= 235 and ft["lum_max"] - hi_ab >= 25:
        fam, margin = "dip-to-white", min(1.0, (ft["lum_max"] - hi_ab) / 80)
    elif ft["same_scene"] >= SAME_SCENE:
        fam, margin = "content-motion", min(1.0, (ft["same_scene"] - SAME_SCENE) * 4)
        note = "the picture before and after is the same scene: a camera move, an animated graphic or text, not a change of shot"
    elif ft["blend_res"] < CROSSFADE:
        fam, margin = "crossfade", 1 - ft["blend_res"] / CROSSFADE
    elif ft["bin_res_shifted"] <= SLIDE_BIN and max(sa, sb) >= SHIFT_FRAC:
        moving_a, moving_b = sa >= SHIFT_FRAC, sb >= SHIFT_FRAC
        if moving_a and moving_b:
            fam, direction = "slide", _dir(sax, say)
        elif moving_b:
            fam, direction = "cover", _dir(-sbx, -sby)
        else:
            fam, direction = "reveal", _dir(sax, say)
        margin = 1 - ft["bin_res_shifted"] / SLIDE_BIN
    elif (ft["coherence"] < DISSOLVE_COH and ft["bin_res"] < 0.35) or (CROSSFADE <= ft["blend_res"] < NOISE_BLEND and ft["bin_res"] >= 0.2 and ft["coherence"] < WIPE_COH):
        fam, margin = "dissolve", 0.5
        note = "random-looking mask (noise dissolve or pixelise): look at the dense sheet for the pattern"
    elif ft["bin_res"] <= WIPE_BIN and ft["coherence"] >= WIPE_COH:
        mm = ft["mask_move"]
        if mm and math.hypot(*mm) >= 0.06:
            fam, direction = "mask-wipe", _dir(*mm)
        else:
            fam, direction = "mask-iris", "centred"
            note = "a mask that grows or shrinks around a point (circle, radial, bars): the shape needs a look"
        margin = 1 - ft["bin_res"] / WIPE_BIN
    else:
        note = "no rule fits: fast-moving mask, zoom or blur transition, or both shots moving; look at the dense sheet"
    conf = round(drift_conf * min(1.0, 0.5 + margin), 2)
    look = fam in ("unknown", "content-motion", "mask-wipe", "mask-iris", "dissolve") or conf < 0.6
    return {"family": fam, "direction": direction, "confidence": conf, "needs_look": bool(look), "note": note}


def classify_cut(luma: np.ndarray, c: int) -> dict:
    """A hard cut at frame `c` (first frame of the new shot): plain, or with a dip / flash frame inside it."""
    a, b = float(luma[max(0, c - 1)]), float(luma[min(len(luma) - 1, c)])
    win = luma[max(0, c - 2): min(len(luma), c + 2)]
    if win.max() > max(a, b) + 25:
        fam, conf = "flash-cut", 0.8
    elif min(a, b) > 40 and win.min() < 0.3 * min(a, b):
        fam, conf = "dip-cut", 0.8
    else:
        fam, conf = "hard-cut", 0.9
    return {"family": fam, "direction": None, "confidence": conf, "needs_look": fam != "hard-cut", "note": ""}


# =====================================================================================================================================
# M2  camera path, M3 speed
# =====================================================================================================================================
def vidstab_vectors(video: Path, fps: float, width: int = 480) -> dict[int, np.ndarray] | None:
    """Per-frame local-motion vectors [vx, vy, fx, fy, size] from libvidstab (pass 1 only), keyed by 0-based frame index (the vectors say how frame i moved against i-1); None when it fails."""
    with tempfile.TemporaryDirectory() as td:
        r = run(["ffmpeg", "-hide_banner", "-v", "error", "-i", str(Path(video).resolve()), "-an", "-vf",
                 f"fps={fps},scale={width}:-2,vidstabdetect=result=m.trf:shakiness=5:accuracy=9:show=0:fileformat=ascii", "-f", "null", "-"],
                cwd=td)
        trf = Path(td) / "m.trf"
        if r.returncode or not trf.is_file():
            return None
        out: dict[int, np.ndarray] = {}
        for line in trf.read_text(errors="replace").splitlines():
            m = re.match(r"Frame (\d+)", line)
            if m:
                lm = re.findall(r"\(LM (-?\d+) (-?\d+) (-?\d+) (-?\d+) (\d+) ", line)
                out[int(m.group(1)) - 1] = np.array(lm, float).reshape(-1, 5)      # vid.stab counts frames from 1
    return out


def fit_similarity(lm: np.ndarray, w: float, h: float):
    """Least-squares v = t + s*(f-c) + r*(-dy, dx) over one frame's vectors, 3 passes of outlier trimming.
    Returns (tx, ty, s, r, n_vectors, inlier_share) or None. vid.stab reports the CAMERA's motion: content zoom = 1 / (1 + s)."""
    if len(lm) < 6:
        return None
    vx, vy, fx, fy = lm[:, 0], lm[:, 1], lm[:, 2] - w / 2, lm[:, 3] - h / 2
    keep = np.ones(len(lm), bool)
    p = np.zeros(4)
    for _ in range(3):
        k = int(keep.sum())
        A = np.zeros((2 * k, 4))
        b = np.zeros(2 * k)
        A[0::2] = np.c_[np.ones(k), np.zeros(k), fx[keep], -fy[keep]]
        b[0::2] = vx[keep]
        A[1::2] = np.c_[np.zeros(k), np.ones(k), fy[keep], fx[keep]]
        b[1::2] = vy[keep]
        p, *_ = np.linalg.lstsq(A, b, rcond=None)
        res = np.hypot(vx - (p[0] + p[2] * fx - p[3] * fy), vy - (p[1] + p[2] * fy + p[3] * fx))
        keep = res < max(1.0, float(np.median(res[keep])) * 2.5)
        if keep.sum() < 6:
            break
    return float(p[0]), float(p[1]), float(p[2]), float(p[3]), len(lm), float(keep.mean())


def _rdp(pts: np.ndarray, eps: float) -> list[int]:
    """Ramer-Douglas-Peucker on a polyline [n, d]: indices of the points that matter."""
    keep = {0, len(pts) - 1}
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        seg = pts[j] - pts[i]
        L2 = float(seg @ seg)
        t = np.clip(((pts[i + 1:j] - pts[i]) @ seg) / L2, 0, 1) if L2 > 0 else np.zeros(j - i - 1)
        dist = np.linalg.norm(pts[i + 1:j] - (pts[i] + t[:, None] * seg), axis=1)
        k = int(np.argmax(dist))
        if dist[k] > eps:
            keep.add(i + 1 + k)
            stack += [(i, i + 1 + k), (i + 1 + k, j)]
    return sorted(keep)


def _ease(y: np.ndarray) -> tuple[str, float]:
    """Which easing the progress curve `y` (monotone move, any scale) looks most like, and its RMS error against it."""
    if abs(y[-1] - y[0]) < 1e-9:
        return "none", 0.0
    p = (y - y[0]) / (y[-1] - y[0])
    t = np.linspace(0, 1, len(y))
    cands = {"linear": t, "ease-in": t ** 2, "ease-out": 1 - (1 - t) ** 2, "ease-in-out": t * t * (3 - 2 * t)}
    errs = {k: float(np.sqrt(np.mean((p - v) ** 2))) for k, v in cands.items()}
    best = min(errs, key=errs.get)
    return (best if errs[best] <= 0.15 else "irregular"), errs[best]


def shot_motion(vec: dict[int, np.ndarray] | None, s: int, e: int, fps: float, w: float, h: float, skip: set[int],
                diff: np.ndarray, vel_floor: float = 0.0008) -> tuple[dict, dict]:
    """(camera, speed) of the shot made of frames [s, e). `skip` = frames inside transition runs, whose vectors mean nothing."""
    cam_unknown = lambda why: {"quality": "unknown", "reason": why, "needs_look": True}   # noqa: E731
    fz = frozen_runs(diff, s, e)
    speed = {"ramp": "none", "ramp_factor": None, "profile": None, "frozen_runs": fz, "basis": "camera velocity (hypothesis)", "needs_look": bool(fz)}
    dups = float(np.mean(diff[s:e - 1] < FREEZE_DIFF)) if e - s > 8 else 0.0
    if 0.25 <= dups < 0.8 and not fz:
        speed["frame_repeat"] = round(dups, 2)
        speed["needs_look"] = True
    if vec is None:
        return cam_unknown("no libvidstab in this ffmpeg"), speed
    idx = [i for i in range(s + 1, e) if i not in skip]
    fits = {}
    for i in idx:
        lm = vec.get(i)
        ft = fit_similarity(lm, w, h) if lm is not None and len(lm) >= MIN_VECTORS else None
        if ft and ft[5] >= MIN_INLIERS:
            fits[i] = ft
    if len(fits) < max(5, 0.5 * (e - s - 1 - len(skip & set(range(s, e))))):
        return cam_unknown(f"only {len(fits)} of {e - s - 1} frames had enough trackable detail (flat, blurred or text-covered picture)"), speed
    good = np.array(sorted(fits))
    allf = np.arange(s + 1, e)
    P = np.array([fits[i][:4] for i in good])
    P = np.stack([np.interp(allf, good, P[:, c]) for c in range(4)], axis=1)      # frames without a fit: interpolated
    tx, ty, sc, rot = P[:, 0] / w, P[:, 1] / w, P[:, 2], P[:, 3]
    zoom = np.exp(-np.cumsum(np.log1p(sc)))                                        # content zoom, 1.0 at the first frame
    px, py = np.cumsum(tx), np.cumsum(ty)                                          # camera pan as a share of the frame width
    zoom, px, py = np.r_[1.0, zoom], np.r_[0.0, px], np.r_[0.0, py]        # one value per frame of the shot, 0 / 1.0 at its first frame
    pts = np.stack([zoom, px, py], axis=1)
    n = len(pts)
    t = np.arange(n) / fps
    at = [int(round(q * (n - 1))) for q in (0, 0.25, 0.5, 0.75, 1)]
    dz, dxp, dyp = math.log(zoom[-1]), px[-1], py[-1]
    if abs(dz) >= MOVE_MIN and abs(dz) * 1.5 >= max(abs(dxp), abs(dyp)):
        driver, chan = ("zoom-in" if dz > 0 else "zoom-out"), np.log(zoom)
    elif max(abs(dxp), abs(dyp)) >= MOVE_MIN:
        driver, chan = "pan-" + _dir(dxp, dyp), px if abs(dxp) >= abs(dyp) else py
    else:
        driver, chan = "static", None
    ease, ease_err = _ease(chan) if chan is not None and n >= 6 else ("none", 0.0)
    ex = tx - np.convolve(tx, np.ones(9) / 9, mode="same")
    ey = ty - np.convolve(ty, np.ones(9) / 9, mode="same")
    shake = float(np.sqrt(np.mean(ex[4:-4] ** 2 + ey[4:-4] ** 2))) * 100 if n > 12 else 0.0
    kf = _rdp(pts, 0.01)
    if len(kf) > 8:
        kf = [kf[0]] + [kf[i] for i in np.linspace(1, len(kf) - 2, 6).astype(int)] + [kf[-1]]
    cam = {
        "quality": "ok", "driver": driver, "zoom_start": 1.0, "zoom_end": round(float(zoom[-1]), 3),
        "zoom_rate_per_s": round(dz / max(t[-1], 1e-6), 3), "pan_x": round(float(dxp), 3), "pan_y": round(float(dyp), 3),
        "curve": {"t": [round(float(t[i]), 2) for i in at], "zoom": [round(float(zoom[i]), 3) for i in at],
                  "pan_x": [round(float(px[i]), 3) for i in at], "pan_y": [round(float(py[i]), 3) for i in at]},
        "ease": ease, "ease_error": round(ease_err, 3),
        "shake": {"rms_pct": round(shake, 2), "level": "locked" if shake < 0.08 else "slight" if shake < 0.3 else "handheld"},
        "keyframes": [{"t": round(float(t[i]), 2), "zoom": round(float(zoom[i]), 3), "pan_x": round(float(px[i]), 3), "pan_y": round(float(py[i]), 3)} for i in kf],
        "vectors_per_frame": int(np.median([fits[i][4] for i in good])), "inliers": round(float(np.mean([fits[i][5] for i in good])), 2),
        "needs_look": ease == "irregular",
    }
    # speed: apparent velocity of the content (translation + half the zoom rate), smoothed over 9 frames
    ok = np.ones(len(allf), bool)
    for a, b in fz:
        ok &= ~((allf >= a) & (allf <= b))
    v = np.hypot(tx, ty) + 0.5 * np.abs(sc)
    vs = np.convolve(np.where(ok, v, 0.0), np.ones(9) / 9, mode="same")
    if n >= 24 and ok.any() and np.median(vs[ok]) >= vel_floor:
        k3 = n // 3
        v1, v3 = float(vs[:k3][ok[:k3]].mean()) if ok[:k3].any() else 0.0, float(vs[-k3:][ok[-k3:]].mean()) if ok[-k3:].any() else 0.0
        if min(v1, v3) > 1e-6:
            ratio = v3 / v1
            speed["ramp_factor"] = round(max(ratio, 1 / ratio), 2)
            if ratio >= 2:
                speed["ramp"] = "speed-up"
            elif ratio <= 0.5:
                speed["ramp"] = "slow-down"
        speed["profile"] = [round(float(vs[int(q * (n - 1))] * fps), 4) for q in np.linspace(0.1, 0.9, 8)]
        if speed["ramp"] != "none":
            speed["needs_look"] = True
            speed["note"] = "velocity change of the content: a retime, OR just an eased camera move (see camera.ease): confirm on the evidence strip"
    return cam, speed


def frozen_runs(diff: np.ndarray, s: int, e: int, min_diffs: int = 3) -> list[tuple[int, int]]:
    """Runs of identical frames inside [s, e): (first frame, last frame). A title card or a still photo is 'frozen' too."""
    out, start = [], None
    for i in range(s, e - 1):
        if diff[i] < FREEZE_DIFF:
            start = i if start is None else start
        elif start is not None:
            if i - start >= min_diffs:
                out.append((start, i))
            start = None
    if start is not None and e - 1 - start >= min_diffs:
        out.append((start, e - 1))
    return out


# =====================================================================================================================================
# M7  grade fingerprint
# =====================================================================================================================================
_M = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]], np.float32)
_WHITE = np.array([0.95047, 1.0, 1.08883], np.float32)


def srgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    c = rgb.astype(np.float32) / 255
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    xyz = (lin @ _M.T) / _WHITE
    fx = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * fx[:, 1] - 16, 500 * (fx[:, 0] - fx[:, 1]), 200 * (fx[:, 1] - fx[:, 2])], axis=1)


def palette(rgb: np.ndarray, k: int = 5, n: int = 3000) -> list[dict]:
    """k dominant colours (k-means in Lab, fixed seed): [{hex, share}] biggest first."""
    rs = np.random.RandomState(0)
    px = rgb[rs.choice(len(rgb), min(n, len(rgb)), replace=False)]
    lab = srgb_to_lab(px)
    cen = [lab[rs.randint(len(lab))]]
    for _ in range(k - 1):                                             # k-means++ start
        d = np.min([((lab - c) ** 2).sum(1) for c in cen], axis=0)
        cen.append(lab[rs.choice(len(lab), p=d / d.sum())] if d.sum() > 0 else lab[rs.randint(len(lab))])
    cen = np.array(cen)
    for _ in range(12):
        lbl = np.argmin(((lab[:, None] - cen[None]) ** 2).sum(2), axis=1)
        cen = np.array([lab[lbl == j].mean(0) if (lbl == j).any() else cen[j] for j in range(k)])
    out = []
    for j in range(k):
        m = lbl == j
        if m.any():
            r, g, b = (int(round(float(x))) for x in px[m].mean(0))
            out.append({"hex": f"#{r:02x}{g:02x}{b:02x}", "share": round(float(m.mean()), 2)})
    return sorted(out, key=lambda d: -d["share"])


def fingerprint(frames: np.ndarray) -> dict:
    """Grade statistics of uint8 frames [k,h,w,3]. Describes the picture AS GRADED: the ungraded original is unknown."""
    k, h, w, _ = frames.shape
    rgb = frames.reshape(-1, 3)
    lab = srgb_to_lab(rgb)
    luma = (rgb.astype(np.float32) @ W709) / 255
    p1, p50, p99 = (float(np.percentile(luma, q)) for q in (1, 50, 99))
    ch, cw = max(1, int(h * 0.15)), max(1, int(w * 0.15))
    lf = frames.astype(np.float32) @ W709
    corners = np.mean([lf[:, :ch, :cw].mean(), lf[:, :ch, -cw:].mean(), lf[:, -ch:, :cw].mean(), lf[:, -ch:, -cw:].mean()])
    centre = lf[:, int(h * 0.3): int(h * 0.7), int(w * 0.3): int(w * 0.7)].mean()
    return {
        "lab_mean": [round(float(x), 1) for x in lab.mean(0)], "lab_std": [round(float(x), 1) for x in lab.std(0)],
        "luma": {"p1": round(p1, 3), "p50": round(p50, 3), "p99": round(p99, 3)},
        "chroma": round(float(np.hypot(lab[:, 1], lab[:, 2]).mean()), 1),
        "warmth_b": round(float(lab[:, 2].mean()), 1), "tint_a": round(float(lab[:, 1].mean()), 1),
        "vignette": round(float(corners / max(centre, 1e-3)), 2), "palette": palette(rgb),
    }


# what a typical un-graded picture looks like: black point, white point, warmth (Lab b*). Priors, not measurements.
PRIOR = {"p1": 0.02, "p99": 0.96, "b": 5.0}


def look_effects(grades_json: Path) -> dict[str, dict]:
    """Fingerprint of every kit look applied to a neutral card (SMPTE bars + ramp), and its change against the card untouched."""
    import json
    looks = json.loads(Path(grades_json).read_text(encoding="utf-8"))["grades"]
    out, base = {}, None
    for name, g in looks.items():
        vf = (g["chain"] + "," if g.get("chain") else "") + "format=rgb24"
        r = run(["ffmpeg", "-hide_banner", "-v", "error", "-f", "lavfi", "-i", "smptehdbars=s=320x180:d=1", "-vf", vf, "-frames:v", "1",
                 "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
        if r.returncode or len(r.stdout) < 320 * 180 * 3:
            continue
        fp = fingerprint(np.frombuffer(r.stdout, np.uint8)[: 320 * 180 * 3].reshape(1, 180, 320, 3))
        base = fp if name == "none" else base
        out[name] = fp
    if base:
        for name, fp in out.items():
            fp["delta"] = {"p1": round(fp["luma"]["p1"] - base["luma"]["p1"], 3), "p99": round(fp["luma"]["p99"] - base["luma"]["p99"], 3),
                           "chroma": round(fp["chroma"] - base["chroma"], 1), "warmth_b": round(fp["warmth_b"] - base["warmth_b"], 1)}
    return out


def nearest_looks(fp: dict, effects: dict[str, dict], top: int = 3) -> list[dict]:
    """Rank the kit's looks by how well PRIOR + the look's effect on the card explains the reference's black point, white point and warmth."""
    rows = []
    for name, e in effects.items():
        d = e.get("delta", {"p1": 0, "p99": 0, "warmth_b": 0})
        dist = math.sqrt(((fp["luma"]["p1"] - PRIOR["p1"] - d["p1"]) / 0.03) ** 2 + ((fp["luma"]["p99"] - PRIOR["p99"] - d["p99"]) / 0.04) ** 2
                         + ((fp["warmth_b"] - PRIOR["b"] - d["warmth_b"]) / 6) ** 2)
        rows.append({"look": name, "distance": round(dist, 2), "effect_on_card": d})
    return sorted(rows, key=lambda r: r["distance"])[:top]


# ---- M8 beat alignment of the reference's cuts --------------------------------------------------------------------------------------
def beat_alignment(video: Path, cut_times: list[float], fps: float, prefer: tuple[float, float] = (80.0, 160.0)) -> dict | None:
    """BPM of the reference's audio (suggest_cuts.beat_grid) and the share of its cuts within +-3 frames of a beat, next to the share a
    RANDOM cut would score (2 x 3 frames over the beat period): only a share well above `chance` says the editor cut on the beat. A voice in
    the mix makes the grid noisy (`confidence` is the onset strength on the beats over the mean, minus 1)."""
    if len(cut_times) < 3:
        return None
    import suggest_cuts
    try:
        g = suggest_cuts.beat_grid(video, prefer)
    except Exception as e:                       # no audio, too short, a decoder error: the rest of the report must still be written
        return {"error": f"beat grid failed: {str(e)[:120]}"}
    beats = np.array(g["beats"]) if g["beats"] else np.array([])
    if len(beats) < 4:
        return {"bpm": g["bpm"], "confidence": g["confidence"], "cuts_on_beat": None, "note": "fewer than 4 beats found"}
    tol = 3 / fps
    hit = [bool(np.abs(beats - c).min() <= tol) for c in cut_times]
    period = 60.0 / g["bpm"]
    return {"bpm": g["bpm"], "confidence": g["confidence"], "beats": len(beats), "cuts": len(cut_times), "cuts_on_beat": round(sum(hit) / len(hit), 2),
            "chance": round(min(1.0, 2 * tol / period), 2), "within_frames": 3, "needs_look": True,
            "note": "compare cuts_on_beat with chance: near it = not cut to the beat; the grid is noisy when a voice is in the mix"}


# ---- M9 sound at known event times (hints, never "heard") ---------------------------------------------------------------------------
BANDS_HZ = {"low": (20, 200), "mid": (200, 2000), "high": (2000, 10000)}


def sound_hints(video: Path, events: list[dict], sr: int = 24000, limit: int = 80) -> list[dict] | None:
    """For each event time: how far the loudest 100 ms around it rises over its +-1 s surroundings, per band, as a z-score. A cut with a
    click or whoosh on it scores high in one band. A HINT: a voice, music or a cut that merely lands on a beat score too. Not listened to."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
    x = np.frombuffer(r.stdout, np.float32)
    if len(x) < sr:
        return None
    hop, nfft = sr // 100, 1024
    win = np.hanning(nfft).astype(np.float32)
    nfr = (len(x) - nfft) // hop
    idx = np.arange(nfft)[None] + hop * np.arange(nfr)[:, None]
    spec = np.abs(np.fft.rfft(x[idx] * win, axis=1)) ** 2
    f = np.fft.rfftfreq(nfft, 1 / sr)
    env = {k: 10 * np.log10(spec[:, (f >= lo) & (f < hi)].sum(axis=1) + 1e-12) for k, (lo, hi) in BANDS_HZ.items()}
    out = []
    for ev in sorted(events, key=lambda e: e["t"])[:limit]:
        c = int(ev["t"] * 100 + nfft / hop / 2)
        a, b = max(0, c - 2), min(nfr, c + 9)
        lo, hi = max(0, c - 100), min(nfr, c + 100)
        z = {}
        for k, e in env.items():
            base = np.concatenate([e[lo: max(lo, c - 15)], e[min(hi, c + 15): hi]])
            if len(base) < 20 or a >= b:
                z[k] = None
                continue
            z[k] = round(float((e[a:b].max() - base.mean()) / max(1.5, base.std())), 1)
        zz = [v for v in z.values() if v is not None]
        out.append({"t": round(ev["t"], 3), "kind": ev["kind"], "band_z": z, "transient": bool(zz and max(zz) >= 4.0), "hint": "hint, not listened"})
    return out


# ---- M10 matte-effect hints: a flat-colour silhouette on the first frames ----------------------------------------------------------
def silhouette_hints(frames: np.ndarray, first: int = 8, later: int = 6) -> list[dict]:
    """A one-colour region with a person-like outline (narrower at the top than at chest height) on frames 0-7 that is gone a few frames later:
    the white-silhouette flash of an agency intro. Frame numbers and colour are measurements; WHAT the shape is, is Claude's reading of the
    evidence. Text BEHIND a subject (a matte layer between text and person) cannot be detected from pixels: it needs a look."""
    n = len(frames)
    found: dict[tuple, dict] = {}
    for i in range(min(first, n)):
        im = frames[i].astype(np.int32)
        key = (im // 32) @ np.array([64, 8, 1])
        vals, cnt = np.unique(key, return_counts=True)
        for k in vals[np.argsort(-cnt)[:3]]:
            col = im[key == k].mean(axis=0)
            m = np.linalg.norm(im - col, axis=2) < 36
            share = float(m.mean())
            if not 0.04 <= share <= 0.7:
                continue
            rows = np.where(m.sum(axis=1) >= 2)[0]
            if len(rows) < 8:
                continue
            top, bot = rows[0], rows[-1]
            span = max(1, bot - top)
            widths = m.sum(axis=1).astype(float)
            w_top = widths[top: top + max(1, int(0.15 * span))].mean()
            w_mid = widths[top + int(0.35 * span): top + int(0.6 * span) + 1].mean()
            cols = np.where(m.sum(axis=0) >= 2)[0]
            person_like = bool(w_top < 0.75 * w_mid and span >= 0.9 * (cols[-1] - cols[0] + 1) and 0.1 <= share <= 0.55)
            after = frames[min(n - 1, first): min(n, first + later)].astype(np.int32)
            share_after = float(np.mean([(np.linalg.norm(a - col, axis=2) < 36).mean() for a in after])) if len(after) else 0.0
            if not person_like or share_after > 0.5 * share:
                continue
            h, w = m.shape
            ent = found.setdefault(tuple((col // 40).astype(int)), {"colour": "#%02x%02x%02x" % tuple(int(v) for v in col), "frames": [], "share": [], "bbox": [round(float(cols[0]) / w, 3), round(top / h, 3), round(float(cols[-1] - cols[0] + 1) / w, 3), round(span / h, 3)]})
            if i not in ent["frames"]:
                ent["frames"].append(i)
                ent["share"].append(round(share, 2))
    return [{"kind": "silhouette-flash", "frames": e["frames"], "colour": e["colour"], "share": e["share"], "bbox": e["bbox"], "needs_look": True,
             "note": "a flat-colour region with a head-and-shoulders outline that is gone within a few frames; confirm on the dense sheet. Text behind the subject is not detectable here"}
            for e in found.values()]
