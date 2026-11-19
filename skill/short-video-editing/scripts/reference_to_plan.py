#!/usr/bin/env python3
"""Turn a reference video's measurements (`analyze_reference.py` -> report.json) into a first-draft edit plan.

The reference decides WHEN and HOW MUCH (where the cuts fall, which transition joins them, how the camera moves, when and where text is on
screen, what colour it is, how it enters); YOU decide the content (which footage, which words). Nothing here is read from a genre playbook:
the plan names the neutral playbook `reference`, and `pacing_checker.py --reference report.json` judges the plan against the sample's own
numbers instead of a genre's.

    python scripts/reference_to_plan.py ref/report.json --out edit-plan.md [--duration 38] [--words words.json]
        [--texts texts.txt] [--genre product-demo] [--title "Name"]

  --duration   runtime of YOUR video; every time of the sample is scaled by duration / sample length (default: the sample's own length,
               scale 1). Transition lengths stay in frames: a 10-frame wipe is a 10-frame wipe.
  --words      word timings of YOUR voice (align_captions.py --words-out): cuts within 0.3 s of a pause are moved onto the pause (never
               inside a word), and a text slot with no line of its own is filled from the words spoken while it is on screen.
  --texts      the lines YOUR on-screen text says, one per line, in the order the sample shows its text. `@12.4 | TEXT` binds a line to the
               slot nearest to that time of the sample. Without --texts and --words a slot keeps its geometry and timing, and the text is
               listed under "Slots without text" for you to write: an OCR string of the sample is never copied into your video.
  --genre      a playbook id whose compliance checklist is copied into the plan (claims in a product demo are still claims when the
               rhythm comes from a sample); its numbers (scene length, transitions, camera) are NOT used.

What it writes (see references/reference-analysis.md for how reliable each source is):
  Scenes     one row per shot of the sample: Start/End (scaled, snapped), Transition from `transitions[]` (family, direction, frames),
             Camera from `shots[].camera` (push/pull/pan/hold, eased keys, handheld shake), Source/In left as [CLIP]/[s] for plan_scenes.py
             or your own hand. The Shot cell says what the sample showed (edge and centre colour) and what to look at.
  Overlays   one row per text event of the sample that is not a caption: Start/End, a vertical position, a colour from the sample's ink,
             an entry effect from its measured entry motion. Component `textbox` (default; `--text-component phrase` for the older blocks) takes the sample's own box.
  Captions   a text that appears as many short lines in the lower part of the frame is a caption track: it becomes a Caption bands row.
  Notes      under each table: what the sample had at each place, and everything that needs a human look (`needs_look`).
Needs only Python 3.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import playbook as playbooks  # noqa: E402

FRAME_H = 1920
BS = chr(92)         # the escape character of the plan tables
FPS = 30
SNAP = 0.30          # a cut moves at most this far onto a pause of the voice
MIN_SCENE = 0.10     # snapping never makes a scene shorter than this
EASE_KEY = {"ease-in": "in", "ease-out": "out", "ease-in-out": "inOut"}
# the sample's measured entry motion -> a text effect of the template (Fx.tsx); the rest keep the default and say "look"
ENTRY_FX = {"fade": "blurin", "pop": "elastic", "typewriter": "typewriter", "slide": "rise"}
CAPTION_MIN_EVENTS = 5
CAPTION_MAX_SECONDS = 1.3
PHRASE_CAPACITY = 28


# ----------------------------------------------------------------------------- the report
def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def fmt(x: float) -> str:
    return f"{x:.2f}".rstrip("0").rstrip(".") or "0"


# ----------------------------------------------------------------------------- scenes
def snap_to_pauses(t: float, words: list[dict]) -> float:
    """Move `t` onto the middle of the nearest pause between two words, if one lies within SNAP seconds; otherwise leave it."""
    best, bd = t, SNAP + 1
    for a, b in zip(words, words[1:]):
        if b["start"] - a["end"] < 0.04:
            continue                                  # no real pause: a cut here would land inside running speech
        mid = (a["end"] + b["start"]) / 2
        if abs(mid - t) < bd:
            best, bd = mid, abs(mid - t)
    return round(best, 3) if bd <= SNAP else t


def scene_bounds(shots: list[dict], k: float, words: list[dict] | None) -> list[tuple[float, float]]:
    """Scaled [start, end) of every shot; the boundaries tile the timeline exactly."""
    cuts = [round(s["start"] * k, 3) for s in shots[1:]]
    if words:
        cuts = [snap_to_pauses(c, words) for c in cuts]
    total = round(shots[-1]["end"] * k, 3)
    pts = [0.0]
    for c in cuts:                                    # keep order and a minimum length even after snapping
        pts.append(max(c, pts[-1] + MIN_SCENE))
    pts.append(max(total, pts[-1] + MIN_SCENE))
    return list(zip(pts, pts[1:]))


def run_for(shot_start: float, runs: list[dict]) -> dict | None:
    """The motion run whose middle is the shot boundary (analyze_reference puts the boundary of a transition in its middle)."""
    best = None
    for t in runs:
        mid = t["t"] + t.get("seconds", 0) / 2
        if abs(mid - shot_start) <= 0.25 and (best is None or abs(mid - shot_start) < abs(best["t"] + best.get("seconds", 0) / 2 - shot_start)):
            best = t
    return best


def transition_cell(i: int, shot: dict, runs: list[dict], cuts: list[dict], flashes: list[float]) -> tuple[str, str]:
    """(Transition cell, note). The family is measured; the geometry (which way, which shape) is not: those carry a note."""
    if i == 0:
        return "–", ""
    enter = shot.get("enter", "hard-cut")
    notes = []
    if enter in ("hard-cut", "start"):
        cut = next((c for c in cuts if abs(c["t"] - shot["start"]) <= 0.1), None)
        fam = (cut or {}).get("family", "hard-cut")
        cell = "cut +flash" if fam == "flash-cut" else "cut"
        if fam == "dip-cut":
            notes.append("a dark frame sits inside this cut")
        if (cut or {}).get("needs_look"):
            notes.append(f"look at the cut ({fam})")
        if any(abs(f - shot["start"]) <= 0.2 for f in flashes) and "+flash" not in cell:
            cell += " +flash"
        return cell, "; ".join(notes)
    run = run_for(shot["start"], runs) or {}
    frames = int(run.get("frames", 0))
    f = f" {frames}f" if 3 <= frames <= 45 else ""
    d = run.get("direction") or ""
    d = f" {d}" if d in ("left", "right", "up", "down") else ""
    cell = {"crossfade": f"fade{f}", "dip-to-black": f"fade{f}", "dip-to-white": f"fade{f}", "dissolve": f"blurDissolve{f}",
            "mask-wipe": f"wipe{d}{f}", "mask-iris": f"iris{f}", "slide": f"slide{d}{f}", "cover": f"slide{d}{f}", "reveal": f"slide{d}{f}"}.get(enter)
    if cell is None:
        return f"cut", f"the sample has a transition here that was not classified ({enter}); look at its dense sheet and pick one from `technique.py list --kind transition`"
    if enter in ("dip-to-black", "dip-to-white", "dissolve", "cover", "reveal", "mask-iris", "mask-wipe") or run.get("needs_look"):
        notes.append(f"sample: {enter}{(' ' + d.strip()) if d else ''}, {frames} frames; check the family and the direction on the dense sheet")
    return cell, "; ".join(notes)


def camera_cell(shot: dict) -> tuple[str, str]:
    cam = shot.get("camera") or {}
    if cam.get("quality") != "ok":
        return "", f"camera of the sample unknown ({cam.get('reason', 'unreliable')}): leave it blank or set it by eye"
    drv, z = cam.get("driver", "static"), float(cam.get("zoom_end", 1.0))
    ease = EASE_KEY.get(cam.get("ease", ""), "")
    shake = " shake mild" if (cam.get("shake") or {}).get("level") == "handheld" else ""
    note = "camera numbers are measured, the framing is yours: check the subject stays in frame"
    if drv == "static":
        return "hold" + shake, ""
    if drv == "zoom-in":
        a, b = 1.0, max(z, 1.02)
    elif drv == "zoom-out":
        a, b = max(1 / z, 1.02) if z > 0 else 1.2, 1.0
    elif drv.startswith("pan-"):
        pct = abs(cam.get("pan_x" if drv in ("pan-left", "pan-right") else "pan_y", 0.0)) * 100
        return f"pan {drv[4:]} {max(2, round(pct))}% 1.15>1.15{shake}", note + " (the direction word is the sample's camera travel: confirm on the strip)"
    else:
        return "", ""
    if ease and abs(b - a) >= 0.05:
        return f"keys 0={a:.2f} ; 1={b:.2f} {ease}{shake}", note
    move = "push" if drv == "zoom-in" else "pull"
    return f"{move} {a:.2f}>{b:.2f}{shake}", note


def shot_note(i: int, shot: dict, extra: list[str]) -> str:
    sp = shot.get("speed") or {}
    bits = [f"sample shot {i + 1}: edge {shot.get('edge', '?')}, centre {shot.get('centre', '?')}"]
    if sp.get("ramp", "none") != "none":
        bits.append(f"speed {sp['ramp']} x{sp.get('ramp_factor')} (hypothesis: look)")
    if sp.get("frozen_runs"):
        bits.append("freeze " + ", ".join(f"{r['start']:g}s x{r['seconds']:g}" for r in sp["frozen_runs"]))
    return "; ".join(bits + [e for e in extra if e])


# ----------------------------------------------------------------------------- text
def is_caption_track(events: list[dict]) -> set[str]:
    """Ids of the events that form a caption track: many short lines in the lower part of the frame."""
    low = [e for e in events if e["bbox"][1] + e["bbox"][3] / 2 >= 0.62 and e["t_out"] - e["t_in"] <= CAPTION_MAX_SECONDS]
    return {e["id"] for e in low} if len(low) >= CAPTION_MIN_EVENTS else set()


def ink_name(hexcol: str | None) -> str:
    """white / yellow / red from the sample's ink: the three colours the `phrase` emphasis line has."""
    if not hexcol or not re.fullmatch(r"#?[0-9a-fA-F]{6}", hexcol):
        return ""
    h = hexcol.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    if min(r, g, b) > 190:
        return "white"
    if r > 180 and g > 150 and b < 120:
        return "yellow"
    if r > g + 40 and r > b + 40:
        return "red"
    return ""


