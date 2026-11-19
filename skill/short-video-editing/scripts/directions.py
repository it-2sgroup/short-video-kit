#!/usr/bin/env python3
"""Three different ways to make the same video, built from one idea, and a table that shows how they differ.

One pass through a skeleton gives one answer, and the answer is the average of the genre. This takes the plan you already have (a skeleton, a plan
from `reference_to_plan.py`, a hand-written one: its timing, footage and words stay) and the video's idea (`concept.json`, see `concept.py`) and
rewrites the CREATIVE cells three times, differently: the transitions, the camera, the look of the text, the colour and the rhythm of the
transitions. Each axis has many options built only from catalogue techniques (`assets/style-axes.json`); a direction is one option per axis, narrowed by the
concept's restraint, scored against the feeling the concept asks for and against what the style ledger says was just made (`style_ledger.py`), and the three
are chosen so that no two share more than a couple of axes. The concept's one signature move and its returning motif are written into every direction.

    python scripts/directions.py edit-plan.md --concept concept.json --out-dir work/dirs [--n 3] [--seed 1]
        [--ledger work/style-ledger.json] [--keep transitions,camera,type,colour,rhythm] [--retime] [--stills RENDER_DIR]

  --keep     axes to leave exactly as the base plan has them (a plan made from a sample keeps its measured `transitions` and `camera`: `--keep transitions,camera`)
  --retime   also move the cuts by the rhythm axis (for plans whose cuts are not tied to a voice or a beat)
  --stills   a render project (new_remotion_project.py): render one still per scene of each direction (the base plan needs real Source cells) and tile them
Writes `out-dir/A/edit-plan.md` (and B, C) with `direction.json`, and `out-dir/compare.md`. Pick one (or take the camera of A and the type of C by hand), then
`concept.py check concept.json --plan ...`, `pacing_checker.py`, `style_ledger.py add` after the video is done. The same --seed gives the same directions.
Needs only Python 3 (--stills also needs the render project's Node).
"""
from __future__ import annotations

import argparse
import json
import math
import random
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import concept as C  # noqa: E402
import plan_to_project as P  # noqa: E402
import style_ledger as SL  # noqa: E402

SKILL = Path(__file__).resolve().parent.parent
AXIS_NAMES = ["transitions", "camera", "type", "colour", "rhythm"]
DIRECTIONAL = {"slide", "wipe", "whip", "flip", "cardslide", "blurslide", "cube", "bookflip"}
TEXT_COMPONENTS = {"textbox", "phrase", "pill", "title"}
LETTERS = "ABCDEFGH"
BARS = " ▁▂▃▄▅▆▇█"
NAMED_INK = {"white": (255, 255, 255), "yellow": (255, 214, 0), "red": (200, 20, 40)}
ACCENT_LEDGER_WEIGHT = 0.8
DIVERSITY_WEIGHT = 0.8
BS = chr(92)


# ----------------------------------------------------------------------------- the vocabulary
def load_axes() -> dict:
    return json.loads((SKILL / "assets" / "style-axes.json").read_text(encoding="utf-8"))


def target_vector(feelings: list[str], axes: dict) -> dict[str, float]:
    """What the concept's feeling words ask of each dimension (sum, clipped to -1..1); words the vocabulary does not know are ignored."""
    tv = {d: 0.0 for d in axes["dimensions"]}
    for w in feelings:
        for d, v in axes["feel_words"].get(w.strip().lower(), {}).items():
            tv[d] += v
    return {d: max(-1.0, min(1.0, v)) for d, v in tv.items()}


def fit(option: dict, target: dict[str, float]) -> float:
    """1 when the option sits where the concept asks on every dimension it asks about; 0.5 when the concept asks nothing."""
    asked = [d for d, v in target.items() if abs(v) > 0.05]
    if not asked:
        return 0.5
    return 1.0 - sum(abs(target[d] - option["feel"].get(d, 0.0)) for d in asked) / (2.0 * len(asked))


