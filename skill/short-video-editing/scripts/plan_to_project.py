#!/usr/bin/env python3
"""Compile an edit plan (markdown) into the project.json rendered by assets/remotion-template.

The plan stays the single source of truth: pacing_checker.py and footage_overlap_checker.py read
the same tables. Nothing about a video is typed into code.

    python scripts/plan_to_project.py plan.md --voice audio/kb7.mp3 \
        --captions captions.srt --words words.json --out remotion/project.json \
        [--auto-camera] [--punch-keywords "saiza,chai hồng,100"] [--caption-style karaoke]

Scenes table (columns by name, any order; extra columns are ignored):
  Start | End | Source | In | Type | Transition | Camera
    Transition  fade | slide [left|right|up|down] | wipe [dir] | iris | pushCut | zoomThrough |
                blurDissolve | whip [dir] | flip [dir] | crossZoom | cut, optional "14f",
                optional accent "+flash" or "+leak" (e.g. "slide up +flash")
    Camera      push [a>b] | pull [a>b] | pan left|right|up|down [6%] | hold, optional
                "focus 0.5,0.4". Blank + --auto-camera = rule-based variety.

Overlays table:  Start | End | Component | Zone | Tone | Content
    Start  seconds, or @"word or phrase"[#n] (n-th occurrence) -> word start minus 3 frames
    End    seconds, +2.5 (duration), auto (reading time), @"word" (end of that word),
           or cut (3 frames before the next scene cut)
    Component  any key of the template registry: title, callout, checklist, step, price, cart,
           highlight, sticker, magnifier, thumbs, ranking, progress, lowerThird,
           plus two pseudo-components: punch (camera punch-in) and sfx (sound cue)
    Content  key=value pairs separated by ';'. Lists use ' / ', points use 'x,y' (0..1).
           e.g.  style=stack; lines=đợi vừa lâu / vừa tốn token; accent=token
                 label=2 cổng USB-C; target=0.42,0.55; side=left
                 cards=IMG_0326@40:Áo thun / IMG_0330@17:Tất     (thumbs)
                 items=Claude#1 / Manus#1 / ChatGPT#2           (ranking)

It also prints a sync report: cuts inside words, text appearing or vanishing on a cut, graphics in
the right-rail no-go zone, caption reading speed. Warnings do not stop the build; errors do.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

FPS = 30
LEAD = 3 / FPS  # graphics land 3 frames before their word
KNOWN = {"title", "callout", "checklist", "step", "price", "cart", "highlight", "sticker",
         "magnifier", "thumbs", "ranking", "progress", "lowerThird", "punch", "sfx"}
CANON = {t.lower(): t for t in ["fade", "slide", "wipe", "iris", "pushCut", "zoomThrough",
                                 "blurDissolve", "whip", "flip", "crossZoom", "cut"]}
DIRS = {"left", "right", "up", "down"}


# ----------------------------------------------------------------------------- markdown tables
def tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
    out, header, rows = [], None, []
    for line in text.splitlines() + [""]:
        s = line.strip()
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if header is None:
                header = [c.lower() for c in cells]
            elif not set("".join(cells)) <= set("-: "):
                rows.append(cells)
        elif header is not None:
            out.append((header, rows))
            header, rows = None, []
    return out


def pick(tabs, *need):
    for h, rows in tabs:
        if all(n in h for n in need):
            return h, rows
    return None, []


def cell(h, row, name):
    i = h.index(name) if name in h else -1
    return row[i].strip() if 0 <= i < len(row) else ""


# ----------------------------------------------------------------------------- words / anchors
def fold(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")
    return re.sub(r"[^a-z0-9 ]", "", s)


def find_phrase(words, phrase: str, nth: int = 1):
    target = fold(phrase).split()
    folded = [fold(w["text"]) for w in words]
    hits = 0
    for i in range(len(words) - len(target) + 1):
        if [folded[i + k].strip() for k in range(len(target))] == target:
            hits += 1
            if hits == nth:
                return words[i], words[i + len(target) - 1]
    return None


ANCHOR = re.compile(r'^@"(.+?)"(?:#(\d+))?$')


def resolve_time(raw: str, words, which: str, scene_cuts, start=None, text_len=0, problems=None):
    raw = raw.strip()
    m = ANCHOR.match(raw)
    if m:
        hit = find_phrase(words, m.group(1), int(m.group(2) or 1))
        if not hit:
            problems.append(f'anchor @"{m.group(1)}" not found in the word timings')
            return None
        return round(hit[0]["start"] - LEAD, 3) if which == "start" else round(hit[1]["end"], 3)
    if which == "end":
        if raw.startswith("+"):
            return round(start + float(raw[1:]), 3)
        if raw == "auto":
            return round(start + max(0.83, 0.3 + text_len / 15), 3)
        if raw == "cut":
            nxt = [c for c in scene_cuts if c > start + 0.2]
            return round((nxt[0] if nxt else start + 3) - 3 / FPS, 3)
    try:
        return float(raw)
    except ValueError:
        problems.append(f"cannot read time '{raw}'")
        return None


# ----------------------------------------------------------------------------- cells
def parse_transition(raw: str):
    if not raw or raw in "-–":
        return None, None
    accent = "flash" if "+flash" in raw else "lightLeak" if "+leak" in raw else None
    parts = re.sub(r"\+\w+", "", raw).split()
    t = {"type": CANON.get(parts[0].lower(), "fade")} if parts else {"type": "fade"}
    for p in parts[1:]:
        if p.lower() in DIRS:
            t["direction"] = p.lower()
        elif re.fullmatch(r"\d+f", p):
            t["frames"] = int(p[:-1])
        elif re.fullmatch(r"[\d.]+s", p):
            t["frames"] = round(float(p[:-1]) * FPS)
    return t, accent


def parse_camera(raw: str):
    if not raw or raw in "-–":
        return None
    cam, parts = {}, raw.replace(",", " , ").split()
    cam["move"] = parts[0].lower() if parts[0].lower() in {"push", "pull", "pan", "hold"} else "push"
    rng = re.search(r"([\d.]+)\s*>\s*([\d.]+)", raw)
    if rng:
        cam["from"], cam["to"] = float(rng.group(1)), float(rng.group(2))
    if cam["move"] == "pan":
        d = next((p for p in parts if p.lower() in DIRS), "left")
        pct = re.search(r"(\d+(?:\.\d+)?)%", raw)
        a = float(pct.group(1)) / 100 if pct else 0.06
        cam["pan"] = {"left": [-a, 0], "right": [a, 0], "up": [0, -a], "down": [0, a]}[d]
    foc = re.search(r"focus\s+([\d.]+)\s*,\s*([\d.]+)", raw)
    if foc:
        cam["focus"] = [float(foc.group(1)), float(foc.group(2))]
    return cam


def value(v: str):
    v = v.strip()
    if " / " in v:
        return [x.strip() for x in v.split(" / ")]
    if re.fullmatch(r"-?[\d.]+\s*,\s*-?[\d.]+", v):
        return [float(x) for x in v.split(",")]
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if re.fullmatch(r"-?\d*\.\d+", v):
        return float(v)
    return v


def parse_content(component: str, raw: str) -> dict:
    props = {}
    for chunk in filter(None, (c.strip() for c in raw.split(";"))):
        if "=" not in chunk:
            continue
        k, v = chunk.split("=", 1)
        props[k.strip()] = value(v)
    if component == "title" and isinstance(props.get("lines"), str):
        props["lines"] = [props["lines"]]
    if component == "checklist" and isinstance(props.get("items"), str):
        props["items"] = [props["items"]]
    if component == "thumbs":
        cards = props.get("cards", [])
        cards = [cards] if isinstance(cards, str) else cards
        out = []
        for c in cards:
            m = re.match(r"(\S+)@([\d.]+)(?::(.*))?", c)
            if m:
                out.append({"clip": Path(m.group(1)).stem.upper(), "at": float(m.group(2)), "caption": (m.group(3) or "").strip()})
        props["cards"] = out
    if component == "ranking":
        items = props.get("items", [])
        items = [items] if isinstance(items, str) else items
        props["items"] = [{"label": i.split("#")[0].strip(), "rank": (i.split("#")[1].strip() if "#" in i else None)} for i in items]
    if component == "magnifier" and "clip" in props:
        props["clip"] = Path(str(props["clip"])).stem.upper()
    return props


def text_of(props: dict) -> str:
    bits = []
    for k in ("lines", "label", "text", "items", "sub", "title"):
        v = props.get(k)
        bits += v if isinstance(v, list) else [str(v)] if v else []
    return " ".join(map(str, bits))


# ----------------------------------------------------------------------------- captions
def read_srt(path: Path):
    blocks = re.split(r"\n\s*\n", path.read_text(encoding="utf-8-sig").strip())
    out = []
    for b in blocks:
        lines = [l for l in b.splitlines() if l.strip()]
        m = re.search(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", "\n".join(lines))
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        s = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        e = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        text = " ".join(l for l in lines if "-->" not in l and not l.strip().isdigit())
        out.append({"text": text.strip(), "start": round(s, 3), "end": round(e, 3)})
    return out


# ----------------------------------------------------------------------------- auto direction
def auto_camera(scenes):
    """Vary the virtual camera: alternate push/pull, change scale tier every 2-3 scenes."""
    pattern = [
        {"move": "push", "from": 1.0, "to": 1.07},
        {"move": "push", "from": 1.06, "to": 1.14},
        {"move": "pull", "from": 1.16, "to": 1.02},
        {"move": "pan", "pan": [-0.05, 0]},
        {"move": "push", "from": 1.0, "to": 1.08},
        {"move": "pan", "pan": [0.05, 0]},
        {"move": "pull", "from": 1.12, "to": 1.0},
    ]
    k = 0
    for s in scenes:
        if s.get("camera"):
            continue
        if s.get("type") in ("REVEAL",):
            s["camera"] = {"move": "hold", "from": 1.03}  # let the result read; no motion fighting it
        elif s.get("type") == "CTA-CLOSE":
            s["camera"] = {"move": "push", "from": 1.0, "to": 1.05}  # calm, room for the cart arrow
        else:
            s["camera"] = dict(pattern[k % len(pattern)])
            k += 1


def auto_punches(words, keywords, cuts, existing, limit=6):
    if not words or not keywords:
        return []
    keys = [fold(k).split() for k in keywords if k.strip()]
    chosen = sorted(p["at"] for p in existing)
    out = []
    for i, w in enumerate(words):
        for key in keys:
            seg = [fold(x["text"]).strip() for x in words[i:i + len(key)]]
            if seg != key:
                continue
            at = round(w["start"] - 2 / FPS, 3)
            if any(abs(at - c) < 0.5 for c in cuts):  # a cut already changes the frame here
                continue
            if any(abs(at - c) < 3.0 for c in chosen):  # at most one punch per 3 s
                continue
            out.append({"at": at, "scale": 1.12})
            chosen.append(at)
        if len(out) + len(existing) >= limit:
            break
    return out


# ----------------------------------------------------------------------------- sync report
def report(scenes, overlays, captions, words):
    warns = []
    cuts = [s["start"] for s in scenes[1:]]
    for c in cuts:
        for w in words:
            if w["start"] + 2 / FPS < c < w["end"] - 2 / FPS:
                warns.append(f"cut at {c:.2f}s falls inside the word '{w['text']}' "
                             f"({w['start']:.2f}-{w['end']:.2f}s); move it to the nearest pause")
                break
    for o in overlays:
        for edge in ("start", "end"):
            t = o[edge]
            near = [c for c in cuts if abs(t - c) < 3 / FPS - 1e-6]
            if near and t > 0:
                warns.append(f"{o['component']} {edge} {t:.2f}s is within 3 frames of the cut at "
                             f"{near[0]:.2f}s; text appearing/vanishing on a cut looks jumpy")
        props = o.get("props", {})
        for key in ("target", "at"):
            pt = props.get(key)
            if isinstance(pt, list) and len(pt) == 2 and pt[0] > 0.83 and pt[1] > 0.36:
                warns.append(f"{o['component']} at {o['start']:.2f}s: {key} {pt} is under TikTok's right action rail")
    # Captions follow the voice, so a fast voice gives fast captions; reading speed is a script
    # problem (word budget), not an edit problem. What the edit must avoid is a group that flashes.
    for c in captions:
        if c["end"] - c["start"] < 0.45:
            warns.append(f"caption '{c['text']}' is on screen only {c['end'] - c['start']:.2f}s; "
                         "merge it with a neighbour (align_captions.py --words)")
    busy = {}
    for o in overlays:
        if o["component"] in ("punch", "sfx"):
            continue
        z = o.get("zone", "top")
        for p in busy.get(z, []):
            if o["start"] < p["end"] and p["start"] < o["end"] and o["component"] not in ("callout", "highlight", "sticker", "cart"):
                warns.append(f"{o['component']} at {o['start']:.2f}s overlaps {p['component']} in zone '{z}'")
        busy.setdefault(z, []).append(o)
    return warns


def missing_assets(project: dict, public: Path) -> list[str]:
    """Files the render will ask for (relative to public/) that are not there yet."""
    need = {f"clips/{s['clip']}.mp4" for s in project["scenes"] if s["clip"]}
    for o in project["overlays"]:
        p = o["props"]
        if o["component"] == "magnifier" and "clip" in p:
            need.add(f"clips/{p['clip']}.mp4")
        need.update(f"clips/{c['clip']}.mp4" for c in p.get("cards", []) if isinstance(c, dict) and "clip" in c)
    need.update(x for x in (project["voice"], (project["music"] or {}).get("src")) if x)
    need.update(c["src"] for c in project["sfx"] if c.get("src"))
    return sorted(f for f in need if not (public / f).is_file())


# ----------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description="Compile an edit plan into a Remotion project.json")
    ap.add_argument("plan", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--voice", help="voiceover path under public/, e.g. audio/kb7.mp3")
    ap.add_argument("--captions", type=Path, help="SRT from align_captions.py")
    ap.add_argument("--words", type=Path, help="word timings from align_captions.py --words-out")
    ap.add_argument("--music", help="music path under public/ (ducked under speech)")
    ap.add_argument("--caption-style", default="karaoke", choices=["karaoke", "plain", "none"])
    ap.add_argument("--auto-camera", action="store_true", help="fill blank Camera cells with varied moves")
    ap.add_argument("--punch-keywords", default="", help="comma-separated words/phrases to punch in on")
    a = ap.parse_args()

    tabs = tables(a.plan.read_text(encoding="utf-8-sig"))
    problems: list[str] = []
    words = json.loads(a.words.read_text(encoding="utf-8")) if a.words else []
    captions = read_srt(a.captions) if a.captions else []

    h, rows = pick(tabs, "start", "end", "source", "in")
    if not rows:
        sys.exit("no scene table with Start/End/Source/In columns")
    scenes = []
    for r in rows:
        try:
            start, end, src = float(cell(h, r, "start")), float(cell(h, r, "end")), cell(h, r, "source")
            inn = float(cell(h, r, "in") or 0)
        except ValueError:
            problems.append(f"scene row unreadable: {r}")
            continue
        s = {"clip": Path(src).stem.upper() if src and src not in "-–" else None, "in": inn,
             "start": start, "end": end, "type": cell(h, r, "type").upper()}
        t, accent = parse_transition(cell(h, r, "transition"))
        if t and scenes:
            s["transition"] = t
        if accent:
            s["accent"] = accent
        cam = parse_camera(cell(h, r, "camera"))
        if cam:
            s["camera"] = cam
        scenes.append(s)
    if a.auto_camera:
        auto_camera(scenes)
    cuts = [s["start"] for s in scenes[1:]]

    oh, orows = pick(tabs, "component", "start", "end")
    overlays, punches, sfx = [], [], []
    for r in orows:
        comp = cell(oh, r, "component")
        if comp not in KNOWN:
            problems.append(f"unknown component '{comp}' (known: {', '.join(sorted(KNOWN))})")
            continue
        props = parse_content(comp, cell(oh, r, "content"))
        start = resolve_time(cell(oh, r, "start"), words, "start", cuts, problems=problems)
        if start is None:
            continue
        end = resolve_time(cell(oh, r, "end") or "auto", words, "end", cuts, start, len(text_of(props)), problems)
        if end is None:
            continue
        start = max(0.0, start)
        if comp == "punch":
            punches.append({"at": start, "scale": float(props.get("scale", 1.12))})
            continue
        if comp == "sfx":
            sfx.append({"src": props.get("src"), "at": start, "volumeDb": float(props.get("volumeDb", -16))})
            continue
        o = {"component": comp, "start": round(start, 3), "end": round(end, 3), "props": props}
        if cell(oh, r, "zone") not in ("", "-", "–"):
            o["zone"] = cell(oh, r, "zone")
        if cell(oh, r, "tone") not in ("", "-", "–"):
            o["tone"] = cell(oh, r, "tone")
        overlays.append(o)

    punches += auto_punches(words, a.punch_keywords.split(","), cuts, punches)

    if problems:
        for p in problems:
            print(f"  x {p}", file=sys.stderr)
        return 1

    project = {
        "duration": scenes[-1]["end"],
        "voice": a.voice,
        "music": {"src": a.music, "volumeDb": -18, "duckDb": -12} if a.music else None,
        "sfx": sfx,
        "captionStyle": a.caption_style,
        "scenes": scenes,
        "overlays": overlays,
        "captions": captions,
        "words": words,
        "punches": sorted(punches, key=lambda p: p["at"]),
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(project, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {a.out}: {len(scenes)} scenes, {len(overlays)} overlays, {len(project['punches'])} punch-ins, "
          f"{len(captions)} captions, {project['duration']}s")
    warns = report(scenes, overlays, captions, words)
    public = a.out.resolve().parent / "public"
    if public.is_dir():  # only when --out sits inside a render project (see new_remotion_project.py)
        warns += [f"not in {public}: {f}" for f in missing_assets(project, public)]
    print("Sync report: " + ("clean" if not warns else f"{len(warns)} warning(s)"))
    for w in warns:
        print(f"  ! {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
