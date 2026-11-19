#!/usr/bin/env python3
"""Check where the text of a project sits: text against text, captions, a speaker's head, TikTok's right rail and the frame edge.

The renderer draws every overlay on its own, so two text blocks (or a block and the captions) that share a place and a time are drawn on top
of each other. Every position is known from the plan, so this finds the collisions without rendering:

    python scripts/layout_check.py project.json [--strict]

`plan_to_project.py` runs it after every build and prints the result in its sync report. A `textbox` has an exact rectangle (its `box`; when
the box has no height, the height is estimated from the text length and size). `phrase` (with `y`), `pill` and `tag`-like blocks are
ESTIMATED from their size and text length, so those are marked "about". Captions use the project's caption windows and bands (a band with
Top `hide` shows none); the head of a scene is its `face` (x, y, r). All of it is advisory: exit 0, or 1 with --strict.
Needs only Python 3.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

W, H = 1080, 1920
CAPTION_TOP = {"feed": 1340, "reels-ad": 1100}
CAPTION_SIZE = 58
CAPTION_X = (90, W - 190)
RAIL_X, RAIL_Y = 900, 0.36 * H      # TikTok's right action rail covers x > 900 below about a third of the frame
MIN_SHARE = 0.10                     # overlap that counts: this share of the smaller rectangle
MIN_SECONDS = 0.15


def num_list(v, n_min=2):
    return [float(x) for x in v] if isinstance(v, list) and len(v) >= n_min and all(isinstance(x, (int, float)) for x in v) else None


def lines_for(text_len: int, size: float, width: float, max_lines: int) -> int:
    return max(1, min(max_lines or 99, math.ceil(text_len * size * 0.52 / max(1.0, width))))


def rect_of(o: dict) -> tuple[tuple[float, float, float, float], bool] | None:
    """((x0, y0, x1, y1) in px, exact?) of an overlay's text, or None when its place cannot be told from its props."""
    c, p = o["component"], o.get("props", {})
    text = p.get("text", p.get("emph", ""))
    text = " ".join(map(str, text)) if isinstance(text, list) else str(text)
    if c == "textbox":
        box = num_list(p.get("box"), 3)
        if not box:
            return None
        x0, y0, w = box[0] * W, box[1] * H, box[2] * W
        size = float(p.get("size", 64))
        if len(box) >= 4:
            return (x0, y0, x0 + w, y0 + box[3] * H), True
        n = lines_for(len(text), size, w, int(p.get("maxLines", 3)))
        return (x0, y0, x0 + w, y0 + n * size * float(p.get("lineHeight", 1.12))), False
    if c == "phrase" and isinstance(p.get("y"), (int, float)):
        top = p["y"] * H
        lead = 62 * 1.12 if p.get("lead") else 0.0
        emph = min(118, 940 / max(1, len(str(p.get("emph", ""))) * 0.43)) * 1.12 if p.get("emph") else 0.0
        return (40, top, W - 40, top + lead + emph), False
    if c == "pill" and num_list(p.get("at")):
        ax, ay = p["at"][0] * W, p["at"][1] * H
        size = float(p.get("size", 46))
        w = len(str(p.get("text", ""))) * size * 0.62 + 64
        return (ax - w / 2, ay, ax + w / 2, ay + size + 22), False
    return None


def inter(a, b) -> float:
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return max(0.0, w) * max(0.0, h)


def area(r) -> float:
    return max(1.0, (r[2] - r[0]) * (r[3] - r[1]))


def caption_windows(project: dict) -> list[tuple[float, float, float]]:
    """(start, end, top) of the captions that will be on screen: the SRT groups (or the word groups) minus the windows a band hides."""
    if project.get("captionStyle", "none") == "none":
        return []
    top0 = CAPTION_TOP.get(project.get("layout", "feed"), CAPTION_TOP["feed"])
    spans = [(c["start"], c["end"]) for c in project.get("captions", [])]
    if not spans and project.get("words"):
        ws = project["words"]
        cur = [ws[0]["start"], ws[0]["end"]]
        for w in ws[1:]:
            if w["start"] - cur[1] > 0.6:
                spans.append(tuple(cur))
                cur = [w["start"], w["end"]]
            else:
                cur[1] = w["end"]
        spans.append(tuple(cur))
    out = []
    bands = project.get("captionBands", [])
    for a, b in spans:
        band = next((x for x in bands if x["start"] <= (a + b) / 2 < x["end"]), None)
        if band and band.get("hide"):
            continue
        out.append((a, b, float(band["top"]) if band else float(top0)))
    return out


def check(project: dict) -> list[str]:
    warns: list[str] = []
    items = []
    for o in project.get("overlays", []):
        r = rect_of(o)
        if r:
            items.append((o, r[0], r[1]))
    label = lambda o: f"{o['component']} {o['start']:.2f}-{o['end']:.2f}s"

    for i, (o, ra, ea) in enumerate(items):
        x0, y0, x1, y1 = ra
        if x0 < -1 or y0 < -1 or x1 > W + 1 or y1 > H + 1:
            warns.append(f"{label(o)}: the text box reaches outside the frame ({x0:.0f},{y0:.0f})-({x1:.0f},{y1:.0f})")
        if x1 > RAIL_X and y1 > RAIL_Y and o["component"] == "textbox":
            warns.append(f"{label(o)}: the box's right edge ({x1:.0f}px) is under TikTok's right action rail (x > {RAIL_X})")
        for b, rb, eb in items[i + 1:]:
            t = min(o["end"], b["end"]) - max(o["start"], b["start"])
            if t >= MIN_SECONDS and inter(ra, rb) > MIN_SHARE * min(area(ra), area(rb)):
                about = "" if ea and eb else " (about: one of the two sizes is estimated)"
                warns.append(f"{label(o)} and {label(b)} share the same place for {t:.1f}s{about}: move one, or end one earlier")
        for a, b, top in caption_windows(project):
            t = min(o["end"], b) - max(o["start"], a)
            cap = (CAPTION_X[0], top, CAPTION_X[1], top + 2 * CAPTION_SIZE * 1.25)
            if t >= MIN_SECONDS and inter(ra, cap) > MIN_SHARE * min(area(ra), area(cap)):
                warns.append(f"{label(o)} sits on the captions (y {top:.0f}-{cap[3]:.0f}) at {max(o['start'], a):.2f}s: hide the captions there (a Caption bands row with Top hide) or move the box")
                break
        for s in project.get("scenes", []):
            f = s.get("face")
            if not f:
                continue
            t = min(o["end"], s["end"]) - max(o["start"], s["start"])
            cx, cy, rad = f["x"] * W, f["y"] * H, f["r"] * W * 1.3
            nx, ny = min(max(cx, x0), x1), min(max(cy, y0), y1)     # the point of the box nearest to the head's centre
            if t >= MIN_SECONDS and math.hypot(nx - cx, ny - cy) < rad:
                warns.append(f"{label(o)} covers the speaker's head in the scene at {s['start']:.2f}s: move the box off the face")
                break
    return warns


def main() -> int:
    ap = argparse.ArgumentParser(description="Check text placement in a project.json.")
    ap.add_argument("project", type=Path)
    ap.add_argument("--strict", action="store_true", help="exit 1 when there is a warning")
    a = ap.parse_args()
    project = json.loads(a.project.read_text(encoding="utf-8-sig"))
    warns = check(project)
    for w in warns:
        print(f"  ! {w}")
    print(f"layout check: {len(warns)} warning(s)" if warns else "layout check: clean")
    return 1 if (warns and a.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
