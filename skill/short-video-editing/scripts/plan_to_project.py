#!/usr/bin/env python3
"""Compile an edit plan (markdown) into the project.json rendered by assets/remotion-template.

The plan stays the single source of truth: pacing_checker.py and footage_overlap_checker.py read
the same tables. Nothing about a video is typed into code. What depends on the kind of video (default
caption style, the auto-camera pattern, sound-design overrides, graphics to avoid) comes from the plan's
playbook (`**Playbook:**` line, or --playbook).

    python scripts/plan_to_project.py plan.md --voice audio/v1.mp3 \
        --captions captions.srt --words words.json --out render/v1.json \
        [--auto-camera [--analysis analysis.json]] [--punch-keywords "tên sản phẩm,100"] \
        [--caption-style karaoke|pop|plain|none] [--music audio/track.mp3] \
        [--auto-sfx [--sfx-map table.json] [--sfx-gain -3]]

Scenes table (columns by name, any order; extra columns are ignored):
  Start | End | Source | In | Type | Layout | Transition | Camera | Speed | Flash | Face
    Face        "0.52,0.50,0.072": where the head is (x, y of its centre and r, half its width, as fractions of the frame; person_matte.py
                --faces measures it): the beauty light (project "faceGlow", --face-glow) is drawn there
    Flash       "0,2,4 @ mattes/C5074": a white silhouette of the person on those frames from the cut (person_matte.py wrote
                public/mattes/C5074_0.png, _2, _4): the social opener's white flash
    Layout      blank/full (the clip fills the frame) | card (the clip plays in a rounded card over the animated grid;
                Source "-" gives the grid alone, for overlays that draw their own cards) | expand (starts as a card and
                grows to the full frame with a fabric-like wave; follow a card scene with a "cut")
    Transition  fade | slide [left|right|up|down] | wipe [dir] | iris | pushCut | zoomThrough |
                blurDissolve | whip [dir] | flip [dir] | crossZoom | cardSlide [right] | cardSwirl | cut, optional "14f",
                optional accent "+flash" or "+leak" (e.g. "slide up +flash"), and CapCut-style hits
                "+shake" "+glitch" "+rgb" "+pulse" (drawn by the HyperFrames renderer only; Remotion ignores them)
    Camera      push [a>b] | pull [a>b] | pan left|right|up|down [6%] | hold [scale], optional
                "focus 0.5,0.4" and "roll -1>1"; or keyframes "keys 0=1.05 ; 0.4=1.38@0.34,0.5 out ; 1=1.38@0.32,0.54 soft"
                (TIME=ZOOM[@X,Y][ ease]: a fraction of the scene or "1.2s"; references/camera-moves.md).
                Blank + --auto-camera = the playbook's pattern (and
                `hold` on clips that analysis.json says already move).
    Speed       blank (1x) | 2x | 0.5x | ramp 1>2.5>1 (speeds spread evenly over the scene, eased).
                Under 1x needs a 60 fps proxy (prepare_footage.py keeps 60 fps sources at 60).

Overlays table:  Start | End | Component | Zone | Tone | Content
    Start  seconds, or @"word or phrase"[#n] (n-th occurrence) -> word start minus 3 frames
    End    seconds, +2.5 (duration), auto (reading time), @"word" (end of that word),
           or cut (3 frames before the next scene cut)
    Component  any key of the template registry (src/components/registry.tsx): title, callout,
           checklist, step, price, cart, highlight, sticker, magnifier, thumbs, compare, ranking,
           progress, lowerThird, specs, pin, label, stat, chart, image, phrase, pill, arc, script, tag, logo,
           counter, icon, circled, rawfinal, plus two pseudo-components: punch (camera punch-in) and sfx (sound cue)
    Content  key=value pairs separated by ';'. Lists use ' / ', points use 'x,y' (0..1).
           e.g.  style=stack; lines=đợi vừa lâu / vừa tốn token; accent=token
                 label=2 cổng USB-C; target=0.42,0.55; side=left
                 cards=IMG_0326@40:Áo thun / IMG_0330@17:Tất     (thumbs; a card may end with
                     +1.2 or +@"word" to land 1.2 s in, or on that word, and ~x,y,zoom to frame the
                     stain: IMG_0319@33:Áo ố+@"áo trắng bị ố"~0.22,0.34,2)
                 before=IMG_0327@1.6; after=IMG_0327@27.6; zoom=1.4   (compare: TRƯỚC/SAU card)
                 items=Claude#1 / Manus#1 / ChatGPT#2           (ranking)
                 items=area:85 m² / bed:3 PN / bath:2 WC        (specs; icons: area bed bath compass
                     car floor tree pool clock tag pin star)
                 items=Tự làm#45 / Thuê thợ#120; unit= phút       (chart)
                 src=images/floorplan.png; at=0.5,0.3; width=600 (image, file under public/)
                 lead=Đang kinh doanh; emph=THIẾU VIDEO; emphColor=yellow (phrase); text=TĂNG NHẬN DIỆN; variant=red (pill)
                 from=5; to=10; label=NGÀY (counter); name=target|megaphone|bang|search|check; at=0.2,0.3 (icon)
                 raw=raw/C5099.mp4; final=clips/C5099.mp4; at=3.2 (rawfinal: two cards, the same take unedited and edited)

Caption bands (optional table, Start | End | Top | Size): where the spoken captions sit while a window is open, e.g. a
strip above the cards: | 14.7 | 19.6 | 250 | 44 |; an optional Highlight column (color box underline glow) restyles the spoken word in that window; Top "hide" shows no captions in the window (a title already says it).

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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import playbook as playbooks  # noqa: E402
from footage_overlap_checker import parse_speed  # noqa: E402

FPS = 30
LEAD = 3 / FPS  # graphics land 3 frames before their word
KNOWN = playbooks.registry_components()  # the template's registry + punch and sfx
CANON = {t.lower(): t for t in ["fade", "slide", "wipe", "iris", "pushCut", "zoomThrough",
                                 "blurDissolve", "whip", "flip", "crossZoom", "cardSlide", "cardSwirl", "cut"]}
LAYOUTS = {"full", "card", "expand"}
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
        return None, None, []
    accent = "flash" if "+flash" in raw else "lightLeak" if "+leak" in raw else None
    fx = [m for m in re.findall(r"\+(shake|glitch|rgb|pulse)\b", raw)]  # CapCut-style hits: drawn by the HyperFrames renderer only
    parts = re.sub(r"\+\w+", "", raw).split()
    t = {"type": CANON.get(parts[0].lower(), "fade")} if parts else {"type": "fade"}
    for p in parts[1:]:
        if p.lower() in DIRS:
            t["direction"] = p.lower()
        elif re.fullmatch(r"\d+f", p):
            t["frames"] = int(p[:-1])
        elif re.fullmatch(r"[\d.]+s", p):
            t["frames"] = round(float(p[:-1]) * FPS)
    return t, accent, fx


KEY_EASES = ("linear", "in", "out", "inOut", "soft", "snap", "back", "hold")
KEY_RE = re.compile(r"^(?P<t>\d*\.?\d+)(?P<s>s?)\s*=\s*(?P<zoom>\d*\.?\d+)"
                    r"(?:\s*@\s*(?P<x>\d*\.?\d+)\s*,\s*(?P<y>\d*\.?\d+))?"
                    r"(?:\s+roll\s+(?P<roll>-?\d*\.?\d+))?"
                    r"(?:\s+(?P<ease>" + "|".join(KEY_EASES) + r"))?$")


def parse_keys(raw: str) -> dict:
    """`keys 0=1.0 ; 0.4=1.35@0.3,0.45 out ; 1=1.1`: a keyframed camera. Each key is TIME=ZOOM, then optionally
    @X,Y (the point of the footage to centre on, 0-1), roll DEGREES, and an easing for the segment that ARRIVES at
    the key. TIME is a fraction of the scene (0-1) or seconds from its start (`1.2s`); resolve_keys() turns it into `ts`."""
    keys = []
    for chunk in filter(None, (c.strip() for c in raw.split(";"))):
        m = KEY_RE.match(chunk)
        if not m:
            raise ValueError(f"camera key '{chunk}': expected TIME=ZOOM[@X,Y][ roll DEG][ {'|'.join(KEY_EASES)}], TIME 0-1 or 1.2s")
        k = {"zoom": float(m["zoom"])}
        k["ts" if m["s"] else "frac"] = float(m["t"])
        if m["x"] is not None:
            k["at"] = [float(m["x"]), float(m["y"])]
        if m["roll"] is not None:
            k["roll"] = float(m["roll"])
        if m["ease"]:
            k["ease"] = m["ease"]
        keys.append(k)
    if len(keys) < 2:
        raise ValueError("camera keys need at least two keyframes (a single framing is `hold 1.2 focus x,y`)")
    return {"move": "keys", "keys": keys}


def resolve_keys(cam: dict, length: float) -> None:
    """Fractions of the scene become seconds from its planned cut, the unit the renderers use."""
    for k in cam.get("keys", []):
        if "frac" in k:
            k["ts"] = round(min(max(k.pop("frac"), 0.0), 1.0) * length, 3)
    cam["keys"].sort(key=lambda k: k["ts"])


def parse_camera(raw: str):
    if not raw or raw in "-–":
        return None
    if raw.strip().lower().startswith("keys"):
        return parse_keys(raw.strip()[4:])
    cam = {}
    roll = re.search(r"roll\s+(-?[\d.]+)\s*>\s*(-?[\d.]+)", raw)  # degrees, e.g. roll -1>1
    if roll:
        cam["roll"] = [float(roll.group(1)), float(roll.group(2))]
        raw = raw.replace(roll.group(0), " ")
    parts = raw.replace(",", " , ").split()
    cam["move"] = parts[0].lower() if parts[0].lower() in {"push", "pull", "pan", "hold"} else "push"
    rng = re.search(r"([\d.]+)\s*>\s*([\d.]+)", raw)
    if rng:
        cam["from"], cam["to"] = float(rng.group(1)), float(rng.group(2))
    elif cam["move"] == "hold":  # "hold 1.2": a fixed framing (talking-head jump cuts alternate them)
        one = re.match(r"hold\s+([\d.]+)(?!\s*%)", raw.strip())
        if one:
            cam["from"] = cam["to"] = float(one.group(1))
    if cam["move"] == "pan":
        d = next((p for p in parts if p.lower() in DIRS), "left")
        pct = re.search(r"(\d+(?:\.\d+)?)%", raw)
        a = float(pct.group(1)) / 100 if pct else 0.08
        cam["pan"] = {"left": [-a, 0], "right": [a, 0], "up": [0, -a], "down": [0, a]}[d]
    foc = re.search(r"focus\s+([\d.]+)\s*,\s*([\d.]+)", raw)
    if foc:
        cam["focus"] = [float(foc.group(1)), float(foc.group(2))]
    return cam


def value(v: str):
    v = unicodedata.normalize("NFC", v.strip())  # letters are split per character by the text effects: composed Vietnamese only
    if " / " in v:
        return [x.strip() for x in v.split(" / ")]
    if re.fullmatch(r"-?[\d.]+\s*,\s*-?[\d.]+", v):
        return [float(x) for x in v.split(",")]
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if re.fullmatch(r"-?\d*\.\d+", v):
        return float(v)
    return v


# Content keys the template draws as text: a bare number there must stay a string ("accent=2026").
TEXT_KEYS = {"accent", "sub", "text", "label", "caption", "title", "name", "role", "unit", "prefix", "note", "lines", "items"}


def parse_content(component: str, raw: str) -> dict:
    props = {}
    for chunk in filter(None, (c.strip() for c in raw.split(";"))):
        if "=" not in chunk:
            continue
        k, v = chunk.split("=", 1)
        k = k.strip()
        val = value(v)
        if k in TEXT_KEYS and not isinstance(val, list):
            val = v.strip()  # "accent=2026" and "lines=300" are words to draw, not numbers
        props[k] = val
    if component == "title" and isinstance(props.get("lines"), str):
        props["lines"] = [props["lines"]]
    if component == "checklist" and isinstance(props.get("items"), str):
        props["items"] = [props["items"]]
    if component == "thumbs":
        cards = props.get("cards", [])
        cards = [cards] if isinstance(cards, str) else cards
        out = []
        for c in cards:  # CLIP@sec[:caption][+delay | +@"phrase"][~x,y[,zoom]]: when it lands, how it is framed
            m = re.match(r'(\S+)@([\d.]+)(?::(.*?))?(?:\s*\+\s*(@".+?"(?:#\d+)?|[\d.]+))?'
                         r'(?:\s*~\s*([\d.]+)\s*,\s*([\d.]+)(?:\s*,\s*([\d.]+))?)?\s*$', c)
            if m:
                card = {"clip": Path(m.group(1)).stem.upper(), "at": float(m.group(2)), "caption": (m.group(3) or "").strip()}
                if m.group(4):
                    card["when"] = m.group(4)
                if m.group(5):
                    card["focus"] = [float(m.group(5)), float(m.group(6))]
                    if m.group(7):
                        card["zoom"] = float(m.group(7))
                out.append(card)
        props["cards"] = out
    if component == "compare":
        for side in ("before", "after"):
            m = re.match(r"(\S+)@([\d.]+)$", str(props.get(side, "")))
            if not m:
                sys.exit(f"compare needs {side}=CLIP@seconds (a frame of a clip already shown in this video)")
            props[side] = {"clip": Path(m.group(1)).stem.upper(), "at": float(m.group(2))}
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
def auto_camera(scenes, pb, moving=frozenset()):
    """Fill blank Camera cells from the playbook (references/camera-moves.md): a named scene type gets
    its `camera.byType` move (e.g. pull back onto a REVEAL), the rest walk `camera.pattern`, which
    alternates shot sizes and directions so no move repeats. A clip that already moves (gimbal walk,
    handheld follow: `motion: high` in analysis.json) gets a near-static framing instead, because a
    virtual move on top of a real one reads as a wobble. Cells written by hand are left alone."""
    by_type, pattern = pb["camera"].get("byType", {}), pb["camera"]["pattern"]
    k = 0
    for s in scenes:
        if s.get("camera"):
            continue
        if s.get("type") in by_type:
            s["camera"] = parse_camera(by_type[s["type"]])
        elif s.get("clip") in moving:
            s["camera"] = {"move": "hold", "from": 1.04, "to": 1.04}
        else:
            s["camera"] = parse_camera(pattern[k % len(pattern)])
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


# ----------------------------------------------------------------------------- sound design
DEFAULT_SFX_MAP = Path(__file__).resolve().parent.parent / "assets" / "sfx" / "sfx-map.json"


def merge_sfx(cfg, overrides):
    """The playbook's `sfx` section replaces single events of sfx-map.json (null = silence)."""
    for section, table in overrides.items():
        if section == "rules":
            cfg["rules"].update(table)  # a playbook may allow more sounds per window (text-heavy genres)
        else:
            cfg["events"].setdefault(section, {}).update(table)
    return cfg


