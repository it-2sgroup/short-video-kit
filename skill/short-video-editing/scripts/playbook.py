#!/usr/bin/env python3
"""Genre playbooks: load them, suggest one, print a plan skeleton, validate them all.

A playbook (playbooks/<id>.json + playbooks/<id>.md) holds everything that depends on the KIND of
video: runtime band, hook and scene lengths, what drives the cuts (voice pauses or music beats), the
beat structure, transitions, camera moves, caption style, colour theme, grade, sound-design overrides,
recommended graphics and the compliance checklist. The scripts read it instead of hard-coded numbers:

    python scripts/playbook.py list
    python scripts/playbook.py show real-estate                    # the rules a plan for it must meet
    python scripts/playbook.py suggest --intent "<the user's own words>" [--analysis analysis.json]
    python scripts/playbook.py skeleton real-estate --duration 40 [--cuts cuts.json] > edit-plan.md
    python scripts/playbook.py check                               # validate every playbook (selftest)

A variant is written `id:variant` (product-demo:unboxing): its keys are deep-merged over the base.
A plan names its playbook in its header, `**Playbook:** real-estate`; pacing_checker.py,
plan_to_project.py and plan_scenes.py read it from there (or take --playbook). Adding a genre = adding
one JSON and one MD file and passing `check`; see playbooks/README.md.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
DIR = SKILL / "playbooks"
DEFAULT = "product-demo"  # plans written before playbooks existed are product demos
HEADER = re.compile(r"^\*\*Playbook:\*\*\s*([\w:-]+)", re.M)

REQUIRED = {"id": str, "title": str, "summary": str, "intents": list, "expect": dict, "signals": list,
            "runtime": dict, "hook": dict, "scenes": dict, "drive": str, "structure": list,
            "transitions": dict, "camera": dict, "captions": str, "theme": str, "grade": str,
            "correction": str, "music": dict, "components": dict, "sfx": dict, "compliance": list,
            "references": list}
CAPTIONS = {"karaoke", "pop", "plain", "none"}
THEMES = {"cool", "warm", "luxe", "crimson"}
DRIVES = {"voice", "music"}


# ----------------------------------------------------------------------------- loading
def merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in over.items():
        out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


def ids() -> list[str]:
    return sorted(p.stem for p in DIR.glob("*.json"))


def load(name: str | None = None) -> dict:
    """`id` or `id:variant`; None = the default playbook."""
    name = name or DEFAULT
    pid, _, variant = name.partition(":")
    path = DIR / f"{pid}.json"
    if not path.is_file():
        sys.exit(f"unknown playbook '{pid}' (known: {', '.join(ids())})")
    pb = json.loads(path.read_text(encoding="utf-8"))
    variants = pb.pop("variants", {})
    if variant:
        if variant not in variants:
            sys.exit(f"playbook '{pid}' has no variant '{variant}' (has: {', '.join(variants) or 'none'})")
        over = {k: v for k, v in variants[variant].items() if k != "about"}
        if "intents" in over:  # a variant's words add to its base's, they do not replace them
            over["intents"] = list(dict.fromkeys(pb["intents"] + over["intents"]))
        pb = merge(pb, over)
    pb["name"] = name
    pb["variants"] = sorted(variants)
    return pb


def from_plan(text: str) -> str | None:
    m = HEADER.search(text)
    return m.group(1) if m else None


def resolve(explicit: str | None, plan_text: str = "") -> dict:
    """--playbook wins, then the plan's **Playbook:** line, then the default (said out loud)."""
    name = explicit or from_plan(plan_text)
    if not name:
        print(f"note: no **Playbook:** line in the plan; using '{DEFAULT}'", file=sys.stderr)
    return load(name)


