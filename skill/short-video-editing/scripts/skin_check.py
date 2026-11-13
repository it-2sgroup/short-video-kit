#!/usr/bin/env python3
"""Did a grade move skin tones? Measure a patch of skin before and after a look. ffmpeg only (signalstats).

    python scripts/skin_check.py clip.mp4 --patch 0.42,0.30,0.16,0.10 --grade warm-food [--time 2.0]
    python scripts/skin_check.py still.png --patch 0.4,0.3,0.2,0.2 --chain "eq=saturation=1.3,hue=h=10"
    python scripts/skin_check.py clip.mp4 --patch 0.42,0.30,0.16,0.10 --grade all      # every look in assets/grades.json

--patch is x,y,w,h as fractions of the frame (a cheek or the forehead: flat skin, no hair, no shadow edge). The patch is cropped,
the look is applied (a name from assets/grades.json, with its `strength`, or any ffmpeg chain), and ffmpeg `signalstats` reports
for each: HUEMED (median hue, degrees, the angle in the U-V plane: skin sits around 105-135 on BT.709 data, not the HSV hue) and
SATAVG (mean saturation, 8-bit chroma units). It prints both numbers and the shift, and warns when the hue moved by more than
--threshold degrees (default 8).

HEURISTIC: 8 degrees is a rule of thumb for "skin still looks like the same person's skin", not a standard. A look that shifts skin
by less can still look wrong on a very pale or very dark face; one that shifts it more can be a deliberate warm look. Look at a
frame before and after (contact_sheet.py). The grade is applied to the corrected picture in the kit (white balance and exposure come
first), so a shift measured here on a raw patch is an estimate. Exit code 0, or 1 with --strict when any look moved skin past the limit.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

GRADES = Path(__file__).resolve().parent.parent / "assets" / "grades.json"


def load_grades() -> dict:
    return json.loads(GRADES.read_text(encoding="utf-8"))["grades"] if GRADES.is_file() else {}


def graded(chain: str, strength: float) -> str:
    """The chain as the kit applies it: mixed with the corrected picture when strength < 1 (prepare_footage.py uses blend all_opacity)."""
    if not chain:
        return "null"
    if strength < 1:
        return f"split[a][b];[b]{chain}[g];[a][g]blend=all_mode=normal:all_opacity={strength:.3f}"
    return chain


def measure(src: Path, patch: tuple[float, float, float, float], t: float, frames: int, chain: str, strength: float) -> dict:
    x, y, w, h = patch
    crop = f"crop=floor(iw*{w}/2)*2:floor(ih*{h}/2)*2:floor(iw*{x}/2)*2:floor(ih*{y}/2)*2"
    vf = f"{crop},format=yuv444p," + (graded(chain, strength) + "," if chain else "") + "format=yuv444p,signalstats,metadata=mode=print:file=-"
    cmd = ["ffmpeg", "-hide_banner", "-v", "error", "-ss", f"{t:.3f}", "-i", str(src), "-frames:v", str(frames), "-vf", vf, "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"ffmpeg failed: {r.stderr.strip()[-400:]}")
    hue = [float(v) for v in re.findall(r"lavfi\.signalstats\.HUEMED=([\d.]+)", r.stdout)]
    sat = [float(v) for v in re.findall(r"lavfi\.signalstats\.SATAVG=([\d.]+)", r.stdout)]
    if not hue:
        sys.exit("signalstats gave no numbers: does this ffmpeg have the signalstats filter, and is the patch inside the frame?")
    return {"hue": round(statistics.median(hue), 1), "sat": round(statistics.median(sat), 1)}


def hue_shift(a: float, b: float) -> float:
    return round((b - a + 180) % 360 - 180, 1)


def main() -> int:
    ap = argparse.ArgumentParser(description="Hue and saturation of a skin patch before and after a grade (ffmpeg signalstats).")
    ap.add_argument("src", type=Path, help="a clip or a still")
    ap.add_argument("--patch", default="0.4,0.4,0.2,0.2", help="x,y,w,h as fractions of the frame (default: the centre)")
    ap.add_argument("--grade", help="a look from assets/grades.json, or `all`")
    ap.add_argument("--chain", help="any ffmpeg video filter chain, instead of --grade")
    ap.add_argument("--time", type=float, default=0.0, help="seconds into a clip (default 0)")
    ap.add_argument("--frames", type=int, default=3, help="frames measured from there; the median is reported (default 3)")
    ap.add_argument("--threshold", type=float, default=8.0, help="degrees of hue shift that earn a warning (default 8: a heuristic)")
    ap.add_argument("--strict", action="store_true", help="exit 1 when any look shifts the hue past the threshold")
    ap.add_argument("--json", type=Path, help="also write the numbers here")
    a = ap.parse_args()
    if not a.src.is_file():
        sys.exit(f"not found: {a.src}")
    try:
        patch = tuple(float(v) for v in a.patch.split(","))
        assert len(patch) == 4 and patch[0] >= 0 and patch[1] >= 0 and patch[2] > 0 and patch[3] > 0 and patch[0] + patch[2] <= 1.001 and patch[1] + patch[3] <= 1.001
    except (ValueError, AssertionError):
        sys.exit("--patch is x,y,w,h as fractions inside the frame, e.g. 0.42,0.30,0.16,0.10")
    grades = load_grades()
    if a.chain:
        todo = {"chain": {"chain": a.chain}}
    elif a.grade == "all":
        todo = {k: v for k, v in grades.items() if v.get("chain")}
    elif a.grade:
        if a.grade not in grades:
            sys.exit(f"unknown grade '{a.grade}' (known: {', '.join(grades)})")
        todo = {a.grade: grades[a.grade]}
    else:
        sys.exit("give --grade NAME (or all) or --chain 'ffmpeg filters'")
    before = measure(a.src, patch, a.time, a.frames, "", 1.0)
    print(f"patch {a.patch} at {a.time:g} s: before  hue {before['hue']:6.1f} deg  saturation {before['sat']:5.1f}")
    rows, warn = [], 0
    for name, g in todo.items():
        after = measure(a.src, patch, a.time, a.frames, g["chain"], float(g.get("strength", 1.0)))
        dh, ds = hue_shift(before["hue"], after["hue"]), round(after["sat"] - before["sat"], 1)
        grey = after["sat"] < 3.0                      # no colour left: signalstats prints a meaningless hue
        bad = grey or abs(dh) > a.threshold
        warn += bad
        rows.append({"look": name, "hue": after["hue"], "hue_shift": dh, "sat": after["sat"], "sat_shift": ds, "warn": bad})
        print(f"  {name:16} hue {after['hue']:6.1f} deg ({dh:+5.1f})  saturation {after['sat']:5.1f} ({ds:+5.1f})" + ("   WARN: skin turned grey (hue undefined)" if grey else f"   WARN: skin hue moved more than {a.threshold:g} deg" if bad else ""))
    if warn:
        print(f"{warn} look(s) moved the skin hue past {a.threshold:g} degrees or removed its colour. That limit is a heuristic: compare a frame before and after, "
              "lower the look's strength (--grade-strength) or choose a gentler look.")
    if a.json:
        a.json.write_text(json.dumps({"patch": patch, "before": before, "looks": rows, "threshold": a.threshold}, indent=1), encoding="utf-8")
    return 1 if (warn and a.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
