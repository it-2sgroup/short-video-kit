#!/usr/bin/env python3
"""The idea of a video, written down before it is edited: validate it, and check that a plan really carries it.

A video with no idea gets the defaults of its genre, which is how every video ends up the same. `concept.json` is the short document that comes
first. It says what the viewer should FEEL, the tension and how it is released, a MOTIF that returns, ONE signature move that breaks the pattern on
purpose and why, which techniques the video will use at all (the RESTRAINT: a small vocabulary used with intent reads as a style, a long list as a
catalogue) and the energy curve the cutting should follow. `directions.py` builds three different plans from it; this checks them.

    python scripts/concept.py example                                   # a filled-in concept to copy
    python scripts/concept.py check concept.json                        # the document itself
    python scripts/concept.py check concept.json --plan edit-plan.md    # and the plan against it
    python scripts/concept.py lock concept.json --direction work/dirs/A/direction.json   # the chosen direction's vocabulary becomes the restraint

The restraint is written in two moments: while exploring, leave `restraint.use` empty (or only fill `restraint.avoid`) so `directions.py` can propose
different vocabularies; once a direction is chosen, `lock` copies its transitions, fonts, text effects and grade into `restraint.use`, and from then on the plan is held to them.

What the plan check looks at (all advisory except a missing signature, an unlisted technique and a broken document, which exit 1):
  * exactly one `[signature]` tag in the Shot column; at least `motif.min_count` `[motif]` tags;
  * every transition, camera move, text effect and font the plan uses is in `restraint.use` (for the kinds that list names; `cut` and `fade` are always allowed);
  * the cutting follows the energy curve (scene-length speed against the curve at each scene's middle; a negative correlation is a warning);
  * the cutting is not monotonous (six or more scenes of nearly equal length are a warning).
Needs only Python 3.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plan_to_project as P  # noqa: E402
import style_ledger as SL  # noqa: E402

SKILL = Path(__file__).resolve().parent.parent
MOTIF_KINDS = {"colour", "movement", "text", "shape", "sound"}
ALWAYS_OK = {"cut", "fade", "hold", "push", "pull", "pan", "keys", "+flash", "+leak"}
EXAMPLE = {
    "title": "A name for the idea, not for the product",
    "feeling": ["warm", "confident"],
    "tension": {"problem": "what is wrong or missing at the start, in one sentence", "release": "how the video resolves it, in one sentence"},
    "motif": {"kind": "colour", "what": "the amber accent returns on every key word", "min_count": 3},
    "signature": {"kind": "hold-then-burst", "at": "middle", "why": "the one place the rhythm breaks, where the claim lands", "text": ""},
    "restraint": {"use": [], "avoid": ["glitchSlice"]},
    "energy": [[0.0, 0.7], [0.4, 0.3], [0.75, 0.55], [1.0, 1.0]],
    "references": [],
}


def catalogue_ids() -> set[str]:
    cards = json.loads((SKILL / "assets" / "techniques.json").read_text(encoding="utf-8"))["techniques"]
    return {c["id"] for c in cards}


def signature_kinds() -> set[str]:
    return set(json.loads((SKILL / "assets" / "style-axes.json").read_text(encoding="utf-8"))["signatures"])


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def validate(c: dict) -> list[str]:
    """Problems of the document itself (empty = valid)."""
    bad: list[str] = []
    if not str(c.get("title", "")).strip():
        bad.append("title is empty")
    f = c.get("feeling")
    if not (isinstance(f, list) and 1 <= len(f) <= 4 and all(isinstance(x, str) and x.strip() for x in f)):
        bad.append("feeling must be 1-4 words (what the viewer should feel)")
    t = c.get("tension") or {}
    if not (str(t.get("problem", "")).strip() and str(t.get("release", "")).strip()):
        bad.append("tension needs a problem and a release (a video without tension is a list)")
    m = c.get("motif") or {}
    if m.get("kind") not in MOTIF_KINDS or not str(m.get("what", "")).strip():
        bad.append(f"motif needs a kind ({', '.join(sorted(MOTIF_KINDS))}) and what returns")
    if int(m.get("min_count", 3) or 0) < 2:
        bad.append("motif.min_count must be at least 2 (a motif that appears once is not one)")
    s = c.get("signature") or {}
    if s.get("kind") not in signature_kinds():
        bad.append(f"signature.kind must be one of {', '.join(sorted(signature_kinds()))}")
    if not str(s.get("why", "")).strip():
        bad.append("signature.why is empty: a rule is broken on purpose, so say why")
    at = str(s.get("at", ""))
    if not (at in ("hook", "middle", "end") or re.fullmatch(r"\d+(\.\d+)?", at)):
        bad.append("signature.at must be hook, middle, end or a time in seconds")
    if s.get("kind") == "text-takeover" and not str(s.get("text", "")).strip():
        bad.append("signature text-takeover needs signature.text (the line that takes the frame)")
    r = c.get("restraint") or {}
    known = catalogue_ids() | ALWAYS_OK
    for key in ("use", "avoid"):
        ids = r.get(key, [])
        if not isinstance(ids, list):
            bad.append(f"restraint.{key} must be a list of technique ids")
        else:
            bad += [f"restraint.{key}: '{u}' is not a catalogue id (technique.py search)" for u in ids if u not in known]
    if isinstance(r.get("use"), list) and r["use"] and not 3 <= len(r["use"]) <= 16:
        bad.append("restraint.use, once locked, must list 3-16 technique ids: the whole vocabulary of this video")
    e = c.get("energy")
    if not (isinstance(e, list) and len(e) >= 3 and all(isinstance(p, list) and len(p) == 2 for p in e)):
        bad.append("energy needs at least 3 points [position 0-1, level 0-1]")
    else:
        lv = [p[1] for p in e]
        if max(lv) - min(lv) < 0.3:
            bad.append("energy is flat (levels differ by under 0.3): a video that never changes pace has no shape")
    return bad


def energy_at(curve: list[list[float]], x: float) -> float:
    pts = sorted(curve)
    if x <= pts[0][0]:
        return pts[0][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / max(1e-9, x1 - x0)
    return pts[-1][1]


def pearson(a: list[float], b: list[float]) -> float:
    if len(a) < 3 or statistics.pstdev(a) == 0 or statistics.pstdev(b) == 0:
        return 0.0
    ma, mb = statistics.mean(a), statistics.mean(b)
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (len(a) * statistics.pstdev(a) * statistics.pstdev(b))


def check_plan(c: dict, plan_text: str) -> tuple[list[str], list[str]]:
    """(errors, warnings) of a plan against its concept."""
    errs, warns = [], []
    tabs = P.tables(plan_text)
    sh, srows = P.pick(tabs, "start", "end", "source")
    shots = [P.cell(sh, r, "shot") for r in srows] if sh else []
    sig = sum(s.count("[signature]") for s in shots)
    mot = sum(s.count("[motif]") for s in shots)
    if sig != 1:
        errs.append(f"the plan has {sig} [signature] tag(s) in the Shot column; it needs exactly one (the one move that breaks the pattern on purpose)")
    need = int((c.get("motif") or {}).get("min_count", 3))
    if mot < need:
        warns.append(f"the motif returns {mot} time(s) ([motif] tags in the Shot column); the concept wants at least {need}")
    use = {u.lower() for u in (c.get("restraint") or {}).get("use", [])} | ALWAYS_OK
    if not (c.get("restraint") or {}).get("use"):
        warns.append("restraint.use is empty: no vocabulary is locked yet (choose a direction, then concept.py lock)")
    fp = SL.fingerprint(plan_text)
    cat = {}
    for card in json.loads((SKILL / "assets" / "techniques.json").read_text(encoding="utf-8"))["techniques"]:
        cat[card["id"].lower()] = card["kind"]
    listed = {u.lower() for u in (c.get("restraint") or {}).get("use", [])}
    listed_kinds = {cat.get(u) for u in listed if u in cat}
    for axis, kind in (("transitions", "transition"), ("text_fx", "text-fx"), ("fonts", "font")):
        if kind not in listed_kinds:
            continue                         # the concept names no technique of this kind: no limit on it
        extra = [t for t in fp[axis] if t.lstrip("+") not in use and t not in use]
        if extra:
            errs.append(f"{axis} used but not in restraint.use: {', '.join(extra)} (add them to the concept on purpose, or take them out of the plan)")
    lengths, mids = [], []
    total = 0.0
    for r in srows if sh else []:
        try:
            a, b = float(P.cell(sh, r, "start")), float(P.cell(sh, r, "end"))
        except ValueError:
            continue
        lengths.append(b - a)
        mids.append((a + b) / 2)
        total = max(total, b)
    if len(lengths) >= 5 and total > 0 and c.get("energy"):
        speed = [1 / max(0.2, x) for x in lengths]
        want = [energy_at(c["energy"], m / total) for m in mids]
        r = pearson(speed, want)
        if r < 0:
            warns.append(f"the cutting runs against the energy curve (correlation {r:+.2f}): the plan cuts fastest where the concept wants calm")
    if len(lengths) >= 6 and statistics.pstdev(lengths) / max(1e-6, statistics.mean(lengths)) < 0.15:
        warns.append("the scenes are almost equal in length: even cutting reads as a template; vary the holds")
    return errs, warns


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate a video concept and check a plan against it.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("example")
    c = sub.add_parser("check")
    c.add_argument("concept", type=Path)
    c.add_argument("--plan", type=Path)
    k = sub.add_parser("lock")
    k.add_argument("concept", type=Path)
    k.add_argument("--direction", type=Path, required=True, help="direction.json written by directions.py")
    a = ap.parse_args()
    if a.cmd == "example":
        print(json.dumps(EXAMPLE, ensure_ascii=False, indent=1))
        return 0
    concept = load(a.concept)
    if a.cmd == "lock":
        picks = json.loads(a.direction.read_text(encoding="utf-8"))["picks"]
        ids = [i for k in ("transitions", "type", "colour") for key in ("ids", "fonts", "fx", "grade") for i in ([picks.get(k, {}).get(key)] if isinstance(picks.get(k, {}).get(key), str) else picks.get(k, {}).get(key, []))]
        concept["restraint"] = {**(concept.get("restraint") or {}), "use": sorted(dict.fromkeys(ids))}
        a.concept.write_text(json.dumps(concept, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"locked {len(concept['restraint']['use'])} techniques into {a.concept}: {', '.join(concept['restraint']['use'])}")
        bad = validate(concept)
        for b in bad:
            print(f"  x {b}")
        return 1 if bad else 0
    bad = validate(concept)
    for b in bad:
        print(f"  x {b}")
    if bad:
        print(f"concept: {len(bad)} problem(s)")
        return 1
    print(f"concept '{concept['title']}': valid ({', '.join(concept['feeling'])}; signature {concept['signature']['kind']} at {concept['signature']['at']}; "
          f"{len(concept['restraint']['use'])} techniques)")
    if a.plan:
        errs, warns = check_plan(concept, a.plan.read_text(encoding="utf-8"))
        for e in errs:
            print(f"  x {e}")
        for w in warns:
            print(f"  ! {w}")
        print(f"plan against the concept: {len(errs)} error(s), {len(warns)} warning(s)")
        return 1 if errs else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
