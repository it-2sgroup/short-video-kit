#!/usr/bin/env python3
"""Draft the edit plan of a talking-head service pitch (`talking-head:agency`) from the voice, the takes and the cutaways.

The pitch is a speaker to camera whose voice file was cut from the takes' own audio, with loud text blocks, portfolio cards over an
animated grid, a brand mark that lands on its name and a closing card. The mechanical half of that edit is the same every time, so
this script writes it; the creative half (which words become a block, which effect, which picture) is a first draft you refine in the plan.

    python scripts/agency_plan.py --words words.json --matches matches.json --cutaways cutaways.json \
        --brand SISMO --out edit-plan.md [--faces faces.json] [--flash C5074] [--tail 1.4] [--title "SISMO pitch"] \
        [--cta "INBOX NGAY" --cta-word inbox]

Run it TWICE: the first run writes the plan and `<out>.face-keys.txt` (the CLIP@seconds list to measure); run `person_matte.py --faces "$(cat
<out>.face-keys.txt)" --clips render/public/clips --faces-out faces.json`, then run this again with `--faces faces.json`.

Inputs (each from a kit script):
  words.json     align_captions.py --script ... --words-out   (script words, Whisper timing)
  matches.json   match_voice_takes.py --out                   (which take holds which stretch of the voice, and the lag)
  cutaways.json  find_cutaways.py --avoid matches.json --json (silent stretches of the takes: the cards' pictures)
  faces.json     person_matte.py --faces ... --faces-out      (optional: the head per CLIP@seconds, for the beauty light)
What it decides:
  * Talking scenes: each matched stretch is cut on the voice's pauses into scenes of ~1.3-3.4 s (never inside a word), `In = start + lag`
    so the lips are exact; framings alternate (hold/push at 1.0-1.4x); a new take enters with zoomThrough +leak, crossZoom or whip.
  * Card scenes: every stretch of the voice that no take holds (0.8 s or more) is cut on its phrases into 0.8-1.6 s cards with the best
    unused cutaways (never one range twice, never two cards from one clip in a row); a long last card grows to full frame (`expand`).
  * Text: every clause the speaker says on camera becomes a `phrase` block (a lead line and a loud emphasis line, effects rotating so no two
    neighbours match), the brand word (one or several words: --brand "Kiiro Sushi") triggers a `logo`, "từ N đến M" a `counter`, --cta-word
    (default "inbox") a neon call to action, and a phrase that would share the top with a logo or counter drops to y=0.285; the first words are a
    `burst` with the silhouette `Flash` on frame 0 when --flash CLIP is given. The closing card repeats the --cta text. Captions are hidden where a block says the words and run (box, glow,
    underline in turn) above the cards.
  * A closing card of --tail seconds with the logo.
Writes `edit-plan.md` for plan_to_project.py (Layout, Flash and Face columns included), then run pacing_checker.py and read the plan:
the draft is a starting point, not the answer. Needs nothing but Python 3.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

END_PUNCT = re.compile(r"[.!?…:;,]$")
SENT_END = re.compile(r"[.!?…]$")
FX_LEAD = ["rise", "maskwipe", "drop", "wave", "flip"]
FX_EMPH = ["stamp", "elastic", "glitch", "shine", "slam"]
CAMERAS = ["push 1.02>1.12", "hold 1.32", "push 1.10>1.22", "hold 1.40", "push 1.12>1.30", "hold 1.30"]
CARD_CAMERAS = ["push 1.14>1.26", "hold 1.22", "push 1.20>1.32", "hold 1.28"]
TAKE_ENTRY = ["zoomThrough 10f +leak", "crossZoom 14f", "whip left 10f", "whip right 10f"]
HIGHLIGHTS = ["box", "glow", "underline"]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def spans_from_matches(matches: dict, voice_len: float, min_corr: float, skip: set[str]) -> list[dict]:
    """Talking stretches [va, vb] with their take and lag, from the match table (the voice file itself is skipped)."""
    segs = []
    for stem, rows in matches.items():
        if stem.upper() in skip:
            continue
        for r in rows:
            if r["corr"] >= min_corr:
                segs.append({"clip": stem.upper(), "va": r["voice_from"], "vb": r["voice_to"], "lag": r["lag"]})
    segs.sort(key=lambda s: s["va"])
    out: list[dict] = []
    for s in segs:  # overlapping windows of two takes (a splice): the earlier one keeps the overlap
        if out and s["va"] < out[-1]["vb"] - 0.01:
            if s["clip"] == out[-1]["clip"] and abs(s["lag"] - out[-1]["lag"]) < 0.04:
                out[-1]["vb"] = max(out[-1]["vb"], s["vb"])
                continue
            s = {**s, "va": out[-1]["vb"]}
            if s["vb"] - s["va"] < 0.3:
                continue
        out.append(s)
    return out


def snap_to_words(t: float, words: list[dict]) -> float:
    """The nearest gap between words (or a word edge): cuts never fall inside a word."""
    best, bd = t, 9.0
    for i, w in enumerate(words):
        for edge in (w["start"], w["end"]):
            d = abs(edge - t)
            if d < bd:
                best, bd = edge, d
        if i + 1 < len(words):
            mid = (w["end"] + words[i + 1]["start"]) / 2
            d = abs(mid - t) * 0.7  # a pause's middle is the best place
            if d < bd:
                best, bd = mid, d
    return round(best, 2)


def boundaries(words: list[dict]) -> list[tuple[float, float]]:
    """Every word boundary as (time, bonus): the middle of the pause between two words; a sentence end or a pause is a better cut."""
    out = []
    for i, w in enumerate(words[:-1]):
        gap = words[i + 1]["start"] - w["end"]
        bonus = (0.6 if SENT_END.search(w["text"]) else 0.0) + (0.3 if gap >= 0.12 else 0.0)
        out.append((round((w["end"] + words[i + 1]["start"]) / 2, 2), bonus))
    return out


def split_range(a: float, b: float, words: list[dict], lo: float, hi: float, target: float) -> list[float]:
    """Cut points inside [a, b] on word boundaries, scenes between lo and hi seconds, near `target`, preferring sentence ends and pauses."""
    marks = [m for m in boundaries(words) if a < m[0] < b]
    cuts, t = [a], a
    while b - t > hi:
        window = [m for m in marks if t + lo <= m[0] <= min(t + hi, b - lo)]
        nxt = min(window, key=lambda m: abs(m[0] - (t + target)) - m[1])[0] if window else min(t + target, b - lo)
        cuts.append(round(nxt, 2))
        t = nxt
    return cuts


def clause_blocks(words: list[dict]) -> list[dict]:
    """Clauses: runs of words that end with , . ! ? : ;"""
    out, cur = [], []
    for w in words:
        cur.append(w)
        if END_PUNCT.search(w["text"]):
            out.append({"words": cur, "start": cur[0]["start"], "end": cur[-1]["end"]})
            cur = []
    if cur:
        out.append({"words": cur, "start": cur[0]["start"], "end": cur[-1]["end"]})
    return out


def clean(s: str) -> str:
    return re.sub(r"[.,!?…:;]+$", "", s.strip())


def split_lead_emph(ws: list[dict], max_emph: int = 28) -> tuple[str, str, float]:
    """Lead line (sentence case) and emphasis line (UPPER): the last words that fit in `max_emph` characters; returns (lead, emph, seconds
    from the clause start when the emphasis word starts)."""
    texts = [clean(w["text"]) for w in ws]
    n = len(texts)
    if sum(len(t) + 1 for t in texts) <= max_emph + 4 and n <= 4:
        return "", " ".join(texts).upper() + ("!" if ws[-1]["text"].endswith("!") else ""), 0.0
    k = 0
    while k < n - 1 and sum(len(t) + 1 for t in texts[n - k - 1:]) <= max_emph and k < 5:
        k += 1
    k = max(2, min(k, n - 1))
    lead = " ".join(texts[:n - k])
    emph = " ".join(texts[n - k:]).upper() + ("!" if ws[-1]["text"].endswith("!") else "")
    return lead, emph, max(0.0, ws[n - k]["start"] - ws[0]["start"])


def main() -> int:
    ap = argparse.ArgumentParser(description="Draft the edit plan of a talking-head service pitch.")
    ap.add_argument("--words", type=Path, required=True)
    ap.add_argument("--matches", type=Path, required=True)
    ap.add_argument("--cutaways", type=Path, required=True)
    ap.add_argument("--faces", type=Path, help="person_matte.py --faces-out JSON (CLIP@seconds keys)")
    ap.add_argument("--brand", default="", help="the brand name as spoken (one or more words): its word gets the logo")
    ap.add_argument("--cta", default="INBOX NGAY", help="the call to action on the neon block and the closing card (default INBOX NGAY)")
    ap.add_argument("--cta-word", default="inbox", help="the spoken word that triggers the neon call to action (default inbox)")
    ap.add_argument("--flash", metavar="CLIP", help="the first take: its first frames get the silhouette Flash (run person_matte.py first)")
    ap.add_argument("--voice-stem", default="", help="stem of the voice file inside the clips folder (skipped as a take)")
    ap.add_argument("--min-corr", type=float, default=0.85)
    ap.add_argument("--tail", type=float, default=1.4, help="seconds of closing card after the voice")
    ap.add_argument("--title", default="Service pitch")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()

    words = load(a.words)
    vend = words[-1]["end"] + 0.15
    matches = load(a.matches)
    skip = {a.voice_stem.upper()} if a.voice_stem else set()
    # the voice file itself matches itself over its whole length: skip any entry that covers (nearly) all of the voice
    for stem, rows in matches.items():
        if any(r["voice_to"] - r["voice_from"] > 0.9 * vend and r["clip_from"] < 0.5 for r in rows):
            skip.add(stem.upper())
    spans = spans_from_matches(matches, vend, a.min_corr, skip)
    if not spans:
        sys.exit("no take matches the voice: this script is for a voice cut from the takes (match_voice_takes.py); otherwise plan by hand")
    cut = [c for c in load(a.cutaways) if c["length"] >= 0.8]
    faces = load(a.faces) if a.faces else {}

    # ---- the timeline: talking spans and the gaps no take holds
    segs: list[dict] = []  # {kind talk|card, a, b, take?, lag?}
    t = 0.0
    for s in spans:
        if s["va"] - t >= 0.8:
            segs.append({"kind": "card", "a": t, "b": s["va"]})
        segs.append({"kind": "talk", "a": s["va"], "b": s["vb"], "take": s["clip"], "lag": s["lag"]})
        t = s["vb"]
    if vend - t >= 0.8:
        segs.append({"kind": "card", "a": t, "b": vend})
    elif segs[-1]["kind"] == "talk":
        segs[-1]["b"] = vend
    segs[0]["a"] = 0.0
    for i in range(1, len(segs)):  # tile with no gap: the boundary is the word boundary nearest the middle of the gap
        mid = (segs[i - 1]["b"] + segs[i]["a"]) / 2
        bd = min((m for m in boundaries(words)), key=lambda m: abs(m[0] - mid))[0]
        segs[i - 1]["b"] = segs[i]["a"] = bd

    # ---- scenes
    scenes: list[dict] = []
    used: list[tuple[str, float, float]] = []
    entry_i = cam_i = card_cam = 0
    last_card_clip = ""
    for si, sg in enumerate(segs):
        if sg["kind"] == "talk":
            pts = split_range(sg["a"], sg["b"], words, 1.2, 3.4, 2.1) + [sg["b"]]
            for k in range(len(pts) - 1):
                tr = "cut"
                if k == 0 and scenes and scenes[-1]["clip"] == sg["take"] and not scenes[-1]["layout"]:
                    tr = "cut"  # the same take after a splice: a jump cut
                elif k == 0 and scenes:
                    if scenes[-1]["layout"]:  # out of a card section: a whip, or the card swirl into a new section
                        tr = "cardSwirl 16f" if entry_i % 2 else "whip left 10f"
                    else:  # a new take
                        tr = TAKE_ENTRY[entry_i % len(TAKE_ENTRY)]
                    entry_i += 1
                scenes.append({"a": pts[k], "b": pts[k + 1], "clip": sg["take"], "in": round(pts[k] + sg["lag"], 3), "layout": "", "tr": tr if scenes else "–",
                               "cam": CAMERAS[cam_i % len(CAMERAS)], "take": sg["take"], "lag": sg["lag"]})
                cam_i += 1
        else:
            ws = [w for w in words if sg["a"] - 0.02 <= w["start"] < sg["b"]]
            # phrase boundaries inside the gap
            marks = [sg["a"]] + [round((w["end"] + (ws[i + 1]["start"] if i + 1 < len(ws) else w["end"] + 0.1)) / 2, 2) for i, w in enumerate(ws) if END_PUNCT.search(w["text"]) and i + 1 < len(ws)] + [sg["b"]]
            pts = [marks[0]]
            for m in marks[1:]:
                if m - pts[-1] >= 0.8 or m == marks[-1]:
                    pts.append(m)
            if len(pts) > 2 and pts[-1] - pts[-2] < 0.8:
                pts.pop(-2)
            # long cards are cut in half
            fin = [pts[0]]
            for m in pts[1:]:
                while m - fin[-1] > 2.0:
                    fin.append(round(fin[-1] + (m - fin[-1]) / 2, 2))
                fin.append(m)
            todo = [(fin[k], fin[k + 1], k == len(fin) - 2) for k in range(len(fin) - 1)]
            while todo:
                c0, c1, is_last = todo.pop(0)
                need = c1 - c0
                pick = None
                for c in cut:
                    if c["clip"] == last_card_clip and len(cut) > 6:
                        continue
                    if c["end"] - c["start"] >= need + 0.2 and not any(u[0] == c["clip"] and c["start"] < u[2] and c["end"] > u[1] for u in used):
                        pick = c
                        break
                if pick is None:
                    if need >= 1.6:  # no range is long enough: two cards of half the length
                        mid = round(c0 + need / 2, 2)
                        todo[:0] = [(c0, mid, False), (mid, c1, is_last)]
                        continue
                    sys.exit(f"no unused cutaway of {need:.1f} s left for the card at {c0:.1f}s: footage ran out (shoot more, run find_cutaways.py --min 0.8 --margin 0.1, or shorten the card)")
                last_card_clip = pick["clip"]
                used.append((pick["clip"], pick["start"], pick["start"] + need + 0.2))
                cut.remove(pick)
                lay = "expand" if (is_last and need >= 2.0) else "card"
                scenes.append({"a": c0, "b": c1, "clip": pick["clip"], "in": round(pick["start"] + 0.1, 2), "layout": lay,
                               "tr": "cut" if lay == "expand" else ("cardSlide 10f" if scenes else "–"), "cam": CARD_CAMERAS[card_cam % len(CARD_CAMERAS)], "take": None, "lag": 0})
                card_cam += 1
    scenes[0]["tr"] = "–"
    n_main = len(scenes)
    scenes.append({"a": round(vend, 2), "b": round(vend + a.tail, 2), "clip": None, "in": 0, "layout": "card", "tr": "cardSlide 12f", "cam": "", "take": None, "lag": 0})
    total = scenes[-1]["b"]
    scenes[0]["a"] = 0.0

    def stype(t0: float) -> str:
        f = t0 / vend
        return "HOOK" if t0 < 3 else "PROBLEM" if f < 0.15 else "SOLUTION" if f < 0.3 else "LIVING" if f < 0.6 else "PROOF" if f < 0.75 else "OFFER" if f < 0.9 else "CTA"

    # ---- face cells and the flash
    def face_keys(sc: dict) -> list[str]:
        return [f"{sc['clip']}@{sc['in'] + (sc['b'] - sc['a']) * f:.1f}" for f in (0.15, 0.5, 0.85)] if sc["clip"] else []

    def face_of(sc: dict) -> str:
        if not sc["clip"]:
            return ""
        vals = []
        for key in face_keys(sc):
            hit = faces.get(key)
            if hit:
                vals.append(hit)
        if not vals:
            near = [v for k, v in faces.items() if k.startswith(sc["clip"] + "@") and v]
            vals = near[:1]
        return ",".join(f"{sum(v[k] for v in vals) / len(vals):.4f}" for k in ("x", "y", "r")) if vals else ""

    # ---- overlays
    ov: list[tuple[float, float, str, str]] = []
    bands: list[tuple[float, float, str, str, str]] = []
    talk_ranges: list[list[float]] = []
    for sc in scenes[:n_main]:  # contiguous talking scenes are one stretch: a clause may cross a jump cut
        if sc["layout"]:
            continue
        if talk_ranges and abs(talk_ranges[-1][1] - sc["a"]) < 0.05:
            talk_ranges[-1][1] = sc["b"]
        else:
            talk_ranges.append([sc["a"], sc["b"]])

    def on_camera(t0: float, t1: float) -> bool:
        return any(a0 - 0.05 <= t0 and t1 <= b0 + 0.15 for a0, b0 in talk_ranges)

    fl = fe = 0
    brand = a.brand.lower().split()
    logo_until = -99.0
    clauses = clause_blocks(words)
    for ci, cl in enumerate(clauses):
        t0, t1 = cl["start"], cl["end"]
        ws = cl["words"]
        txt = " ".join(clean(w["text"]) for w in ws)
        if not on_camera(t0, t1):
            continue
        if ci == 0 and a.flash:
            first = " ".join(clean(w["text"]) for w in ws).upper()
            ov.append((0.30, min(1.05, t1 + 0.2), "burst", f"text={first}; at=0.5,0.215; speed=1.7"))
            continue
        lead, emph, emph_at = split_lead_emph(ws)
        end = round(min(t1 + 0.12, t1 + 0.4), 2)
        props = []
        if lead:
            props.append(f"lead={lead}; leadFx={FX_LEAD[fl % len(FX_LEAD)]}")
            fl += 1
        props.append(f"emph={emph}; fx={FX_EMPH[fe % len(FX_EMPH)]}")
        fe += 1
        if lead:
            props.append(f"emphAt={emph_at:.2f}")
        props.append("y=0.20")
        if len(ws) <= 3:
            props.append("exit=fade")
        ov.append((round(max(0.0, t0 - 0.1), 2), end, "phrase", "; ".join(props)))
        m = re.search(r"từ (\d+) đến (\d+)", txt.lower())
        if m:
            nxt = next((w for w in words if w["start"] >= t1), None)
            ov.append((round(t0 + 0.2, 2), round(t1 + 0.8, 2), "counter", f"from={m.group(1)}; to={m.group(2)}; label={clean(nxt['text']).upper() if nxt else ''}; at=0.5,0.185"))
    for i, w in enumerate(words):
        t0 = w["start"]
        names = [clean(x["text"]).lower() for x in words[i:i + len(brand)]]
        if brand and len(names) == len(brand) and names[0].startswith(brand[0]) and all(n == b for n, b in zip(names[1:], brand[1:])) \
                and t0 - logo_until > 8 and on_camera(t0, t0 + 0.3):
            ov.append((round(t0 - 0.05, 2), round(t0 + 2.9, 2), "logo", "at=0.5,0.185; width=380"))
            logo_until = t0 + 2.9
        if a.cta_word and clean(w["text"]).lower() == a.cta_word.lower():
            ov.append((round(t0 - 0.05, 2), round(t0 + 1.1, 2), "phrase", f"emph={a.cta}; y=0.16; emphColor=yellow; fx=neon; exit=fade"))
    # a phrase that would share the top with a logo or counter (the same strip, y 0.185) drops below it, as in the hand-finished SISMO plan
    logos = [(o0, o1) for o0, o1, c, _ in ov if c == "logo"]
    dropped = [o for o in ov if o[2] == "counter" and any(o[0] < b0 and o[1] > a0 for a0, b0 in logos)]   # one mark at a time in the top strip
    ov = [o for o in ov if o not in dropped]
    tops = [(o0, o1) for o0, o1, c, _ in ov if c in ("logo", "counter")]
    ov = [(o0, o1, c, content.replace("y=0.20", "y=0.285") if c == "phrase" and any(o0 < b0 and o1 - a0 > 0.15 for a0, b0 in tops) else content)
          for o0, o1, c, content in ov]
    ov.append((round(vend + 0.17, 2), round(total + 2, 2), "logo", "at=0.5,0.40; width=620; tint=white; hold=1"))
    ov.append((round(vend + 0.27, 2), round(total + 2, 2), "pill", f"text={a.cta}; variant=white; at=0.5,0.60; size=64"))

    # captions: hidden where a block says the words, a strip above the cards elsewhere
    cur_h = 0
    for s in scenes[:n_main]:
        if s["layout"]:
            bands.append((s["a"], s["b"], "250", "44", HIGHLIGHTS[cur_h % 3]))
        else:
            bands.append((s["a"], s["b"], "hide", "", ""))
    merged: list[list] = []
    for b in bands:
        if merged and merged[-1][2] == b[2] and merged[-1][4] == b[4] and abs(merged[-1][1] - b[0]) < 0.05:
            merged[-1][1] = b[1]
        else:
            if b[2] == "250" and merged and merged[-1][2] != "250":
                cur_h += 1
            merged.append(list(b))
    # a card section keeps one highlight; the next section changes it
    sect = -1
    prev_card = False
    for b in merged:
        if b[2] == "250":
            if not prev_card:
                sect += 1
            b[4] = HIGHLIGHTS[sect % 3]
            prev_card = True
        else:
            prev_card = False
    merged.append([vend, total + 2, "hide", "", ""])

    # ---- write
    rows = []
    for i, s in enumerate(scenes, 1):
        flash = f"0,2,4 @ mattes/{a.flash}" if (i == 1 and a.flash and s["clip"] == a.flash.upper()) else ""
        face = face_of(s)
        cam = s["cam"]
        if cam and face and not s["layout"] and "focus" not in cam:
            fx, fy, _ = (float(v) for v in face.split(","))
            cam += f" focus {fx:.2f},{max(0.3, min(0.55, fy - 0.08)):.2f}"
        elif cam and not s["layout"] and "focus" not in cam:
            cam += " focus 0.5,0.42"
        elif cam and s["layout"] and "focus" not in cam:
            cam += " focus 0.5,0.58"
        note = "closing card: logo" if not s["clip"] else ("talk" if not s["layout"] else "cutaway")
        rows.append(f"| {i} | {s['a']:.2f} | {s['b']:.2f} | {s['clip'] or '–'} | {s['in']:.3f} | {stype(s['a'])} | {s['layout']} | {s['tr']} | {cam} | | {flash} | {face} | {note} |")
    orows = [f"| {i} | {o0:.2f} | {o1:.2f} | {c} | – | – | {content} |" for i, (o0, o1, c, content) in enumerate(sorted(ov), 1)]
    brows = [f"| {b[0]:.2f} | {b[1]:.2f} | {b[2]} | {b[3]} | {b[4]} |" for b in merged]
    md = f"""# Edit Plan: {a.title}

