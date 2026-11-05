#!/usr/bin/env python3
"""Synthesize the kit's own sound effects with ffmpeg: nothing to download, nothing to license.

    python scripts/make_sfx.py public/sfx                # all six
    python scripts/make_sfx.py public/sfx --only pop,ding

pop      0.12 s  soft downward blip: a title or sticker appears
tick     0.06 s  light click: a list item, a callout, a step
ding     1.00 s  bell with three partials: a result, a price, a success
thud     0.40 s  low impact with a noise click: an emphasis beat, a flash
swoosh   0.55 s  noise sweep, low band then high band: a slide or wipe transition
riser    1.00 s  rising noise and tone that stops dead: the run-up to a reveal

Every file is mono 44.1 kHz 16-bit WAV with its peak at -3 dB, like the recorded CC0 files in
assets/sfx, so one level table (assets/sfx/sfx-map.json) works for all of them. The sounds are
code-made, so they belong to whoever runs this. Needs ffmpeg with the `amix normalize` option (4.4+).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PEAK_DB = -3.0

# name -> (inputs, filter_complex or None, extra -af). `{n}` is the seconds of the noise inputs.
NOISE = "anoisesrc=d={d}:c={c}:r=44100:a=0.9"
SOUNDS: dict[str, tuple[list[str], str | None]] = {
    "pop": (["aevalsrc=exprs='sin(2*PI*(900*t-2750*t*t))*exp(-45*t)*min(1,t/0.002)':d=0.12:s=44100"], None),
    "tick": (["aevalsrc=exprs='(sin(2*PI*2400*t)+0.4*sin(2*PI*3600*t))*exp(-90*t)*min(1,t/0.0005)':d=0.06:s=44100"], None),
    "ding": (["aevalsrc=exprs='(sin(2*PI*880*t)*exp(-4*t)+0.5*sin(2*PI*2217*t)*exp(-6*t)"
              "+0.25*sin(2*PI*3520*t)*exp(-9*t))*min(1,t/0.003)':d=1.0:s=44100"], None),
    "thud": (["aevalsrc=exprs='sin(2*PI*(120*t-100*t*t))*exp(-9*t)*min(1,t/0.003)"
              "+(random(0)*2-1)*exp(-80*t)*0.25':d=0.4:s=44100"], None),
    "swoosh": ([NOISE.format(d=0.55, c="pink"), NOISE.format(d=0.55, c="white")],
               "[0]lowpass=f=900,volume='exp(-pow((t-0.15)/0.12,2))':eval=frame[lo];"
               "[1]highpass=f=2500,lowpass=f=9000,volume='exp(-pow((t-0.32)/0.12,2))':eval=frame[hi];"
               "[lo][hi]amix=inputs=2:normalize=0,afade=t=in:d=0.02,afade=t=out:st=0.5:d=0.05"),
    "riser": ([NOISE.format(d=1.0, c="white"), "aevalsrc=exprs='sin(2*PI*(250*t+500*t*t))*pow(t,2)*0.5':d=1.0:s=44100"],
              "[0]highpass=f=1500,volume='pow(t/1.0,2.2)':eval=frame[n];"
              "[n][1]amix=inputs=2:normalize=0,afade=t=out:st=0.97:d=0.03"),
}


def ffmpeg(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-loglevel", "error", *args],
                          capture_output=True, text=True)


def peak_db(path: Path) -> float:
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.search(r"max_volume: (-?[\d.]+) dB", log)
    if not m:
        sys.exit(f"could not measure {path.name}")
    return float(m.group(1))


def make(name: str, out_dir: Path) -> None:
    inputs, graph = SOUNDS[name]
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "raw.wav"
        cmd: list[str] = ["-y"]
        for i in inputs:
            cmd += ["-f", "lavfi", "-i", i]
        cmd += ["-filter_complex", graph] if graph else []
        r = ffmpeg(*cmd, "-ac", "1", "-ar", "44100", str(raw))
        if r.returncode:
            sys.exit(f"ffmpeg failed for {name}:\n{r.stderr}")
        gain = PEAK_DB - peak_db(raw)
        dest = out_dir / f"{name}.wav"
        r = ffmpeg("-y", "-i", str(raw), "-af", f"volume={gain:.2f}dB", "-ac", "1", "-ar", "44100",
                   "-c:a", "pcm_s16le", str(dest))
        if r.returncode:
            sys.exit(f"ffmpeg failed for {name}:\n{r.stderr}")
    print(f"  {dest.name:12} peak {peak_db(dest):5.1f} dB")


def main() -> int:
    ap = argparse.ArgumentParser(description="Synthesize the kit's own sound effects with ffmpeg.")
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--only", help="comma-separated names (default: all)")
    a = ap.parse_args()
    names = a.only.split(",") if a.only else list(SOUNDS)
    unknown = [n for n in names if n not in SOUNDS]
    if unknown:
        sys.exit(f"unknown sound(s): {', '.join(unknown)} (have: {', '.join(SOUNDS)})")
    a.out_dir.mkdir(parents=True, exist_ok=True)
    print(f"writing {len(names)} sound(s) to {a.out_dir}")
    for n in names:
        make(n, a.out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