def auto_sfx(scenes, overlays, cfg, manual, offset_db=0.0):
    """Sound cues from assets/sfx/sfx-map.json: transitions (an accent beats the transition type; a
    `sceneStart` entry "A>B" or "*>B" beats both, and null means silence, e.g. across the reveal), a silhouette
    flash, and graphic entrances. An event's value is a sound name, a LIST of names (alternatives, used in turn so
    the same sound never plays twice in a row), or {"sound": name-or-list, "offset": s, "also": [name, ...]} where
    `also` sounds are layered on the same moment (a whoosh with a soft impact). An overlay is looked up by
    "component:fx" (a text effect or style), then "component". Cues you wrote by hand (`manual`) always stay; the rest
    are thinned so sounds never crowd each other: minGap apart, at most maxInWindow per window."""
    sounds, ev, rules = cfg["sounds"], cfg["events"], cfg["rules"]
    cand = []  # (priority, time, event key, entry)
    for k, s in enumerate(scenes[1:], 1):
        prev, cut = scenes[k - 1], s["start"]
        key, entry = None, None
        acc, ttype = s.get("accent"), s.get("transition", {}).get("type", "fade")
        if ev["accent"].get(acc):
            key, entry = f"accent:{acc}", ev["accent"][acc]
        elif ev["transition"].get(ttype):
            key, entry = f"transition:{ttype}", ev["transition"][ttype]
        for sk in (f"{prev['type']}>{s['type']}", f"*>{s['type']}"):
            if sk in ev["sceneStart"]:
                key, entry = f"sceneStart:{sk}", ev["sceneStart"][sk]
                break
        if entry:
            cand.append((0, cut, key, entry))
    fps = 30
    direct = []  # (time, key, entry): played whatever the thinning says (the silhouette flash, the pops of a text pile)
    for s in scenes:  # a silhouette flash: a camera click on its first frame
        if s.get("flash") and ev.get("flash"):
            direct.append((s["start"] + s["flash"]["frames"][0] / fps, "flash", ev["flash"]))
    for o in overlays:  # a burst of copies pops one after another: a pop for each main copy
        if o["component"] == "burst" and ev.get("burst"):
            sp = float(o["props"].get("speed", 1))
            for n, at in enumerate((3, 8, 12, 15, 19)):
                direct.append((o["start"] + at / fps / sp, "burst", ev["burst"]))
    for o in overlays:
        props = o["props"]
        for k in (f"{o['component']}:{props.get('fx') or props.get('style')}", o["component"]):
            if ev["overlay"].get(k):
                cand.append((1, o["start"] + (ev["overlay"][k].get("offset", 0.0) if isinstance(ev["overlay"][k], dict) else 0.0), f"overlay:{k}", ev["overlay"][k]))
                break
    kept = [m["at"] for m in manual]
    cues, turn = [], {}

    def emit(t, key, entry):
        names = entry["sound"] if isinstance(entry, dict) else entry
        names = names if isinstance(names, list) else [names]
        pick = names[turn.get(key, 0) % len(names)]
        turn[key] = turn.get(key, 0) + 1
        for name in [pick] + (entry.get("also", []) if isinstance(entry, dict) else []):
            snd = sounds[name]
            cues.append({"src": snd["file"], "at": round(max(0.0, t - snd["lead"]), 3), "volumeDb": round(snd["gainDb"] + offset_db, 1)})

    for t, key, entry in direct:
        emit(t, key, entry)
    for _, t, key, entry in sorted(cand, key=lambda c: (c[0], c[1])):
        near = [a for a in kept if abs(a - t) < rules["window"] / 2]
        if t < rules["notBefore"] or any(abs(a - t) < rules["minGap"] for a in kept) or len(near) >= rules["maxInWindow"]:
            continue
        kept.append(t)
        emit(t, key, entry)
    return sorted(cues, key=lambda c: c["at"])


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
        if o["component"] == "cart":
            continue  # the cart arrow lives at the bottom-left and keeps its own label
        if any(k in o.get("props", {}) for k in ("at", "y")):
            continue  # placed by hand (at / y): the zone is only the default position, so two of them cannot be judged by it
        # the compare card is tall: its note line reaches into the lower zone as well
        for z in [o.get("zone", "top")] + (["lower"] if o["component"] == "compare" else []):
            for p in busy.get(z, []):
                if o["start"] < p["end"] and p["start"] < o["end"] and o["component"] not in ("callout", "highlight", "sticker"):
                    warns.append(f"{o['component']} at {o['start']:.2f}s overlaps {p['component']} in zone '{z}'")
            busy.setdefault(z, []).append(o)
    return warns