def words_in(words: list[dict], t0: float, t1: float) -> list[str]:
    return [w["text"].strip(".,!?…:;") for w in words if w["end"] >= t0 - 0.15 and w["start"] <= t1 + 0.15]


def fit_words(ws: list[str], capacity: int) -> str:
    """The last words that fit `capacity` characters: the end of a spoken thought is its point."""
    out, n = [], 0
    for w in reversed(ws):
        if n + len(w) + (1 if out else 0) > capacity and out:
            break
        out.insert(0, w)
        n += len(w) + 1
    return " ".join(out)


def read_texts(path: Path | None) -> tuple[list[str], dict[float, str]]:
    seq, bound = [], {}
    if path is None:
        return seq, bound
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^@([\d.]+)\s*\|\s*(.+)$", line)
        if m:
            bound[float(m.group(1))] = m.group(2).strip()
        else:
            seq.append(line)
    return seq, bound


def split_lead_emph(text: str) -> tuple[str, str]:
    ws = text.split()
    if len(text) <= PHRASE_CAPACITY or len(ws) < 3:
        return "", text
    emph = fit_words(ws, PHRASE_CAPACITY)
    k = len(emph.split())
    return " ".join(ws[:-k]), emph


def esc(text: str) -> str:
    """Make a line safe inside a plan table cell: ';' ends a key, '|' ends a cell, ' / ' separates list items."""
    return text.replace(";", BS + ";").replace("|", BS + "|").replace(" / ", " " + BS + "/ ")


