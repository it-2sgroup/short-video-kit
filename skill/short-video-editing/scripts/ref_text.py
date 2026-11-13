#!/usr/bin/env python3
"""Text measurements behind `analyze_reference.py`: OCR text events, caption style, font class, layout. Optional: needs RapidOCR.

Not a command: `analyze_reference.py` imports it. Without `rapidocr` and `opencv-python-headless` (./setup.sh --ocr, ~85 MB, ask first)
every function returns None and the analyzer says so; nothing else in the report depends on it. RapidOCR reads Latin Vietnamese PARTLY
(diacritics are sometimes dropped), so every STRING here is a hint for a human to correct; the boxes, the frame numbers and the colours are
measurements. What each key means and how it was checked: references/reference-analysis.md.

  text_events   M4  OCR on chosen frames (shot starts, the frame before each cut, every 0.5 s, dense ranges), boxes merged across frames by
                IoU and text, appear/disappear refined to the exact frame by a local test, the entry and exit animation from the frames
                around the stable one (fade, slide + direction, pop, typewriter, cut, unknown)
  style         M5  fill, stroke and background colour, ink height, position; for several words, the first frame each word changes colour
  font          M6  NOT a name: class features (stroke weight, serif or sans, condensed or wide) and in_kit_candidates from src/fonts.ts, with
                the crop saved as evidence. Always needs_look.
  layout        M11 where text sits against the kit's viewer-first bands
"""
from __future__ import annotations

import difflib
import re
import subprocess
from pathlib import Path

import numpy as np

INSTALL = "install: ./setup.sh --ocr"
OCR_W = 540            # OCR runs on frames this wide (a 1080-wide caption is still 20+ px tall)
REF_W = 270            # the whole video, in grey, at this width: the local appear/disappear test
HP_SIGMA = 3.0
FONTS_TS = Path(__file__).resolve().parent.parent / "assets" / "remotion-template" / "src" / "fonts.ts"
# the kit's viewer-first layout on a 1920-tall frame (CLAUDE.md): title y 236-420, captions about 1340 (58 px, 2 lines)
BANDS = [("top", 0.0, 236 / 1920), ("title", 236 / 1920, 420 / 1920), ("upper-middle", 420 / 1920, 1240 / 1920), ("caption", 1240 / 1920, 1480 / 1920),
         ("lower", 1480 / 1920, 1.0)]


def engine():
    """The OCR engine or None when rapidocr / opencv are not installed."""
    try:
        import cv2  # noqa: F401
        from rapidocr import RapidOCR
    except Exception:
        return None
    return RapidOCR(params={"Rec.lang_type": "vi"})


def available() -> bool:
    try:
        import cv2  # noqa: F401
        import rapidocr  # noqa: F401
        return True
    except Exception:
        return False


# ---------------------------------------------------------------- frames
def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True)


def read_selected(video: Path, fps: float, idxs: list[int], w: int, h: int) -> dict[int, np.ndarray]:
    """RGB frames with these numbers (the numbering of analyze_reference.read_frames), at w x h, in one pass."""
    idxs = sorted(set(idxs))
    if not idxs:
        return {}
    sel = "+".join(f"eq(n,{i})" for i in idxs)
    r = _run(["ffmpeg", "-hide_banner", "-v", "error", "-i", str(video), "-vf", f"fps={fps},select='{sel}',scale={w}:{h}:flags=area", "-fps_mode", "passthrough",
              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    a = np.frombuffer(r.stdout, np.uint8)
    k = len(a) // (w * h * 3)
    a = a[: k * w * h * 3].reshape(k, h, w, 3)
    return {i: a[j] for j, i in enumerate(idxs[:k])}


def read_gray(video: Path, fps: float, w: int, h: int, cap_bytes: float = 4e8) -> np.ndarray | None:
    """Every frame in grey at w x h (None when it would not fit in `cap_bytes`)."""
    r = _run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)])
    try:
        n = int(float(r.stdout.decode().strip()) * fps) + 2
    except ValueError:
        return None
    if n * w * h > cap_bytes:
        return None
    r = _run(["ffmpeg", "-hide_banner", "-v", "error", "-i", str(video), "-vf", f"fps={fps},scale={w}:{h}:flags=area", "-f", "rawvideo", "-pix_fmt", "gray", "-"])
    a = np.frombuffer(r.stdout, np.uint8)
    k = len(a) // (w * h)
    return a[: k * w * h].reshape(k, h, w)