# ----------------------------------------------------------------------------- shared choices
def choose_transition(pb: dict, types: list[str], i: int, state: dict) -> str:
    """Transition cell for scene i (0-based) from the playbook: `hook` between hook beats, `into` a named
    type, else `change` (the beat changes) or `same` (within a beat). Accents (+flash, +leak) are capped by `accentsMax`."""
    if i == 0:
        return "–"
    t = pb["transitions"]
    into = t.get("into", {})
    if types[i] == "HOOK" and types[i - 1] == "HOOK" and t.get("hook"):
        cell = t["hook"]  # between the hook's beats (product-demo: the BEFORE -> AFTER wipe)
    elif types[i] in into and types[i] != types[i - 1]:
        cell = into[types[i]]
    elif types[i] != types[i - 1]:
        cell = t["change"][i % len(t["change"])]
    else:
        cell = t["same"][i % len(t["same"])]
    if "+" in cell:
        if state.get("accents", 0) >= t.get("accentsMax", 2):
            cell = cell.split(" +")[0]
        else:
            state["accents"] = state.get("accents", 0) + 1
    return cell


# ----------------------------------------------------------------------------- skeleton
def phases(pb: dict, duration: float) -> list[dict]:
    """Expand the structure into phases with absolute [start, end) on a timeline of `duration`."""
    hook = pb["hook"]
    hook_len = hook["beats"] * hook["beat"]
    fixed = sum(p.get("seconds", 0) for p in pb["structure"])
    share_total = sum(p.get("share", 0) for p in pb["structure"]) or 1
    rest = max(0.0, duration - hook_len - fixed)
    out, t = [{"type": "HOOK", "start": 0.0, "end": hook_len, "purpose": hook.get("purpose", ""),
               "graphics": hook.get("graphics", "")}], hook_len
    for p in pb["structure"]:
        length = p.get("seconds", 0) + rest * p.get("share", 0) / share_total
        out.append({**p, "start": t, "end": t + length})
        t += length
    out[-1]["end"] = duration
    return out


def scene_counts(ph: list[dict], lo: float, hi: float, target: float) -> tuple[list[int], float]:
    """Scenes per phase (at least one each) so that ONE common scene length, body / total, lies in
    [lo, hi]: phases are then resized to whole scenes instead of being split on their own, which would
    leave a 4.1 s phase as two 2.05 s scenes."""
    body = ph[-1]["end"] - ph[0]["end"]
    counts = [max(1, round((p["end"] - p["start"]) / target)) for p in ph[1:]]
    for _ in range(200):
        length = body / sum(counts)
        if length < lo - 1e-6 and max(counts) > 1:  # too many scenes: drop one from the most crowded phase
            counts[counts.index(max(counts))] -= 1
        elif length > hi + 1e-6:  # too few: add one to the phase whose scenes are longest
            spans = [(p["end"] - p["start"]) / c for p, c in zip(ph[1:], counts)]
            counts[spans.index(max(spans))] += 1
        else:
            break
    return counts, body / sum(counts)


def skeleton_rows(pb: dict, duration: float, cuts: list[dict] | None) -> list[dict]:
    ph = phases(pb, duration)
    sc, hook = pb["scenes"], pb["hook"]
    if cuts:  # boundaries from suggest_cuts.py; types from where each scene's middle falls
        bounds = [(round(c["start"], 2), round(c["end"], 2), c.get("text", "")) for c in cuts]
        sources = [(c.get("clip", ""), c.get("in", "")) for c in cuts]  # trim_voice.py --jumpcut gives both
        ph_of = None
    else:
        starts = [round(hook["beat"] * k, 1) for k in range(hook["beats"])]
        counts, length = scene_counts(ph, sc["min"], sc["max"], sc["target"])
        t, types = ph[0]["end"], []
        for p, c in zip(ph[1:], counts):
            for _ in range(c):
                starts.append(round(t, 1))
                types.append(p)
                t += length
        ends = starts[1:] + [round(duration, 1)]
        bounds = [(s, e, "") for s, e in zip(starts, ends)]
        ph_of = [ph[0]] * hook["beats"] + types
        sources = [("", "")] * len(bounds)
    rows = []
    for k, (s, e, text) in enumerate(bounds):
        mid = (s + e) / 2
        if ph_of:
            p = ph_of[k]
        else:
            p = ph[0] if k < hook["beats"] else next((x for x in ph[1:] if x["start"] <= mid < x["end"]), ph[-1])
        rows.append({"start": s, "end": e, "type": p["type"], "speed": "" if sources[k][0] else p.get("speed", ""),
                     "clip": sources[k][0], "in": sources[k][1],
                     "shot": "; ".join(x for x in (p.get("purpose", ""), f"→ {p['graphics']}" if p.get("graphics") else "") if x),
                     "audio": text})
    state: dict = {}
    types = [r["type"] for r in rows]
    for i, r in enumerate(rows):
        r["transition"] = choose_transition(pb, types, i, state)
    return rows


