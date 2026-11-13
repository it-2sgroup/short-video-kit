#!/usr/bin/env python3
"""The technique catalogue: one card per technique the kit can do, kept honest against the code.

Why: the kit grows. A reference video shows a transition, a text effect, a grade or a sound the kit lacks;
the technique is researched, implemented and recorded here, so the next chat finds it by name instead of
reinventing it. `assets/techniques.json` holds one card per technique (id, kind, what it looks like, how to
ask for it in a plan, where it lives, which doc explains it, which selftest proves it, where the idea came
from). `check` compares the cards with the CODE, both ways, so a technique cannot exist without a card, a
doc and a test, and a card cannot describe something that is gone.

    python technique.py list [--kind transition]       # every card (id, kind, one line)
    python technique.py kinds                          # the kinds and how many cards each has
    python technique.py show whip                      # the whole card
    python technique.py search "glitch rgb split"     # by id, name, aliases (CapCut / After Effects names), tags
    python technique.py match ref/report.json          # which cards explain what analyze_reference.py measured in a reference video
    python technique.py check                          # cards <-> code <-> docs <-> selftest; exit 1 on a problem
    python technique.py scaffold transition my-wipe    # the files to touch to add one, and a card to paste

Adding a technique is always the same loop (references/adding-techniques.md): name it, find it in `search`
(it may exist under another name), implement it where its kind says, write the card, document it, prove it in
selftest.sh, run `check`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import playbook  # noqa: E402

SKILL = Path(__file__).resolve().parent.parent
CATALOG = SKILL / "assets" / "techniques.json"
TEMPLATE = SKILL / "assets" / "remotion-template" / "src"
HYPERFRAMES = SKILL / "assets" / "hyperframes-template"
SELFTEST = SKILL.parent.parent / "selftest.sh"  # <repo>/selftest.sh; absent in an installed skill (then tests are not checked)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def union(path: Path, name: str) -> set[str]:
    return set(playbook.ts_union(path, name))


def project_ts() -> Path:
    return TEMPLATE / "project.ts"


# kind -> (what its code-side set is read from, function returning that set). A new kind needs one line here.
def _hits() -> set[str]:
    m = re.search(r'\\\+\(([\w|]+)\)', read(SKILL / "scripts" / "plan_to_project.py"))
    return set(m.group(1).split("|")) if m else set()


def _fx() -> set[str]:
    m = re.search(r"FX_NAMES[^=]*=\s*\[(.*?)\]", read(TEMPLATE / "components" / "text" / "Fx.tsx"), re.S)
    return set(re.findall(r'"([\w-]+)"', m.group(1))) if m else set()


def _type_keys(path: Path, name: str, skip: set[str] = frozenset()) -> set[str]:
    """The property names of `type NAME = { a?: ...; b: ... };` (comments ignored)."""
    text = re.sub(r"//[^\n]*", "", read(path))
    m = re.search(r"type\s+" + re.escape(name) + r"\s*=\s*\{(.*?)\n?\};?\s*(?:\n\n|$)", text, re.S)
    body = re.sub(r"\{[^{}]*\}", "", m.group(1)) if m else ""  # drop nested object types: only the top-level properties count
    return {k for k in re.findall(r"(?:^|[;\n])\s*(\w+)\??:", body) if k not in skip}


def _fonts() -> set[str]:
    return set(re.findall(r'\{\s*id:\s*"([\w-]+)"', read(TEMPLATE / "fonts.ts")))


def _speed_curves() -> set[str]:
    import footage_overlap_checker as f
    return set(f.SPEED_PRESETS) | {"ramp"}


KINDS = {
    "overlay": ("components/registry.tsx keys", lambda: set(playbook.registry_components())),
    "transition": ("TransitionType in project.ts", lambda: union(project_ts(), "TransitionType")),
    "hit": ("+word hits in plan_to_project.py", _hits),
    "text-fx": ("FX_NAMES in text/Fx.tsx", _fx),
    "subject-fx": ("SubjectMode in project.ts", lambda: union(project_ts(), "SubjectMode")),
    "title-style": ("TitleStyle in text/Title.tsx", lambda: union(TEMPLATE / "components" / "text" / "Title.tsx", "TitleStyle")),
    "caption-style": ("CaptionStyle in project.ts", lambda: union(project_ts(), "CaptionStyle")),
    "caption-highlight": ("CaptionHighlight in project.ts", lambda: union(project_ts(), "CaptionHighlight")),
    "camera-move": ("CameraMove in project.ts", lambda: union(project_ts(), "CameraMove")),
    "camera-option": ("Camera fields in project.ts", lambda: _type_keys(project_ts(), "Camera", {"keys", "move", "from", "to"})),
    "speed-curve": ("SPEED_PRESETS in footage_overlap_checker.py + ramp", _speed_curves),
    "look": ("Look fields in project.ts", lambda: _type_keys(project_ts(), "Look")),
    "font": ("ids in src/fonts.ts", _fonts),
    "camera-ease": ("CameraEase in project.ts", lambda: union(project_ts(), "CameraEase")),
    "grade": ("grades in assets/grades.json", lambda: set(json.loads(read(SKILL / "assets" / "grades.json"))["grades"])),
    "theme": ("ThemeName in theme.ts", lambda: union(TEMPLATE / "theme.ts", "ThemeName")),
}

REQUIRED = ("id", "kind", "name", "about", "doc")
# `plan` says how to ask for it (a plan cell, a flag, a command); `renderers` says where it is drawn; `source` where the idea
# and its licence come from; `tags`/`aliases` are for search (the names editors use: CapCut, Premiere, After Effects).
OPTIONAL = ("plan", "renderers", "source", "tags", "aliases", "test", "playbooks",
            # how to choose it, what its knobs are, where it came from, and how the analyser recognises it:
            "params", "use_when", "avoid_when", "pairs_with", "licence", "since", "status", "deprecated", "replaced_by", "timing", "renderer_notes", "detect")
# The analyser outputs (report.json paths) a card's `detect.measure` may name; `match` reads the same paths.
MEASURES = ("transitions.family", "shots.camera.driver", "shots.camera.ease", "shots.camera.shake.level", "shots.speed.ramp", "grade.nearest")
PARAM_TYPES = ("integer", "number", "enum", "color", "string", "boolean", "point")
STATUSES = ("stable", "experimental")  # a card made from a single reference stays experimental until a second case or a test supports it

SCAFFOLD = {
    "overlay": ["src/components/graphics/<File>.tsx or text/ (the component: a pure function of the frame)",
                "src/components/registry.tsx (one line)", "scripts/plan_to_project.py (content keys, if it has any)",
                "references/layout-and-motion-graphics.md (a row with its keys)", "a playbook's components.use (playbook.py check fails when nothing uses it)",
                "scripts/project_to_hyperframes.py + assets/hyperframes-template/kit.js (or list it as Remotion-only)"],
    "transition": ["src/project.ts (TransitionType)", "src/engine/transitions.tsx (presentationFor)", "assets/hyperframes-template/kit.js (present()), or note it as Remotion-only",
                   "references/transitions.md (a row)", "a playbook's transitions.same/change lists"],
    "hit": ["scripts/plan_to_project.py (the +word regex and scenes[].fx)", "assets/hyperframes-template/kit.js", "references/capcut-techniques.md"],
    "subject-fx": ["src/project.ts (SubjectMode)", "src/engine/Subject.tsx (the branch)", "scripts/plan_to_project.py (SUBJECT_MODES)", "scripts/project_to_hyperframes.py lists it as Remotion-only",
                   "references/subject-effects.md (a row)"],
    "text-fx": ["src/components/text/Fx.tsx (FX_NAMES, FxName and the effect branch)", "src/components/text/Phrase.tsx (its duration)",
                "assets/sfx/sfx-map.json (its sound key)", "references/typography.md (a row)"],
    "title-style": ["src/components/text/Title.tsx (TitleStyle and the branch)", "assets/hyperframes-template/kit.js", "references/typography.md"],
    "caption-style": ["src/project.ts (CaptionStyle)", "src/components/text/Captions.tsx", "scripts/playbook.py (CAPTIONS)", "references/captions-and-text.md"],
    "caption-highlight": ["src/project.ts (CaptionHighlight)", "src/components/text/Captions.tsx", "references/captions-and-text.md"],
    "camera-move": ["src/project.ts (CameraMove)", "src/engine/camera.ts", "assets/hyperframes-template/kit.js", "references/camera-moves.md"],
    "camera-option": ["src/project.ts (Camera)", "src/engine/camera.ts", "scripts/plan_to_project.py (parse_camera)", "assets/hyperframes-template/kit.js or list it as Remotion-only", "references/camera-moves.md"],
    "speed-curve": ["scripts/footage_overlap_checker.py (SPEED_PRESETS)", "references/cutting-and-pacing.md"],
    "font": ["src/fonts.ts (an import and a row in `defs`: the family needs a loader in @remotion/google-fonts and the `vietnamese` subset)", "references/typography.md (a row)"],
    "look": ["src/project.ts (Look)", "src/engine/Short.tsx (LookLayer / lookFilter)", "scripts/plan_to_project.py (--look, --look-fx)", "assets/hyperframes-template/kit.js", "references/image-processing.md"],
    "camera-ease": ["src/project.ts (CameraEase)", "src/engine/camera.ts", "references/camera-moves.md"],
    "grade": ["assets/grades.json (chain + wbStrength)", "a playbook's \"grade\"", "references/image-processing.md (measure on real stills first)"],
    "theme": ["src/theme.ts (ThemeName and the palette)", "scripts/playbook.py (THEMES)", "scripts/new_remotion_project.py (--theme choices)", "references/typography.md"],
}


def load_catalog() -> dict:
    return json.loads(read(CATALOG)) if CATALOG.is_file() else {"techniques": []}


def cards() -> list[dict]:
    return load_catalog().get("techniques", [])


def check() -> int:
    bad = 0

    def fail(msg: str) -> None:
        nonlocal bad
        print(f"FAIL {msg}")
        bad += 1

    cs = cards()
    seen: set[tuple[str, str]] = set()
    selftest = read(SELFTEST)
    for c in cs:
        key = (c.get("kind", "?"), c.get("id", "?"))
        for f in REQUIRED:
            if not c.get(f):
                fail(f"{key[0]}:{key[1]} has no '{f}'")
        for f in c:
            if f not in REQUIRED + OPTIONAL:
                fail(f"{key[0]}:{key[1]} has an unknown field '{f}'")
        if key in seen:
            fail(f"{key[0]}:{key[1]} appears twice")
        seen.add(key)
        if c.get("kind") not in KINDS:
            fail(f"{key[0]}:{key[1]}: unknown kind (known: {', '.join(KINDS)})")
            continue
        doc = c.get("doc", "")
        path = SKILL / doc.split("#")[0]
        if not path.is_file():
            fail(f"{key[0]}:{key[1]}: doc '{doc}' does not exist")
        elif c["id"].lower() not in read(path).lower():
            fail(f"{key[0]}:{key[1]}: doc '{doc}' never mentions '{c['id']}'")
        if selftest and c.get("test") and c["test"] not in selftest:
            fail(f"{key[0]}:{key[1]}: selftest.sh has no test labelled '{c['test']}'")
        for prm in c.get("params", []):
            where = f"{key[0]}:{key[1]} param '{prm.get('key', '?')}'"
            if not re.fullmatch(r"[a-z][a-zA-Z0-9]*", str(prm.get("key", ""))) or prm.get("type") not in PARAM_TYPES:
                fail(f"{where}: needs a camelCase key and a type of {', '.join(PARAM_TYPES)}")
            lo, hi, d = prm.get("min"), prm.get("max"), prm.get("default")
            if all(isinstance(v, (int, float)) for v in (lo, hi)) and lo > hi:
                fail(f"{where}: min > max")
            if all(isinstance(v, (int, float)) for v in (lo, d)) and d < lo or all(isinstance(v, (int, float)) for v in (hi, d)) and d > hi:
                fail(f"{where}: default outside min..max")
            if prm.get("type") == "enum" and not prm.get("options"):
                fail(f"{where}: an enum needs options")
        det = c.get("detect")
        if det is not None and (det.get("measure") not in MEASURES or not det.get("signature")):
            fail(f"{key[0]}:{key[1]}: detect needs a measure of {', '.join(MEASURES)} and a non-empty signature")
        if c.get("status", "stable") not in STATUSES:
            fail(f"{key[0]}:{key[1]}: status must be one of {', '.join(STATUSES)}")
        for pb in c.get("playbooks", []):
            if not (SKILL / "playbooks" / f"{pb.split(':')[0]}.json").is_file():
                fail(f"{key[0]}:{key[1]}: playbook '{pb}' does not exist")
    for kind, (origin, getter) in KINDS.items():
        code = getter()
        if not code:
            fail(f"kind '{kind}': read nothing from {origin} (the catalogue and the code have drifted apart)")
            continue
        have = {i for k, i in seen if k == kind}
        for i in sorted(code - have):
            fail(f"{kind}:{i} exists in the code ({origin}) but has no card in assets/techniques.json")
        for i in sorted(have - code):
            fail(f"{kind}:{i} has a card but is not in the code ({origin})")
    fj = SKILL / "assets" / "fonts.json"  # generated from fonts.ts for the HyperFrames converter: same ids, or it has drifted
    if fj.is_file() and set(json.loads(read(fj))["fonts"]) != _fonts():
        fail("assets/fonts.json has drifted from src/fonts.ts (regenerate it: its 'about' says how)")
    per = {k: sum(1 for kk, _ in seen if kk == k) for k in KINDS}
    print(f"{len(cs)} technique card(s) in {len(KINDS)} kinds; " + ("all consistent." if not bad else f"{bad} problem(s)."))
    if not bad:
        print("  " + ", ".join(f"{k} {n}" for k, n in per.items()))
    return 1 if bad else 0


def line(c: dict) -> str:
    return f"{c['kind']:<18} {c['id']:<16} {c['name']} — {c['about'].split('. ')[0].rstrip('.')}"


def show(c: dict) -> str:
    out = [f"{c['id']}  ({c['kind']})  {c['name']}", f"  {c['about']}"]
    for f in ("plan", "renderers", "doc", "test", "playbooks", "aliases", "tags", "source"):
        v = c.get(f)
        if v:
            out.append(f"  {f}: " + (", ".join(v) if isinstance(v, list) else str(v)))
    return "\n".join(out)


def search(words: str) -> list[dict]:
    terms = [t for t in re.split(r"[\s,]+", words.lower()) if t]
    scored = []
    for c in cards():
        hay = {"id": c["id"].lower(), "name": c["name"].lower(), "al": " ".join(c.get("aliases", [])).lower(),
               "tag": " ".join(c.get("tags", [])).lower(), "about": c["about"].lower()}
        score = sum(4 * (t == hay["id"]) + 3 * (t in hay["id"] or t in hay["name"]) + 3 * (t in hay["al"]) + 2 * (t in hay["tag"]) + (t in hay["about"]) for t in terms)
        if score:
            scored.append((score, c))
    return [c for _, c in sorted(scored, key=lambda s: -s[0])]


def observations(report: dict) -> list[tuple[str, str, str]]:
    """(measure path, value, where) for every thing the analyser measured that a card can claim."""
    out = []
    for t in report.get("transitions", []):
        out.append(("transitions.family", str(t.get("family")), f"transition at {t.get('t')}s ({t.get('frames')} frames, {t.get('direction') or 'no direction'})"))
    for i, sh in enumerate(report.get("shots", []), 1):
        where = f"shot {i} ({sh.get('start')}-{sh.get('end')}s)"
        cam = sh.get("camera") or {}
        if cam.get("quality") == "ok":
            out.append(("shots.camera.driver", str(cam.get("driver")), where))
            out.append(("shots.camera.ease", str(cam.get("ease")), where))
            out.append(("shots.camera.shake.level", str((cam.get("shake") or {}).get("level")), where))
        out.append(("shots.speed.ramp", str((sh.get("speed") or {}).get("ramp")), where))
    for n in (report.get("grade") or {}).get("nearest", [])[:1]:
        out.append(("grade.nearest", str(n.get("look")), "the whole video's grade (nearest kit look)"))
    return out


def match(report_path: str) -> int:
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    by_measure: dict[tuple[str, str], list[dict]] = {}
    for c in cards():
        det = c.get("detect")
        if det:
            for v in det["signature"]:
                by_measure.setdefault((det["measure"], v), []).append(c)
    seen: dict[tuple[str, str], list[str]] = {}
    for m, v, where in observations(report):
        seen.setdefault((m, v), []).append(where)
    for (m, v), wheres in seen.items():
        if v in ("None", "none", "locked", "static", "slight") and m != "shots.camera.driver":
            continue  # nothing was seen: not an observation worth a card
        found = by_measure.get((m, v), [])
        names = ", ".join(f"{c['kind']}:{c['id']}" + (" (read the strip)" if c["detect"].get("needs_look") else "") for c in found) or "NO CARD: a new technique, or a name Claude must read from the evidence strip"
        print(f"{m} = {v}   x{len(wheres)}  e.g. {wheres[0]}\n    -> {names}")
    print("\nThe measurement gives WHEN and HOW MUCH; the name comes from the evidence strips (references/reference-analysis.md). "
          "A line with no card is where `technique.py search`, then references/adding-techniques.md, comes in.")
    return 0


def scaffold(kind: str, ident: str) -> int:
    if kind not in SCAFFOLD:
        print(f"unknown kind '{kind}'. Known: {', '.join(SCAFFOLD)}")
        return 1
    hits = search(ident)
    if hits:
        print("Does one of these already do it? (search first; an existing technique may carry another name)")
        for c in hits[:5]:
            print("  " + line(c))
        print()
    print(f"To add the {kind} '{ident}', touch, in this order:")
    for i, f in enumerate(SCAFFOLD[kind], 1):
        print(f"  {i}. {f}")
    print(f"  {len(SCAFFOLD[kind]) + 1}. assets/techniques.json: the card below")
    print(f"  {len(SCAFFOLD[kind]) + 2}. selftest.sh: a test (label it with the card's \"test\"), then `python scripts/technique.py check`\n")
    print(json.dumps({"id": ident, "kind": kind, "name": "", "about": "what it looks like, and when it earns its place", "plan": "how a plan asks for it",
                      "renderers": ["remotion", "hyperframes"], "doc": "references/<file>.md", "test": "<label in selftest.sh>",
                      "aliases": [], "tags": [], "source": "where the idea comes from, with its licence"}, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list"); p.add_argument("--kind")
    sub.add_parser("kinds")
    p = sub.add_parser("show"); p.add_argument("id")
    p = sub.add_parser("search"); p.add_argument("words")
    sub.add_parser("check")
    p = sub.add_parser("scaffold"); p.add_argument("kind"); p.add_argument("id")
    p = sub.add_parser("match"); p.add_argument("report")
    a = ap.parse_args()
    if a.cmd == "check":
        return check()
    if a.cmd == "scaffold":
        return scaffold(a.kind, a.id)
    if a.cmd == "match":
        return match(a.report)
    cs = cards()
    if a.cmd == "kinds":
        for k, (origin, getter) in KINDS.items():
            print(f"{k:<18} {sum(1 for c in cs if c['kind'] == k):>3} cards, {len(getter()):>3} in code  ({origin})")
        return 0
    if a.cmd == "list":
        for c in cs:
            if not a.kind or c["kind"] == a.kind:
                print(line(c))
        return 0
    if a.cmd == "show":
        hit = [c for c in cs if c["id"] == a.id]
        print("\n\n".join(show(c) for c in hit) if hit else f"no card '{a.id}'; try: technique.py search {a.id}")
        return 0 if hit else 1
    found = search(a.words)
    print("\n".join(line(c) for c in found[:15]) if found else "nothing found: it may be a new technique (technique.py scaffold <kind> <id>)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