def restrict(axes: dict, use: set[str], avoid: set[str] = frozenset()) -> tuple[dict[str, list[dict]], list[str]]:
    """The options of every axis narrowed by the concept's restraint: `use` (ids of the kinds it names are all that is left) and `avoid` (those ids are taken out);
    an axis that would be emptied keeps all of its options."""
    kinds = {c["id"].lower(): c["kind"] for c in json.loads((SKILL / "assets" / "techniques.json").read_text(encoding="utf-8"))["techniques"]}
    named = {k for k in (kinds.get(u) for u in use) if k}
    notes, out = [], {}
    for name in AXIS_NAMES:
        opts = []
        for o in axes["axes"][name]:
            o = dict(o)
            if avoid:
                for key in ("ids", "fonts", "fx"):
                    if key in o:
                        o[key] = [i for i in o[key] if i.lower() not in avoid]
                if name == "colour" and o["grade"].lower() in avoid:
                    continue
                if not (o.get("ids", o.get("fonts", ["x"])) and o.get("fx", ["x"])):
                    continue
            if name == "transitions" and "transition" in named:
                o["ids"] = [i for i in o["ids"] if i.lower() in use or i in ("cut", "fade")]
                if len([i for i in o["ids"] if i not in ("cut", "fade")]) < (0 if o["id"] == "quiet" else 2):
                    continue
            if name == "type":
                if "font" in named:
                    o["fonts"] = [f for f in o["fonts"] if f in use]
                if "text-fx" in named:
                    o["fx"] = [f for f in o["fx"] if f.lower() in use]
                if not o["fonts"] or not o["fx"]:
                    continue
            if name == "colour" and "grade" in named and o["grade"].lower() not in use:
                continue
            opts.append(o)
        if not opts:
            notes.append(f"restraint leaves no option on the {name} axis: it is left open")
            opts = [dict(o) for o in axes["axes"][name]]
        out[name] = opts
    return out, notes


# ----------------------------------------------------------------------------- choosing directions
def sample(rng: random.Random, opts: dict[str, list[dict]], target: dict[str, float], keep: set[str]) -> dict:
    d: dict = {"axes": {}, "picks": {}, "seed": rng.getrandbits(32)}
    for name in AXIS_NAMES:
        if name in keep:
            d["axes"][name] = "(base plan)"
            continue
        ws = [math.exp(1.5 * fit(o, target)) for o in opts[name]]
        o = rng.choices(opts[name], weights=ws)[0]
        d["axes"][name] = o["id"]
        d["picks"][name] = o
    for name, key, lo, hi in (("transitions", "ids", 3, 5), ("camera", "cells", 2, 4), ("type", "fonts", 1, 2), ("type", "fx", 2, 3)):
        if name in d["picks"]:
            pool = d["picks"][name][key]
            d["picks"][name] = {**d["picks"][name], key: rng.sample(pool, min(len(pool), rng.randint(lo, hi)))}
    return d


def energy_spread(d: dict) -> float:
    e = [o["feel"].get("energy", 0.0) for n, o in d["picks"].items() if n in ("transitions", "camera", "type", "rhythm")]
    return max(e) - min(e) if e else 0.0


def distance(a: dict, b: dict) -> int:
    return sum(1 for n in AXIS_NAMES if a["axes"][n] != b["axes"][n])


def choose(base: str, concept: dict, opts, target, rng, n: int, keep: set[str], ledger: dict, retime: bool) -> list[dict]:
    pool: dict[tuple, dict] = {}
    for _ in range(900):
        d = sample(rng, opts, target, keep)
        if energy_spread(d) <= 1.5:
            pool.setdefault(tuple(d["axes"][a] for a in AXIS_NAMES), d)
    cands = list(pool.values())
    for d in cands:
        d["fit"] = sum(fit(o, target) for o in d["picks"].values()) / max(1, len(d["picks"]))
    cands = sorted(cands, key=lambda d: -(d["fit"] + rng.random() * 0.05))[:200]
    for d in cands:
        d["plan"] = apply(d, base, concept, keep, retime)
        d["fp"] = SL.fingerprint(d["plan"])
        reps = SL.repeats(d["fp"], ledger)
        d["ledger_sim"] = reps[0][1] if reps else 0.0
    free = len([a for a in AXIS_NAMES if a not in keep])
    need = min(4, free)
    chosen: list[dict] = []
    for _ in range(n):
        best, best_score = None, -9.0
        for d in cands:
            if d in chosen or any(distance(d, c) < need for c in chosen):
                continue
            score = d["fit"] - ACCENT_LEDGER_WEIGHT * d["ledger_sim"] - DIVERSITY_WEIGHT * max((SL.similarity(d["fp"], c["fp"])[0] for c in chosen), default=0.0)
            if score > best_score:
                best, best_score = d, score
        if best is None:                      # not enough distinct candidates: relax the distance by one
            need = max(1, need - 1)
            for d in cands:
                if d not in chosen and all(distance(d, c) >= need for c in chosen):
                    best = d
                    break
        if best is None:
            break
        chosen.append(best)
    return chosen


