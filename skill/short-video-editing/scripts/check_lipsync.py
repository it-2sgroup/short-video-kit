#!/usr/bin/env python3
"""Check, on the FINISHED video, that every talking scene still lines up with its take: the proof that the lips are in sync.

    python scripts/check_lipsync.py project.json final.mp4 --clips /path/to/clips-or-proxies [--tolerance 0.035]

For each scene that plays a take (a clip, not a card, with speech in its own audio), the take's camera audio from the scene's planned `In` is
correlated with the final soundtrack around the scene's start. If the voice was cut from those takes (match_voice_takes.py), the best match is at
offset 0: the printed offset (ms) is how far the soundtrack is from the picture's own sound. More than one frame (33 ms) is a bug in the timeline
(wrong lag, a transition handle, a trimmed clip). Scenes whose take is silent there, or whose voice does not come from that take, print nothing
or a low correlation. Needs numpy and ffmpeg.
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
EXT = (".mp4", ".MP4", ".mov", ".MOV", ".m4v", ".mkv")


def audio(path: Path, tmp: Path) -> np.ndarray:
    out = tmp / (path.stem + ".wav")
    if not out.is_file():
        subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", str(path), "-vn", "-ac", "1", "-ar", str(SR), str(out)], capture_output=True)
    if not out.is_file():
        return np.zeros(0, np.float32)  # no audio stream (a proxy made without sound)
    with wave.open(str(out), "rb") as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768


def main() -> int:
    ap = argparse.ArgumentParser(description="Check that talking scenes still line up with their takes in the finished video.")
    ap.add_argument("project", type=Path)
    ap.add_argument("video", type=Path)
    ap.add_argument("--clips", type=Path, required=True, help="folder holding the ORIGINAL clips (proxies are made without sound)")
    ap.add_argument("--tolerance", type=float, default=0.035, help="seconds (one frame is 0.033)")
    a = ap.parse_args()

    project = json.loads(a.project.read_text(encoding="utf-8"))
    bad = checked = 0
    no_file: set[str] = set()
    silent = 0
    originals = {p.stem.upper(): p for p in a.clips.iterdir() if p.suffix.lower() in {e.lower() for e in EXT}}   # plans store clip names in upper case
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        fin_path = tmp / "final_audio.wav"
        subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", str(a.video), "-vn", "-ac", "1", "-ar", str(SR), str(fin_path)], capture_output=True)
        with wave.open(str(fin_path), "rb") as w:
            fin = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768
        cache: dict[str, np.ndarray] = {}
        for s in project["scenes"]:
            if not s.get("clip") or s.get("layout") in ("card", "expand"):
                continue
            path = originals.get(s["clip"].upper())
            if path is None:
                no_file.add(s["clip"])
                continue
            clip = cache.setdefault(s["clip"], audio(path, tmp))
            L = int(min(1.2, s["end"] - s["start"] - 0.1) * SR)
            i0 = int(s["in"] * SR)
            seg = clip[i0:i0 + L]
            if len(seg) < L or np.sqrt((seg ** 2).mean()) < 0.005:
                silent += 1
                continue  # the take is silent here, or has no audio (point --clips at the originals)
            seg = seg - seg.mean()
            c0 = int(s["start"] * SR)
            lo, hi = max(0, c0 - int(0.3 * SR)), c0 + L + int(0.3 * SR)
            ref = fin[lo:hi] - fin[lo:hi].mean()
            n = 1 << int(np.ceil(np.log2(len(ref) + L)))
            cc = np.fft.irfft(np.fft.rfft(ref, n) * np.conj(np.fft.rfft(seg, n)), n)[:len(ref) - L + 1]
            cs = np.concatenate([[0], np.cumsum(ref.astype(np.float64) ** 2)])
            en = np.sqrt(np.maximum(cs[L:L + len(cc)] - cs[:len(cc)], 1e-9)) * np.linalg.norm(seg)
            nc = np.abs(cc) / en
            k = int(np.argmax(nc))
            off = (lo + k - c0) / SR
            checked += 1
            flag = "" if abs(off) <= a.tolerance else "   <-- OUT OF SYNC"
            bad += bool(flag)
            if flag or nc[k] < 0.5:
                print(f"scene at {s['start']:6.2f}s {s['clip']}: offset {off * 1000:+5.0f} ms, correlation {nc[k]:.2f}{flag}")
    print(f"{checked} talking scene(s) checked, {bad} off by more than {a.tolerance * 1000:.0f} ms")
    if no_file:
        print(f"  no original found in {a.clips} for: {', '.join(sorted(no_file))}")
    if silent:
        print(f"  {silent} scene(s) skipped: the original is silent there, or has no audio (--clips must hold the ORIGINALS, not proxies)")
    if not checked:
        print("NOTHING WAS CHECKED: this is not a pass. Point --clips at the folder with the original takes.")
        return 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