def crop_native(video: Path, fps: float, idx: int, box: tuple[float, float, float, float], info: dict, margin: float = 0.25) -> np.ndarray | None:
    """One frame's crop of the text box (+ margin) at the video's own resolution, RGB."""
    W, H = info["width"], info["height"]
    x0, y0, x1, y1 = box
    mw, mh = (x1 - x0) * margin, (y1 - y0) * margin
    cx0, cy0 = max(0.0, x0 - mw), max(0.0, y0 - mh)
    cw, ch = min(1.0, x1 + mw) - cx0, min(1.0, y1 + mh) - cy0
    pw, ph = max(8, int(cw * W) // 2 * 2), max(8, int(ch * H) // 2 * 2)
    r = _run(["ffmpeg", "-hide_banner", "-v", "error", "-i", str(video), "-vf", f"fps={fps},select='eq(n,{idx})',crop={pw}:{ph}:{int(cx0 * W)}:{int(cy0 * H)}",
              "-frames:v", "1", "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    if len(r.stdout) != pw * ph * 3:
        return None
    return np.frombuffer(r.stdout, np.uint8).reshape(ph, pw, 3)


# ---------------------------------------------------------------- M4: OCR and tracks
def pick_frames(starts: list[int], n: int, fps: float, dense: list[tuple[float, float]], step: int, cap: int) -> list[int]:
    idx = set()
    ends = starts[1:] + [n]
    for s, e in zip(starts, ends):
        idx.update({min(n - 1, s + max(1, round(0.1 * fps))), max(0, e - 1), (s + e) // 2})
    idx.update(range(0, n, max(1, round(0.5 * fps))))
    for a, b in dense:
        idx.update(range(int(a * fps), min(n, int(b * fps)), max(1, step)))
    out = sorted(i for i in idx if 0 <= i < n)
    while len(out) > cap:                          # drop evenly, keep the first and last
        out = [v for k, v in enumerate(out) if k % 2 == 0 or k == len(out) - 1] if len(out) > 2 * cap else out[:: -(-len(out) // cap)]
    return out


def _norm(t: str) -> str:
    return re.sub(r"\s+", " ", t.strip().lower())


def _iou(a, b) -> float:
    iw, ih = min(a[2], b[2]) - max(a[0], b[0]), min(a[3], b[3]) - max(a[1], b[1])
    if iw <= 0 or ih <= 0:
        return 0.0
    inter = iw * ih
    return inter / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter)


def _same_text(a: str, b: str) -> bool:
    a, b = _norm(a), _norm(b)
    return difflib.SequenceMatcher(None, a, b).ratio() >= 0.5 or a.startswith(b) or b.startswith(a)


def ocr_frames(eng, frames: dict[int, np.ndarray]) -> dict[int, list[dict]]:
    out: dict[int, list[dict]] = {}
    for i, rgb in frames.items():
        res = eng(np.ascontiguousarray(rgb[:, :, ::-1]))
        boxes, txts, scores = getattr(res, "boxes", None), getattr(res, "txts", None), getattr(res, "scores", None)
        h, w = rgb.shape[:2]
        dets = []
        if boxes is not None and txts is not None:
            for b, t, s in zip(boxes, txts, scores):
                b = np.asarray(b, np.float32)
                if len(str(t).strip()) < 2 or float(s) < 0.5:
                    continue
                dets.append({"box": (float(b[:, 0].min() / w), float(b[:, 1].min() / h), float(b[:, 0].max() / w), float(b[:, 1].max() / h)), "text": str(t).strip(), "score": float(s)})
        out[i] = dets
    return out


def build_tracks(dets: dict[int, list[dict]], order: list[int]) -> list[dict]:
    """Merge detections across the sampled frames: same place (IoU) and same text. One missed sample does not end a track."""
    tracks: list[dict] = []
    for k, i in enumerate(order):
        taken = set()
        for d in sorted(dets.get(i, []), key=lambda d: -d["score"]):
            best, bi = None, 0.0
            for tr in tracks:
                if id(tr) in taken or tr["last_k"] < k - 2 or tr["closed"]:
                    continue
                v = _iou(tr["box"], d["box"])
                if v > bi and v >= 0.3 and _same_text(tr["text"], d["text"]):
                    best, bi = tr, v
            if best is None:
                best = {"dets": [], "closed": False, "box": d["box"], "text": d["text"], "last_k": k}
                tracks.append(best)
            taken.add(id(best))
            best["dets"].append({"frame": i, **d})
            best["last_k"], best["box"] = k, d["box"]
            if d["score"] >= max(x["score"] for x in best["dets"]):
                best["text"] = d["text"]
        for tr in tracks:
            if tr["last_k"] < k - 1:
                tr["closed"] = True
    return tracks


def _hp(g: np.ndarray) -> np.ndarray:
    import cv2
    g = g.astype(np.float32)
    return np.abs(g - cv2.GaussianBlur(g, (0, 0), HP_SIGMA))


def _window(box, W, H, mx: float, my: float) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    return (max(0, int((x0 - mx * w) * W)), max(0, int((y0 - my * h) * H)), min(W, int((x1 + mx * w) * W) + 1), min(H, int((y1 + my * h) * H) + 1))


def _amp(frame: np.ndarray, win) -> float:
    x0, y0, x1, y1 = win
    return float(np.percentile(_hp(frame[y0:y1, x0:x1]), 99)) if x1 - x0 > 3 and y1 - y0 > 3 else 0.0


def refine_track(G: np.ndarray, tr: dict, sample_idx: list[int], fps: float) -> dict:
    """Exact appear and disappear frames: walk outward from the detected frames while the local high-pass amplitude (the text's edges) stays
    above a level between the background's and the stable frame's. Returns frames, or the sampled ones when the picture has too little texture."""
    n, H, W = G.shape
    frames = [d["frame"] for d in tr["dets"]]
    first, last, mid = frames[0], frames[-1], frames[len(frames) // 2]
    box = tr["box"]
    win = _window(box, W, H, 0.6, 0.6)
    amp_s = _amp(G[min(mid, n - 1)], win)
    k0 = sample_idx.index(first)
    prev = sample_idx[k0 - 1] if k0 > 0 else None
    k1 = sample_idx.index(last)
    nxt = sample_idx[k1 + 1] if k1 + 1 < len(sample_idx) else None
    bg_idx = prev if prev is not None else None
    amp_bg = _amp(G[bg_idx], win) if bg_idx is not None else 0.0
    if amp_s - amp_bg < 3.0:
        return {"appear": first, "disappear": last + 1, "precision": "sampled", "amp_s": amp_s, "amp_bg": amp_bg, "mid": mid, "win": win}
    thr = amp_bg + 0.25 * (amp_s - amp_bg)
    lo = prev if prev is not None else 0
    a = first
    while a - 1 >= lo and _amp(G[a - 1], win) >= thr:
        a -= 1
    hi = nxt if nxt is not None else n
    b = last
    while b + 1 < hi and b + 1 < n and _amp(G[b + 1], win) >= thr:
        b += 1
    return {"appear": a, "disappear": b + 1, "precision": "frame" if (prev is None or a > prev) and (nxt is None or b + 1 <= nxt) else "sampled",
            "amp_s": amp_s, "amp_bg": amp_bg, "mid": mid, "win": win}


def _ink_stats(frame: np.ndarray, win, thr: float) -> tuple[float, float, float, float, float, float] | None:
    """Energy-weighted centre (x, y) and the 5-95 percentile extents (x0, x1, y0, y1) of the text edges in a window, in pixels."""
    x0, y0, x1, y1 = win
    hp = _hp(frame[y0:y1, x0:x1])
    m = hp > thr
    if m.sum() < 12:
        return None
    ys, xs = np.where(m)
    wgt = hp[m]
    cx, cy = float((xs * wgt).sum() / wgt.sum()) + x0, float((ys * wgt).sum() / wgt.sum()) + y0
    return cx, cy, float(np.percentile(xs, 3)) + x0, float(np.percentile(xs, 97)) + x0, float(np.percentile(ys, 3)) + y0, float(np.percentile(ys, 97)) + y0


def classify_motion(G: np.ndarray, rf: dict, tr: dict, enter: bool, fps: float, span: int = 24) -> dict:
    """The entry (or exit) animation, from the frames walking away from the stable one. Measures per frame, against the stable frame:
    amplitude of the text edges (fade), centre of the ink in a wide window (slide + direction), extent of the ink (pop, typewriter)."""
    n, H, W = G.shape
    x0, y0, x1, y1 = tr["box"]
    bw, bh = (x1 - x0) * W, (y1 - y0) * H
    wide = (0, max(0, int((y0 - 1.0 * (y1 - y0)) * H)), W, min(H, int((y1 + 1.0 * (y1 - y0)) * H) + 1))
    S = G[min(rf["mid"], n - 1)]
    amp_s = max(rf["amp_s"], 1e-6)
    thr = 0.3 * amp_s
    st = _ink_stats(S, rf["win"], thr)
    edge = rf["appear"] if enter else rf["disappear"] - 1
    if st is None:
        return {"family": "unknown", "needs_look": True, "note": "too little edge contrast to measure the motion"}
    seq = []
    for k in range(span):
        i = edge + k if enter else edge - k
        if not 0 <= i < n:
            break
        amp = _amp(G[i], rf["win"]) / amp_s
        ink = _ink_stats(G[i], wide, thr * max(0.4, min(1.0, amp)))
        seq.append({"i": i, "amp": amp, "ink": ink})
        if k >= 2 and amp >= 0.9 and ink and abs(ink[0] - st[0]) < 0.03 * bw and abs(ink[1] - st[1]) < 0.03 * bh and abs((ink[3] - ink[2]) / max(1.0, st[3] - st[2]) - 1) < 0.04:
            break
    amps = [s["amp"] for s in seq]
    arrive = next((k for k, s in enumerate(seq) if s["amp"] >= 0.9 and s["ink"] and abs(s["ink"][0] - st[0]) < 0.03 * bw and abs(s["ink"][1] - st[1]) < 0.03 * bh), len(seq))
    vis = [s for s in seq[: max(arrive, 1)] if s["amp"] >= 0.4 and s["ink"]]
    ox = [(s["ink"][0] - st[0]) / max(bw, 1.0) for s in vis]
    oy = [(s["ink"][1] - st[1]) / max(bh, 1.0) for s in vis]
    sx = [(s["ink"][3] - s["ink"][2]) / max(1.0, st[3] - st[2]) for s in vis]
    sy = [(s["ink"][5] - s["ink"][4]) / max(1.0, st[5] - st[4]) for s in vis]
    left = [(s["ink"][2] - st[2]) / max(bw, 1.0) for s in vis]
    ramp = len(amps) >= 3 and amps[0] <= 0.55 and arrive >= 2 and all(b >= a - 0.08 for a, b in zip(amps[: arrive + 1], amps[1: arrive + 1]))
    big_x = max((abs(v) for v in ox), default=0.0)
    big_y = max((abs(v) for v in oy), default=0.0)
    fam, note, conf = "unknown", "", 0.4
    if vis and max(big_x / 0.2, big_y / 0.5) >= 1.0 and arrive >= 1:
        k = int(np.argmax([max(abs(a) / 0.2, abs(b) / 0.5) for a, b in zip(ox, oy)]))
        vertical = abs(oy[k]) / 0.5 > abs(ox[k]) / 0.2
        d = ("from-top" if oy[k] < 0 else "from-bottom") if vertical else ("from-left" if ox[k] < 0 else "from-right")
        d = d.replace("from-", "to-") if not enter else d
        fam, note, conf = "slide", d + (" + fade" if ramp else ""), 0.8
    elif vis and min(sx) < 0.6 and abs(left[int(np.argmin(sx))]) < 0.12 and min(sy) > 0.8 and arrive >= 2:
        fam, note, conf = "typewriter", "ink grows left to right from a fixed left edge", 0.7
    elif vis and min(sx) < 0.9 and min(sy) < 0.9 and arrive >= 1:
        fam, note, conf = "pop", ("scale from %.2f" % min(sx)) + (", overshoot %.2f" % max(sx) if max(sx) > 1.04 else ""), 0.7
    elif ramp:
        fam, note, conf = "fade", f"{arrive} frames", 0.8
    elif arrive <= 1 and (amps[0] >= 0.85 if amps else True):
        fam, note, conf = "cut", "full strength on the first frame", 0.8
    return {"family": fam, "detail": note, "frames": int(arrive), "confidence": conf, "needs_look": conf < 0.75 or fam == "unknown"}


# ---------------------------------------------------------------- M5: style
def _hex(c) -> str:
    return "#%02x%02x%02x" % tuple(int(round(float(v))) for v in c)


def style_of(crop: np.ndarray) -> dict | None:
    """Fill, stroke and background colour of a text crop (native resolution): the background is the border ring, the ink everything far from
    it; two ink colours split into fill (deeper inside the strokes) and stroke (the outer skin)."""
    import cv2
    h, w, _ = crop.shape
    ring = np.concatenate([crop[:2].reshape(-1, 3), crop[-2:].reshape(-1, 3), crop[:, :2].reshape(-1, 3), crop[:, -2:].reshape(-1, 3)]).astype(np.float32)
    bg = np.median(ring, axis=0)
    d = np.linalg.norm(crop.astype(np.float32) - bg, axis=2)
    m = d > 70
    if m.sum() < 30:
        return None
    px = crop[m].astype(np.float32)
    sub = px[:: max(1, len(px) // 4000)]
    _, labels, centres = cv2.kmeans(sub, 2, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0), 3, cv2.KMEANS_PP_CENTERS)
    dt = cv2.distanceTransform(m.astype(np.uint8), cv2.DIST_L2, 3)
    far = np.linalg.norm(crop.astype(np.float32)[:, :, None, :] - centres[None, None], axis=3).argmin(axis=2)
    depth = [float(dt[m & (far == k)].mean()) if (m & (far == k)).any() else 0.0 for k in range(2)]
    share = [float((m & (far == k)).sum()) / max(1, m.sum()) for k in range(2)]
    two = float(np.linalg.norm(centres[0] - centres[1])) > 60 and min(share) > 0.08
    fill_k = int(np.argmax(depth))
    ys, xs = np.where(m)
    return {"fill": _hex(centres[fill_k]), "stroke": _hex(centres[1 - fill_k]) if two else None, "background": _hex(bg),
            "stroke_share": round(share[1 - fill_k], 2) if two else 0.0, "ink_height_px": int(ys.max() - ys.min() + 1), "_fill_rgb": centres[fill_k], "_mask": m,
            "_fill_mask": m & (far == fill_k) if two else m}


def word_highlights(video: Path, fps: float, ev: dict, info: dict, style: dict, words: list[str]) -> dict | None:
    """For a multi-word line shown for a while: the first frame each word's ink changes colour (karaoke, pop) from the native crops of every frame."""
    t0, t1 = ev["t_in"], ev["t_out"]
    x0, y0, x1, y1 = ev["bbox_xyxy"]
    W, H = info["width"], info["height"]
    pw, ph = max(8, int((x1 - x0) * W) // 2 * 2), max(8, int((y1 - y0) * H) // 2 * 2)
    nfr = min(120, max(1, round((t1 - t0) * fps)))
    r = _run(["ffmpeg", "-hide_banner", "-v", "error", "-ss", f"{t0:.3f}", "-i", str(video), "-vf", f"fps={fps},crop={pw}:{ph}:{int(x0 * W)}:{int(y0 * H)}", "-frames:v", str(nfr),
              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    a = np.frombuffer(r.stdout, np.uint8)
    k = len(a) // (pw * ph * 3)
    if k < 4:
        return None
    fr = a[: k * pw * ph * 3].reshape(k, ph, pw, 3).astype(np.float32)
    ring = np.concatenate([fr[0][:2].reshape(-1, 3), fr[0][-2:].reshape(-1, 3), fr[0][:, :2].reshape(-1, 3), fr[0][:, -2:].reshape(-1, 3)])
    bg = np.median(ring, axis=0)
    ink0 = (np.linalg.norm(fr[0] - bg, axis=2) > 70).any(axis=0)
    inkall = np.zeros(pw, bool)
    for f in fr[:: max(1, k // 8)]:
        inkall |= (np.linalg.norm(f - bg, axis=2) > 70).any(axis=0)
    cols = inkall | ink0
    gap = max(3, int(0.3 * ph))
    segs, s, run = [], None, 0
    for x, on in enumerate(np.append(cols, False)):
        if on:
            if s is None:
                s = x
            run = 0
        elif s is not None:
            run += 1
            if run >= gap or x == pw:
                segs.append((s, x - run))
                s = None
    if len(segs) != len(words):                  # no clean gaps: split the ink span in proportion to the letters
        xs = np.where(cols)[0]
        if len(xs) == 0:
            return None
        tot = sum(len(w) for w in words)
        edges = np.cumsum([0] + [len(w) for w in words]) / tot * (xs.max() - xs.min()) + xs.min()
        segs = [(int(edges[j]), int(edges[j + 1])) for j in range(len(words))]
    cols_rgb = []
    for sx0, sx1 in segs:
        series = []
        for f in fr:
            seg = f[:, sx0: sx1 + 1]
            dd = np.linalg.norm(seg - bg, axis=2)
            ink = dd > 70
            series.append(np.median(seg[ink], axis=0) if ink.sum() > 6 else None)
        cols_rgb.append(series)
    out_words, changed_last = [], 0
    for word, series in zip(words, cols_rgb):
        base = next((c for c in series if c is not None), None)
        first = None
        if base is not None:
            for j in range(len(series) - 1):
                if series[j] is not None and series[j + 1] is not None and np.linalg.norm(series[j] - base) > 60 and np.linalg.norm(series[j + 1] - base) > 60:
                    first = j
                    break
        last = series[-1]
        persists = bool(first is not None and last is not None and base is not None and np.linalg.norm(last - base) > 60)
        changed_last += persists
        out_words.append({"word": word, "frame": first, "t": round(ev["t_in"] + first / fps, 3) if first is not None else None, "colour": _hex(series[first]) if first is not None else None})
    seen = [w for w in out_words if w["frame"] is not None]
    if not seen:
        return {"mode": "none", "words": out_words, "needs_look": False}
    mode = "karaoke" if changed_last >= max(1, int(0.6 * len(seen))) else "active-word"
    return {"mode": mode, "words": out_words, "needs_look": False, "note": "colour change per word, from the native crops; `pop` (a scale change) is not separated here"}


# ---------------------------------------------------------------- M6: font class
def kit_fonts() -> list[dict]:
    try:
        src = FONTS_TS.read_text(encoding="utf-8")
    except OSError:
        return []
    return [{"id": m[1], "mood": m[2], "ratio": float(m[3])} for m in re.finditer(r'id:\s*"([a-z0-9-]+)",\s*mod:\s*\w+,\s*mood:\s*"(\w+)",\s*ratio:\s*([\d.]+)', src)]


def font_class(crop: np.ndarray, st: dict, text: str) -> dict | None:
    """Class features of the lettering, never a font name. Measured on the fill mask: stroke width over ink height, vertical-stem over
    horizontal-stroke thickness (contrast: serifs and didones are high), ink share at the baseline over mid-height (serif feet), the width
    of the letters over their height (condensed or wide)."""
    import cv2
    m = st["_fill_mask"].astype(np.uint8)
    ys, xs = np.where(m)
    if len(ys) < 80:
        return None
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    m = m[y0:y1, x0:x1]
    h, w = m.shape
    dt = cv2.distanceTransform(m, cv2.DIST_L2, 3)
    stroke = 2 * float(np.percentile(dt[dt > 0], 95))
    n, _, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    comps = [s for s in stats[1:] if s[3] >= 0.6 * h and s[2] >= 2]
    aspect = float(np.median([s[2] / s[3] for s in comps])) if comps else None
    hr = [len(r) for row in m for r in re.findall(r"1+", "".join(map(str, row.tolist())))]
    vr = [len(r) for col in m.T for r in re.findall(r"1+", "".join(map(str, col.tolist())))]
    contrast = float(np.median(hr) / max(1.0, np.median(vr))) if hr and vr else None
    band = max(2, h // 10)
    foot = float(m[h - band:].mean() / max(1e-6, m[h // 2 - band // 2: h // 2 + band // 2 + 1].mean()))
    ratio = stroke / h
    weight = "light" if ratio < 0.10 else "regular" if ratio < 0.15 else "bold" if ratio < 0.22 else "black"
    serif = bool((contrast is not None and contrast >= 1.6) or foot >= 1.45)
    width = "unknown" if aspect is None else "condensed" if aspect < 0.5 else "wide" if aspect > 0.85 else "normal"
    cls = "serif" if serif else "sans"
    fonts = kit_fonts()
    want = {"serif": {"serif"}, "condensed": {"condensed"}, "wide": {"bold", "retro"}}.get("serif" if serif else width, {"bold", "rounded", "tech"})
    cand = [f["id"] for f in fonts if f["mood"] in want and (width != "wide" or f["ratio"] >= 0.6)]
    return {"class": cls, "width": width, "weight": weight, "stroke_ratio": round(ratio, 3), "letter_aspect": round(aspect, 2) if aspect else None,
            "contrast_vh": round(contrast, 2) if contrast else None, "foot_ratio": round(foot, 2), "in_kit_candidates": cand[:8], "needs_look": True,
            "note": "class features only, not a font name: open the evidence crop and compare with the candidates"}


# ---------------------------------------------------------------- M11: layout
def layout(events: list[dict], dur: float) -> dict:
    """Seconds of text exposure by y band of the frame (box centre), against the kit's viewer-first bands."""
    share = {b[0]: 0.0 for b in BANDS}
    for e in events:
        cy = e["bbox"][1] + e["bbox"][3] / 2
        band = next(b[0] for b in BANDS if b[1] <= cy < b[2] or b[2] >= 1.0 and cy >= b[1])
        e["band"] = band
        share[band] += max(0.0, e["t_out"] - e["t_in"])
    tot = sum(share.values()) or 1.0
    return {"bands": [{"band": b[0], "y_from": round(b[1], 3), "y_to": round(b[2], 3), "seconds": round(share[b[0]], 2), "share": round(share[b[0]] / tot, 2)} for b in BANDS],
            "kit": "viewer-first: title hugs the top edge (y 236-420 of 1920), captions in the lower third (y about 1340), the middle belongs to the footage",
            "middle_share": round(share["upper-middle"] / tot, 2)}


# ---------------------------------------------------------------- the whole of M4/M5/M6/M11
def analyze_text(video: Path, info: dict, fps: float, n: int, starts: list[int], dense: list[tuple[float, float]], step: int, out: Path, cap: int = 160) -> dict:
    eng = engine()
    if eng is None:
        return {"available": False, "install": INSTALL, "text_events": [], "layout": None, "note": "OCR is optional: " + INSTALL + " (RapidOCR + OpenCV, ~85 MB: ask first)"}
    W, H = info["width"], info["height"]
    oh = max(2, round(OCR_W * H / W / 2) * 2)
    idxs = pick_frames(starts, n, fps, dense, step, cap)
    dets: dict[int, list[dict]] = {}
    for k in range(0, len(idxs), 24):
        dets.update(ocr_frames(eng, read_selected(video, fps, idxs[k: k + 24], OCR_W, oh)))
    tracks = [t for t in build_tracks(dets, idxs) if len(t["dets"]) >= 1]
    rh = max(2, round(REF_W * H / W / 2) * 2)
    G = read_gray(video, fps, REF_W, rh)
    events = []
    (out / "text").mkdir(exist_ok=True)
    for tr in sorted(tracks, key=lambda t: t["dets"][0]["frame"]):
        rf = refine_track(G, tr, idxs, fps) if G is not None else {"appear": tr["dets"][0]["frame"], "disappear": tr["dets"][-1]["frame"] + 1, "precision": "sampled"}
        bx = tr["box"]
        best = max(tr["dets"], key=lambda d: d["score"])
        ev = {"id": f"tx{len(events) + 1:02d}", "text": tr["text"], "text_needs_human": True, "lang": "vi", "conf": round(float(np.mean([d["score"] for d in tr["dets"]])), 2),
              "bbox": [round(bx[0], 4), round(bx[1], 4), round(bx[2] - bx[0], 4), round(bx[3] - bx[1], 4)], "bbox_xyxy": [round(v, 4) for v in bx],
              "frame_in": int(rf["appear"]), "frame_out": int(rf["disappear"]), "t_in": round(rf["appear"] / fps, 3), "t_out": round(rf["disappear"] / fps, 3),
              "precision": rf["precision"], "detections": len(tr["dets"]), "text_variants": len({_norm(d["text"]) for d in tr["dets"]})}
        if G is not None and rf["precision"] == "frame":
            ev["motion_in"], ev["motion_out"] = classify_motion(G, rf, tr, True, fps), classify_motion(G, rf, tr, False, fps)
        else:
            ev["motion_in"] = ev["motion_out"] = {"family": "unknown", "needs_look": True, "note": "no frame-exact refinement (too little texture, or sampled only)"}
        ev["needs_look"] = bool(ev["motion_in"]["needs_look"] or ev["precision"] != "frame" or ev["conf"] < 0.8)
        events.append(ev)
    # style, highlight and font class: native crops, the first 40 events
    feats = {}
    kit_words = 0
    for ev in events[:40]:
        best = max((t for t in tracks if t["text"] == ev["text"]), key=lambda t: len(t["dets"]), default=None)
        if best is None:
            continue
        d = max(best["dets"], key=lambda d: d["score"])
        crop = crop_native(video, fps, d["frame"], d["box"], info, 0.25)
        if crop is None:
            continue
        st = style_of(crop)
        if st is None:
            continue
        ev["style"] = {"fill": st["fill"], "stroke": st["stroke"], "background": st["background"], "ink_height_frac": round(ev["bbox"][3], 4),
                       "size_frac_est": round(ev["bbox"][3] / 0.72, 4), "centre_x": round(ev["bbox"][0] + ev["bbox"][2] / 2, 3), "bottom_y": round(ev["bbox"][1] + ev["bbox"][3], 3),
                       "needs_look": True, "note": "ink height includes accents; size is an estimate"}
        words = ev["text"].split()
        if len(words) >= 2 and ev["t_out"] - ev["t_in"] >= 0.5:
            hl = word_highlights(video, fps, ev, info, st, words)
            if hl:
                ev["style"]["highlight"] = hl
        if len(re.sub(r"\W", "", ev["text"])) >= 4 and kit_words < 12:
            fc = font_class(crop, st, ev["text"])
            if fc:
                import cv2
                name = f"text/{ev['id']}_crop.png"
                cv2.imwrite(str(out / name), np.ascontiguousarray(crop[:, :, ::-1]))
                ev["font"] = {**fc, "evidence": name}
                kit_words += 1
    return {"available": True, "frames_ocr": len(idxs), "text_events": events, "layout": layout(events, n / fps),
            "note": "strings are OCR hints (Vietnamese diacritics are sometimes lost): correct them by hand; boxes, frames and colours are measurements"}
