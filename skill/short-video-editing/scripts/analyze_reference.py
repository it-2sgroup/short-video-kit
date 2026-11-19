#!/usr/bin/env python3
"""Measure a REFERENCE video (a sample clip you were asked to match) before planning a copy of it.

Reading a sample by eye misses what happens between two looks: a flash on frames 0, 2 and 4, a cut every 0.4 s, a sound on each
cut. This script reads every frame once (small, in memory) and every sample of the audio, and writes the facts a plan needs:

    python scripts/analyze_reference.py sample.mp4 --out ref/ [--dense auto | 0-3,10.2-12 --step 2] [--compare mine.mp4]

  report.md / report.json   - the facts below, as a table and as data (how to read every key: references/reference-analysis.md)
  scenes.png (+ scenes_2.png) - one frame just after every cut / change of shot, labelled with its time
  dense_<a>-<b>.png         - every --step-th frame of each --dense range (default: the first 3 s; `auto` = around every transition
                              run and flash): flashes, letters that jump up, a transition's in-between frames
  evidence/ev_*.png         - ONE strip per unique observation (a transition family, a flash, a camera move, a speed ramp, a freeze)
  diff.md + mine/           - with --compare: the same analysis of your recreation and a table of the differences, biggest first

What it measures (numbers, not opinions):
  shots         hard cuts (frame-to-frame change above --cut) AND the middle of every transition that changes the scene; the
                length of every shot, the median and the shortest
  transitions   `transitions[]`: every stretch of 4+ changing frames (a motion run) and every hard cut, with a FAMILY (crossfade,
                dip-to-black, dip-to-white, dissolve, mask-wipe, mask-iris, slide, cover, reveal, hard-cut, flash-cut, dip-cut,
                content-motion, unknown), its length in frames, a confidence and `needs_look`
  camera        `shots[i].camera`: zoom and pan curve, ease, shake per shot, from libvidstab vectors (unknown when the picture
                has too little detail)
  speed         `shots[i].speed`: velocity profile, ramps (hypothesis), runs of identical frames (freezes)
  flashes       a one-frame brightening that falls back within 6 frames (a white flash, a silhouette fill, a glint)
  grade         `grade`: Lab mean/std, luma p1/p50/p99, warmth, vignette, 5-colour palette, per shot and overall, and the kit
                looks (assets/grades.json) it resembles most (low confidence: the ungraded original is unknown)
  colours       the colour of the frame edge and centre just after each cut, named
  loudness      integrated LUFS, loudness range, true peak (ffmpeg ebur128): the target to master to
  spectrograms  spectrum_<a>-<b>.png, 15 s each: a click or pop is a thin vertical streak, a whoosh a slanted band, a riser a rising
                one, a note a horizontal line. (Detecting sounds automatically under a voice does not work: tested against a mix
                whose 68 cues are known, a detector found 5 of them.)

What it cannot do: say WHAT a graphic is, read text, or hear a sound's character (say so in the report you give: "not listened").
Numbers give timing and size; Claude reads the evidence strips for the NAME. Needs numpy (the kit's venv: SVK_PYTHON) and ffmpeg;
libvidstab for the camera, drawtext (libfreetype) only for burnt-in labels (without it the tiles are clean and the report lists
which time sits in which tile).
"""
from __future__ import annotations

import argparse
import colorsys
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _venv import ensure_venv  # noqa: E402

ensure_venv()
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import montage  # noqa: E402  (same folder)
import ref_measure as rm  # noqa: E402
import ref_text as rt  # noqa: E402


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, **kw)


def probe(path: Path) -> dict:
    r = run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,avg_frame_rate,sample_rate,pix_fmt,color_range:format=duration",
             "-of", "json", str(path)], text=True)
    if r.returncode:
        sys.exit(f"ffprobe failed: {r.stderr.strip()[:300]}")
    j = json.loads(r.stdout)
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), None)
    au = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    if not v:
        sys.exit("no video stream")
    n, d = (v["avg_frame_rate"].split("/") + ["1"])[:2]
    return {"width": v["width"], "height": v["height"], "fps": round(float(n) / float(d or 1), 3), "duration": float(j["format"]["duration"]),
            "codec": v["codec_name"], "pix_fmt": v.get("pix_fmt"), "range": v.get("color_range"), "audio": au["codec_name"] if au else None}