def textbox_content(e: dict, txt: str, fx: str) -> str:
    """The Content cell of a `textbox` overlay: the sample's own box, size, alignment, ink and entry; the user's words."""
    x, y, w, h = e["bbox"]
    st = e.get("style") or {}
    padx, pady = 0.04, h * 0.25
    bx, by = max(0.0, x - padx), max(0.0, y - pady / 2)
    bw, bh = min(1.0 - bx, w + 2 * padx), min(1.0 - by, h + pady)
    cx = x + w / 2
    size_px = min(160, max(30, round(float(st.get("size_frac_est", h / 0.72)) * FRAME_H)))
    parts = [f"text={esc(txt)}", f"box={bx:.3f},{by:.3f},{bw:.3f},{bh:.3f}", f"size={size_px}", f"align={'center' if abs(cx - 0.5) < 0.08 else 'left' if cx < 0.5 else 'right'}"]
    if e["text"].strip() and e["text"].strip() == e["text"].strip().upper() and any(ch.isalpha() for ch in e["text"]):
        parts.append("case=upper")
    if re.fullmatch(r"#[0-9a-fA-F]{6}", st.get("fill") or ""):
        parts.append(f"color={st['fill']}")
    if re.fullmatch(r"#[0-9a-fA-F]{6}", st.get("stroke") or ""):
        parts.append(f"stroke={st['stroke']}")
    elif st.get("fill"):
        parts.append("stroke=none")
    cands = (e.get("font") or {}).get("in_kit_candidates")
    if isinstance(cands, list) and cands and isinstance(cands[0], str):
        parts.append(f"font={cands[0]}")
    if fx:
        parts.append(f"in={fx}")
    parts.append("out=fade")
    return "; ".join(parts)


