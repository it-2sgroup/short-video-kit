#!/usr/bin/env python3
"""Synthesize a licence-free music bed that follows the edit (numpy + ffmpeg, nothing downloaded).

Music from a library needs a licence that fits the platform and the account (a business TikTok account may only
use the Commercial Music Library, which a render cannot reach: references/audio-and-music.md). A bed you made
yourself has no licence question, and it can follow the edit: its sections start exactly on the video's section
cuts, with an impact and a riser into the big ones. It is a plain, bright pop-corporate groove (Am-F-C-G), meant
to sit under a voice. Levelling to -14 LUFS stays with `process_audio.py music`.

    python scripts/make_music.py --duration 40 --out music.wav \
        --sections "0:0.5,8:1.0,20:0.8,30:0.9,38:0.0" \
        --hits "8,30,38" --bpm 120

--sections  TIME:INTENSITY pairs. The beat grid restarts at every section start, so cuts land on a beat.
            Intensity 0..1 picks the layers: > 0.1 pad, > 0.3 bass, > 0.45 kick and hats, > 0.6 chord stabs,
            > 0.7 claps, open hats and arpeggio, > 0.95 sixteenth hats. 0 = silence after the last hit's tail.
--hits      seconds where an impact (low boom + crash) lands; a riser fills the second before it.
Writes a stereo 44.1 kHz WAV peaking at -3 dBFS. Not listened to: play it before shipping.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _venv import ensure_venv  # noqa: E402

ensure_venv()
import numpy as np  # noqa: E402

SR = 44100
PROG = [  # Am F C G: (bass midi, chord midi)
    (45, [57, 60, 64]),
    (41, [53, 57, 60]),
    (48, [60, 64, 67]),
    (43, [55, 59, 62]),
]


def hz(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12)


def add(buf: np.ndarray, at: float, x: np.ndarray, gain: float = 1.0) -> None:
    i = int(at * SR)
    if i >= len(buf) or i + len(x) <= 0:
        return
    a, b = max(0, -i), min(len(x), len(buf) - i)
    buf[i + a:i + b] += gain * x[a:b]


def tt(n: int) -> np.ndarray:
    return np.arange(n) / SR


def saw(f: float, n: int, detune: float = 0.0) -> np.ndarray:
    t = tt(n)
    return 2 * ((f * (1 + detune) * t) % 1.0) - 1


def kick() -> np.ndarray:
    n = int(0.42 * SR)
    t = tt(n)
    f = 46 + 120 * np.exp(-t * 38)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 9) + 0.25 * np.exp(-t * 400) * np.sign(np.sin(2 * np.pi * 1800 * t))


def noise(n: int, rng: np.random.Generator) -> np.ndarray:
    return rng.standard_normal(n)


def clap(rng: np.random.Generator) -> np.ndarray:
    n = int(0.3 * SR)
    t = tt(n)
    env = sum(np.exp(-(np.maximum(t - d, 0)) * 55) * (t >= d) for d in (0.0, 0.011, 0.022)) * 0.6 + np.exp(-t * 14) * 0.5
    return noise(n, rng) * env


def hat(open_: bool, rng: np.random.Generator) -> np.ndarray:
    n = int((0.2 if open_ else 0.06) * SR)
    return noise(n, rng) * np.exp(-tt(n) * (22 if open_ else 90))


def boom() -> np.ndarray:
    n = int(1.4 * SR)
    t = tt(n)
    ph = 2 * np.pi * np.cumsum(70 * np.exp(-t * 1.2) + 28) / SR
    return np.sin(ph) * np.exp(-t * 2.4)


def crash(rng: np.random.Generator) -> np.ndarray:
    n = int(1.8 * SR)
    return noise(n, rng) * np.exp(-tt(n) * 2.2)


def riser(dur: float, rng: np.random.Generator) -> np.ndarray:
    n = int(dur * SR)
    t = tt(n)
    k = t / dur
    sweep = np.sin(2 * np.pi * np.cumsum(180 + 2600 * k ** 2) / SR)
    return (noise(n, rng) * 0.5 + sweep * 0.5) * k ** 2.2


def pluck(f: float, dur: float) -> np.ndarray:
    n = int(dur * SR)
    return (saw(f, n) + saw(f, n, 0.006)) * np.exp(-tt(n) * 9)


def ffmpeg_filter(x: np.ndarray, chain: str, tmp: Path, name: str) -> np.ndarray:
    """Run a mono float array through an ffmpeg audio filter chain and read it back."""
    src, dst = tmp / f"{name}_in.wav", tmp / f"{name}_out.wav"
    write_wav(src, np.stack([x, x], 1))
    r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", str(src), "-af", chain, str(dst)], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"ffmpeg filter '{chain}' failed:\n{r.stderr}")
    y = read_wav(dst)[:, 0]  # echo filters add a tail: keep the length of the input
    return y[:len(x)] if len(y) >= len(x) else np.concatenate([y, np.zeros(len(x) - len(y))])


def write_wav(path: Path, x: np.ndarray) -> None:
    pcm = np.clip(x, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(x.shape[1])
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((pcm * 32767).astype("<i2").tobytes())


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        d = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64) / 32768
        return d.reshape(-1, w.getnchannels())


def main() -> int:
    ap = argparse.ArgumentParser(description="Synthesize a licence-free music bed that follows the edit.")
    ap.add_argument("--duration", type=float, required=True, help="seconds")
    ap.add_argument("--sections", required=True, help="TIME:INTENSITY,TIME:INTENSITY,... (the first TIME is 0)")
    ap.add_argument("--hits", default="", help="seconds where an impact lands (riser before it)")
    ap.add_argument("--bpm", type=float, default=120.0)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()

    rng = np.random.default_rng(a.seed)
    secs = sorted((float(t), float(i)) for t, i in (p.split(":") for p in a.sections.split(",")))
    hits = [float(h) for h in a.hits.split(",") if h.strip()]
    n = int(a.duration * SR)
    L = {k: np.zeros(n) for k in ("kick", "clap", "hat", "bass", "chord", "pad", "arp", "fx")}
    beat = 60.0 / a.bpm
    step = beat / 4
    duck_at: list[float] = []

    kk, cl, h1, h2 = kick(), clap(rng), hat(False, rng), hat(True, rng)
    for si, (t0, inten) in enumerate(secs):
        t1 = secs[si + 1][0] if si + 1 < len(secs) else a.duration
        if inten <= 0:
            continue
        bar_len = 16 * step
        bars = int(np.ceil((t1 - t0) / bar_len))
        for b in range(bars):
            bass_m, chord = PROG[(b + si) % len(PROG)]
            base = t0 + b * bar_len
            if base >= t1 - 0.02:
                break
            room = t1 - base  # keep every note inside the section (the next section restarts the grid)
            if inten > 0.1:
                dur = min(bar_len, room)
                nn = int(dur * SR)
                env = np.minimum(1, tt(nn) / 0.25) * np.minimum(1, (dur - tt(nn)) / 0.15)
                pad = sum(saw(hz(m), nn, d) for m in chord for d in (0.0, 0.007, -0.006)) * env
                add(L["pad"], base, pad, 0.05)
            for s in range(16):
                at = base + s * step
                if at >= t1 - 0.03:
                    break
                if inten > 0.45 and s % 4 == 0 or (0.3 < inten <= 0.45 and s in (0, 8)):
                    add(L["kick"], at, kk, 1.0)
                    duck_at.append(at)
                if inten > 0.7 and s in (4, 12):
                    add(L["clap"], at, cl, 0.5)
                if inten > 0.45 and s % 4 == 2:
                    add(L["hat"], at, h1, 0.32)
                if inten > 0.7 and s == 14:
                    add(L["hat"], at, h2, 0.3)
                if inten > 0.95 and s % 2 == 1:
                    add(L["hat"], at, h1, 0.16)
                if inten > 0.3 and s in (0, 3, 6, 10, 14):
                    nn = int(min(0.36, t1 - at) * SR)
                    if nn > 0:
                        env = np.exp(-tt(nn) * 7) * np.minimum(1, (tt(nn) + 1e-9) / 0.004)
                        add(L["bass"], at, (saw(hz(bass_m), nn) * 0.7 + np.sin(2 * np.pi * hz(bass_m) * tt(nn)) * 0.6) * env, 0.5)
                if inten > 0.6 and s in (0, 3, 6, 10):
                    for m in chord:
                        add(L["chord"], at, pluck(hz(m + 12), min(0.32, t1 - at)), 0.075)
                if inten > 0.7:
                    m = chord[(s // 2) % 3] + 12 + (12 if (s // 2) % 4 == 3 else 0)
                    add(L["arp"], at, pluck(hz(m), min(0.2, t1 - at)) * 0.5, 0.06)
        if si and secs[si - 1][1] < inten and t0 not in hits:
            add(L["fx"], t0, boom(), 0.35)  # a section that steps up gets a soft low hit on its first beat

    for h in hits:
        add(L["fx"], h, boom(), 0.9)
        add(L["fx"], h, crash(rng), 0.30)
        add(L["fx"], max(0.0, h - 1.0), riser(min(1.0, h), rng), 0.40)
        duck_at.append(h)

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        L["hat"] = ffmpeg_filter(L["hat"], "highpass=f=7000", tmp, "hat")
        L["clap"] = ffmpeg_filter(L["clap"], "highpass=f=700,lowpass=f=6500", tmp, "clap")
        L["bass"] = ffmpeg_filter(L["bass"], "lowpass=f=520", tmp, "bass")
        L["pad"] = ffmpeg_filter(L["pad"], "lowpass=f=1500,aecho=0.8:0.6:70|140:0.3|0.18", tmp, "pad")
        L["chord"] = ffmpeg_filter(L["chord"], "highpass=f=250,lowpass=f=3800,aecho=0.8:0.6:90|180:0.3|0.18", tmp, "chord")
        L["arp"] = ffmpeg_filter(L["arp"], "highpass=f=500,lowpass=f=5000,aecho=0.8:0.6:110|220:0.28|0.16", tmp, "arp")
        L["fx"] = ffmpeg_filter(L["fx"], "lowpass=f=9000", tmp, "fx")

    # sidechain: bass, pad, chords and arp dip on every kick and impact
    duck = np.ones(n)
    for at in duck_at:
        i = int(at * SR)
        m = int(0.22 * SR)
        if i < n:
            seg = 1 - 0.62 * np.exp(-tt(min(m, n - i)) * 16)
            duck[i:i + len(seg)] = np.minimum(duck[i:i + len(seg)], seg)
    mono = (L["kick"] * 0.95 + L["clap"] * 0.9 + L["hat"] * 0.7 + L["fx"] + (L["bass"] + L["pad"] + L["chord"] + L["arp"]) * duck)
    # a little stereo width: the chord and arp layers delayed by 11 ms on one side
    d = int(0.011 * SR)
    wide = (L["chord"] + L["arp"] + L["pad"]) * duck
    left = mono + 0.18 * wide
    right = mono + 0.18 * np.concatenate([np.zeros(d), wide[:-d]])
    out = np.stack([left, right], 1)
    out *= 0.707 / max(1e-9, np.abs(out).max())  # peak -3 dBFS
    # soft fade over the very end so a section that was cut at the edge never clicks
    f = int(0.4 * SR)
    out[-f:] *= np.linspace(1, 0, f)[:, None]
    a.out.parent.mkdir(parents=True, exist_ok=True)
    write_wav(a.out, out)
    print(f"wrote {a.out}: {a.duration:g} s, {len(secs)} section(s), {len(hits)} impact(s), peak -3 dBFS (not listened to)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