def read_frames(path: Path, fps: float, w: int, h: int) -> np.ndarray:
    """Every frame as a small RGB array [n, h, w, 3] (uint8): about 20 KB per frame."""
    r = run(["ffmpeg", "-hide_banner", "-v", "error", "-i", str(path), "-vf", f"fps={fps},scale={w}:{h}:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    if r.returncode:
        sys.exit(f"ffmpeg failed: {r.stderr.decode(errors='ignore')[-300:]}")
    a = np.frombuffer(r.stdout, np.uint8)
    n = len(a) // (w * h * 3)
    return a[: n * w * h * 3].reshape(n, h, w, 3)


def loudness(path: Path) -> dict | None:
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"], text=True)
    tail = r.stderr.split("Summary:")[-1] if "Summary:" in r.stderr else ""
    def num(label: str) -> float | None:
        m = re.search(rf"{label}:\s+(-?[\d.]+)", tail)
        return float(m.group(1)) if m else None
    i, lra, peak = num("I"), num("LRA"), num("Peak")
    return {"lufs": i, "lra": lra, "true_peak_db": peak} if i is not None else None


def colour_name(rgb: np.ndarray) -> str:
    r, g, b = (float(x) / 255 for x in rgb)
    hh, s, v = colorsys.rgb_to_hsv(r, g, b)
    if v < 0.16:
        return "black"
    if s < 0.14:
        return "white" if v > 0.86 else ("light grey" if v > 0.6 else ("grey" if v > 0.35 else "dark grey"))
    hue = hh * 360
    name = ("red" if hue < 14 or hue >= 346 else "orange" if hue < 40 else "yellow" if hue < 68 else "green" if hue < 165
            else "cyan" if hue < 200 else "blue" if hue < 255 else "purple" if hue < 290 else "magenta" if hue < 330 else "pink")
    return ("dark " if v < 0.4 else "light " if s < 0.4 and v > 0.8 else "") + name


def hard_cuts(diff: np.ndarray, thr: float) -> list[int]:
    """Frame indices where the picture jumps: a big change that its neighbours do not share (a slide is a RUN of medium changes)."""
    out = []
    for i in range(1, len(diff)):
        if diff[i] >= thr and diff[i] >= 1.6 * max(diff[i - 1] if i > 1 else 0, diff[i + 1] if i + 1 < len(diff) else 0):
            out.append(i + 1)   # diff[i] compares frame i with i+1: the new shot starts at i+1
    return out


def motion_runs(diff: np.ndarray, cuts: list[int], lo: float, min_len: int = 4) -> list[tuple[int, int]]:
    """Runs of >= min_len frames each changing by more than `lo` with no hard cut inside: transitions and animated graphics."""
    cutset = set(cuts)
    runs, start = [], None
    for i, d in enumerate(diff):
        moving = d >= lo and (i + 1) not in cutset
        if moving and start is None:
            start = i
        if (not moving or i == len(diff) - 1) and start is not None:
            end = i if not moving else i + 1
            if end - start >= min_len:
                runs.append((start, end))
            start = None
    return runs


def flashes(luma: np.ndarray, rise: float = 18.0, back: int = 6) -> list[int]:
    out = []
    for i in range(1, len(luma) - 1):
        if luma[i] - luma[i - 1] >= rise and luma[i + 1 : i + 1 + back].min() < luma[i] - rise * 0.6:
            out.append(i)
    return out


def spectrograms(video: Path, dur: float, out: Path, chunk: float = 15.0) -> list[str]:
    names = []
    t = 0.0
    while t < dur - 0.2:
        name = f"spectrum_{t:g}-{min(dur, t + chunk):g}.png"
        r = run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-ss", f"{t:.2f}", "-t", f"{chunk:.2f}", "-i", str(video), "-vn", "-ac", "1", "-lavfi",
                 "showspectrumpic=s=1500x300:legend=0:fscale=log:color=intensity", str(out / name)])
        if r.returncode == 0:
            names.append(name)
        t += chunk
    return names


def grab_frames(video: Path, fps: float, idxs: list[int], tmp: Path, prefix: str, width: int = 0) -> list[str]:
    """The frames with these numbers (the same numbering as read_frames), in ONE pass; files are named <prefix>_<seconds>.jpg so the
    number in the name is the label. Returns the paths of the frames that exist."""
    idxs = sorted({max(0, int(i)) for i in idxs})
    if not idxs:
        return []
    vf = f"fps={fps},select='{'+'.join(f'eq(n,{i})' for i in idxs)}'" + (f",scale={width}:-2" if width else "")
    pat = tmp / f"{prefix}_%04d.jpg"
    for flag in (["-fps_mode", "passthrough"], ["-vsync", "0"]):         # old ffmpeg builds only know -vsync
        r = run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", str(video), "-vf", vf, *flag, "-q:v", "3", str(pat)])
        if r.returncode == 0:
            break
    out = []
    for k, i in enumerate(idxs, 1):
        src = tmp / f"{prefix}_{k:04d}.jpg"
        if src.exists():
            dst = tmp / f"{prefix}_{i / fps:.3f}.jpg"
            src.replace(dst)
            out.append(str(dst))
    return out


def sheet(files: list[str], out: Path, cols: int, width: int, labels: list[str] | None = None) -> list[float]:
    """Tile the frames; returns the time of every tile in reading order (the index when this ffmpeg cannot draw labels)."""
    if not files:
        return []
    montage.tile(files, str(out), cols, width, labels)
    return [montage.number_in(Path(f).name) or 0.0 for f, _ in montage.plan(files)]


def parse_ranges(spec: str, dur: float, runs: list[tuple[int, int]], fl: list[int], fps: float) -> list[tuple[float, float]]:
    """--dense: `a-b,c-d` seconds, or `auto` = half a second of margin around every motion run and flash, merged, at most 6."""
    if spec.strip() != "auto":
        out = []
        for rng in [r for r in spec.split(",") if r.strip()]:
            lo, _, hi = rng.partition("-")
            out.append((float(lo), float(hi or float(lo) + 3)))
        return out
    marks = sorted([(s / fps - 0.5, e / fps + 0.5) for s, e in runs] + [(i / fps - 0.5, i / fps + 0.9) for i in fl])
    merged: list[list[float]] = []
    for lo, hi in marks:
        lo, hi = max(0.0, lo), min(dur, hi)
        if merged and lo <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    merged.sort(key=lambda r: -(r[1] - r[0]))
    return sorted((round(a, 2), round(min(b, a + 4.0), 2)) for a, b in merged[:6]) or [(0.0, min(3.0, dur))]


