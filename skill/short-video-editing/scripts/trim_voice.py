#!/usr/bin/env python3
"""Shorten a supplied voiceover at real pauses.

A creator's recording is often longer than the 45 s ceiling. Cut it between sentences, never inside
a word: list the pauses first, then keep the stretches you want.

    python scripts/trim_voice.py voice.mp3 --silences                          # pauses and their midpoints
    python scripts/trim_voice.py voice.mp3 --keep 0-3.8,8.3-16.1 --out short.mp3

--silences  list pauses of at least --min seconds (default 0.25) quieter than --noise (default -35 dB).
            Use a midpoint as a cut point.
--keep      comma-separated start-end ranges in seconds of the ORIGINAL file; they are joined in order.
            Say which sentences were dropped when you report the result.

Needs ffmpeg and ffprobe on PATH. Re-run align_captions.py on the trimmed file: every timing moves.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


def duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def silences(path: Path, noise: str, min_len: float) -> list[tuple[float, float]]:
    log = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af",
                          f"silencedetect=noise={noise}:d={min_len}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    if len(ends) < len(starts):  # the file ends in silence
        ends.append(duration(path))
    return list(zip(starts, ends))


def parse_ranges(spec: str, total: float) -> list[tuple[float, float]]:
    ranges = []
    for chunk in spec.split(","):
        m = re.fullmatch(r"\s*([\d.]+)\s*-\s*([\d.]+)\s*", chunk)
        if not m:
            sys.exit(f"bad range '{chunk}': write start-end in seconds, e.g. 0-3.8")
        a, b = float(m.group(1)), float(m.group(2))
        if not 0 <= a < b <= total + 0.05:
            sys.exit(f"range {a}-{b} is outside the file (0-{total:.2f}s) or backwards")
        ranges.append((a, b))
    return ranges


def trim(path: Path, ranges: list[tuple[float, float]], out: Path) -> None:
    parts = [f"[0:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS[a{i}]" for i, (a, b) in enumerate(ranges)]
    joined = "".join(f"[a{i}]" for i in range(len(ranges)))
    graph = ";".join(parts + [f"{joined}concat=n={len(ranges)}:v=0:a=1[out]"])
    codec = ["-c:a", "libmp3lame", "-q:a", "2"] if out.suffix.lower() == ".mp3" else []
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(path), "-filter_complex", graph,
                    "-map", "[out]", *codec, str(out)], check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="List pauses in a voiceover, or keep only chosen ranges of it.")
    ap.add_argument("audio", type=Path)
    ap.add_argument("--silences", action="store_true", help="list pauses and exit")
    ap.add_argument("--noise", default="-35dB", help="silence threshold (default -35dB)")
    ap.add_argument("--min", type=float, default=0.25, help="shortest pause to report, seconds (default 0.25)")
    ap.add_argument("--keep", help="ranges to keep, e.g. 0-3.8,8.3-16.1")
    ap.add_argument("--out", type=Path, help="output file (required with --keep)")
    a = ap.parse_args()

    total = duration(a.audio)
    if a.silences:
        found = silences(a.audio, a.noise, a.min)
        print(f"{a.audio.name}: {total:.2f}s, {len(found)} pause(s) >= {a.min}s")
        for s, e in found:
            print(f"  {s:7.2f} - {e:7.2f}   ({e - s:.2f}s)   cut at {(s + e) / 2:.2f}")
        return 0
    if not (a.keep and a.out):
        ap.error("give --silences, or --keep together with --out")
    ranges = parse_ranges(a.keep, total)
    trim(a.audio, ranges, a.out)
    kept = sum(b - a_ for a_, b in ranges)
    print(f"wrote {a.out}: {duration(a.out):.2f}s (kept {kept:.2f}s of {total:.2f}s in {len(ranges)} range(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