def missing_assets(project: dict, public: Path) -> list[str]:
    """Files the render will ask for (relative to public/) that are not there yet."""
    need = {f"clips/{s['clip']}.mp4" for s in project["scenes"] if s["clip"]}
    for s in project["scenes"]:
        if s.get("flash"):
            need.update(f"{s['flash']['matte']}_{n}.png" for n in s["flash"]["frames"])
    for o in project["overlays"]:
        p = o["props"]
        if o["component"] == "magnifier" and "clip" in p:
            need.add(f"clips/{p['clip']}.mp4")
        if o["component"] == "compare":
            need.update(f"clips/{p[s]['clip']}.mp4" for s in ("before", "after"))
        if o["component"] == "image" and p.get("src"):
            need.add(str(p["src"]))
        if o["component"] == "logo":
            need.add(str(p.get("src", "images/logo.png")))
        if o["component"] == "rawfinal":
            need.update(str(p[k]) for k in ("raw", "final") if p.get(k))
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
    ap.add_argument("--music", help="music path under public/, levelled first with process_audio.py music (ducked under speech)")
    ap.add_argument("--platform", choices=["tiktok", "reels", "reels-ad"], default="tiktok",
                    help="tiktok and reels share the feed layout; reels-ad raises captions above Meta's bottom 35%% and checks its safe zone")
    ap.add_argument("--playbook", help="playbook id[:variant]; default: the plan's **Playbook:** line")
    ap.add_argument("--caption-style", choices=["karaoke", "pop", "plain", "none"], help="default: the playbook's")
    ap.add_argument("--auto-camera", action="store_true", help="fill blank Camera cells from the playbook's camera pattern")
    ap.add_argument("--analysis", type=Path, help="analysis.json from inspect_footage.py --measure: clips that already move get a static framing")
    ap.add_argument("--punch-keywords", default="", help="comma-separated words/phrases to punch in on")
    ap.add_argument("--auto-sfx", action="store_true", help="add sound effects on transitions and graphics (assets/sfx/sfx-map.json)")
    ap.add_argument("--sfx-map", type=Path, default=DEFAULT_SFX_MAP, help="sound-design table to use with --auto-sfx")
    ap.add_argument("--sfx-gain", type=float, default=0.0, help="dB added to every automatic sound effect")
    ap.add_argument("--music-levels", help="VOLUME,DUCK in dB for the music bed (default -10,-8 with a voice): the bed's level in pauses, then the extra dip under speech")
    ap.add_argument("--caption-highlight", choices=["color", "box", "underline", "glow"], help="how the spoken word is marked in karaoke captions (default color)")
    ap.add_argument("--caption-keywords", default="", help="comma-separated words that are marked all the time in the captions (bigger, coloured)")
    ap.add_argument("--face-glow", help="BRIGHTNESS,SATURATE,BLUR[,SIZE[,WARM[,VEIL]]] of the beauty light on scenes that have a Face (e.g. 1.16,0.92,0.6)")
    ap.add_argument("--look", help="SATURATE,CONTRAST,BRIGHTNESS[,WARM] factors (1 = unchanged; WARM 0 = none, 0.06 = a little) pushed onto the footage only, e.g. 1.12,1.05,1.03,0.06")
    a = ap.parse_args()

    text = a.plan.read_text(encoding="utf-8-sig")
    pb = playbooks.resolve(a.playbook, text)
    tabs = tables(text)
    problems: list[str] = []
    analysis = {c["stem"]: c for c in json.loads(a.analysis.read_text(encoding="utf-8"))["clips"]} if a.analysis else {}
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
        fl = cell(h, r, "flash")
        m = re.match(r"^([\d,\s]+)@\s*(\S+)$", fl) if fl and fl not in "-–" else None
        if m:
            s["flash"] = {"frames": [int(x) for x in m.group(1).replace(" ", "").strip(",").split(",") if x], "matte": m.group(2)}
        elif fl and fl not in "-–":
            problems.append(f"scene row {len(scenes) + 1}: flash '{fl}' should look like '0,2,4 @ mattes/C5074'")
        fc = cell(h, r, "face")
        if fc and fc not in "-–":
            try:
                fx, fy, fr = (float(x) for x in fc.split(","))
                s["face"] = {"x": fx, "y": fy, "r": fr}
            except ValueError:
                problems.append(f"scene row {len(scenes) + 1}: face '{fc}' should look like '0.52,0.50,0.072'")
        layout = cell(h, r, "layout").lower()
        if layout in LAYOUTS and layout != "full":
            s["layout"] = layout
        elif layout and layout not in LAYOUTS | {"-", "–"}:
            problems.append(f"scene row {len(scenes) + 1}: layout '{layout}' is not one of {sorted(LAYOUTS)}")
        t, accent, fx = parse_transition(cell(h, r, "transition"))
        if t and scenes:
            s["transition"] = t
        if accent:
            s["accent"] = accent
        if fx and scenes:
            s["fx"] = fx
        try:
            cam = parse_camera(cell(h, r, "camera"))
        except ValueError as e:
            problems.append(f"scene {len(scenes) + 1}: {e}")
            cam = None
        if cam:
            if cam.get("keys"):
                resolve_keys(cam, end - start)
            s["camera"] = cam
        try:
            speed, ramp = parse_speed(cell(h, r, "speed"))
        except ValueError as e:
            problems.append(str(e))
            speed, ramp = None, None
        if speed and speed != 1:
            s["speed"] = speed
        if ramp:
            s["ramp"] = ramp
        scenes.append(s)
    if a.auto_camera:
        auto_camera(scenes, pb, {k for k, c in analysis.items() if c.get("motion") == "high"})
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
        for card in props.get("cards", []) if comp == "thumbs" else []:
            when = card.pop("when", None)
            if when is None:
                continue
            m = ANCHOR.match(when)
            if not m:
                card["delay"] = float(when)
                continue
            hit = find_phrase(words, m.group(1), int(m.group(2) or 1))
            if hit:
                card["delay"] = round(max(0.0, hit[0]["start"] - LEAD - start), 3)
            else:
                problems.append(f'thumbs card anchor @"{m.group(1)}" not found in the word timings')
        o = {"component": comp, "start": round(start, 3), "end": round(end, 3), "props": props}
        if cell(oh, r, "zone") not in ("", "-", "–"):
            o["zone"] = cell(oh, r, "zone")
        if cell(oh, r, "tone") not in ("", "-", "–"):
            o["tone"] = cell(oh, r, "tone")
        overlays.append(o)

    bh, brows = pick(tabs, "start", "end", "top")
    bands = []
    for r in brows if bh and "component" not in bh and "source" not in bh else []:
        try:
            hide = cell(bh, r, "top").lower() in ("hide", "none")
            band = {"start": float(cell(bh, r, "start")), "end": float(cell(bh, r, "end")), "top": 0.0 if hide else float(cell(bh, r, "top"))}
            if hide:
                band["hide"] = True
            if cell(bh, r, "size"):
                band["size"] = float(cell(bh, r, "size"))
            if cell(bh, r, "highlight") in ("color", "box", "underline", "glow"):
                band["highlight"] = cell(bh, r, "highlight")
            bands.append(band)
        except ValueError:
            problems.append(f"caption band row unreadable: {r}")

    punches += auto_punches(words, a.punch_keywords.split(","), cuts, punches)
    if a.auto_sfx:
        cfg = merge_sfx(json.loads(a.sfx_map.read_text(encoding="utf-8")), pb["sfx"])
        sfx += auto_sfx(scenes, overlays, cfg, sfx, a.sfx_gain)

    if problems:
        for p in problems:
            print(f"  x {p}", file=sys.stderr)
        return 1

    project = {
        "duration": scenes[-1]["end"],
        "voice": a.voice,
        # A track levelled to -14 LUFS (process_audio.py music) sits ~10 LU under a -16 LUFS voice in the
        # pauses and ~18 LU under it while it speaks; with no voice the music is the soundtrack.
        "music": ({"src": a.music, "volumeDb": -10, "duckDb": -8, **({"volumeDb": float(a.music_levels.split(",")[0]), "duckDb": float(a.music_levels.split(",")[1])} if a.music_levels else {})}
                  if a.voice else {"src": a.music, "volumeDb": 0, "duckDb": 0}) if a.music else None,
        "layout": "reels-ad" if a.platform == "reels-ad" else "feed",
        "sfx": sfx,
        "captionStyle": a.caption_style or pb["captions"],
        **({"captionHighlight": a.caption_highlight} if a.caption_highlight else {}),
        **({"captionKeywords": [k.strip() for k in a.caption_keywords.split(",") if k.strip()]} if a.caption_keywords.strip() else {}),
        **({"faceGlow": dict(zip(("brightness", "saturate", "blur", "size", "warm", "veil"), (float(x) for x in a.face_glow.split(","))))} if a.face_glow else {}),
        **({"look": dict(zip(("saturate", "contrast", "brightness", "warm"), (float(x) for x in a.look.split(","))))} if a.look else {}),
        "scenes": scenes,
        "overlays": overlays,
        "captions": captions,
        "captionBands": bands,
        "words": words,
        "punches": sorted(punches, key=lambda p: p["at"]),
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(project, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {a.out}: {len(scenes)} scenes, {len(overlays)} overlays, {len(project['punches'])} punch-ins, "
          f"{len(project['sfx'])} sound cues, {len(captions)} captions, {project['duration']}s")
    warns = report(scenes, overlays, captions, words)
    if a.platform != "tiktok":
        warns += [f"cart at {o['start']:.2f}s: the cart arrow points at TikTok Shop's product bar, which {a.platform} does not have"
                  for o in overlays if o["component"] == "cart"]
    if a.platform == "reels-ad":  # Meta: keep the top 14 %, bottom 35 % and 6 % each side clear
        for o in overlays:
            for key in ("target", "at"):
                pt = o["props"].get(key)
                if isinstance(pt, list) and len(pt) == 2 and not (0.06 <= pt[0] <= 0.94 and 0.14 <= pt[1] <= 0.65):
                    warns.append(f"{o['component']} at {o['start']:.2f}s: {key} {pt} is outside the Reels ad safe zone")
            if o.get("zone") == "lower":
                warns.append(f"{o['component']} at {o['start']:.2f}s: zone 'lower' (y 1230) is inside the Reels ad bottom 35%")
    for i, s in enumerate(scenes):  # keyframed cameras: a zoom the proxies cannot hold, a key outside the scene
        for k in (s.get("camera") or {}).get("keys", []):
            if k["zoom"] > 1.5:
                warns.append(f"scene {i + 1}: camera key zoom {k['zoom']} is past 1.5: a 2880 px proxy of 4K footage softens beyond it, and a 720p or 1080p clip "
                             "softens much earlier (the limit is the clip's own pixels: 720p holds about 1.3)")
            if k["ts"] > (s["end"] - s["start"]) + 0.3:
                warns.append(f"scene {i + 1}: camera key at {k['ts']:.2f}s is after the scene ends ({s['end'] - s['start']:.2f}s)")
    avoid = set(pb["components"].get("avoid", []))
    warns += [f"{o['component']} at {o['start']:.2f}s: playbook {pb['name']} avoids this component (playbooks/{pb['id']}.md)"
              for o in overlays if o["component"] in avoid]
    fx_scenes = [i + 1 for i, s in enumerate(scenes) if s.get("fx")]
    if fx_scenes:
        warns.append(f"scene(s) {fx_scenes} use +shake/+glitch/+rgb/+pulse: only the HyperFrames renderer draws them "
                     "(project_to_hyperframes.py); Remotion ignores them")
    public = a.out.resolve().parent / "public"
    corr = public / "clips" / "corrections.json"  # written by prepare_footage.py: the proxies' real fps
    proxy_fps = {k: v.get("fps", 30) for k, v in json.loads(corr.read_text(encoding="utf-8"))["clips"].items()} if corr.is_file() else {}
    for s in scenes:  # slow motion shows repeated frames unless the proxy has the frames
        slowest = min(s.get("ramp") or [s.get("speed", 1)])
        fps = proxy_fps.get(s["clip"] or "", 30 if corr.is_file() else None)
        if slowest < 1 and fps and fps * slowest < FPS - 0.5:
            src = analysis.get(s["clip"] or "", {}).get("fps")
            warns.append(f"scene at {s['start']:.2f}s plays {s['clip']} at {slowest:g}x but its proxy is {fps:g} fps: it will stutter "
                         + (f"(source {src:g} fps: rebuild with prepare_footage.py --slowmo --force)" if src and src >= 50 else "(shoot 60 fps for slow motion)"))
    if public.is_dir():  # only when --out sits inside a render project (see new_remotion_project.py)
        warns += [f"not in {public}: {f}" for f in missing_assets(project, public)]
    print("Sync report: " + ("clean" if not warns else f"{len(warns)} warning(s)"))
    for w in warns:
        print(f"  ! {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
