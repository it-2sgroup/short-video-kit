#!/usr/bin/env python3
"""Build a HyperFrames project (HTML + GSAP playhead, rendered by `npx hyperframes`) from the same
project.json that plan_to_project.py writes for Remotion. The plan, the checkers, the proxies, the voice,
the captions and the music are shared; only the renderer changes (references/hyperframes-flow.md).

    python scripts/project_to_hyperframes.py RENDER/v1.json --out ~/videos/hf/v1 [--playbook food-fnb | --theme warm]
    python scripts/project_to_hyperframes.py RENDER/v1.json --out hf/v1 --check      # + npx hyperframes check
    python scripts/project_to_hyperframes.py RENDER/v1.json --out hf/v1 --render out.mp4 --quality high

What it does, in order:
  1. lays the scenes out exactly like the Remotion template (centred transitions, pre-roll handles);
  2. bakes scenes with `speed` or `ramp` into their own clip with ffmpeg (HyperFrames plays constant rates);
  3. mixes voice + ducked music + sound effects into one audio/mix.wav with ffmpeg (same levels and ducking
     as engine/audio.tsx), so the render needs no audio automation;
  4. links the clips the scenes use, writes index.html, kit.js (the renderer), kit.css, package.json.

Overlay components the HyperFrames kit does not draw (read from kit.js: today magnifier, thumbs, compare, ranking and the
agency-pitch set phrase, pill, arc, burst, script, tag, logo, counter, icon, circled, rawfinal) and scene or project features
only Remotion has (card/expand layouts, the silhouette flash, face light, look, caption highlights and bands, cardSlide and
cardSwirl) are listed and left out: render such a video with Remotion instead (the agency recipe is Remotion only). Ask the user before the first `npx hyperframes`
(it downloads the package). Needs ffmpeg; rendering needs Node 22+ and Chrome.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL / "assets" / "hyperframes-template"
HF_VERSION = "0.9.26"  # the CLI the kit was tested with; package.json pins it so a re-render is identical
GSAP = "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"
FACTORY_RE = re.compile(r"^    (\w+)\(\w+, ov\) \{", re.M)   # an overlay drawn by kit.js: `    title(root, ov) {`
REMOTION_ONLY_SCENE = {"layout": "card/expand layouts over the grid", "flash": "the silhouette flash", "face": "face light"}
REMOTION_ONLY_PROJECT = {"faceGlow": "face light", "captionHighlight": "caption highlight modes", "captionKeywords": "caption keywords"}
REMOTION_ONLY_TRANSITIONS = {"cardSlide", "cardSwirl"}


def remotion_only(proj: dict) -> list[str]:
    """Features the plan uses that kit.js does not draw: one short line each, so nothing disappears silently."""
    out = []
    for k, why in REMOTION_ONLY_SCENE.items():
        n = sum(1 for s in proj.get("scenes") or [] if s.get(k))
        if n:
            out.append(f"{n} scene(s) with {k} ({why})")
    for k, why in REMOTION_ONLY_PROJECT.items():
        if proj.get(k):
            out.append(f"{k} ({why})")
    grade = sorted(set(proj.get("look") or {}) - {"vignette", "grain"})   # HyperFrames' own look is only vignette and grain
    if grade:
        out.append(f"look {'/'.join(grade)} (the picture grade: bake it into the proxies, or render with Remotion)")
    bands = [b for b in proj.get("captionBands") or [] if b.get("hide") or b.get("highlight")]
    if bands:
        out.append(f"{len(bands)} caption band(s) with hide/highlight")
    t = sorted({s.get("transition", {}).get("type") for s in proj.get("scenes") or []} & REMOTION_ONLY_TRANSITIONS)
    if t:
        out.append(f"transition {', '.join(t)} (drawn as a fade)")
    return out

DEFAULT_FRAMES = {"cut": 0, "fade": 12, "slide": 14, "wipe": 14, "iris": 18, "pushCut": 11, "zoomThrough": 12,
                  "blurDissolve": 14, "whip": 9, "flip": 16, "crossZoom": 16}


# ---------------------------------------------------------------- layout (engine/timeline.ts)
def rnd(x: float) -> int:
    """JavaScript's Math.round (halves go up); Python's round() sends halves to the even number and would drift a frame."""
    return int(math.floor(x + 0.5))


def even(n: float) -> int:
    return 0 if n <= 0 else max(2, rnd(n / 2) * 2)


def speed_at(scene: dict, f: float, duration: int) -> float:
    r = scene.get("ramp")
    if not r or len(r) < 2:
        return scene.get("speed") or 1.0
    x = min(max(f / max(1, duration), 0), 1) * (len(r) - 1)
    i = min(int(math.floor(x)), len(r) - 2)
    t = x - i
    # Easing.inOut(Easing.sin): symmetric, so a segment's average speed is the mean of its ends
    s = lambda u: 1 - math.cos(u * math.pi / 2)
    e = s(t * 2) / 2 if t < 0.5 else 1 - s((1 - t) * 2) / 2
    return r[i] + (r[i + 1] - r[i]) * e


def advancer(scene: dict, duration: int):
    if not scene.get("ramp") or len(scene["ramp"]) < 2:
        v = scene.get("speed") or 1.0
        return lambda f: f * v
    acc = [0.0]
    for f in range(duration + 1):
        acc.append(acc[f] + speed_at(scene, f + 0.5, duration))
    return lambda f: acc[min(max(0, rnd(f)), len(acc) - 1)]


def layout(scenes: list[dict], fps: int) -> list[dict]:
    cuts = [rnd(s["start"] * fps) for s in scenes]
    ends = [rnd(s["end"] * fps) for s in scenes]
    tr = []
    for k, s in enumerate(scenes):
        if k == 0:
            tr.append(0)
            continue
        t = s.get("transition") or {"type": "fade"}
        wanted = even(t.get("frames") or DEFAULT_FRAMES.get(t["type"], 12))
        room = min(cuts[k] - cuts[k - 1], ends[k] - cuts[k])
        tr.append(min(wanted, even(room / 2)))
    out = []
    for k, s in enumerate(scenes):
        begin = 0 if k == 0 else cuts[k] - tr[k] // 2
        finish = ends[k] if k == len(scenes) - 1 else cuts[k + 1] + tr[k + 1] // 2
        adv = advancer(s, finish - begin)
        out.append({"index": k, "scene": s, "begin": begin, "duration": finish - begin, "cut": cuts[k], "transitionIn": tr[k],
                    "startFrom": max(0, rnd(rnd(s["in"] * fps) - adv(cuts[k] - begin))), "advance": adv})
    return out


# ---------------------------------------------------------------- ffmpeg pieces
def run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        sys.exit(f"ffmpeg failed:\n{' '.join(cmd)[:400]}\n{r.stderr[-1500:]}")


def duration_of(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def bake_scene(src: Path, out: Path, slot: dict, fps: int) -> float:
    """Write the scene's footage already re-timed (constant speed or a ramp) for exactly its slot.
    Returns the seconds of the scene the source cannot cover (held on its last frame), 0 when it is long enough."""
    scene, n = slot["scene"], slot["duration"]
    t0 = slot["startFrom"] / fps
    ramp = scene.get("ramp")
    if ramp and len(ramp) > 1:
        adv = slot["advance"]
        pts = list(range(0, n + 1, 3))
        if pts[-1] != n:
            pts.append(n)
        xs = [adv(j) / fps for j in pts]  # source seconds after j output frames
        ys = [j / fps for j in pts]
        expr = f"{ys[-1]:.6f}"
        for j in range(len(pts) - 2, -1, -1):
            dx = max(xs[j + 1] - xs[j], 1e-9)
            expr = f"if(lt(X,{xs[j + 1]:.6f}),{ys[j]:.6f}+(X-{xs[j]:.6f})*{(ys[j + 1] - ys[j]) / dx:.6f},{expr})"
        setpts = "setpts='(" + expr.replace("X", "(PTS*TB)") + ")/TB'"
        read = xs[-1] + 0.6
    else:
        v = scene.get("speed") or 1.0
        setpts = f"setpts=PTS/{v}"
        read = n / fps * v + 0.6
    # tpad holds the last frame if the source ends early (reported below), so the clip always fills its slot
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.4f}", "-t", f"{read:.4f}", "-i", str(src), "-an",
         "-vf", f"{setpts},fps={fps},tpad=stop_mode=clone:stop_duration=3", "-frames:v", str(n), "-c:v", "libx264",
         "-crf", "14", "-preset", "fast", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)])
    have = max(0.0, duration_of(src) - t0)
    need = xs[-1] if ramp and len(ramp) > 1 else n / fps * (scene.get("speed") or 1.0)
    return max(0.0, (need - have) / ((need / (n / fps)) or 1))


def speech_spans(words: list[dict]) -> list[tuple[float, float]]:
    spans: list[list[float]] = []
    for w in words:
        if spans and w["start"] - spans[-1][1] < 0.4:
            spans[-1][1] = max(spans[-1][1], w["end"])
        else:
            spans.append([w["start"], w["end"]])
    return [(a, b) for a, b in spans]


def mix_audio(proj: dict, public: Path, out: Path, fps: int) -> bool:
    """voice + music (ducked under speech, 2-frame attack, 12-frame release) + sound effects -> one WAV."""
    inputs: list[str] = []
    chains: list[str] = []
    labels: list[str] = []

    def add(path: str, chain: str) -> None:
        f = public / path
        if not f.exists():
            print(f"  ! missing audio {f}")
            return
        inputs.extend(["-i", str(f)])
        i = len(labels)
        chains.append(f"[{i}:a]{chain}[a{i}]")
        labels.append(f"[a{i}]")

    fmt = "aformat=sample_rates=48000:channel_layouts=stereo"
    if proj.get("voice"):
        add(proj["voice"], fmt)
    m = proj.get("music")
    if m:
        bed = 10 ** ((m.get("volumeDb", -18)) / 20)
        duck = 10 ** ((m.get("volumeDb", -18) + m.get("duckDb", -12)) / 20)
        a, r = 2 / fps, 12 / fps
        terms = [f"clip(min((t-{s - a:.4f})/{a:.4f},1-(t-{e:.4f})/{r:.4f}),0,1)" for s, e in speech_spans(proj.get("words") or [])]
        d = "0"
        for t in terms:
            d = f"max({d},{t})"
        add(m["src"], f"{fmt},volume='{bed:.6f}+({duck - bed:.6f})*{d}':eval=frame")
    for c in proj.get("sfx") or []:
        ms = max(0, round(c["at"] * 1000))
        add(c["src"], f"{fmt},volume={10 ** (c.get('volumeDb', -16) / 20):.6f},adelay={ms}|{ms}")
    if not labels:
        return False
    graph = ";".join(chains) + f";{''.join(labels)}amix=inputs={len(labels)}:normalize=0:duration=longest,atrim=0:{proj['duration']}[mix]"
    out.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph, "-map", "[mix]", "-ar", "48000", "-ac", "2", str(out)])
    return True


# ---------------------------------------------------------------- project files
def link(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        if dst.stat().st_size == src.stat().st_size and dst.stat().st_mtime >= src.stat().st_mtime:
            return  # already the same file (a hard link, or an up-to-date copy)
        dst.unlink()  # the proxy was regenerated: relink it
    try:
        os.link(src, dst)  # same volume: no copy of the (large) proxies
    except OSError:
        shutil.copy2(src, dst)


def build_html(proj: dict, slots: list[dict], fps: int, has_audio: bool) -> str:
    w, h, dur = proj["width"], proj["height"], proj["duration"]
    rows = []
    for s in slots:
        i, sc = s["index"], s["scene"]
        begin, length = s["begin"] / fps, s["duration"] / fps
        if sc.get("clip"):
            baked = s.get("baked")
            src = f"clips/_scene{i}.mp4" if baked else f"clips/{sc['clip']}.mp4"
            media = 0 if baked else s["startFrom"] / fps
            media_el = (f'<video class="clip" id="v{i}" src="{src}" data-start="{begin:.4f}" data-duration="{length:.4f}" '
                        f'data-media-start="{media:.4f}" data-track-index="0" muted playsinline></video>')
        else:
            media_el = '<div class="placeholder"></div>'  # layout preview without footage
        # the camera layer is scaled past the frame on purpose (push-ins, pans): not a layout error
        rows.append(f'<div class="tr" id="tr{i}"><div class="cam" id="cam{i}" data-layout-allow-overflow>{media_el}</div></div>')
    audio = (f'<audio id="mix" src="audio/mix.wav" data-start="0" data-duration="{dur:.4f}" data-track-index="9" data-volume="1"></audio>'
             if has_audio else "")
    return f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width={w}, height={h}" />
<link rel="stylesheet" href="kit.css" />
<script src="{GSAP}"></script>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{dur:.4f}" data-width="{w}" data-height="{h}">
{chr(10).join(rows)}
<div id="look" class="layer"></div>
<div id="accents" class="layer"></div>
<div id="overlays" class="layer"></div>
<div id="captions" class="layer"></div>
{audio}
</div>
<script>window.__SVK_PROJECT__ = {json.dumps(proj, ensure_ascii=False)};</script>
<script src="kit.js"></script>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a HyperFrames project from a project.json.")
    ap.add_argument("project", type=Path, help="project.json written by plan_to_project.py")
    ap.add_argument("--out", type=Path, required=True, help="folder of the HyperFrames project (created or refreshed)")
    ap.add_argument("--public", type=Path, help="folder holding clips/, audio/, sfx/ (default: public/ beside project.json)")
    ap.add_argument("--playbook", help="playbook id[:variant]: sets the colour theme")
    ap.add_argument("--theme", choices=["cool", "warm", "luxe"], help="colour theme (default: the playbook's, else cool)")
    ap.add_argument("--look", metavar="vignette=0.35,grain=0.06",
                    help="film look over the footage: a vignette and/or film grain, strength 0..1 (a CapCut-style finish; subtle values)")
    ap.add_argument("--check", action="store_true", help="run `npx hyperframes check` afterwards (downloads the CLI on first use)")
    ap.add_argument("--render", metavar="FILE", help="render to FILE (relative to the project) with `npx hyperframes render`")
    ap.add_argument("--quality", choices=["draft", "standard", "high"], default="high", help="render quality (default high)")
    a = ap.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found (python scripts/doctor.py).")
    src = a.project.expanduser().resolve()
    proj = json.loads(src.read_text(encoding="utf-8"))
    public = (a.public or src.parent / "public").expanduser().resolve()
    if not public.is_dir():
        sys.exit(f"no public folder at {public}: pass --public.")
    fps = proj.setdefault("fps", 30)
    proj.setdefault("width", 1080)
    proj.setdefault("height", 1920)
    theme = a.theme
    if a.playbook and not theme:
        sys.path.insert(0, str(SKILL / "scripts"))
        import playbook as playbooks
        theme = playbooks.load(a.playbook)["theme"]
    theme = theme or "cool"
    proj["theme"] = theme
    unsupported = remotion_only(proj)   # before --look replaces the project's own look
    if a.look:
        look = {}
        for part in a.look.split(","):
            key, _, val = part.partition("=")
            if key.strip() not in ("vignette", "grain"):
                sys.exit(f"--look: unknown effect '{key}' (vignette, grain)")
            look[key.strip()] = min(1.0, max(0.0, float(val or 0.3)))
        proj["look"] = look

    out = a.out.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    for name in ("kit.js", "kit.css"):
        shutil.copy2(TEMPLATE / name, out / name)

    slots = layout(proj["scenes"], fps)
    punches = [{"frame": rnd(p["at"] * fps), "scale": p.get("scale", 1.12)} for p in proj.get("punches") or []]
    for s in slots:
        nxt = slots[s["index"] + 1] if s["index"] + 1 < len(slots) else None
        s["punches"] = [{"frame": p["frame"] - s["begin"], "scale": p["scale"]} for p in punches
                        if p["frame"] >= s["cut"] and (not nxt or p["frame"] < nxt["cut"])]

    missing = []
    for s in slots:
        sc = s["scene"]
        if not sc.get("clip"):
            continue
        clip = public / "clips" / f"{sc['clip']}.mp4"
        if not clip.exists():
            missing.append(str(clip))
            continue
        retimed = (sc.get("ramp") and len(sc["ramp"]) > 1) or (sc.get("speed") or 1) != 1
        if retimed:
            short = bake_scene(clip, out / "clips" / f"_scene{s['index']}.mp4", s, fps)
            s["baked"] = True
            print(f"  scene {s['index']}: baked {'ramp ' + str(sc['ramp']) if sc.get('ramp') else str(sc['speed']) + 'x'}")
            if short > 0.04:
                print(f"  ! scene {s['index']}: {sc['clip']} ends {short:.2f} s before the scene does at this speed (last frame held): "
                      "use a longer range or a slower speed")
        else:
            link(clip, out / "clips" / f"{sc['clip']}.mp4")
    if missing:
        sys.exit("missing proxies:\n  " + "\n  ".join(missing))

    drawn = set(FACTORY_RE.findall((TEMPLATE / "kit.js").read_text(encoding="utf-8")))
    skipped = sorted({o["component"] for o in proj.get("overlays") or [] if o["component"] not in drawn})
    proj["overlays"] = [o for o in proj.get("overlays") or [] if o["component"] in drawn]
    for o in proj["overlays"]:
        if o["component"] == "image":
            img = public / o["props"]["src"]
            if img.exists():
                link(img, out / o["props"]["src"])
            else:
                print(f"  ! missing image {img}")

    has_audio = mix_audio(proj, public, out / "audio" / "mix.wav", fps)
    proj["slots"] = [{k: v for k, v in s.items() if k not in ("advance", "baked")} for s in slots]
    (out / "index.html").write_text(build_html(proj, slots, fps, has_audio), encoding="utf-8", newline="\n")
    (out / "package.json").write_text(json.dumps({
        "name": out.name, "private": True, "type": "module",
        "scripts": {"check": f"npx --yes hyperframes@{HF_VERSION} check", "preview": f"npx --yes hyperframes@{HF_VERSION} preview",
                    "render": f"npx --yes hyperframes@{HF_VERSION} render"}}, indent=2) + "\n", encoding="utf-8")
    (out / "hyperframes.json").write_text(json.dumps({
        "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
        "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
        "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
        "media": {"autoProxy": True}}, indent=2) + "\n", encoding="utf-8")
    (out / "meta.json").write_text(json.dumps({"id": out.name, "name": out.name}, indent=2) + "\n", encoding="utf-8")

    print(f"HyperFrames project: {out}  ({proj['duration']} s, {len(slots)} scenes, theme {theme}, "
          f"{len(proj['overlays'])} overlays, audio {'mixed' if has_audio else 'none'})")
    if skipped:
        print(f"  ! not drawn by the HyperFrames kit: {', '.join(skipped)}. Render this video with Remotion, or drop them from the plan.")
    if unsupported:
        print("  ! used by this project but only Remotion draws them: " + "; ".join(unsupported) + ". Render it with Remotion.")
    status = 0
    if a.check:
        status = subprocess.run(["npx", "--yes", f"hyperframes@{HF_VERSION}", "check"], cwd=out, shell=os.name == "nt").returncode
    if a.render and not status:
        status = subprocess.run(["npx", "--yes", f"hyperframes@{HF_VERSION}", "render", "--quality", a.quality, "--output", a.render],
                                cwd=out, shell=os.name == "nt").returncode
    if not a.check and not a.render:
        print(f"next: cd {out} && npx hyperframes@{HF_VERSION} check && npx hyperframes@{HF_VERSION} render --quality high --output final.mp4")
    return status


if __name__ == "__main__":
    sys.exit(main())
