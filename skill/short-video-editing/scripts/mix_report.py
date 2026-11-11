#!/usr/bin/env python3
"""Check a FINISHED video's picture format and sound mix with numbers, so "it sounds fine" is never the only evidence.

    python scripts/mix_report.py final.mp4 --project project.json [--words words.json] [--nomusic final_nomusic.mp4]

Prints (and exits 1 on any error):
  picture   size, fps, pixel format and colour range, duration against the project's. Remotion writes FULL-range yuvj420p;
            phones and editors expect limited-range BT.709, so a full-range file is flagged (`finish_video.py` converts it).
  loudness  integrated LUFS, loudness range, true peak; flagged outside -15..-13 LUFS or above -1 dBTP (common practice: neither
            TikTok nor Instagram publishes a target). Then short-term loudness per 10 s, to catch a section that dips or pumps.
  mix       with --words: the level of the voice while speaking and in the pauses between words (a pause above about -45 dBFS in a file
            without music means noise is left in the voice). With --nomusic: the same on the no-music master, and the music bed's
            level = the difference in the pauses.
  cues      with --project: how many sound effects, how many in the busiest 3 s, music source and levels. NONE for music is printed on
            purpose: a project compiled from a stale file once rendered a whole video without its music and nobody noticed.
It measures; it does not listen. Say "not listened" in your report unless a person did. Needs numpy (the kit's venv) and ffmpeg.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _venv import ensure_venv  # noqa: E402

ensure_venv()
import numpy as np  # noqa: E402

SR = 16000


def probe(path: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "stream=codec_type,width,height,avg_frame_rate,pix_fmt,color_range,color_space:format=duration", "-of", "json", str(path)],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"ffprobe failed on {path}: {r.stderr.strip()[:300]}")
    j = json.loads(r.stdout)
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), None)
    au = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    n, d = (v["avg_frame_rate"].split("/") + ["1"])[:2] if v else ("0", "1")
    return {"video": v, "audio": au, "fps": float(n) / float(d or 1), "duration": float(j["format"]["duration"])}


def audio(path: Path) -> np.ndarray:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True)
    return np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768


def ebur(path: Path) -> tuple[dict | None, list[tuple[float, float]]]:
    """Summary (I, LRA, true peak) and the short-term series [(t, S)] from ffmpeg's ebur128 log."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    err = r.stderr
    series = [(float(m.group(1)), float(m.group(2))) for m in re.finditer(r"t:\s*([\d.]+)\s+TARGET:\S+\s+LUFS\s+M:\s*\S+\s+S:\s*(-?[\d.]+)", err)]
    if not series:
        series = [(float(m.group(1)), float(m.group(2))) for m in re.finditer(r"t:\s*([\d.]+)\s+M:\s*\S+\s+S:\s*(-?[\d.]+)", err)]
    tail = err.split("Summary:")[-1] if "Summary:" in err else ""

    def num(label: str) -> float | None:
        m = re.search(rf"{label}:\s+(-?[\d.]+)", tail)
        return float(m.group(1)) if m else None

    i = num("I")
    return ({"lufs": i, "lra": num("LRA"), "peak": num("Peak")} if i is not None else None), series


def rms_db(x: np.ndarray, a: float, b: float) -> float | None:
    seg = x[int(a * SR): int(b * SR)]
    return None if len(seg) < 160 else float(20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-9))


def levels(x: np.ndarray, words: list[dict]) -> tuple[list[float], list[float]]:
    speech = [v for w in words if (v := rms_db(x, w["start"], w["end"])) is not None]
    gaps = []
    for p, n in zip(words, words[1:]):
        if n["start"] - p["end"] > 0.3:   # a real pause: trim 50 ms each side so the word's tail and attack are not counted
            v = rms_db(x, p["end"] + 0.05, n["start"] - 0.05)
            if v is not None:
                gaps.append(v)
    return speech, gaps