# ----------------------------------------------------------------------------- rewriting a plan
def profile_scale(profile: str, i: int, n: int) -> float:
    x = i / max(1, n - 1)
    return {"steady": 1.0, "build": 1.5 - x, "pulse": 1.4 if i % 2 == 0 else 0.6, "drop": 1.6 if x < 0.6 else 0.4}.get(profile, 1.0)


def retime_weight(profile: str, i: int, n: int) -> float:
    x = i / max(1, n - 1)
    return {"steady": 1.0, "build": 1.4 - 0.8 * x, "pulse": 1.3 if i % 2 == 0 else 0.7, "drop": 1.4 if x < 0.6 else 0.6}.get(profile, 1.0)


def render_row(cells: list[str]) -> str:
    return "| " + " | ".join(c.replace("|", BS + "|") for c in cells) + " |"


def nearest_ink(hexcol: str) -> str:
    h = hexcol.lstrip("#")
    rgb = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    return min(NAMED_INK, key=lambda k: sum((a - b) ** 2 for a, b in zip(rgb, NAMED_INK[k])))


def set_prop(content: str, key: str, value: str, force: bool = True) -> str:
    parts = [p for p in re.split(r"(?<!" + re.escape(BS) + r");", content) if p.strip()]
    for i, p in enumerate(parts):
        if p.strip().split("=", 1)[0].strip() == key:
            if force:
                parts[i] = f" {key}={value}"
            return ";".join(parts).strip()
    return "; ".join([p.strip() for p in parts] + [f"{key}={value}"])


def next_no_repeat(rng: random.Random, pool: list[str], prev: str | None) -> str:
    options = [p for p in pool if p != prev] or pool
    return rng.choice(options)