**Playbook:** talking-head:agency
**Platform:** tiktok
**Target runtime:** {total:.0f} s
**Drive:** voice (cuts on pauses; each talking scene uses the take's own picture: In = start + lag from match_voice_takes.py)
**Look:** theme crimson, captions karaoke above the cards
**Source footage:** (fill in)

This is a DRAFT written by scripts/agency_plan.py: read every row, fix the text blocks, check the cards on a contact sheet.

---

## Scenes

| # | Start | End | Source | In | Type | Layout | Transition | Camera | Speed | Flash | Face | Shot |
|---|-------|-----|--------|----|------|--------|------------|--------|-------|-------|------|------|
""" + "\n".join(rows) + """

---

## Overlays

| # | Start | End | Component | Zone | Tone | Content |
|---|-------|-----|-----------|------|------|---------|
""" + "\n".join(orows) + """

---

## Caption bands

| Start | End | Top | Size | Highlight |
|-------|-----|-----|------|-----------|
""" + "\n".join(brows) + "\n"
    a.out.write_text(md, encoding="utf-8", newline="\n")
    ntalk = sum(1 for s in scenes if s["take"])
    print(f"wrote {a.out}: {len(scenes)} scenes ({ntalk} talking, {len(scenes) - ntalk - 1} cards, 1 closing card), {len(ov)} overlays, {total:.1f} s")
    keys = sorted({k for sc in scenes if not sc["layout"] for k in face_keys(sc)})
    keys_file = a.out.with_suffix(".face-keys.txt")
    keys_file.write_text(",".join(keys), encoding="utf-8")
    for o in dropped:
        print(f"note: the counter at {o[0]:.1f} s ({o[3].split(';')[0]} ...) was left out because the logo holds the top strip then: add it by hand where it fits")
    print(f"cutaways left: {len(cut)}; flash: {'yes' if a.flash else 'no'}; faces: {'yes' if faces else 'no'}")
    if not faces:
        print(f"next: person_matte.py --faces \"$(cat {keys_file})\" --clips <render>/public/clips --faces-out faces.json, then run this again with --faces faces.json "
              f"({len(keys)} head positions to measure)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
