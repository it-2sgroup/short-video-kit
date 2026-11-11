#!/usr/bin/env python3
"""Find which takes a supplied voice was cut from, and where: the key to lip-sync when the voice is NOT a fresh recording.

A "voice" file handed over with the footage is often the camera audio of the chosen takes, cut and joined (a talking
head, an interview, a presenter on a street). The picture of each take then matches its part of the voice sample for
sample, so a scene can use the take's own video with the voice laid over it and the lips are exact. This script
correlates the voice with every clip's audio and prints, per clip, the stretches that match and the LAG between the
two timelines:

    clip time = voice time + lag          (so a scene starting at voice time T uses `In = T + lag`)

    python scripts/match_voice_takes.py voice.mp3 /path/to/clips [--out matches.json] [--min-corr 0.85]

How: both sides become mono 16 kHz; each clip is cut into 1.5 s windows (0.75 s apart); each window is searched in the
voice by FFT cross-correlation, normalised by the local energy of the voice (a correlation of ~1 = the same samples). A
splice inside one take (a pause cut out of the voice) shows as a second lag of that clip: cut the scene there.
Windows below --min-corr are ignored; a take whose lines the voice does not contain simply prints nothing.
Needs numpy (the kit's venv) and ffmpeg. Camera audio that was re-recorded or noise-reduced hard may fall under the
threshold: lower --min-corr to 0.6 and read the numbers.
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

ensure_venv()
import numpy as np  # noqa: E402

SR = 16000
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".mxf", ".avi", ".wav", ".mp3", ".m4a"}


def load(path: Path, tmp: Path) -> np.ndarray:
    out = tmp / (path.stem + ".wav")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", str(path), "-vn", "-ac", "1", "-ar", str(SR), str(out)],
                       capture_output=True, text=True)
    if r.returncode or not out.is_file():
        return np.zeros(0, dtype=np.float32)
    with wave.open(str(out), "rb") as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768


def match(voice: np.ndarray, clip: np.ndarray, min_corr: float, win_s: float = 1.5, hop_s: float = 0.75) -> list[tuple[float, float, float]]:
    """(clip_time, voice_time, correlation) for every window of the clip found in the voice."""
    W, hop = int(win_s * SR), int(hop_s * SR)
    a = voice - voice.mean()
    n = 1 << int(np.ceil(np.log2(len(a) + W)))
    A = np.fft.rfft(a, n)
    cs2 = np.concatenate([[0.0], np.cumsum(a.astype(np.float64) ** 2)])
    rows = []
    for s in range(0, max(0, len(clip) - W), hop):
        b = clip[s:s + W] - clip[s:s + W].mean()
        if np.sqrt((b ** 2).mean()) < 0.004:  # silence correlates with everything: skip it
            continue
        cc = np.fft.irfft(A * np.conj(np.fft.rfft(b, n)), n)[:len(a) - W + 1]
        en = np.sqrt(np.maximum(cs2[W:W + len(cc)] - cs2[:len(cc)], 1e-9)) * np.linalg.norm(b)
        nc = np.abs(cc) / en
        k = int(np.argmax(nc))
        if nc[k] >= min_corr:
            rows.append((s / SR, k / SR, float(nc[k])))
    return rows


def segments(rows: list[tuple[float, float, float]], win_s: float = 1.5) -> list[dict]:
    """Group consecutive windows that share one lag (within 40 ms) into stretches."""
    out: list[dict] = []
    for c, v, nc in rows:
        lag = c - v
        if out and abs(out[-1]["lag"] - lag) < 0.04 and c - out[-1]["clip_to"] < win_s:
            out[-1].update(clip_to=c + win_s, voice_to=v + win_s)
            out[-1]["corr"] = round(max(out[-1]["corr"], nc), 3)
        else:
            out.append({"lag": round(lag, 4), "clip_from": c, "clip_to": c + win_s, "voice_from": v, "voice_to": v + win_s, "corr": round(nc, 3)})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Find which takes a supplied voice was cut from, and the lag between timelines.")
    ap.add_argument("voice", type=Path)
    ap.add_argument("clips", type=Path, help="folder of clips (or one clip)")
    ap.add_argument("--out", type=Path, help="write the matches as JSON")
    ap.add_argument("--min-corr", type=float, default=0.85, help="normalised correlation that counts as the same recording")
    a = ap.parse_args()

    files = sorted(p for p in (a.clips.iterdir() if a.clips.is_dir() else [a.clips]) if p.suffix.lower() in VIDEO_EXT)
    result: dict[str, list[dict]] = {}
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        voice = load(a.voice, tmp)
        if not len(voice):
            sys.exit(f"cannot read audio from {a.voice}")
        for f in files:
            clip = load(f, tmp)
            if len(clip) < SR:
                continue
            segs = segments(match(voice, clip, a.min_corr))
            if segs:
                result[f.stem] = segs
    if not result:
        print(f"no clip matches the voice at correlation >= {a.min_corr}: the voice is a separate recording (use trim_voice.py / align_captions.py), "
              "or the audio was processed too hard (try --min-corr 0.6)")
        return 1
    print("clip   voice (s)         clip (s)          lag      corr   (clip time = voice time + lag)")
    for stem, segs in result.items():
        for s in segs:
            print(f"{stem:6} {s['voice_from']:6.2f}-{s['voice_to']:6.2f}   {s['clip_from']:6.2f}-{s['clip_to']:6.2f}   {s['lag']:+8.3f}  {s['corr']:.2f}")
    covered = sorted((s["voice_from"], s["voice_to"]) for segs in result.values() for s in segs)
    gaps, t = [], 0.0
    for a0, b0 in covered:
        if a0 - t > 0.8:
            gaps.append((t, a0))
        t = max(t, b0)
    dur = len(voice) / SR
    if dur - t > 0.8:
        gaps.append((t, dur))
    if gaps:
        print("not covered by any take (show other pictures here, e.g. cutaways): " + ", ".join(f"{g0:.1f}-{g1:.1f}s" for g0, g1 in gaps))
    if a.out:
        a.out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