def apply(d: dict, base: str, concept: dict, keep: set[str], retime: bool) -> str:
    """The base plan with the creative cells rewritten as direction `d` says (deterministic for the direction's seed)."""
    rng = random.Random(d["seed"])
    axes = load_axes()
    picks = d["picks"]
    lines = base.splitlines()
    # ---- pass 1: read the scene table (indices, header) so the signature and motif scenes are known
    scenes: list[tuple[int, float, float]] = []   # (line index, start, end)
    mode, header = None, None
    for ln, line in enumerate(lines):
        s = line.strip()
        if s.startswith("|"):
            cells = P.split_cells(s)
            low = [c.lower() for c in cells]
            if header is None:
                header = low
                mode = "scenes" if {"start", "end", "source"} <= set(low) else "overlays" if {"start", "end", "component"} <= set(low) else "other"
            elif not set("".join(cells)) <= set("-: ") and mode == "scenes":
                try:
                    scenes.append((ln, float(P.cell(header, cells, "start")), float(P.cell(header, cells, "end"))))
                except ValueError:
                    pass
        else:
            mode, header = None, None
    n = len(scenes)
    if n == 0:
        return base
    total = scenes[-1][2]
    sig = concept["signature"]
    at = str(sig["at"])
    sig_i = 1 if at == "hook" else n // 2 if at == "middle" else max(1, n - 2) if at == "end" else next((i for i, (_, a, b) in enumerate(scenes) if a <= float(at) < b), n // 2)
    sig_i = min(max(sig_i, 1 if n > 1 else 0), n - 1)
    k = max(int(concept["motif"].get("min_count", 3)), 3)
    free = [i for i in range(n) if i != sig_i]
    motif_i = {free[round(j * (len(free) - 1) / max(1, k - 1))] for j in range(min(k, len(free)))} if free else set()
    rhythm = picks.get("rhythm", {}).get("profile", "steady")
    colour = picks.get("colour")
    accent = colour["accent"] if colour else None

    # ---- retime (optional): move the cuts by the rhythm profile, total unchanged
    new_times = {i: (a, b) for i, (_, a, b) in enumerate(scenes)}
    if retime and "rhythm" not in keep:
        w = [retime_weight(rhythm, i, n) * (b - a) for i, (_, a, b) in enumerate(scenes)]
        scale = total / sum(w)
        t = scenes[0][1]
        for i in range(n):
            new_times[i] = (round(t, 2), round(t + w[i] * scale, 2) if i < n - 1 else total)
            t = new_times[i][1]

    # ---- pass 2: rewrite
    out: list[str] = []
    mode, header, row_i = None, None, -1
    prev_cam = prev_tr = prev_fx = None
    accents_used = 0
    text_i = 0
    signature_text_row = None
    scene_span = {i: (new_times[i][0], new_times[i][1]) for i in range(n)}
    for ln, line in enumerate(lines):
        s = line.strip()
        if not s.startswith("|"):
            mode, header = None, None
            out.append(line)
            continue
        cells = P.split_cells(s)
        low = [c.lower() for c in cells]
        if header is None:
            header = low
            mode = "scenes" if {"start", "end", "source"} <= set(low) else "overlays" if {"start", "end", "component"} <= set(low) else "other"
            out.append(line)
            continue
        if set("".join(cells)) <= set("-: ") or mode not in ("scenes", "overlays"):
            out.append(line)
            continue
        if mode == "scenes":
            row_i += 1
            i = row_i
            ti, ci, si, ki, li = (header.index(c) if c in header else -1 for c in ("transition", "camera", "shot", "speed", "layout"))
            card = 0 <= li < len(cells) and cells[li].strip() not in ("", "full")
            if retime and "rhythm" not in keep:
                cells[header.index("start")], cells[header.index("end")] = f"{new_times[i][0]:g}", f"{new_times[i][1]:g}"
            base_tr = cells[ti].strip().lower() if 0 <= ti < len(cells) else ""
            if "transitions" in picks and i >= 1 and ti >= 0 and not card and base_tr not in ("", "-", "–", "cut") and not base_tr.startswith("card"):
                o = picks["transitions"]
                tid = next_no_repeat(rng, o["ids"], prev_tr)
                if rhythm == "drop" and i / max(1, n - 1) >= 0.6 and rng.random() < 0.7:
                    tid = "cut"                   # after the drop the cuts are hard
                prev_tr = tid
                tok = tid
                if tid != "cut":
                    if tid.lower() in DIRECTIONAL:
                        tok += " " + rng.choice(["left", "right", "up", "down"])
                    lo, hi = o["frames"]
                    tok += f" {int(max(4, min(30, round(rng.randint(lo, hi) * profile_scale(rhythm, i, n)))))}f"
                    if o["accents"] and accents_used < 2 and rng.random() < 0.3:
                        tok += " " + rng.choice(o["accents"])
                        accents_used += 1
                cells[ti] = tok
            if "camera" in picks and ci >= 0 and not card and "keys" not in cells[ci].lower():
                focus = re.search(r"focus\s+[\d.]+\s*,\s*[\d.]+", cells[ci])
                cell = next_no_repeat(rng, picks["camera"]["cells"], prev_cam)
                prev_cam = cell
                if i in motif_i and concept["motif"]["kind"] == "movement":
                    cell = picks["camera"]["cells"][0]
                cells[ci] = cell + (" " + focus.group(0) if focus else "")
            # the signature move
            tags = []
            if i == sig_i:
                spec = axes["signatures"][sig["kind"]]
                tags.append("[signature]")
                if "transition" in spec and ti >= 0:
                    cells[ti] = spec["transition"]
                if "camera" in spec and ci >= 0:
                    cells[ci] = spec["camera"]
                if "speed" in spec and ki >= 0:
                    cells[ki] = spec["speed"]
                if "overlay" in spec:
                    signature_text_row = (new_times[i][0], new_times[i][1], spec["overlay"].replace("{text}", str(sig.get("text", "")).replace(";", P.BSC)))
            if i == sig_i - 1 and sig["kind"] == "hold-then-burst" and i >= 1 and ti >= 0:
                cells[ti] = axes["signatures"]["hold-then-burst"]["before"]
            if i in motif_i:
                tags.append("[motif]")
            if tags and si >= 0 and si < len(cells):
                cells[si] = (cells[si] + " " + " ".join(tags)).strip()
            out.append(render_row(cells))
            continue
        # overlays
        ci_ = header.index("component")
        comp = cells[ci_]
        content_i = header.index("content") if "content" in header else -1
        if comp in TEXT_COMPONENTS and content_i >= 0 and content_i < len(cells):
            ct = cells[content_i]
            if "type" in picks and comp in ("textbox", "phrase", "title", "pill"):
                o = picks["type"]
                fx = next_no_repeat(rng, o["fx"], prev_fx)
                prev_fx = fx
                font = o["fonts"][text_i % len(o["fonts"])]
                ct = set_prop(ct, "font", font)
                if comp == "textbox":
                    ct = set_prop(ct, "in", fx)
                    if o["case"] == "upper":
                        ct = set_prop(ct, "case", "upper", force=False)
                elif comp == "phrase":
                    ct = set_prop(ct, "fx", fx)
                    ct = set_prop(ct, "leadFx", o["fx"][0])
                text_i += 1
            if colour and "colour" not in keep:
                try:
                    t0 = float(cells[header.index("start")])
                except ValueError:
                    t0 = 0.0
                on_motif = concept["motif"]["kind"] == "colour" and any(scene_span[j][0] <= t0 < scene_span[j][1] for j in motif_i)
                if comp == "textbox":
                    ct = set_prop(ct, "color", accent if on_motif else colour["text"][0], force=on_motif or False)
                elif comp == "phrase":
                    ct = set_prop(ct, "emphColor", nearest_ink(accent) if on_motif else nearest_ink(colour["text"][0]), force=on_motif)
            cells[content_i] = ct
        out.append(render_row(cells))

    text = "\n".join(out) + ("\n" if base.endswith("\n") else "")
    if signature_text_row:  # a text takeover is one more Overlays row
        t0, t1, row = signature_text_row
        text = add_overlay_row(text, t0, t1, row)
    # ---- header lines and the build hints
    sig_line = f"**Signature:** {sig['kind']}"
    chosen_axes = ", ".join(a + " " + d["axes"][a] for a in AXIS_NAMES)
    head = [f"**Direction:** {d.get('name', '?')} ({chosen_axes})"]
    if colour:
        head.append(f"**Grade:** {colour['grade']}")
    head.append(sig_line)
    head.append(f"**Concept:** {concept['title']}")
    text = re.sub(r"(\*\*Playbook:\*\*[^\n]*\n)", lambda m: m.group(1) + "\n".join(h + "  " for h in head) + "\n", text, count=1) if "**Playbook:**" in text else "\n".join(h + "  " for h in head) + "\n" + text
    if colour:
        flags = " ".join(x for x in ((f"--look {colour['look']}" if colour["look"] else ""), (f"--look-fx {colour['look_fx']}" if colour["look_fx"] else "")) if x)
        hints = [f"- footage: `prepare_footage.py SRC DEST --grade {colour['grade']}`", f"- build: `plan_to_project.py PLAN --out PROJECT {flags}`" if flags else "- build: no extra look flags"]
        block = f"\n## Build hints (direction {d.get('name', '?')})\n\n" + "\n".join(hints) + "\n"
        text = text.replace("\n## Pacing check result", block + "\n## Pacing check result", 1) if "\n## Pacing check result" in text else text.rstrip("\n") + "\n" + block
    return text