def skeleton(pb: dict, duration: float, cuts: list[dict] | None, title: str) -> str:
    rows = skeleton_rows(pb, duration, cuts)
    rt = pb["runtime"]
    out = [f"# Edit Plan — {title}", "",
           f"**Playbook:** {pb['name']}  ",
           f"**Platform:** {', '.join(pb.get('platforms', ['tiktok', 'reels']))}  ",
           f"**Target runtime:** {rt['ideal'][0]:g}–{rt['ideal'][1]:g}s (allowed {rt['min']:g}–{rt['max']:g}s)  ",
           f"**Drive:** {pb['drive']} (cuts on {'pauses in the voice' if pb['drive'] == 'voice' else 'music beats'})  ",
           f"**Look:** theme `{pb['theme']}`, grade `{pb['grade']}`, captions `{pb['captions']}`  ",
           "**Goal / CTA:** [what the viewer should do]  ",
           "**Source footage:** [folder; analysis.json]", "",
           "## Scenes", "",
           "| # | Start | End | Source | In | Type | Transition | Camera | Speed | Shot | Audio |",
           "|---|-------|-----|--------|----|------|------------|--------|-------|------|-------|"]
    for n, r in enumerate(rows, 1):
        out.append(f"| {n} | {r['start']:g} | {r['end']:g} | {r['clip']} | {r['in']} | {r['type']} | {r['transition']} | | {r['speed']} | {r['shot']} | {r['audio']} |")
    use = ", ".join(f"`{c}`" for c in pb["components"]["use"])
    out += ["", "## Overlays", "", f"Recommended for this playbook: {use}.", "",
            "| # | Start | End | Component | Zone | Tone | Content |",
            "|---|-------|-----|-----------|------|------|---------|", "", "## Compliance check", ""]
    out += [f"- [ ] {c}" for c in pb["compliance"]]
    out += ["", "## Pacing check result", "", "```", "```", ""]
    return "\n".join(out)


# ----------------------------------------------------------------------------- suggest
def fold(s: str) -> str:
    # Vietnamese language data: strips tone marks and maps "đ" to "d", so a request typed without diacritics still matches.
    import unicodedata
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")