def overlay_rows(events: list[dict], k: float, texts: tuple[list[str], dict[float, str]], words: list[dict] | None, mode: str = "textbox"):
    """(rows, notes, unfilled). Rows: [start, end, component, content]. mode: `textbox` (the sample's box, measured fit) or `phrase` (the older
    vertical-position-only blocks)."""
    seq, bound = texts
    seq = list(seq)
    rows, notes, unfilled = [], [], []
    for e in events:
        t0, t1 = round(e["t_in"] * k, 2), round(e["t_out"] * k, 2)
        ref = e["text"].strip()
        x, y, w, h = e["bbox"]
        txt, src = "", ""
        near = min(bound, key=lambda b: abs(b - e["t_in"]), default=None)
        if near is not None and abs(near - e["t_in"]) <= 1.0:
            txt, src = bound.pop(near), "--texts (bound)"
        elif seq:
            txt, src = seq.pop(0), "--texts"
        elif words:
            txt = fit_words(words_in(words, t0, t1), max(6, min(PHRASE_CAPACITY if mode == "phrase" else 60, int(len(ref) * 1.15))))
            src = "spoken words" if txt else ""
        geom = f"sample box x {x:.2f} y {y:.2f} w {w:.2f} h {h:.2f}, {e['t_in']:g}-{e['t_out']:g} s"
        if not txt:
            unfilled.append(f"{t0:g}-{t1:g} s: {geom}; the sample said {len(ref)} characters ({e.get('motion_in', {}).get('family', '?')} in)")
            continue
        st = e.get("style") or {}
        fx = ENTRY_FX.get((e.get("motion_in") or {}).get("family", ""), "")
        colour = ink_name(st.get("fill"))
        if mode == "textbox":
            comp, content = "textbox", textbox_content(e, txt, fx)
        elif len(txt) <= 30 and h < 0.04:
            comp, content = "pill", f"text={txt.upper()}; at={x + w / 2:.2f},{y + h / 2:.2f}; size={max(30, round(h * FRAME_H * 0.9))}"
            if colour in ("white", "yellow", "red"):
                content += f"; variant={'white' if colour == 'white' else 'red' if colour == 'red' else 'yellow'}"
        else:
            lead, emph = split_lead_emph(txt)
            parts = [f"lead={lead}"] if lead else []
            parts.append(f"emph={emph.upper()}")
            parts.append(f"y={max(0.05, y - (0.035 if lead else 0)):.3f}")
            if colour in ("white", "yellow"):
                parts.append(f"emphColor={colour}")
            if fx:
                parts.append(f"fx={fx}")
            parts.append("exit=fade")
            comp, content = "phrase", "; ".join(parts)
        doubts = [b for b in ("the entry animation was not measured" if not fx else "", "OCR confidence under 0.8" if e.get("conf", 1) < 0.8 else "",
                              "timing is sampled, not frame-exact" if e.get("precision") != "frame" else "") if b]
        look = f" (look: {', '.join(doubts)})" if doubts else ""
        rows.append([t0, t1, comp, content])
        notes.append(f"{t0:g}-{t1:g} s {comp}: text from {src}; {geom}; ink {st.get('fill', '?')}{look}")
    if mode == "phrase":
        for i, a in enumerate(rows):
            for b in rows[i + 1:]:
                if a[0] < b[1] and b[0] < a[1]:
                    notes.append(f"! {a[0]:g}-{a[1]:g} s and {b[0]:g}-{b[1]:g} s are on screen together: phrase blocks are stacked at their own positions, so look at the stills")
    # textbox rows carry the sample's own boxes: where two of them really overlap, layout_check.py (run by plan_to_project.py) says so
    return rows, notes, unfilled