def add_overlay_row(text: str, t0: float, t1: float, row_spec: str) -> str:
    """Append `component | zone | tone | content` as one more Overlays row (a table is created when the plan has none)."""
    lines = text.splitlines()
    comp, zone, tone, content = [c.strip() for c in row_spec.split("|", 3)]
    idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("|") and {"start", "end", "component"} <= set(c.lower() for c in P.split_cells(line.strip())):
            idx = i
    if idx is None:
        lines += ["", "## Overlays", "", "| # | Start | End | Component | Zone | Tone | Content |", "|---|-------|-----|-----------|------|------|---------|"]
        idx = len(lines) - 1
    j = idx + 1
    while j < len(lines) and lines[j].strip().startswith("|"):
        j += 1
    num = sum(1 for x in lines[idx + 1:j] if x.strip().startswith("|") and not set("".join(P.split_cells(x.strip()))) <= set("-: "))
    lines.insert(j, render_row([str(num), f"{t0:g}", f"{t1:g}", comp, zone, tone, content]))
    return "\n".join(lines) + "\n"


# ----------------------------------------------------------------------------- the comparison
def bars(lengths: list[float]) -> str:
    hi = max(lengths) if lengths else 1
    return "".join(BARS[min(8, max(1, round(8 * x / hi)))] for x in lengths)