def suggest(intent: str, analysis: dict | None) -> list[tuple[float, str, list[str], int]]:
    """Score every playbook (and variant) by the user's words and, when given, the footage analysis.
    The footage summary (inspect_footage.py --measure --json) says whether there is speech on camera
    and how much the camera moves. It is a first guess for Claude to confirm by LOOKING, never a verdict."""
    # Match with the diacritics when the user typed them: folded, "giày" (shoes) equals "giây" (seconds).
    # Only a request typed without any diacritic is matched folded. Whole words only ("sale" not "wholesale").
    import unicodedata
    plain = intent == fold(intent) or not any(unicodedata.category(c) == "Mn" for c in unicodedata.normalize("NFD", intent))
    text = fold(intent) if plain else unicodedata.normalize("NFC", intent.lower())
    norm = (lambda k: fold(k)) if plain else (lambda k: unicodedata.normalize("NFC", k.lower()))
    # Vietnamese negation words ("không", "chẳng", "chả"...) and the filler after them: a keyword right after one of
    # these is not a request ("không có giọng đọc" = "no voiceover"). Both toned and untoned spellings are listed.
    neg = re.compile(r"(?:không|chẳng|chả|ko|khong|chang|cha|no|without)\s+(?:có\s+|co\s+|dùng\s+|dung\s+|cần\s+|can\s+)?$")

    def hit(k: str) -> bool:
        """A whole-word match that is not negated (Vietnamese "không có giọng đọc", "no voiceover", does not ask for a voice)."""
        for m in re.finditer(r"(?<!\w)" + re.escape(norm(k)) + r"(?!\w)", text):
            if not neg.search(text[max(0, m.start() - 16):m.start()]):
                return True
        return False
    summary = (analysis or {}).get("summary", {})
    scored = []
    for pid in ids():
        base = json.loads((DIR / f"{pid}.json").read_text(encoding="utf-8"))
        for var in [None] + list(base.get("variants", {})):
            pb = load(f"{pid}:{var}" if var else pid)
            why, score = [], 0.0
            for kw in pb["intents"]:
                if hit(kw):
                    score += 2 + len(kw.split()) * 0.5
                    why.append(f"'{kw}'")
            if summary:
                exp = pb["expect"]
                speech = summary.get("speech")  # "on-camera" | "none"
                if exp.get("speech") == "on-camera" and speech == "on-camera":
                    score += 2; why.append("speech on camera")
                if exp.get("speech") in ("voiceover", "none") and speech == "none":
                    score += 1; why.append("no speech on camera")
                if exp.get("speech") == "on-camera" and speech == "none":
                    score -= 2
                if exp.get("motion") and exp["motion"] == summary.get("motion"):
                    score += 1; why.append(f"camera motion {summary['motion']}")
            if var and score > 0:  # a variant is chosen by its own words; without them its base ranks first
                own = sum(hit(k) for k in base["variants"][var].get("intents", []))
                score += 1.5 * own if own else -0.5
            words = sum(1 for w in why if w.startswith("'"))
            scored.append((round(score, 2), pb["name"], why, words))
    return sorted(scored, key=lambda s: -s[0])


# ----------------------------------------------------------------------------- check
def ts_union(path: Path, name: str) -> list[str]:
    """The string members of `type NAME = "a" | "b" ...;` in a TypeScript file, in order (comments ignored)."""
    text = re.sub(r"//[^\n]*", "", path.read_text(encoding="utf-8") if path.is_file() else "")  # comments may contain ';'
    m = re.search(r"type\s+" + re.escape(name) + r"\s*=\s*(.*?);", text, re.S)
    return re.findall(r'"([\w-]+)"', m.group(1)) if m else []


def transition_types() -> list[str]:
    """Every transition the template can draw (TransitionType in assets/remotion-template/src/project.ts)."""
    return ts_union(SKILL / "assets" / "remotion-template" / "src" / "project.ts", "TransitionType")


def registry_components() -> set[str]:
    reg = (SKILL / "assets" / "remotion-template" / "src" / "components" / "registry.tsx").read_text(encoding="utf-8")
    body = reg.split("registry: Record<string, OverlayComponent> = {", 1)[1].split("};", 1)[0]
    return set(re.findall(r"^\s*(\w+):", body, re.M)) | {"punch", "sfx"}