def caption_band(events: list[dict], k: float) -> str:
    if not events:
        return ""
    top = min(e["bbox"][1] for e in events)
    size = sorted(e["bbox"][3] for e in events)[len(events) // 2]
    t0, t1 = min(e["t_in"] for e in events) * k, max(e["t_out"] for e in events) * k
    return f"| {t0:.2f} | {t1:.2f} | {round(top * FRAME_H)} | {max(30, round(size * FRAME_H * 0.8))} | |"


# ----------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description="Draft an edit plan from a reference video's report.json.")
    ap.add_argument("report", type=Path, help="report.json written by analyze_reference.py")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--duration", type=float, help="runtime of your video in seconds (default: the sample's)")
    ap.add_argument("--words", type=Path, help="words.json of your voice (align_captions.py --words-out)")
    ap.add_argument("--texts", type=Path, help="your on-screen lines, one per line; '@12.4 | TEXT' binds a line to the sample's slot nearest 12.4 s")
    ap.add_argument("--genre", help="playbook id whose compliance checklist is copied into the plan")
    ap.add_argument("--title", default="Video made like a reference")
    ap.add_argument("--platform", default="tiktok")
    ap.add_argument("--text-component", choices=["textbox", "phrase"], default="textbox",
                    help="textbox: the sample's own box, measured wrapping and fit (default); phrase: the older blocks positioned by height only")
    a = ap.parse_args()

    rep = load(a.report)
    shots = rep.get("shots") or []
    if not shots:
        sys.exit("the report has no shots: run analyze_reference.py first")
    ref_dur = float(rep["duration"])
    k = (a.duration / ref_dur) if a.duration else 1.0
    words = load(a.words) if a.words else None
    texts = read_texts(a.texts)
    bounds = scene_bounds(shots, k, words)
    total = bounds[-1][1]
    runs = [t for t in rep.get("transitions", []) if t.get("kind") == "run"]
    cuts = [t for t in rep.get("transitions", []) if t.get("kind") == "cut"]
    flashes = rep.get("flashes", [])

    srows, snotes = [], []
    for i, (shot, (s, e)) in enumerate(zip(shots, bounds)):
        tr, tnote = transition_cell(i, shot, runs, cuts, flashes)
        cam, cnote = camera_cell(shot)
        srows.append(f"| {i + 1} | {fmt(s)} | {fmt(e)} | [CLIP] | [s] | {'HOOK' if s < 3 - 1e-6 else 'SHOT'} | {tr} | {cam} | | {shot_note(i, shot, [tnote, cnote])} |")
        if tnote or cnote:
            snotes.append(f"- scene {i + 1} ({fmt(s)}-{fmt(e)} s): " + "; ".join(x for x in (tnote, cnote) if x))

    events = rep.get("text_events") or []
    cap_ids = is_caption_track(events)
    ov_events = [e for e in events if e["id"] not in cap_ids]
    orows, onotes, unfilled = overlay_rows(ov_events, k, texts, words, a.text_component)
    band = caption_band([e for e in events if e["id"] in cap_ids], k)

    g = (rep.get("grade") or {}).get("nearest") or []
    near = ", ".join(f"{x.get('look') or x.get('id') or x}" if isinstance(x, dict) else str(x) for x in g[:2])
    sl = rep.get("shot_length", {})
    loud = rep.get("loudness") or {}
    head = [f"# Edit Plan: {a.title}", "",
            "**Playbook:** reference",
            f"**Platform:** {a.platform}",
            f"**Target runtime:** {total:.1f} s (the sample runs {ref_dur:.1f} s; every time is scaled by {k:.3f})",
            f"**Reference:** {rep.get('video', '?')}: {sl.get('count', len(shots))} shots, median {sl.get('median', '?')} s, shortest {sl.get('shortest', '?')} s, {sl.get('cuts_per_minute', '?')} cuts/min",
            f"**Look:** nearest kit grade to the sample (indicative, look at stills side by side): {near or 'not measured'}",
            f"**Sound of the sample:** {loud.get('lufs', loud.get('integrated', '?'))} LUFS" if loud else "**Sound of the sample:** none measured",
            "**Source footage:** (fill in)", "",
            "This is a DRAFT written by scripts/reference_to_plan.py from the sample's measurements. The rhythm, transitions, camera and text slots are the sample's;",
            "the footage and the words are yours. Check it with `pacing_checker.py edit-plan.md --reference REPORT.json`.", "", "---", "", "## Scenes", "",
            "| # | Start | End | Source | In | Type | Transition | Camera | Speed | Shot |",
            "|---|-------|-----|--------|----|------|------------|--------|-------|------|"]
    out = head + srows
    if snotes:
        out += ["", "Notes on the scenes:"] + snotes
    out += ["", "---", "", "## Overlays", "", "| # | Start | End | Component | Zone | Tone | Content |", "|---|-------|-----|-----------|------|------|---------|"]
    out += [f"| {i} | {r[0]:g} | {r[1]:g} | {r[2]} | – | – | {r[3]} |" for i, r in enumerate(orows, 1)]
    if onotes:
        out += ["", "Notes on the overlays (what the sample had at each place):"] + [f"- {n}" for n in onotes]
    if unfilled:
        out += ["", "Slots without text (the sample shows text here; write yours, then add an Overlays row with `textbox`):"] + [f"- {u}" for u in unfilled]
    if band:
        out += ["", "---", "", "## Caption bands", "", "| Start | End | Top | Size | Highlight |", "|-------|-----|-----|------|-----------|", band, "",
                f"The sample's lower text is a caption track ({len(cap_ids)} short lines): the spoken captions of your voice (`--captions captions.srt`) take this band; set the style with `--caption-style`."]
    elif not (rep.get("text") or {}).get("available"):
        out += ["", "The report has no text events (OCR was off or not installed: `./setup.sh --ocr`, then analyze_reference.py again): read the text of the sample from `scenes.png` and the dense sheets, and add the Overlays rows by hand."]
    if a.genre:
        pb = playbooks.load(a.genre)
        out += ["", "---", "", f"## Compliance check (from `{pb['name']}`; its numbers are not used)", ""] + [f"- [ ] {c}" for c in pb["compliance"]]
    out += ["", "## Pacing check result", "", "```", "```", ""]
    a.out.write_text("\n".join(out), encoding="utf-8", newline="\n")
    print(f"wrote {a.out}: {len(srows)} scenes, {len(orows)} overlay rows, {len(unfilled)} slot(s) without text, "
          f"{'a caption band' if band else 'no caption band'}, {total:.1f} s")
    print(f"next: fill [CLIP]/[s] (plan_scenes.py or by hand), write the slots without text, pacing_checker.py {a.out} --reference {a.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