def compare_md(chosen: list[dict], concept: dict, notes: list[str], target: dict, ledger: dict) -> str:
    out = [f"# Directions for: {concept['title']}", "",
           f"Feeling asked: {', '.join(concept['feeling'])}. Pulled toward: " + (", ".join(f"{d} {v:+.1f}" for d, v in target.items() if abs(v) > 0.05) or "nothing in particular (the vocabulary does not know those words)") + ".",
           f"Signature: {concept['signature']['kind']} at {concept['signature']['at']} ({concept['signature']['why']}). Motif: {concept['motif']['kind']}, {concept['motif']['what']}.", ""]
    out += [f"Note: {n}." for n in notes]
    out += ["", "| | " + " | ".join(f"**{d['name']}**" for d in chosen) + " |", "|---|" + "---|" * len(chosen)]
    for a in AXIS_NAMES:
        out.append(f"| {a} | " + " | ".join(d["axes"][a] + (f": {', '.join((d['picks'][a].get('ids') or d['picks'][a].get('cells') or d['picks'][a].get('fx') or [''])[:4])}" if a in d["picks"] and a not in ("colour", "rhythm") else (f" ({d['picks'][a]['grade']}, accent {d['picks'][a]['accent']})" if a == "colour" and a in d["picks"] else "")) for d in chosen) + " |")
    out.append("| fit with the concept | " + " | ".join(f"{d['fit']:.2f}" for d in chosen) + " |")
    if ledger.get("videos"):
        out.append("| likeness to the last videos | " + " | ".join(f"{d['ledger_sim']:.2f}" for d in chosen) + " |")
    out += ["", "## How different they really are (style similarity: 1 = the same, 0 = nothing shared)", "", "| | " + " | ".join(d["name"] for d in chosen) + " |", "|---|" + "---|" * len(chosen)]
    for a in chosen:
        out.append(f"| {a['name']} | " + " | ".join(f"{SL.similarity(a['fp'], b['fp'])[0]:.2f}" for b in chosen) + " |")
    out += ["", "## Rhythm of each direction (scene lengths)", ""]
    for d in chosen:
        tabs = P.tables(d["plan"])
        sh, rows = P.pick(tabs, "start", "end", "source")
        ls = [float(P.cell(sh, r, "end")) - float(P.cell(sh, r, "start")) for r in rows] if sh else []
        out.append(f"- {d['name']}: `{bars(ls)}`")
    out += ["", "Choose one, or take one axis from another by hand. Then `concept.py check CONCEPT --plan PLAN`, `pacing_checker.py`, and after the video `style_ledger.py add`."]
    return "\n".join(out) + "\n"


def make_stills(plan: Path, render: Path, name: str) -> str:
    proj = render / f"dir_{name}.json"
    r = subprocess.run([sys.executable, "-X", "utf8", str(SKILL / "scripts" / "plan_to_project.py"), str(plan), "--out", str(proj)], capture_output=True, text=True)
    if r.returncode:
        return f"{name}: plan_to_project failed ({(r.stderr or r.stdout).strip().splitlines()[-1:]})"
    r = subprocess.run(["node", "stills.mjs", proj.name, f"out/dir_{name}", "--cuts"], cwd=render, capture_output=True, text=True)
    if r.returncode:
        return f"{name}: stills failed ({(r.stderr or r.stdout).strip().splitlines()[-1:]})"
    r = subprocess.run([sys.executable, "-X", "utf8", str(SKILL / "scripts" / "montage.py"), f"out/dir_{name}_*.jpg", "--cols", "6", "--out", f"out/dir_{name}_sheet.jpg"], cwd=render, capture_output=True, text=True)
    return f"{name}: {render / 'out' / f'dir_{name}_sheet.jpg'}" if r.returncode == 0 else f"{name}: montage failed"