def evidence_plan(rep: dict, fps: float, n: int) -> list[dict]:
    """One packet per UNIQUE observation (not per occurrence): which frames to show and what the numbers say."""
    packets: dict[tuple, dict] = {}

    def add(key: tuple, kind: str, frames: list[int], note: str, when: float) -> None:
        if key in packets:
            packets[key]["occurrences"].append(round(when, 2))
        elif len(packets) < 16:
            packets[key] = {"kind": kind, "frames": [min(max(0, f), n - 1) for f in frames], "note": note, "occurrences": [round(when, 2)]}

    for t in rep["transitions"]:
        if t["family"] == "hard-cut":
            continue
        c = round(t["t"] * fps)
        if t["kind"] == "cut":
            add(("tr", t["family"]), "transition", list(range(c - 3, c + 4)), f"{t['family']} around a cut at {t['t']:.2f} s", t["t"])
        else:
            step = max(1, -(-(t["frames"] + 2) // 10))
            add(("tr", t["family"], round(t["frames"] / 3)), "transition", list(range(c - 1, c + t["frames"] + 2, step)),
                f"{t['family']}{' ' + t['direction'] if t['direction'] else ''}, {t['frames']} frames, confidence {t['confidence']}", t["t"])
    if rep["flashes"]:
        i = round(rep["flashes"][0] * fps)
        add(("flash",), "flash", list(range(i - 2, i + 6)), f"flash at {rep['flashes'][0]:.2f} s (brightens, falls back within 6 frames)", rep["flashes"][0])
        packets[("flash",)]["occurrences"] = [round(t, 2) for t in rep["flashes"]]
    for i, sh in enumerate(rep["shots"]):
        a, b = round(sh["start"] * fps), round(sh["end"] * fps) - 1
        cam, sp = sh.get("camera", {}), sh.get("speed", {})
        if cam.get("quality") == "ok" and cam["driver"] != "static":
            add(("cam", cam["driver"], cam["ease"]), "camera", [round(a + (b - a) * q / 5) for q in range(6)],
                f"shot {i + 1}: {cam['driver']}, zoom 1.00 -> {cam['zoom_end']}, pan {cam['pan_x']:+.2f}/{cam['pan_y']:+.2f} of the width, ease {cam['ease']}", sh["start"])
        if sp.get("ramp", "none") != "none":
            add(("speed", sp["ramp"]), "speed", [round(a + (b - a) * q / 5) for q in range(6)], f"shot {i + 1}: {sp['ramp']} x{sp['ramp_factor']} (hypothesis)", sh["start"])
        for fr0, fr1 in sp.get("frozen_frames", [])[:1]:
            add(("freeze",), "freeze", [fr0 - 1, fr0, (fr0 + fr1) // 2, fr1, fr1 + 1], f"identical frames {fr0 / fps:.2f}-{fr1 / fps:.2f} s ({fr1 - fr0 + 1} frames)", fr0 / fps)
    return [{"id": f"ev{k + 1:02d}_{p['kind']}", **p} for k, p in enumerate(packets.values())]


def analyze(video: Path, out: Path, a: argparse.Namespace) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    for stale in [*out.glob("scenes*.png"), *out.glob("dense_*.png"), *out.glob("spectrum_*.png"), *out.glob("evidence/ev*.png")]:
        stale.unlink()                      # sheets of an earlier run in this folder would be read as this video's
    info = probe(video)
    fps, dur = info["fps"], info["duration"]
    w = 64
    h = max(2, round(w * info["height"] / info["width"] / 2) * 2)
    print(f"{video.name}: {info['width']}x{info['height']} {fps} fps, {dur:.2f} s, {info['codec']} {info['pix_fmt']} {info['range'] or ''}, audio {info['audio'] or 'none'}")
    fr = read_frames(video, fps, w, h)
    n = len(fr)
    f32 = fr.astype(np.float32)
    diff = np.abs(f32[1:] - f32[:-1]).mean(axis=(1, 2, 3)) / 255
    luma = (f32 @ np.array([0.2126, 0.7152, 0.0722], np.float32)).mean(axis=(1, 2))
    del f32
    wh = next(x for x in (96, 80, 64) if dur * fps * x * (x * info["height"] // info["width"]) * 3 < 6e8)       # bound the memory of long references
    fh = read_frames(video, fps, wh, max(2, round(wh * info["height"] / info["width"] / 2) * 2))

    cuts = hard_cuts(diff, a.cut)
    fast = motion_runs(diff, cuts, a.motion)
    # a crossfade or soft wipe changes the picture by only ~1-2 % per frame, below --motion: look for those at the lower --gradual level
    # (capped at 1.5 s so a long camera move is not one "transition"); each candidate is kept below only if it is a real change of scene
    slow = [r for r in motion_runs(diff, cuts, a.gradual, min_len=6) if r[1] - r[0] <= round(1.5 * fps)]
    cand = sorted(slow + [r for r in fast if not any(r[0] < x[1] and x[0] < r[1] for x in slow)])
    fl = flashes(luma)

    # ---- M1 transitions: every motion run, then every hard cut
    trans, runs = [], []
    for k, (s, e) in enumerate(cand):
        lo = max([c for c in cuts if c <= s] + [cand[k - 1][1] if k else 0])
        hi = min([c - 1 for c in cuts if c > e] + [cand[k + 1][0] if k + 1 < len(cand) else n - 1])
        ft = rm.transition_features(fh, s, min(e, n - 1), lo, hi)
        cl = rm.classify_run(ft)
        if e - s > round(1.5 * fps):          # nothing that long is a transition: a continuous camera move or animation
            cl = {"family": "content-motion", "direction": None, "confidence": 0.5, "needs_look": True,
                  "note": f"{(e - s) / fps:.1f} s of continuous change: a camera move or an animated graphic, not a transition"}
        if cl["family"] == "content-motion" and (s, e) not in fast and not any(s < x[1] and x[0] < e for x in fast):
            continue
        runs.append((s, e))
        trans.append({"t": round(s / fps, 3), "kind": "run", "frames": e - s, "seconds": round((e - s) / fps, 2), **cl, "features": ft})
    for c in cuts:
        trans.append({"t": round(c / fps, 3), "kind": "cut", "frames": 0, "seconds": 0.0, **rm.classify_cut(luma, c), "strength": round(float(diff[c - 1]), 2)})
    trans.sort(key=lambda t: t["t"])

    # ---- shots: hard cuts plus the middle of every run that changes the scene
    bounds = {c: "hard-cut" for c in cuts}
    for (s, e), t in zip(runs, [t for t in trans if t["kind"] == "run"]):
        if t["family"] != "content-motion":
            bounds[(s + e) // 2] = t["family"]
    starts = [0] + sorted(bounds)
    ends = starts[1:] + [n]
    shots = [{"start": round(s0 / fps, 3), "end": round(e0 / fps, 3), "length": round((e0 - s0) / fps, 3), "enter": bounds.get(s0, "start")} for s0, e0 in zip(starts, ends)]
    lens = np.array([x["length"] for x in shots])
    skip = {i for (s, e), tr in zip(runs, [x for x in trans if x['kind'] == 'run']) if tr['family'] != 'content-motion' for i in range(s + 1, e + 1)}

    # colours just after each shot start: the edge band (12 % of the frame) and the centre
    bh, bw = max(1, h // 8), max(1, w // 8)
    for sh, s0 in zip(shots, starts):
        im = fr[min(n - 1, s0 + 2)]
        edge = np.concatenate([im[:bh].reshape(-1, 3), im[-bh:].reshape(-1, 3), im[:, :bw].reshape(-1, 3), im[:, -bw:].reshape(-1, 3)])
        sh["edge"], sh["centre"] = colour_name(np.median(edge, axis=0)), colour_name(np.median(im[h // 3: 2 * h // 3, w // 3: 2 * w // 3].reshape(-1, 3), axis=0))

    # ---- M2 camera and M3 speed per shot
    vec = rm.vidstab_vectors(video, fps) if montage.has_filter("vidstabdetect") else None
    vw = 480.0
    vh = 2 * round(480 * info["height"] / info["width"] / 2)
    for sh, s0, e0 in zip(shots, starts, ends):
        sh["camera"], sh["speed"] = rm.shot_motion(vec, s0, e0, fps, vw, vh, skip, diff)
        sh["speed"]["frozen_frames"] = rm.frozen_runs(diff, s0, e0)
        sh["speed"]["frozen_runs"] = [{"start": round(x / fps, 3), "seconds": round((y - x + 1) / fps, 2), "frames": y - x + 1} for x, y in sh["speed"]["frozen_frames"]]

    # ---- M7 grade: three frames per shot (outside transition runs), per shot and pooled
    per_shot, pool = [], []
    for s0, e0 in zip(starts, ends):
        pick = [i for i in (s0 + round((e0 - s0 - 1) * q) for q in (0.25, 0.5, 0.75)) if i < n]
        pick = [min([j for j in range(s0, e0) if j not in skip] or [s0], key=lambda j: abs(j - i)) for i in pick]
        per_shot.append(rm.fingerprint(fh[pick]))
        pool.append(fh[pick])
    gfp = rm.fingerprint(np.concatenate(pool))
    effects = rm.look_effects(HERE.parent / "assets" / "grades.json") if (HERE.parent / "assets" / "grades.json").is_file() else {}
    grade = {"global": gfp, "per_shot": per_shot, "nearest": rm.nearest_looks(gfp, effects) if effects else [],
             "nearest_note": "indicative only: the ungraded original is unknown, so a scene that is warm by nature reads as a warm grade",
             "needs_look": True}

    # ---- M4/M5/M6/M11 text (optional OCR), M8 beats, M9 sound hints, M10 silhouette hints
    dense_ranges = parse_ranges(a.dense, dur, runs, fl, fps)
    text = rt.analyze_text(video, info, fps, n, starts, dense_ranges, a.step, out) if not a.no_ocr else {"available": False, "install": None, "text_events": [], "layout": None, "note": "skipped (--no-ocr)"}
    cut_t = [round(c / fps, 3) for c in cuts] + [round((s + e) / 2 / fps, 3) for (s, e), t in zip(runs, [t for t in trans if t["kind"] == "run"]) if t["family"] != "content-motion"]
    music = rm.beat_alignment(video, sorted(cut_t), fps) if info["audio"] else None
    ev_times = [{"t": t, "kind": "cut"} for t in sorted(cut_t)] + [{"t": t, "kind": "flash"} for t in [round(i / fps, 3) for i in fl]] + \
              [{"t": e["t_in"], "kind": "text-in"} for e in text["text_events"]]
    hints = rm.sound_hints(video, ev_times) if info["audio"] else None
    effects = rm.silhouette_hints(fh)

    # ---- audio
    loud = loudness(video) if info["audio"] else None
    spectra = spectrograms(video, dur, out) if info["audio"] else []

    report = {
        "video": video.name, **info, "frames": n, "ffmpeg": {"drawtext": montage.has_filter("drawtext"), "vidstab": vec is not None},
        "shots": shots,
        "shot_length": {"count": len(lens), "median": round(float(np.median(lens)), 2), "shortest": round(float(lens.min()), 2), "longest": round(float(lens.max()), 2),
                        "cuts_per_minute": round((len(shots) - 1) / dur * 60, 1)},
        "transitions": trans,
        "motion_runs": [{"start": round(s / fps, 3), "frames": e - s, "seconds": round((e - s) / fps, 2)} for s, e in fast],
        "flashes": [round(i / fps, 3) for i in fl],
        "grade": grade, "loudness": loud,
        "text": {k: text.get(k) for k in ("available", "install", "frames_ocr", "note")}, "text_events": text["text_events"], "layout": text["layout"],
        "music": music, "sound_hints": hints, "effects": effects,
    }

    # ---- pictures: scenes, dense ranges, one evidence packet per unique observation
    sheet_times: dict[str, list[float]] = {}
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        scene_idx = [min(n - 1, s0 + max(1, round(0.1 * fps))) for s0 in starts]
        for k in range(0, len(scene_idx), 40):
            files = grab_frames(video, fps, scene_idx[k: k + 40], tmp, f"s{k // 40}", 180)
            name = "scenes.png" if k == 0 else f"scenes_{k // 40 + 1}.png"
            sheet_times[name] = sheet(files, out / name, 8, 180)
        dense_written = []
        for t0, t1 in dense_ranges:
            idx = [int(round(t * fps)) for t in np.arange(t0, min(t1, dur), a.step / fps)][:48]
            name = f"dense_{t0:g}-{t1:g}.png"
            sheet_times[name] = sheet(grab_frames(video, fps, idx, tmp, "d", 160), out / name, 8, 160)
            dense_written.append(name)
        (out / "evidence").mkdir(exist_ok=True)
        evidence = []
        for pk in evidence_plan(report, fps, n):
            files = grab_frames(video, fps, pk["frames"], tmp, pk["id"], 200)
            if not files:
                continue
            name = f"evidence/{pk['id']}.png"
            times = sheet(files, out / name, min(6, len(files)), 200, [f"{montage.number_in(Path(f).name):.2f}s" for f in files])
            evidence.append({"id": pk["id"], "kind": pk["kind"], "file": name, "note": pk["note"], "occurrences": pk["occurrences"], "tile_times": times})
    report["evidence"] = evidence
    report["sheets"] = ["scenes.png", *[s for s in sheet_times if s.startswith("scenes_")], *dense_written, *[e["file"] for e in evidence], *spectra]
    report["sheet_times"] = sheet_times
    report["read_by_claude"] = ["name of each transition marked needs_look", "what any graphic, text or sticker is", "whether a ramp is a retime or an eased camera",
                                "sound effects and music (never listened to by this tool: sound_hints are hints)", "every text string (OCR reads Vietnamese partly)",
                                "the font (font.in_kit_candidates are class matches, never a name)", "text behind a subject (not detectable)"]
    (out / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "report.md").write_text(report_md(report, info, n, dur), encoding="utf-8")
    fam: dict[str, int] = {}
    for t in trans:
        fam[t["family"]] = fam.get(t["family"], 0) + 1
    print(f"{len(lens)} shots (median {report['shot_length']['median']} s, shortest {report['shot_length']['shortest']} s), transitions {fam or 'none'}, "
          f"{len(fl)} flashes, {len(evidence)} evidence strips" + (f", {loud['lufs']} LUFS / {loud['true_peak_db']} dBTP" if loud else ""))
    return report


def report_md(rep: dict, info: dict, n: int, dur: float) -> str:
    sl, g = rep["shot_length"], rep["grade"]["global"]
    md = [f"# Reference: {rep['video']}", "", f"{info['width']}x{info['height']}, {info['fps']} fps, {dur:.1f} s, {n} frames. Audio: {info['audio'] or 'none'}. "
          f"drawtext in this ffmpeg: {'yes' if rep['ffmpeg']['drawtext'] else 'no (tiles are unlabelled: the time of each tile is listed under every sheet)'}; "
          f"libvidstab: {'yes' if rep['ffmpeg']['vidstab'] else 'no (camera unknown)'}.", "",
          "Keys are explained in `references/reference-analysis.md`. **Measured** = timing, sizes, numbers. **Read by Claude** = the name of anything marked "
          "`look`, what a graphic is, whether a ramp is a retime: open the evidence strips.", "",
          "## Shots", "", f"{sl['count']} shots, {sl['cuts_per_minute']} changes/min (hard cuts and scene-changing transitions); median {sl['median']} s, "
          f"shortest {sl['shortest']} s, longest {sl['longest']} s.", "",
          "| # | start | end | length | enter | edge colour | centre colour | camera | speed |", "|---|---|---|---|---|---|---|---|---|"]
    for i, s in enumerate(rep["shots"]):
        c, sp = s["camera"], s["speed"]
        cam = "unknown" if c["quality"] != "ok" else f"{c['driver']} z{c['zoom_end']} ease {c['ease']}, shake {c['shake']['level']}"
        spd = sp["ramp"] + (f" x{sp['ramp_factor']}" if sp["ramp"] != "none" else "") + (f", {len(sp['frozen_runs'])} freeze" if sp["frozen_runs"] else "")
        md.append(f"| {i + 1} | {s['start']:.2f} | {s['end']:.2f} | {s['length']:.2f} | {s['enter']} | {s['edge']} | {s['centre']} | {cam} | {spd} |")
    md += ["", "## Transitions (family, length, confidence; `look` = Claude must read the dense sheet or evidence strip)", "",
           "| t (s) | kind | frames | family | direction | confidence | look | note |", "|---|---|---|---|---|---|---|---|"]
    rows = [t for t in rep["transitions"] if t["family"] != "hard-cut"]
    md += [f"| {t['t']:.2f} | {t['kind']} | {t['frames']} | {t['family']} | {t['direction'] or ''} | {t['confidence']} | {'look' if t['needs_look'] else ''} | {t['note']} |" for t in rows] or ["| none | | | | | | | |"]
    md += ["", f"{sum(1 for t in rep['transitions'] if t['family'] == 'hard-cut')} plain hard cuts (listed in report.json)."]
    md += ["", "## Flashes (a one-frame brightening that falls back)", "", ", ".join(f"{t:.2f} s" for t in rep["flashes"]) or "none"]
    md += ["", "## Grade (as graded: the original is unknown)", "",
           f"Lab mean {g['lab_mean']}, std {g['lab_std']}; luma p1 {g['luma']['p1']} / p50 {g['luma']['p50']} / p99 {g['luma']['p99']}; chroma {g['chroma']}; "
           f"warmth (b*) {g['warmth_b']}, tint (a*) {g['tint_a']}; corner/centre luma {g['vignette']}.", "",
           "Palette: " + ", ".join(f"{p['hex']} ({int(p['share'] * 100)} %)" for p in g["palette"])]
    if rep["grade"]["nearest"]:
        md.append("")
        md.append("Nearest kit looks (indicative, low confidence): " + ", ".join(f"{x['look']} ({x['distance']})" for x in rep["grade"]["nearest"]))
    md += ["", "## Text (OCR: strings are hints, boxes, frames and colours are measurements)", ""]
    tx = rep["text"]
    if not tx["available"]:
        md.append(f"No text measurements: {tx['note']}")
    else:
        md += [f"{len(rep['text_events'])} text events from {tx['frames_ocr']} OCR frames. {tx['note']}.", "",
               "| id | in (frame) | out (frame) | text (hint) | bbox x,y,w,h | entry | exit | fill / stroke | highlight | look |", "|---|---|---|---|---|---|---|---|---|---|"]
        for e in rep["text_events"]:
            st, mi, mo = e.get("style") or {}, e["motion_in"], e["motion_out"]
            hl = st.get("highlight") or {}
            md.append(f"| {e['id']} | {e['t_in']:.2f} ({e['frame_in']}) | {e['t_out']:.2f} ({e['frame_out']}) | {e['text'][:40]} | {', '.join(f'{v:g}' for v in e['bbox'])} | "
                      f"{mi['family']}{' ' + mi.get('detail', '') if mi.get('detail') else ''} | {mo['family']} | {st.get('fill', '')} / {st.get('stroke') or '-'} | {hl.get('mode', '')} | {'look' if e['needs_look'] else ''} |")
        fonts = [e for e in rep["text_events"] if e.get("font")]
        if fonts:
            md += ["", "Font class (features, never a name; compare the crop with the candidates): "] + [f"- {e['id']}: {e['font']['class']}, {e['font']['width']}, {e['font']['weight']} (stroke {e['font']['stroke_ratio']}); kit candidates "
                                                                        f"{', '.join(e['font']['in_kit_candidates'][:5]) or 'none'}; crop `{e['font']['evidence']}`" for e in fonts[:12]]
        if rep["layout"]:
            md += ["", "Layout (seconds of text by band; the kit: " + rep["layout"]["kit"] + "): " + ", ".join(f"{b['band']} {b['share']:.0%}" for b in rep["layout"]["bands"])]
    md += ["", "## Music and cuts", ""]
    mu = rep["music"]
    md.append("no audio or too few cuts." if not mu else mu.get("error") or (f"{mu['bpm']} bpm (confidence {mu['confidence']}); cuts within 3 frames of a beat: {mu['cuts_on_beat']} "
              f"(a random cut scores {mu.get('chance')}: only a clearly higher share means cut to the beat). Hint." if mu.get("cuts_on_beat") is not None else mu.get("note", "")))
    md += ["", "## Sound at the cuts, flashes and texts (hint, not listened)", ""]
    sh_ = [h for h in (rep["sound_hints"] or []) if h["transient"]]
    md += [f"- {h['t']:.2f} s {h['kind']}: band z low/mid/high {h['band_z']['low']}/{h['band_z']['mid']}/{h['band_z']['high']}" for h in sh_[:20]] or ["- no transient stands out (a voice or music can hide one)"]
    md += ["", "## Effect hints", ""]
    md += [f"- {e['kind']} on frames {e['frames']}, colour {e['colour']}, bbox {e['bbox']}: {e['note']}" for e in rep["effects"]] or ["- no silhouette flash found on the first 8 frames (text behind a subject cannot be detected from pixels)"]
    md += ["", "## Sound", ""]
    if rep["loudness"]:
        md.append(f"Integrated {rep['loudness']['lufs']} LUFS, range {rep['loudness']['lra']} LU, true peak {rep['loudness']['true_peak_db']} dBFS.")
    md.append("Sound effects are not detected automatically (a voice hides them): read the spectrum_*.png sheets against the cut times and say nobody listened.")
    md += ["", "## Evidence strips (one per unique observation)", ""]
    md += [f"- `{e['file']}`: {e['note']}; seen at {', '.join(f'{t:.2f}' for t in e['occurrences'][:8])} s" for e in rep["evidence"]] or ["- none"]
    md += ["", "## Sheets to look at", ""]
    for s in rep["sheets"]:
        tt = rep["sheet_times"].get(s) or next((e["tile_times"] for e in rep["evidence"] if e["file"] == s), None)
        md.append(f"- `{s}`" + (f": tiles in order = {', '.join(f'{t:g}' for t in tt)} s" if tt and not rep["ffmpeg"]["drawtext"] else ""))
    md += ["", "Numbers give timing; the sheets give the technique. List what you SEE in each sheet next to these times."]
    return "\n".join(md) + "\n"


def write_diff(ref: dict, mine: dict, path: Path) -> None:
    """diff.md: the recreation against the reference, the biggest differences first."""
    def fams(r: dict) -> dict:
        d: dict[str, int] = {}
        for t in r["transitions"]:
            if t["family"] != "hard-cut":
                d[t["family"]] = d.get(t["family"], 0) + 1
        return d

    def zooms(r: dict) -> list[float]:
        return [s["camera"]["zoom_end"] for s in r["shots"] if s["camera"].get("quality") == "ok" and s["camera"]["driver"] != "static"]

    def mean_run(r: dict) -> float:
        v = [t["frames"] for t in r["transitions"] if t["kind"] == "run" and t["family"] != "content-motion"]
        return round(float(np.mean(v)), 1) if v else 0.0

    rows = [("duration (s)", ref["duration"], mine["duration"]), ("shots", ref["shot_length"]["count"], mine["shot_length"]["count"]),
            ("changes per minute", ref["shot_length"]["cuts_per_minute"], mine["shot_length"]["cuts_per_minute"]),
            ("median shot (s)", ref["shot_length"]["median"], mine["shot_length"]["median"]), ("shortest shot (s)", ref["shot_length"]["shortest"], mine["shot_length"]["shortest"]),
            ("transition frames (mean of runs)", mean_run(ref), mean_run(mine)), ("flashes", len(ref["flashes"]), len(mine["flashes"])),
            ("camera moves (shots)", len(zooms(ref)), len(zooms(mine))),
            ("zoom end, largest", max(zooms(ref), default=1.0), max(zooms(mine), default=1.0)),
            ("LUFS", (ref["loudness"] or {}).get("lufs"), (mine["loudness"] or {}).get("lufs")),
            ("true peak (dBFS)", (ref["loudness"] or {}).get("true_peak_db"), (mine["loudness"] or {}).get("true_peak_db")),
            ("grade warmth b*", ref["grade"]["global"]["warmth_b"], mine["grade"]["global"]["warmth_b"]),
            ("grade chroma", ref["grade"]["global"]["chroma"], mine["grade"]["global"]["chroma"]),
            ("luma p1", ref["grade"]["global"]["luma"]["p1"], mine["grade"]["global"]["luma"]["p1"]),
            ("luma p99", ref["grade"]["global"]["luma"]["p99"], mine["grade"]["global"]["luma"]["p99"])]
    rt_, mt_ = ref.get("text_events") or [], mine.get("text_events") or []
    if (ref.get("text") or {}).get("available") and (mine.get("text") or {}).get("available"):   # text rows only when OCR ran on both
        med = lambda ev, k: round(float(np.median([e["bbox"][k] for e in ev])), 3) if ev else None   # noqa: E731
        rows += [("text events", len(rt_), len(mt_)), ("text on screen (s)", round(sum(e["t_out"] - e["t_in"] for e in rt_), 1), round(sum(e["t_out"] - e["t_in"] for e in mt_), 1)),
                 ("text: median box height (share of the frame)", med(rt_, 3), med(mt_, 3)), ("text: median top (share of the frame)", med(rt_, 1), med(mt_, 1))]
    md = [f"# Reference vs recreation", "", f"Reference `{ref['video']}`, recreation `{mine['video']}`. Fix the biggest relative differences first.", "",
          "| measure | reference | mine | difference |", "|---|---|---|---|"]
    scored = []
    for name, r, m in rows:
        if r is None or m is None:
            md.append(f"| {name} | {r} | {m} | n/a |")
            continue
        d = round(m - r, 2)
        scored.append((abs(d) / (abs(r) + 1e-6) if name not in ("LUFS", "true peak (dBFS)") else abs(d) / 6, name, r, m, d))
        md.append(f"| {name} | {r} | {m} | {d:+} |")
    md += ["", f"Transition families: reference {fams(ref) or 'none'}; mine {fams(mine) or 'none'}.", "", "## Transitions, paired by time (within 0.5 s)", "",
           "| reference t | reference family, frames | mine t | mine family, frames |", "|---|---|---|---|"]
    mt = [t for t in mine["transitions"] if t["family"] != "hard-cut"]
    for t in [t for t in ref["transitions"] if t["family"] != "hard-cut"]:
        near = min(mt, key=lambda x: abs(x["t"] - t["t"]), default=None)
        ok = near is not None and abs(near["t"] - t["t"]) <= 0.5
        md.append(f"| {t['t']:.2f} | {t['family']}, {t['frames']} | " + (f"{near['t']:.2f} | {near['family']}, {near['frames']} |" if ok else "missing | |"))
    md += ["", "## Shots, paired by order" + ("" if len(ref["shots"]) == len(mine["shots"]) else f" (counts differ: {len(ref['shots'])} vs {len(mine['shots'])})"), "",
           "| # | ref length | mine length | ref camera | mine camera |", "|---|---|---|---|---|"]
    cam = lambda s: "unknown" if s["camera"].get("quality") != "ok" else f"{s['camera']['driver']} z{s['camera']['zoom_end']} {s['camera']['ease']}"   # noqa: E731
    for i in range(min(len(ref["shots"]), len(mine["shots"]), 60)):
        r, m = ref["shots"][i], mine["shots"][i]
        md.append(f"| {i + 1} | {r['length']:.2f} | {m['length']:.2f} | {cam(r)} | {cam(m)} |")
    if (ref.get("text") or {}).get("available") and (mine.get("text") or {}).get("available"):
        md += ["", "## Text events, paired by time (within 0.7 s)", "",
               "Strings are not compared (OCR is a hint and your words are your own): when, where, how big and how it enters are.", "",
               "| reference in-out | ref top, height | ref enters | mine in-out | mine top, height | mine enters | top diff | height diff |", "|---|---|---|---|---|---|---|---|"]
        used: set[str] = set()
        for e in rt_:
            near = min((x for x in mt_ if x["id"] not in used), key=lambda x: abs(x["t_in"] - e["t_in"]), default=None)
            ref_cells = f"{e['t_in']:.2f}-{e['t_out']:.2f} | {e['bbox'][1]:.3f}, {e['bbox'][3]:.3f} | {(e.get('motion_in') or {}).get('family', '?')}"
            if near is None or abs(near["t_in"] - e["t_in"]) > 0.7:
                md.append(f"| {ref_cells} | missing | | | | |")
                continue
            used.add(near["id"])
            md.append(f"| {ref_cells} | {near['t_in']:.2f}-{near['t_out']:.2f} | {near['bbox'][1]:.3f}, {near['bbox'][3]:.3f} | {(near.get('motion_in') or {}).get('family', '?')} | "
                      f"{near['bbox'][1] - e['bbox'][1]:+.3f} | {near['bbox'][3] - e['bbox'][3]:+.3f} |")
        extra = [x for x in mt_ if x["id"] not in used]
        md += ["", f"Text of yours with no counterpart in the reference: {len(extra)}" + (" (" + ", ".join(f"{x['t_in']:.2f} s" for x in extra[:8]) + ")" if extra else "") + "."]
    md += ["", "## Biggest differences", ""] + [f"- {name}: reference {r}, mine {m} ({d:+})" for _, name, r, m, d in sorted(scored, reverse=True)[:5]]
    md += ["", "Put the two side by side at the same seconds with `montage.py` before trusting any row: these are measurements, not a judgement."]
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Measure a reference video: shots, transition families, camera, speed, grade, flashes, loudness, evidence strips.")
    ap.add_argument("video", type=Path)
    ap.add_argument("--out", type=Path, default=Path("ref"))
    ap.add_argument("--cut", type=float, default=0.10, help="hard-cut threshold: mean change of a frame, 0..1 (default 0.10)")
    ap.add_argument("--motion", type=float, default=0.025, help="per-frame change that counts as movement for a transition run (default 0.025)")
    ap.add_argument("--gradual", type=float, default=0.010, help="per-frame change that counts for a SLOW transition run of 6-45 frames (default 0.010)")
    ap.add_argument("--dense", default="0-3", help="seconds ranges to pull every --step-th frame from, e.g. 0-3,10.2-12, or `auto` (around every transition and flash)")
    ap.add_argument("--step", type=int, default=2, help="every n-th frame in the dense sheets (default 2)")
    ap.add_argument("--no-ocr", action="store_true", help="skip the text measurements (OCR is optional: ./setup.sh --ocr)")
    ap.add_argument("--compare", type=Path, help="your recreation: analysed the same way into <out>/mine/, with diff.md beside the report")
    a = ap.parse_args()
    for v in (a.video, a.compare):
        if v and not v.is_file():
            sys.exit(f"not found: {v}")
    ref = analyze(a.video, a.out, a)
    if a.compare:
        mine = analyze(a.compare, a.out / "mine", a)
        write_diff(ref, mine, a.out / "diff.md")
        print(f"wrote {a.out / 'diff.md'}")
    print(f"wrote {a.out / 'report.md'}, report.json and {', '.join(ref['sheets'][:3])}...: LOOK at the sheets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