def check_one(pb: dict, comps: set[str], grades: set[str], sounds: set[str]) -> list[str]:
    errs = []
    for k, typ in REQUIRED.items():
        if not isinstance(pb.get(k), typ):
            errs.append(f"'{k}' missing or not a {typ.__name__}")
    if errs:
        return errs
    rt, hk, sc = pb["runtime"], pb["hook"], pb["scenes"]
    if not rt["min"] <= rt["ideal"][0] <= rt["ideal"][1] <= rt["max"]:
        errs.append("runtime must satisfy min <= ideal[0] <= ideal[1] <= max")
    if not 0 < sc["min"] <= sc["target"] <= sc["max"]:
        errs.append("scenes must satisfy 0 < min <= target <= max")
    if hk["beats"] * hk["beat"] > hk["deadline"] + 0.05 or hk["minBeat"] > hk["beat"]:
        errs.append("hook beats must fit the deadline and minBeat <= beat")
    if pb["drive"] not in DRIVES:
        errs.append(f"drive must be one of {sorted(DRIVES)}")
    if pb["captions"] not in CAPTIONS:
        errs.append(f"captions must be one of {sorted(CAPTIONS)}")
    if pb["theme"] not in THEMES:
        errs.append(f"theme must be one of {sorted(THEMES)}")
    if pb["grade"] not in grades:
        errs.append(f"grade '{pb['grade']}' is not in assets/grades.json")
    if pb["correction"] not in ("per-clip", "shared"):
        errs.append("correction must be per-clip or shared")
    lo, hi = pb["music"].get("bpm", [0, 0])
    if not 60 <= lo <= hi <= 200:
        errs.append("music.bpm must be [lo, hi] within 60-200")
    for c in pb["components"].get("use", []) + pb["components"].get("avoid", []):
        if c not in comps:
            errs.append(f"component '{c}' is not in the template registry")
    for sec, section in pb["sfx"].items():
        if sec == "rules":  # numbers (minGap, window, maxInWindow, notBefore), not sounds
            continue
        for v in section.values():
            for entry in (v if isinstance(v, list) else [v]):
                for name in ([entry.get("sound"), *entry.get("also", [])] if isinstance(entry, dict) else [entry]):
                    for nm in (name if isinstance(name, list) else [name]):
                        if nm and nm not in sounds:
                            errs.append(f"sfx override names unknown sound '{nm}'")
    for ref in pb["references"]:
        if not (SKILL / ref).is_file():
            errs.append(f"reference '{ref}' does not exist")
    if not (DIR / f"{pb['id']}.md").is_file():
        errs.append(f"playbooks/{pb['id']}.md is missing")
    t = pb["transitions"]
    if not t.get("same") or not t.get("change"):
        errs.append("transitions needs non-empty 'same' and 'change' lists")
    for cell in list(pb["camera"].get("byType", {}).values()) + list(pb["camera"].get("byKind", {}).values()) + pb["camera"].get("pattern", []):
        if not re.match(r"^(push|pull|pan|hold)\b", cell):
            errs.append(f"camera cell '{cell}' does not start with push/pull/pan/hold")
    if not pb["camera"].get("pattern"):
        errs.append("camera.pattern is empty")
    if not pb["compliance"]:
        errs.append("compliance checklist is empty")
    return errs


def check_all() -> int:
    comps = registry_components()
    grades = set(json.loads((SKILL / "assets" / "grades.json").read_text(encoding="utf-8"))["grades"])
    sounds = set(json.loads((SKILL / "assets" / "sfx" / "sfx-map.json").read_text(encoding="utf-8"))["sounds"])
    used_comp, used_grade, used_theme, used_caps, bad = set(), set(), set(), set(), 0
    for pid in ids():
        raw = json.loads((DIR / f"{pid}.json").read_text(encoding="utf-8"))
        if raw.get("id") != pid:
            print(f"FAIL {pid}: 'id' must equal the file name"); bad += 1
            continue
        for name in [pid] + [f"{pid}:{v}" for v in raw.get("variants", {})]:
            pb = load(name)
            errs = check_one(pb, comps, grades, sounds)
            if not errs:  # the generated skeleton must satisfy the playbook's own pacing rules
                import pacing_checker
                for dur in (pb["runtime"]["ideal"][0], pb["runtime"]["ideal"][1]):
                    scenes, probs = pacing_checker.parse_plan(skeleton(pb, dur, None, "check"))
                    rep = pacing_checker.check(scenes, pb)
                    errs += [f"skeleton at {dur:g}s: {e}" for e in probs + rep.errors]
            print(f"{'ok  ' if not errs else 'FAIL'} {name}")
            for e in errs:
                print(f"       x {e}")
            bad += bool(errs)
            used_comp |= set(pb["components"]["use"])
            used_grade.add(pb["grade"]); used_theme.add(pb["theme"]); used_caps.add(pb["captions"])
    # A component, grade, theme or caption style that no playbook recommends is not an error: the kit is a library, and a
    # playbook picks what suits its genre. What keeps the library honest is `technique.py check` (every technique has a card, a
    # doc and a test). Here we only list what is recommended nowhere, so a playbook author can see what exists.
    for label, have, used in (("component", comps - {"punch", "sfx"}, used_comp), ("grade", grades - {"none"}, used_grade),
                              ("theme", THEMES, used_theme), ("caption style", CAPTIONS, used_caps)):
        free = sorted(have - used)
        if free:
            print(f"note: {label}(s) no playbook recommends yet: {', '.join(free)}")
    print(f"\n{len(ids())} playbook(s); " + ("all valid." if not bad else f"{bad} problem(s)."))
    return 1 if bad else 0


