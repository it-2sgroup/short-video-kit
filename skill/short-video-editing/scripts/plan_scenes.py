#!/usr/bin/env python3
"""Fill the Scenes table of an edit plan from a shot library, without reusing any footage.

    python scripts/plan_scenes.py --library library.json --cuts cuts.json \
        --kinds "STAIN,STAIN,STAIN|SOAK,POUR_PINK,LIFT@IMG_0329" \
        --types "HOOK,HOOK,PROBLEM,DEMO,REVEAL" --used kb4/edit-plan.md kb7/edit-plan.md --seed 3

cuts.json   scene boundaries, e.g. the output of `suggest_cuts.py --json` ([{"start":0,"end":1.1}, ...]).
--kinds     one entry per scene: the KIND of shot wanted. `A|B` = try A, else B. `KIND@CLIP` = only that
            clip (use it to keep a before/after pair on the same garment). `ANY` matches every kind: the
            last resort at the end of a list.
--types     the plan's Type column (HOOK, PROBLEM, DEMO, REVEAL, CTA-CLOSE ...), one per scene.
--used      plans whose source ranges are already spent; nothing is reused within or across them, and
            every range keeps `gap` seconds (default 0.5) from the ones taken.
--seed      varies which candidate is picked, so two videos from one library differ.

library.json (see assets/shot-library.example.json): {"gap": 0.5, "spans": [{"clip": "IMG_0319",
"kind": "POUR_PINK", "start": 0, "end": 15, "focus": [0.3, 0.4], "size": "close"}, ...]}. A span is a
stretch of a clip where one kind of shot holds; `focus` is the part of the frame the camera should
move toward (0..1), `size` is wide | medium | close.

Prints the Scenes table (Source and In filled, Transition and Camera chosen by rules from the span's
size and kind) and exits 1 if some scene cannot be filled. Check it with footage_overlap_checker.py.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from footage_overlap_checker import parse_plan  # noqa: E402

SAME_TYPE = ["fade 14f", "slide left", "blurDissolve", "slide right", "fade 18f"]
NEW_TYPE = ["slide up", "wipe left 14f", "zoomThrough +flash", "slide down", "wipe right 14f"]
INTO_REVEAL = ["blurDissolve", "wipe right 14f +leak"]


def free_intervals(span, taken, gap):
    """Parts of the span not within `gap` seconds of a taken range of the same clip."""
    free = [(span["start"], span["end"])]
    for a, b in taken.get(span["clip"], []):
        nxt = []
        for x, y in free:
            if b + gap <= x or a - gap >= y:
                nxt.append((x, y))
                continue
            if x < a - gap:
                nxt.append((x, a - gap))
            if y > b + gap:
                nxt.append((b + gap, y))
        free = nxt
    return [(round(x, 2), round(y, 2)) for x, y in free if y - x > 0.05]


def camera_for(span, kind, i):
    """A camera cell chosen from the span's size and the kind of action, varied scene to scene."""
    fx, fy = span.get("focus", [0.5, 0.5])
    focus = f"focus {fx:.2f},{fy:.2f}"
    size = span.get("size", "medium")
    lean = [-1.0, 1.0] if i % 4 == 1 else [1.0, -1.0] if i % 4 == 3 else None
    roll = f" roll {lean[0]}>{lean[1]}" if lean else ""
    direction = "left" if i % 2 else "right"
    if kind.startswith("LIFT"):
        return f"pull 1.32>1.0 {focus}"
    if kind.startswith("STAIN"):
        return f"push 1.22>1.46 {focus}{roll}"
    if kind.startswith("POUR") or kind == "PRODUCT":
        return f"push 1.14>1.4 {focus}{roll}" if size != "wide" else f"push 1.0>1.22 {focus}"
    if kind.startswith("SOAK"):
        return f"pan {direction} 8% 1.2>1.32 {focus}"
    return f"push 1.0>1.2 {focus}{roll}"  # WIDE and anything else


