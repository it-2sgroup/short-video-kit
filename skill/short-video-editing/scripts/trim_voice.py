#!/usr/bin/env python3
"""Shorten a voice at real pauses, or cut a talking-head take into jump cuts.

A creator's recording is often longer than its playbook allows. Cut it between sentences, never inside
a word: list the pauses first, then keep the stretches you want. A talking head (A-roll) is the same job
done everywhere at once: every pause longer than --max-pause comes out, and the kept stretches become
the scenes, each with its source time, so picture and sound stay in sync.

    python scripts/trim_voice.py voice.mp3 --silences                          # pauses and their midpoints
    python scripts/trim_voice.py voice.mp3 --keep 0-3.8,8.3-16.1 --out short.mp3
    python scripts/trim_voice.py talk.mp4 --jumpcut --out talk_cut.wav --scenes-out cuts.json \
        [--max-pause 0.35] [--pad 0.08] [--playbook talking-head]

--silences  list pauses of at least --min seconds (default 0.25) quieter than --noise (default -35 dB).
            Use a midpoint as a cut point.
--keep      comma-separated start-end ranges in seconds of the ORIGINAL file; they are joined in order.
            Say which sentences were dropped when you report the result.
--jumpcut   keep everything but the pauses longer than --max-pause (each kept stretch padded by --pad so
            breaths and consonants are not clipped). A stretch shorter than the playbook's scenes.min is
            joined to the next (that pause stays); a stretch longer than scenes.max is split at its
            quietest moment near the middle (a punch-in on the same take). Writes the joined sound
            (--out: the voice track for plan_to_project.py) and --scenes-out: [{start, end, clip, in}],
            which `playbook.py skeleton ID --cuts cuts.json` turns into a Scenes table with Source and In
            filled. Pauses are found, fillers ("ờ", "à", repeats) are not: read the transcript and drop
            them with --keep.

Needs ffmpeg and ffprobe on PATH. Re-run align_captions.py on the trimmed file: every timing moves.
"""
from __future__ import annotations

import argparse
import json
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


def quietest(path: Path, a: float, b: float) -> float:
    """Time of the quietest 100 ms window between a and b (a split point inside continuous speech)."""
    af = (f"atrim=start={a}:end={b},asetpts=PTS-STARTPTS,aresample=48000,asetnsamples=n=4800,"
          "astats=metadata=1:reset=1,ametadata=mode=print:key=lavfi.astats.Overall.RMS_level:file=-")
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-af", af, "-f", "null", "-"],
                         capture_output=True, text=True).stdout
    vals = [float(v) if v != "-inf" else -200.0 for v in re.findall(r"RMS_level=(-?[\d.]+|-inf)", out)]
    return a + (min(range(len(vals)), key=vals.__getitem__) + 0.5) * 0.1 if vals else (a + b) / 2


def jumpcut(path: Path, total: float, noise: str, max_pause: float, pad: float, lo: float, hi: float):
    """Kept source ranges, merged and split to the playbook's scene lengths."""
    keep, t = [], 0.0
    for s, e in silences(path, noise, max_pause):
        if s - t > 0.05:
            keep.append((max(0.0, t - pad if t else 0.0), min(total, s + pad)))
        t = e
    if total - t > 0.05:
        keep.append((max(0.0, t - pad), total))
    merged = []
    for r in keep:  # too short to stand as a scene: keep the pause before the next stretch instead
        if merged and (merged[-1][1] - merged[-1][0] < lo or r[0] - merged[-1][1] < 0.02):
            merged[-1] = (merged[-1][0], r[1])
        else:
            merged.append(r)
    if len(merged) > 1 and merged[-1][1] - merged[-1][0] < lo:  # a short last stretch joins the one before
        merged[-2:] = [(merged[-2][0], merged[-1][1])]
    out = []
    for a, b in merged:
        n = max(1, int((b - a) // hi) + (1 if (b - a) % hi > 1e-6 else 0))
        cuts = [a] + [round(quietest(path, a + (b - a) * k / n - 0.6, a + (b - a) * k / n + 0.6), 2) for k in range(1, n)] + [b]
        out += [(x, y) for x, y in zip(cuts, cuts[1:])]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="List pauses in a voice, keep chosen ranges of it, or jump-cut a talking head.")
    ap.add_argument("audio", type=Path)
    ap.add_argument("--silences", action="store_true", help="list pauses and exit")
    ap.add_argument("--noise", default="-35dB", help="silence threshold (default -35dB)")
    ap.add_argument("--min", type=float, default=0.25, help="shortest pause to report, seconds (default 0.25)")
    ap.add_argument("--keep", help="ranges to keep, e.g. 0-3.8,8.3-16.1")
    ap.add_argument("--out", type=Path, help="output file (required with --keep and --jumpcut)")
    ap.add_argument("--jumpcut", action="store_true", help="remove every pause longer than --max-pause (talking head)")
    ap.add_argument("--max-pause", type=float, default=0.35, help="pauses longer than this are cut out (default 0.35 s)")
    ap.add_argument("--pad", type=float, default=0.08, help="sound kept either side of a cut (default 0.08 s)")
    ap.add_argument("--playbook", default="talking-head", help="whose scene lengths to respect (default talking-head)")
    ap.add_argument("--scenes-out", type=Path, help="with --jumpcut: write the scenes (timeline start/end, source in)")
    a = ap.parse_args()

    total = duration(a.audio)
    if a.jumpcut:
        if not a.out:
            ap.error("--jumpcut needs --out")
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import playbook as playbooks
        sc = playbooks.load(a.playbook)["scenes"]
        ranges = jumpcut(a.audio, total, a.noise, a.max_pause, a.pad, sc["min"], sc["max"])
        trim(a.audio, ranges, a.out)
        scenes, t = [], 0.0
        for x, y in ranges:
            scenes.append({"start": round(t, 2), "end": round(t + y - x, 2), "clip": a.audio.stem.upper(), "in": round(x, 2), "text": ""})
            t += y - x
        scenes[-1]["end"] = round(duration(a.out), 2)
        if a.scenes_out:
            a.scenes_out.write_text(json.dumps(scenes, indent=1), encoding="utf-8")
        print(f"wrote {a.out}: {duration(a.out):.2f}s of {total:.2f}s, {len(scenes)} scene(s); removed {total - sum(y - x for x, y in ranges):.2f}s of pauses")
        for s_ in scenes:
            print(f"  {s_['start']:6.2f} - {s_['end']:6.2f}  source {s_['in']:6.2f}")
        return 0
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
