#!/usr/bin/env python3
"""Fill the Scenes table of an edit plan from a shot library, without reusing any footage.

    python scripts/plan_scenes.py --library library.json --plan skeleton.md \
        --kinds "STAIN,STAIN,STAIN|SOAK,POUR,LIFT@IMG_0329" --used v4/edit-plan.md v7/edit-plan.md --seed 3
    python scripts/plan_scenes.py --library library.json --cuts cuts.json --types "HOOK,HOOK,DEMO,..." \
        --kinds "..." --playbook product-demo

--plan      a plan skeleton (`playbook.py skeleton ID --cuts cuts.json`): its Start, End, Type, Speed and
            Transition columns are kept, Source/In/Camera are filled. Its **Playbook:** line is used.
--cuts/--types  the same without a skeleton: scene boundaries (`suggest_cuts.py --json`) and one Type
            per scene; transitions then come from the playbook.
--kinds     one entry per scene: the KIND of shot wanted. `A|B` = try A, else B. `KIND@CLIP` = only that
            clip (keep a before/after pair on the same item). `ANY` matches every kind: the last resort.
--used      plans whose source ranges are already spent; nothing is reused within or across them, and
            every range keeps `gap` seconds (default 0.5) from the ones taken.
--seed      varies which candidate is picked, so two videos from one library differ.

library.json (see assets/shot-library.example.json): {"gap": 0.5, "spans": [{"clip": "IMG_0319",
"kind": "POUR", "start": 0, "end": 15, "focus": [0.3, 0.4], "size": "close", "move": "push"}, ...]}.
A span is a stretch of a clip where one kind of shot holds. Kinds are your own words for the footage
(ROOM, VIEW, MACRO, FACE, STAIN...); `focus` is where the action is (0..1), `size` wide | medium | close,
`move` an optional camera hint. The camera cell comes from `move`, else the playbook's `camera.byKind`
(a kind starting with that key), else the shot size. A scene with a Speed reads speed x length of footage.

Prints the Scenes table and exits 1 if some scene cannot be filled. Check with footage_overlap_checker.py.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import playbook as playbooks  # noqa: E402
from footage_overlap_checker import parse_plan, speed_factor  # noqa: E402


def free_intervals(span, taken, gap):
    """Parts of the span not within `gap` seconds of a taken range of the same clip."""
    free = [(span["start"], span["end"])]
    for a, b in taken.get(span["clip"].upper(), []):
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


SIZE_MOVE = {"wide": "push 1.0>1.2", "medium": "push 1.08>1.28", "close": "pull 1.3>1.06"}


def camera_for(span, kind, i, pb):
    """A camera cell from the span's `move` hint, else the playbook's byKind, else the shot size; aimed
    at the span's focus, with a slow lean on every other push when the playbook's pattern leans."""
    fx, fy = span.get("focus", [0.5, 0.5])
    by_kind = pb["camera"].get("byKind", {})
    key = next((k for k in sorted(by_kind, key=len, reverse=True) if kind.startswith(k)), None)
    if span.get("move"):
        cell = span["move"]
    elif key:
        cell = by_kind[key]
    else:
        cell = SIZE_MOVE.get(span.get("size", "medium"), SIZE_MOVE["medium"])
    if cell.startswith("pan") and not any(d in cell for d in ("left", "right", "up", "down")):
        cell = cell.replace("pan", f"pan {'left' if i % 2 else 'right'}", 1)
    leans = any("roll" in c for c in pb["camera"]["pattern"])
    if leans and cell.startswith("push") and "roll" not in cell and i % 2:
        cell += " roll -1>1" if i % 4 == 1 else " roll 1>-1"
    return f"{cell} focus {fx:.2f},{fy:.2f}" if "focus" not in cell else cell


def read_skeleton(path: Path):
    """Rows of a plan skeleton: start, end, type, speed, transition, shot, audio."""
    import plan_to_project
    tabs = plan_to_project.tables(path.read_text(encoding="utf-8-sig"))
    h, rows = plan_to_project.pick(tabs, "start", "end", "type")
    cell = plan_to_project.cell
    return [{"start": float(cell(h, r, "start")), "end": float(cell(h, r, "end")), "type": cell(h, r, "type").upper(),
             "speed": cell(h, r, "speed"), "transition": cell(h, r, "transition"), "shot": cell(h, r, "shot"),
             "text": cell(h, r, "audio")} for r in rows]


def main() -> int:
    ap = argparse.ArgumentParser(description="Choose non-overlapping footage for every scene of a plan.")
    ap.add_argument("--library", type=Path, required=True)
    ap.add_argument("--plan", type=Path, help="plan skeleton from playbook.py skeleton (Start/End/Type/Speed/Transition)")
    ap.add_argument("--cuts", type=Path, help="scene boundaries from suggest_cuts.py --json (with --types)")
    ap.add_argument("--kinds", required=True)
    ap.add_argument("--types", help="the Type of each scene, comma-separated (with --cuts)")
    ap.add_argument("--playbook", help="playbook id[:variant]; default: the skeleton's **Playbook:** line")
    ap.add_argument("--used", nargs="*", default=[], type=Path)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--reserve", default="", help="CLIP:KIND,CLIP:KIND to keep free for a later video (e.g. its before/after pair)")
    ap.add_argument("--json", action="store_true", help="print the chosen scenes as JSON instead of a table")
    a = ap.parse_args()

    lib = json.loads(a.library.read_text(encoding="utf-8-sig"))
    gap = float(lib.get("gap", 0.5))
    if a.plan:
        cuts = read_skeleton(a.plan)
        pb = playbooks.resolve(a.playbook, a.plan.read_text(encoding="utf-8-sig"))
        types = [c["type"] for c in cuts]
    elif a.cuts and a.types:
        cuts = json.loads(a.cuts.read_text(encoding="utf-8-sig"))
        pb = playbooks.resolve(a.playbook)
        types = [t.strip().upper() for t in a.types.split(",")]
    else:
        sys.exit("give --plan skeleton.md, or --cuts cuts.json with --types")
    kinds = [k.strip() for k in a.kinds.split(",")]
    if not len(cuts) == len(kinds) == len(types):
        sys.exit(f"{len(cuts)} scenes, {len(kinds)} kinds, {len(types)} types: they must match")

    taken: dict[str, list[tuple[float, float]]] = {}
    for p in a.used:
        for r in parse_plan(p):
            taken.setdefault(r["src"], []).append((r["a"], r["b"]))
    rng = random.Random(a.seed)
    reserved = {tuple(x.split(":", 1)) for x in a.reserve.split(",") if ":" in x}

    rows, failed, prev_clip, per_clip = [], [], None, {}
    state: dict = {}
    for i, (c, wanted, typ) in enumerate(zip(cuts, kinds, types)):
        length = round((c["end"] - c["start"]) * speed_factor(c.get("speed", "")), 2)  # footage it reads
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
        taken.setdefault(span["clip"].upper(), []).append((start, round(start + length, 2)))
        prev_clip = span["clip"]
        per_clip[prev_clip] = per_clip.get(prev_clip, 0) + 1
        trans = c.get("transition") or playbooks.choose_transition(pb, types, i, state)
        shot = kind + (f" — {c['shot']}" if c.get("shot") else "")
        rows.append({"start": c["start"], "end": c["end"], "clip": span["clip"], "in": start, "type": typ, "transition": trans,
                     "camera": camera_for(span, kind, i, pb), "speed": c.get("speed", ""), "shot": shot, "text": c.get("text", "")})

    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
    else:
        print(f"**Playbook:** {pb['name']}\n")
        print("| # | Start | End | Source | In | Type | Transition | Camera | Speed | Shot | Audio |")
        print("|---|-------|-----|--------|----|------|------------|--------|-------|------|-------|")
        for n, r in enumerate(rows, 1):
            if r is None:
                print(f"| {n} | {cuts[n - 1]['start']} | {cuts[n - 1]['end']} | ??? | ??? | {types[n - 1]} | | | | UNFILLED | |")
                continue
            print(f"| {n} | {r['start']} | {r['end']} | {r['clip']} | {r['in']} | {r['type']} | {r['transition']} | {r['camera']} | {r['speed']} | {r['shot']} | {r['text']} |")
    if failed:
        print("\nCould not fill: " + "; ".join(failed), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