def main() -> int:
    ap = argparse.ArgumentParser(description="Numbers for a finished video: picture format, loudness, voice and pause levels, cue count.")
    ap.add_argument("video", type=Path)
    ap.add_argument("--project", type=Path, help="the project.json it was rendered from")
    ap.add_argument("--words", type=Path, help="words.json of the voice (from align_captions.py --words-out)")
    ap.add_argument("--nomusic", type=Path, help="the no-music master, to measure the music bed")
    a = ap.parse_args()
    errors = warnings = 0

    def flag(level: str, msg: str) -> None:
        nonlocal errors, warnings
        print(f"  {'ERROR' if level == 'e' else 'warn '} {msg}")
        errors += level == "e"
        warnings += level == "w"

    info = probe(a.video)
    v = info["video"]
    proj = json.loads(a.project.read_text(encoding="utf-8")) if a.project else None
    print(f"{a.video.name}")
    if v:
        print(f"picture: {v['width']}x{v['height']}, {info['fps']:.2f} fps, {v.get('pix_fmt')}, range {v.get('color_range') or '?'}, {info['duration']:.2f} s")
        if (v["width"], v["height"]) != (1080, 1920):
            flag("w", f"size is {v['width']}x{v['height']}, not 1080x1920 (the vertical-video format)")
        if v.get("pix_fmt") == "yuvj420p" or v.get("color_range") == "pc":
            flag("e", "full-range video (yuvj420p): a phone shows it washed out or crushed. Run finish_video.py, which converts to limited-range BT.709")
    else:
        print(f"audio only, {info['duration']:.2f} s")
    if proj and abs(info["duration"] - float(proj.get("duration", info["duration"]))) > 0.15:
        flag("w", f"duration {info['duration']:.2f} s differs from the project's {proj['duration']} s: check the audio or the render range")

    if not info["audio"]:
        flag("e", "no audio stream")
    else:
        loud, series = ebur(a.video)
        if loud:
            print(f"loudness: {loud['lufs']} LUFS integrated, range {loud['lra']} LU, true peak {loud['peak']} dBFS")
            if v and not -15.0 <= loud["lufs"] <= -13.0:   # an audio-only stem is not a master
                flag("w", f"{loud['lufs']} LUFS is outside -15..-13 (common practice for TikTok and Reels is -14): run process_audio.py master / finish_video.py")
            if loud["peak"] is not None and loud["peak"] > -1.0:
                flag("e", f"true peak {loud['peak']} dBFS is above -1: it can clip after the platform's re-encode")
        if series:
            sec = {}
            for t, s in series:
                if s > -70:
                    sec.setdefault(int(t // 10), []).append(s)
            row = "  ".join(f"{k * 10}-{k * 10 + 10}s {np.mean(vs):.1f}" for k, vs in sorted(sec.items()))
            print(f"short-term LUFS by 10 s: {row}")
            means = [np.mean(vs) for vs in sec.values()]
            if means and max(means) - min(means) > 6:
                flag("w", f"sections differ by {max(means) - min(means):.1f} LU: a part is much louder or quieter than the rest")

        if a.words:
            words = json.loads(a.words.read_text(encoding="utf-8"))
            x = audio(a.video)
            speech, gaps = levels(x, words)
            if speech and gaps:
                print(f"mix: voice {np.median(speech):.1f} dBFS median while speaking; pauses {np.median(gaps):.1f} median, {max(gaps):.1f} loudest ({len(gaps)} pauses)")
                if np.median(gaps) > -45 and proj is not None and not proj.get("music"):
                    flag("w", f"pauses sit at {np.median(gaps):.1f} dBFS with no music in the project: noise is audible between sentences")
            if a.nomusic:
                y = audio(a.nomusic)
                _, gaps2 = levels(y, words)
                if gaps2 and gaps:
                    print(f"no-music master pauses: {np.median(gaps2):.1f} dBFS median -> the music bed is about {np.median(gaps) - np.median(gaps2):+.1f} dB there")
                    if np.median(gaps2) > -45:
                        flag("w", f"the no-music master has {np.median(gaps2):.1f} dBFS in the pauses: background noise is left in the voice (process_audio.py voice)")
                    if np.median(gaps) - np.median(gaps2) < 3:
                        flag("w", "the music master is barely louder than the no-music one in the pauses: is the music in this file?")
        elif a.nomusic:
            flag("w", "--nomusic needs --words to measure the pauses")

    if proj:
        cues = proj.get("sfx") or []
        music = proj.get("music")
        busiest = 0
        ts = sorted(c["at"] for c in cues)
        for i, t in enumerate(ts):
            busiest = max(busiest, sum(1 for u in ts[i:] if u < t + 3.0))
        names = sorted({Path(c["src"]).stem.rsplit("-", 1)[0] for c in cues})
        print(f"cues: {len(cues)} sound effects ({len(names)} families), at most {busiest} within 3 s; "
              f"music: {Path(music['src']).name if isinstance(music, dict) and music.get('src') else (music or 'NONE')}"
              + (f", levels {music.get('volumeDb')}/{music.get('duckDb')}" if isinstance(music, dict) else ""))
        late = [c for c in cues if c["at"] > proj.get("duration", 1e9)]
        if late:
            flag("e", f"{len(late)} sound effect(s) are placed after the end of the video")
        if not cues:
            flag("w", "the project has no sound effects")

    print(f"{errors} error(s), {warnings} warning(s). Measured, not listened to.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