def main() -> int:
    ap = argparse.ArgumentParser(description="Choose non-overlapping footage for every scene of a plan.")
    ap.add_argument("--library", type=Path, required=True)
    ap.add_argument("--cuts", type=Path, required=True)
    ap.add_argument("--kinds", required=True)
    ap.add_argument("--types", required=True)
    ap.add_argument("--used", nargs="*", default=[], type=Path)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--reserve", default="", help="CLIP:KIND,CLIP:KIND to keep free for a later video (e.g. its before/after pair)")
    ap.add_argument("--json", action="store_true", help="print the chosen scenes as JSON instead of a table")
    a = ap.parse_args()

    lib = json.loads(a.library.read_text(encoding="utf-8-sig"))
    gap = float(lib.get("gap", 0.5))
    cuts = json.loads(a.cuts.read_text(encoding="utf-8-sig"))
    kinds = [k.strip() for k in a.kinds.split(",")]
    types = [t.strip() for t in a.types.split(",")]
    if not len(cuts) == len(kinds) == len(types):
        sys.exit(f"{len(cuts)} scenes in cuts, {len(kinds)} kinds, {len(types)} types: they must match")

    taken: dict[str, list[tuple[float, float]]] = {}
    for p in a.used:
        for r in parse_plan(p):
            taken.setdefault(r["src"], []).append((r["a"], r["b"]))
    rng = random.Random(a.seed)
    reserved = {tuple(x.split(":", 1)) for x in a.reserve.split(",") if ":" in x}

    rows, failed, prev_clip, per_clip = [], [], None, {}
    accents = 0
    for i, (c, wanted, typ) in enumerate(zip(cuts, kinds, types)):
        length = round(c["end"] - c["start"], 2)
        need = length + 0.2  # the outgoing transition handle
        chosen = None
        for alt in wanted.split("|"):
            kind, _, only = alt.partition("@")
            options = []
            for s in lib["spans"]:
                if (kind != "ANY" and s["kind"] != kind) or (only and s["clip"] != only) or (s["clip"], s["kind"]) in reserved and not only:
                    continue
                for x, y in free_intervals(s, taken, gap):
                    x = math.ceil(x * 10 - 1e-6) / 10  # the plan table holds one decimal: round the start up, never into the margin
                    if y - x >= need:
                        # prefer a clip not used in the previous scene or more than twice, then best fit
                        penalty = (3 if s["clip"] == prev_clip else 0) + (2 if per_clip.get(s["clip"], 0) >= 2 else 0)
                        options.append((penalty, round(y - x, 1) + rng.random() * 0.3, s, x))
            if options:
                options.sort(key=lambda o: (o[0], o[1]))
                _, _, span, start = options[0]
                chosen = (kind, span, start)
                break
        if not chosen:
            failed.append(f"scene {i + 1} ({wanted}, {length:.2f}s)")
            rows.append(None)
            continue
        kind, span, start = chosen
        start = round(start, 1)
        taken.setdefault(span["clip"], []).append((start, round(start + length, 2)))
        prev_clip = span["clip"]
        per_clip[prev_clip] = per_clip.get(prev_clip, 0) + 1
        if i == 0:
            trans = "–"
        elif types[i] == "REVEAL" and types[i - 1] != "REVEAL":
            trans = INTO_REVEAL[0] if accents >= 2 else INTO_REVEAL[i % 2]
        elif types[i] != types[i - 1]:
            trans = NEW_TYPE[i % len(NEW_TYPE)]
        else:
            trans = SAME_TYPE[i % len(SAME_TYPE)]
        if "+flash" in trans or "+leak" in trans:
            if accents >= 2:
                trans = trans.split(" +")[0]
            else:
                accents += 1
        rows.append({"start": c["start"], "end": c["end"], "clip": span["clip"], "in": start, "type": typ,
                     "transition": trans, "camera": camera_for(span, kind, i), "kind": kind, "text": c.get("text", "")})

    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
    else:
        print("| # | Start | End | Source | In | Type | Transition | Camera | Shot | Audio |")
        print("|---|-------|-----|--------|----|------|------------|--------|------|-------|")
        for n, r in enumerate(rows, 1):
            if r is None:
                print(f"| {n} | {cuts[n - 1]['start']} | {cuts[n - 1]['end']} | ??? | ??? | {types[n - 1]} | | | UNFILLED | |")
                continue
            print(f"| {n} | {r['start']} | {r['end']} | {r['clip']} | {r['in']} | {r['type']} | {r['transition']} | {r['camera']} | {r['kind']} | {r['text']} |")
    if failed:
        print("\nCould not fill: " + "; ".join(failed), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