# ----------------------------------------------------------------------------- CLI
def show(pb: dict) -> str:
    rt, hk, sc = pb["runtime"], pb["hook"], pb["scenes"]
    lines = [f"{pb['name']} — {pb['title']}", "", pb["summary"], "",
             f"runtime   {rt['min']:g}-{rt['max']:g}s (ideal {rt['ideal'][0]:g}-{rt['ideal'][1]:g})",
             f"hook      {hk['beats']} beat(s) of ~{hk['beat']:g}s, resolved by {hk['deadline']:g}s",
             f"scenes    {sc['min']:g}-{sc['max']:g}s, aim {sc['target']:g}s",
             f"drive     {pb['drive']}   captions {pb['captions']}   theme {pb['theme']}   grade {pb['grade']} ({pb['correction']})",
             f"music     {pb['music'].get('bpm')} bpm, {pb['music'].get('mood', '')}",
             "structure HOOK → " + " → ".join(p["type"] for p in pb["structure"]),
             "graphics  " + ", ".join(pb["components"]["use"]) + (f"   (avoid: {', '.join(pb['components']['avoid'])})" if pb["components"].get("avoid") else ""),
             "variants  " + (", ".join(pb["variants"]) or "none"),
             "read      " + ", ".join([f"playbooks/{pb['id']}.md"] + pb["references"])]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Genre playbooks for the short-video kit.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    s = sub.add_parser("show"); s.add_argument("name")
    g = sub.add_parser("suggest"); g.add_argument("--intent", required=True); g.add_argument("--analysis", type=Path)
    k = sub.add_parser("skeleton"); k.add_argument("name"); k.add_argument("--duration", type=float)
    k.add_argument("--cuts", type=Path, help="scene boundaries from suggest_cuts.py --json"); k.add_argument("--title", default="[video]")
    sub.add_parser("check")
    a = ap.parse_args()

    if a.cmd == "list":
        for pid in ids():
            pb = load(pid)
            print(f"{pid:15} {pb['title']}" + (f"   [variants: {', '.join(pb['variants'])}]" if pb["variants"] else ""))
        return 0
    if a.cmd == "show":
        print(show(load(a.name)))
        return 0
    if a.cmd == "suggest":
        analysis = json.loads(a.analysis.read_text(encoding="utf-8")) if a.analysis else None
        ranked = suggest(a.intent, analysis)
        top = [r for r in ranked if r[3] > 0][:4]
        if not top:
            hint = max(ranked, key=lambda r: r[0]) if analysis else None
            print("No playbook matches the words of the request. Ask the user what kind of video it is "
                  "(playbooks/README.md → Questions)"
                  + (f"; the footage alone looks like {hint[1]} ({', '.join(hint[2])})." if hint and hint[0] > 0 else "."))
            return 1
        for score, name, why, _ in top:
            print(f"{score:5.1f}  {name:28} {', '.join(why)}")
        rival = next((r for r in top[1:] if r[1].split(":")[0] != top[0][1].split(":")[0]), None)  # another genre
        if rival and top[0][0] - rival[0] <= 1.5:
            print("\nClose call: look at the contact sheet and ask the user before choosing.")
        return 0
    if a.cmd == "skeleton":
        pb = load(a.name)
        cuts = json.loads(a.cuts.read_text(encoding="utf-8-sig")) if a.cuts else None
        dur = a.duration or (cuts[-1]["end"] if cuts else sum(pb["runtime"]["ideal"]) / 2)
        print(skeleton(pb, dur, cuts, a.title))
        return 0
    return check_all()


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.exit(main())
