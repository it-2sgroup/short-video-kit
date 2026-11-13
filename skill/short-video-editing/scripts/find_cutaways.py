#!/usr/bin/env python3
"""List the stretches of a take that can serve as cutaways: no one is speaking, someone (or a place) is on screen.

A talking-head pitch needs pictures for the stretches of the voice that no take holds (the portfolio part, the process
part). With no B-roll, the best free material is what surrounds the takes: the pre-roll (the speaker settles, smiles,
adjusts, steps into an empty frame), the walk-off after the line, the empty establishing shot before the speaker enters.
This script finds those stretches by the clip's own audio energy (speech = loud, in 50 ms windows) and ranks them:

    python scripts/find_cutaways.py /path/to/clips [--min 1.0] [--avoid used.json] [--json out.json] [--person MODEL]

Output per range: clip, start, end, length, a score (longer, quieter, brighter is better) and `person` (the share of the range
with a person in frame, measured on three frames with person_matte.py's model; skipped without --person). `--avoid` takes the
matches JSON of match_voice_takes.py: ranges a talking scene already uses (the take's spoken stretch, with a margin) are cut out.
Not judged here: pose, expression, lip movement (a director's countdown is louder than room tone and reads as speech, so the
usual result starts after it; --pre-roll counts it as quiet and gives many more ranges). Look at every range on a contact sheet before using it.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _venv import ensure_venv  # noqa: E402

ensure_venv("numpy", "onnxruntime")
import numpy as np  # noqa: E402

SR = 16000
EXT = {".mp4", ".mov", ".m4v", ".mkv", ".mxf", ".avi"}


def load_audio(path: Path, tmp: Path) -> np.ndarray:
    out = tmp / (path.stem + ".wav")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", str(path), "-vn", "-ac", "1", "-ar", str(SR), str(out)], capture_output=True)
    if r.returncode or not out.is_file():
        return np.zeros(0, np.float32)
    with wave.open(str(out), "rb") as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768


def speech_mask(x: np.ndarray, win: float = 0.05, pre_roll: bool = False) -> np.ndarray:
    n = int(win * SR)
    k = len(x) // n
    if k < 4:
        return np.ones(k, bool)
    rms = np.sqrt((x[:k * n].reshape(k, n) ** 2).mean(1))
    loud = np.percentile(rms, 90)
    floor = np.percentile(rms, 10)
    thr = max(0.006, floor * 2.5, loud * 0.12)  # speech is well above both the room tone and a fraction of the loud parts
    m = rms > thr
    if pre_roll:  # before the first loud speech, the speaker's countdown ("ok, 2, 3") counts as quiet: far fewer ranges are lost
        first = int(np.argmax(rms > loud * 0.5))
        m[:first] = rms[:first] > loud * 0.5
    # close short holes (a pause inside a sentence) and drop blips (a click): 0.3 s and 0.1 s
    from itertools import groupby
    out, i = m.copy(), 0
    for val, grp in groupby(m):
        ln = len(list(grp))
        if not val and ln < int(0.3 / win):
            out[i:i + ln] = True
        i += ln
    return out


def quiet_ranges(mask: np.ndarray, win: float, min_len: float, margin: float) -> list[tuple[float, float]]:
    out, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            i += 1
            continue
        j = i
        while j < n and not mask[j]:
            j += 1
        a, b = i * win + margin, j * win - margin
        if b - a >= min_len:
            out.append((round(a, 2), round(b, 2)))
        i = j
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="List quiet stretches of takes that can serve as cutaways.")
    ap.add_argument("clips", type=Path)
    ap.add_argument("--min", type=float, default=1.0, help="shortest range (s)")
    ap.add_argument("--margin", type=float, default=0.15, help="trimmed from each side of a quiet stretch (s)")
    ap.add_argument("--pre-roll", action="store_true", help="count the countdown before the first loud speech as quiet (the lips may still move: look at the frames)")
    ap.add_argument("--avoid", type=Path, help="matches JSON from match_voice_takes.py: stretches a talking scene already uses")
    ap.add_argument("--person", metavar="MODEL", nargs="?", const="auto", help="also measure how much of each range has a person in frame (needs the u2net_human_seg model)")
    ap.add_argument("--json", type=Path, help="write the ranges as JSON")
    a = ap.parse_args()

    avoid: dict[str, list[tuple[float, float]]] = {}
    if a.avoid:
        for stem, segs in json.loads(a.avoid.read_text(encoding="utf-8")).items():
            avoid[stem.upper()] = [(s["clip_from"] - 0.5, s["clip_to"] + 0.5) for s in segs]
    session = pm = None
    if a.person:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import onnxruntime as ort
        import person_matte as pm  # noqa: F811

        session = ort.InferenceSession(str(pm.find_model(None if a.person == "auto" else a.person)), providers=["CPUExecutionProvider"])

    files = sorted(p for p in (a.clips.iterdir() if a.clips.is_dir() else [a.clips]) if p.suffix.lower() in EXT)
    rows = []
    with tempfile.TemporaryDirectory() as td:
        for f in files:
            x = load_audio(f, Path(td))
            if len(x) < SR:
                continue
            for s, e in quiet_ranges(speech_mask(x, 0.05, a.pre_roll), 0.05, a.min, a.margin):
                for u0, u1 in avoid.get(f.stem.upper(), []):  # cut out what a talking scene uses
                    if s < u1 and e > u0:
                        if s < u0 - 0.01:
                            e = min(e, u0)
                        else:
                            s = max(s, u1)
                if e - s < a.min:
                    continue
                person = None
                if session is not None:
                    hits = [(pm.matte(session, pm.grab(f, s + (e - s) * q)) > 127).mean() > 0.02 for q in (0.15, 0.5, 0.85)]
                    person = round(sum(hits) / 3, 2)
                rows.append({"clip": f.stem.upper(), "start": s, "end": e, "length": round(e - s, 2), "person": person})
    for r in rows:
        r["score"] = round(min(r["length"], 4.0) + (1.5 if r["person"] else 0.0) * (r["person"] or 0), 2)
    rows.sort(key=lambda r: -r["score"])
    print("clip   start    end   length  person  score")
    for r in rows:
        print(f"{r['clip']:6} {r['start']:6.2f} {r['end']:6.2f}  {r['length']:5.2f}   {'' if r['person'] is None else r['person']!s:6}  {r['score']}")
    print(f"{len(rows)} range(s) of {a.min:g} s or more in {len(files)} clip(s). Look at them before using them.")
    if a.json:
        a.json.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
