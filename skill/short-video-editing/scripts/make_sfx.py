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
sparkle  0.70 s  "tinh tinh": two bright bell notes a fifth apart, 90 ms apart: an icon or a label pops on
chime3   0.90 s  three rising bell notes (a short arpeggio): a result, a plan, a good ending
twinkle  0.45 s  one high glassy "ting" with a shimmering tail: a small accent on a word
shutter  0.12 s  a camera-flash click and a short airy tail: the white silhouette flash
glitch   0.30 s  a digital error burst: bit-crushed noise stutter: a glitch text effect
bubble   0.18 s  a rising water-drop blip: a soft pop on a pill or a tag
boing    0.45 s  a springy wobble down then up: an elastic text effect
typing   0.60 s  six quick key clicks: a typed label
whoosh_s 0.28 s  short bright swish: a quick card slide
whoosh_l 1.00 s  long swell and tail: a hero entrance or a big transition
slam     0.60 s  a deep hit with a bright slap and a short tail: a slam or stamp text effect

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
    "sparkle": (["aevalsrc=exprs='sin(2*PI*1760*t)*exp(-11*t)*min(1,t/0.002)+0.45*sin(2*PI*3520*t)*exp(-16*t)+0.2*sin(2*PI*5300*t)*exp(-22*t)':d=0.7:s=44100",
                 "aevalsrc=exprs='if(gte(t,0.09),(sin(2*PI*2637*(t-0.09))*exp(-9*(t-0.09))+0.45*sin(2*PI*5274*(t-0.09))*exp(-14*(t-0.09))+0.2*sin(2*PI*7900*(t-0.09))*exp(-20*(t-0.09)))*min(1,(t-0.09)/0.002),0)':d=0.7:s=44100"],
                "[0][1]amix=inputs=2:normalize=0,aecho=0.7:0.5:55:0.25"),
    "chime3": (["aevalsrc=exprs='if(lt(t,0.12),0,sin(2*PI*1319*(t))*exp(-9*t))+if(lt(t,0.12),0,0.3*sin(2*PI*2638*t)*exp(-13*t))':d=0.9:s=44100",
                "aevalsrc=exprs='if(lt(t,0.2),0,sin(2*PI*1760*(t-0.2))*exp(-9*(t-0.2))+0.3*sin(2*PI*3520*(t-0.2))*exp(-13*(t-0.2)))':d=0.9:s=44100",
                "aevalsrc=exprs='if(lt(t,0.3),0,sin(2*PI*2349*(t-0.3))*exp(-8*(t-0.3))+0.3*sin(2*PI*4698*(t-0.3))*exp(-12*(t-0.3)))':d=0.9:s=44100"],
               "[0][1][2]amix=inputs=3:normalize=0,aecho=0.7:0.5:60:0.3"),
    "twinkle": (["aevalsrc=exprs='(sin(2*PI*3136*t)*exp(-14*t)+0.5*sin(2*PI*6272*t)*exp(-20*t)+0.25*sin(2*PI*9400*t)*exp(-28*t))*(1+0.25*sin(2*PI*28*t))*min(1,t/0.0015)':d=0.45:s=44100"],
                "aecho=0.7:0.5:45:0.3"),
    "shutter": (["aevalsrc=exprs='(random(0)*2-1)*exp(-120*t)*0.9+(random(1)*2-1)*if(gte(t,0.035),exp(-40*(t-0.035)),0)*0.35':d=0.12:s=44100"],
                "highpass=f=1200,lowpass=f=9000"),
    "glitch": (["aevalsrc=exprs='(random(0)*2-1)*if(lt(mod(t*40,1),0.55),1,0)*exp(-6*t)':d=0.3:s=44100"],
               "acrusher=bits=4:mix=0.9:mode=lin,highpass=f=500,lowpass=f=9000"),
    "bubble": (["aevalsrc=exprs='sin(2*PI*(500*t+4200*t*t))*exp(-22*t)*min(1,t/0.003)':d=0.18:s=44100"], "aecho=0.7:0.5:25:0.2"),
    "boing": (["aevalsrc=exprs='sin(2*PI*(260+90*sin(2*PI*11*t))*t)*exp(-6*t)*min(1,t/0.004)':d=0.45:s=44100"], None),
    "typing": (["aevalsrc=exprs='(sin(2*PI*1900*t)+0.5*sin(2*PI*3300*t))*(exp(-160*mod(t,0.1))*min(1,mod(t,0.1)/0.0005))*if(lt(t,0.6),1,0)':d=0.6:s=44100"], None),
    "whoosh_s": ([NOISE.format(d=0.28, c="white")], "highpass=f=1800,lowpass=f=10000,volume='exp(-pow((t-0.11)/0.07,2))':eval=frame,afade=t=in:d=0.01,afade=t=out:st=0.24:d=0.04"),
    "whoosh_l": ([NOISE.format(d=1.0, c="pink"), NOISE.format(d=1.0, c="white")],
                 "[0]lowpass=f=700,volume='exp(-pow((t-0.35)/0.2,2))':eval=frame[lo];[1]highpass=f=2200,lowpass=f=9500,volume='exp(-pow((t-0.55)/0.18,2))':eval=frame[hi];[lo][hi]amix=inputs=2:normalize=0,afade=t=in:d=0.04,afade=t=out:st=0.9:d=0.1"),
    "slam": (["aevalsrc=exprs='sin(2*PI*(95*t-110*t*t))*exp(-6*t)*min(1,t/0.002)+(random(0)*2-1)*exp(-60*t)*0.4+0.2*sin(2*PI*1800*t)*exp(-50*t)':d=0.6:s=44100"], "aecho=0.7:0.5:70:0.2"),
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
