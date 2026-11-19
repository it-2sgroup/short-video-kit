#!/usr/bin/env python3
"""A memory of the style of the videos already made, so the next one is not the same video again.

`footage_overlap_checker.py` keeps one source range out of two videos; this keeps one STYLE out of two. Every plan has a fingerprint: the
transitions, camera moves, speed treatments, text effects, fonts, colours, rhythm, grade and signature move it uses. The ledger (a JSON file that lives
with your work, outside this repo) stores the fingerprints of finished videos; a new plan is compared with the last ones and warned when it
repeats them. `directions.py` uses the same comparison to push its candidates away from what was just made.

    python scripts/style_ledger.py add edit-plan.md --ledger work/style-ledger.json --name v3
    python scripts/style_ledger.py check edit-plan.md --ledger work/style-ledger.json [--last 8] [--max 0.55] [--strict]
    python scripts/style_ledger.py show --ledger work/style-ledger.json

Similarity is the mean Jaccard overlap of the sets on each axis (an axis that both plans leave empty is skipped): 1.0 is the same style, 0 shares nothing.
A single sample of the same genre lands around 0.3-0.5 because the same few techniques fit it; above `--max` (0.55) the plan is warned as a repeat.
Needs only Python 3.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plan_to_project as P  # noqa: E402

AXES = ["transitions", "camera", "speed", "text_fx", "fonts", "colours", "rhythm", "grade", "signature"]   # style only: which graphics a video needs (cart, compare...) is its content
FX_KEYS = ("fx", "leadFx", "in", "enter")
FONT_KEYS = ("font", "leadFont")
COLOUR_KEYS = ("color", "emphColor", "stroke", "bg", "variant")


def fingerprint(plan_text: str) -> dict[str, list[str]]:
    """The style of a plan as sorted token lists per axis (see AXES)."""
    tabs = P.tables(plan_text)
    sh, srows = P.pick(tabs, "start", "end", "source")
    oh, orows = P.pick(tabs, "start", "end", "component")
    fp: dict[str, set[str]] = {a: set() for a in AXES}
    lengths = []
    for r in srows if sh else []:
        try:
            lengths.append(float(P.cell(sh, r, "end")) - float(P.cell(sh, r, "start")))
        except ValueError:
            continue
        tr = P.cell(sh, r, "transition").lower()
        if tr not in ("", "-", "–"):
            fp["transitions"].add(re.sub(r"\+\w+", "", tr).split()[0] if re.sub(r"\+\w+", "", tr).split() else "cut")
            fp["transitions"].update("+" + a for a in re.findall(r"\+(\w+)", tr))
        cam = P.cell(sh, r, "camera").lower()
        if cam:
            fp["camera"].add(cam.split()[0])
            if "shake" in cam:
                fp["camera"].add("shake")
        sp = P.cell(sh, r, "speed").lower()
        if sp:
            fp["speed"].add(sp.split()[0])
    for r in orows if oh else []:
        props = {}
        for chunk in re.split(r"(?<!" + re.escape(chr(92)) + r");", P.cell(oh, r, "content")):
            if "=" in chunk:
                k, v = chunk.split("=", 1)
                props[k.strip()] = v.strip().lower()
        fp["text_fx"].update(props[k] for k in FX_KEYS if k in props)
        fp["fonts"].update(props[k] for k in FONT_KEYS if k in props)
        fp["colours"].update(props[k] for k in COLOUR_KEYS if k in props)
    if len(lengths) >= 3:
        med, cv = statistics.median(lengths), statistics.pstdev(lengths) / max(1e-6, statistics.mean(lengths))
        fp["rhythm"] = {"med:fast" if med < 1.2 else "med:mid" if med < 2.5 else "med:slow", "cv:even" if cv < 0.25 else "cv:varied" if cv < 0.5 else "cv:wild"}
    for axis, label in (("grade", "Grade"), ("signature", "Signature")):
        m = re.search(r"\*\*" + label + r":\*\*\s*([\w:+-]+)", plan_text)
        if m:
            fp[axis].add(m.group(1).lower())
    return {a: sorted(fp[a]) for a in AXES}


def similarity(a: dict[str, list[str]], b: dict[str, list[str]]) -> tuple[float, dict[str, float]]:
    """Mean Jaccard overlap over the axes at least one of the two uses; also the per-axis values."""
    per = {}
    for ax in AXES:
        x, y = set(a.get(ax, [])), set(b.get(ax, []))
        if x or y:
            per[ax] = round(len(x & y) / len(x | y), 2)
    return (round(sum(per.values()) / len(per), 3) if per else 0.0), per


def load_ledger(path: Path | None) -> dict:
    if path and path.is_file():
        return json.loads(path.read_text(encoding="utf-8-sig"))
    return {"videos": []}


def repeats(fp: dict, ledger: dict, last: int = 8) -> list[tuple[str, float, dict]]:
    """(name, similarity, per-axis) against the last `last` videos of the ledger, most similar first."""
    out = []
    for v in ledger.get("videos", [])[-last:]:
        s, per = similarity(fp, v["fingerprint"])
        out.append((v["name"], s, per))
    return sorted(out, key=lambda x: -x[1])


def main() -> int:
    ap = argparse.ArgumentParser(description="Remember and compare the style of finished videos.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("add", "check"):
        s = sub.add_parser(name)
        s.add_argument("plan", type=Path)
        s.add_argument("--ledger", type=Path, required=True)
        if name == "add":
            s.add_argument("--name", required=True, help="a name for this video (v3, 2026-11-20-lavender)")
        else:
            s.add_argument("--last", type=int, default=8, help="compare with this many of the newest videos")
            s.add_argument("--max", type=float, default=0.55, help="a similarity above this is a repeat")
            s.add_argument("--strict", action="store_true", help="exit 1 on a repeat")
    s = sub.add_parser("show")
    s.add_argument("--ledger", type=Path, required=True)
    a = ap.parse_args()

    if a.cmd == "show":
        led = load_ledger(a.ledger)
        for v in led["videos"]:
            print(f"{v['name']:24} {v.get('date', '')}  " + "; ".join(f"{k}={','.join(t[:4])}" for k, t in v["fingerprint"].items() if t))
        print(f"{len(led['videos'])} video(s)")
        return 0
    fp = fingerprint(a.plan.read_text(encoding="utf-8"))
    led = load_ledger(a.ledger)
    if a.cmd == "add":
        led["videos"] = [v for v in led["videos"] if v["name"] != a.name] + [{"name": a.name, "date": datetime.date.today().isoformat(), "fingerprint": fp}]
        a.ledger.parent.mkdir(parents=True, exist_ok=True)
        a.ledger.write_text(json.dumps(led, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"remembered {a.name}: " + "; ".join(f"{k}={len(t)}" for k, t in fp.items() if t))
        return 0
    reps = repeats(fp, led, a.last)
    if not reps:
        print("the ledger is empty: nothing to repeat")
        return 0
    bad = [r for r in reps if r[1] > a.max]
    for name, s, per in reps[:5]:
        print(f"  {'!' if s > a.max else ' '} {name:24} similarity {s:.2f}  (" + ", ".join(f"{k} {v:.2f}" for k, v in per.items()) + ")")
    print(f"style check: {len(bad)} repeat(s) above {a.max}" if bad else "style check: fresh against the last videos")
    if bad:
        top = max(bad[0][2], key=bad[0][2].get)
        print(f"  most shared: {top}; change it, or run directions.py for three other ways to make this video")
    return 1 if (bad and a.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