def main() -> int:
    ap = argparse.ArgumentParser(description="Three different directions for one video, from one idea.")
    ap.add_argument("plan", type=Path)
    ap.add_argument("--concept", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--ledger", type=Path)
    ap.add_argument("--keep", default="", help="comma list of axes left as the base plan has them: " + ", ".join(AXIS_NAMES))
    ap.add_argument("--retime", action="store_true")
    ap.add_argument("--stills", type=Path, metavar="RENDER_DIR")
    a = ap.parse_args()

    concept = C.load(a.concept)
    bad = C.validate(concept)
    if bad:
        for b in bad:
            print(f"  x {b}", file=sys.stderr)
        sys.exit("the concept is not valid: fix it first (concept.py check)")
    keep = {k.strip() for k in a.keep.split(",") if k.strip()}
    if keep - set(AXIS_NAMES):
        sys.exit(f"--keep: unknown axis {sorted(keep - set(AXIS_NAMES))}; axes are {', '.join(AXIS_NAMES)}")
    axes = load_axes()
    target = target_vector(concept["feeling"], axes)
    opts, notes = restrict(axes, {u.lower() for u in concept["restraint"].get("use", [])}, {u.lower() for u in concept["restraint"].get("avoid", [])})
    base = a.plan.read_text(encoding="utf-8")
    ledger = SL.load_ledger(a.ledger)
    notes += [f"restraint.use leaves one option on the {name} axis ({opts[name][0]['id']}): the directions cannot differ there; name more techniques of that kind to open it"
              for name in AXIS_NAMES if name not in keep and len(opts[name]) == 1]
    chosen = choose(base, concept, opts, target, random.Random(f"{a.seed}"), min(a.n, len(LETTERS)), keep, ledger, a.retime)
    if not chosen:
        sys.exit("no direction could be built from this concept and plan")
    for i, d in enumerate(chosen):                    # the names first: they are written into every plan header
        d["name"] = LETTERS[i]
    for d in chosen:
        d["plan"] = apply(d, base, concept, keep, a.retime)
        d["fp"] = SL.fingerprint(d["plan"])
        folder = a.out_dir / d["name"]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "edit-plan.md").write_text(d["plan"], encoding="utf-8", newline="\n")
        keys = ("ids", "cells", "fonts", "fx", "grade", "accent", "profile")
        (folder / "direction.json").write_text(json.dumps({"name": d["name"], "axes": d["axes"], "seed": d["seed"], "fit": round(d["fit"], 3), "ledger_similarity": round(d["ledger_sim"], 3),
                                                          "picks": {k: {kk: vv for kk, vv in v.items() if kk in keys} for k, v in d["picks"].items()}}, ensure_ascii=False, indent=1), encoding="utf-8")
    sims = [SL.similarity(x["fp"], y["fp"])[0] for i, x in enumerate(chosen) for y in chosen[i + 1:]]
    if sims and max(sims) > 0.6:
        notes.append(f"the directions share most of their style (highest similarity {max(sims):.2f}): widen restraint.use, or keep fewer axes")
    if not a.retime and "rhythm" not in keep and len({tuple(x["fp"]["rhythm"]) for x in chosen}) == 1:
        notes.append("the cuts are the base plan's (tied to the voice or the beat), so the rhythm axis only changes the length of the transitions; --retime moves the cuts too, for plans with no voice")
    (a.out_dir / "compare.md").write_text(compare_md(chosen, concept, notes, target, ledger), encoding="utf-8", newline="\n")
    print(f"wrote {len(chosen)} directions to {a.out_dir}: " + "; ".join(f"{d['name']} = " + "/".join(d["axes"][x] for x in AXIS_NAMES) for d in chosen))
    if sims:
        print(f"style similarity between them: highest {max(sims):.2f} (1 = identical); see {a.out_dir / 'compare.md'}")
    for note in notes:
        print(f"note: {note}")
    if a.stills:
        for d in chosen:
            print("stills " + make_stills(a.out_dir / d["name"] / "edit-plan.md", a.stills, d["name"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
