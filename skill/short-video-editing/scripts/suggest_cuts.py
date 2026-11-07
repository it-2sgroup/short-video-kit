#!/usr/bin/env python3
"""Suggest scene cut points: on pauses of the voice, or on the beats of the music.

    python scripts/suggest_cuts.py words.json --playbook product-demo          # cut on pauses (voice-driven)
    python scripts/suggest_cuts.py --music track.mp3 --end 40 --playbook real-estate   # cut on beats
    python scripts/suggest_cuts.py words.json --music track.mp3 --json > cuts.json     # pauses, nudged onto beats

Voice: words.json comes from `align_captions.py --words-out`. A candidate sits between two words: a pause
(>= 0.25 s) is best, a shorter pause or a punctuation mark is acceptable, a plain word boundary is a last
resort. With --music as well, a cut within 4 frames of a beat moves onto it when that keeps it out of a word.

Music: the track's beats are found (spectral-flux onsets; tempo by weighted autocorrelation over 70-180
bpm, a half or double tempo inside the playbook's `music.bpm` range preferred; dynamic-programming beat
tracking; bar starts = the beat phase with the strongest low end). Needs numpy: the script re-launches
itself in the kit's venv. Bar starts are the best cut points, other beats are fine, nothing between
beats is used. --beats-out keeps the grid with a confidence (how much stronger the onsets on the beats
are than average; under 0.3 the beat is weak: check the cuts).

Either way the cuts are chosen together (dynamic programming) so every scene is near the target length:
the first hook beats are short, the rest aim for the target and stay within [min, max]. Lengths default
to the playbook's `hook` and `scenes` (the plan's genre); the flags override them. The last scene ends at
--end (default: the last word plus 0.8 s).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import playbook as playbooks  # noqa: E402

_VENV = Path.home() / ".local" / "share" / "short-video-kit" / "venv"
KIT_PYTHON = _VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def ensure_numpy() -> None:
    """--music needs numpy; re-run under the kit's venv (or $SVK_PYTHON) when this Python lacks it."""
    try:
        import numpy  # noqa: F401
        return
    except ImportError:
        pass
    if not os.environ.get("SVK_REEXEC"):
        for candidate in (os.environ.get("SVK_PYTHON"), str(KIT_PYTHON)):
            if candidate and Path(candidate).exists():
                os.environ["SVK_REEXEC"] = "1"
                os.execv(candidate, [candidate] + sys.argv)
    sys.exit("--music needs numpy: run the kit's setup.sh (it builds the venv), or pip install numpy")


SR, NFFT, STEP = 22050, 2048, 220  # ~10 ms frames


def onset_strength(path: Path):
    """Spectral flux (log-magnitude rises summed over frequency) of the whole spectrum, and of the bins
    below 150 Hz (kick drums, for bar starts). Needs numpy (the kit's venv has it)."""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32)
    if len(x) < NFFT * 4:
        sys.exit(f"{path}: too short to find a beat")
    frames = np.lib.stride_tricks.sliding_window_view(x, NFFT)[::STEP] * np.hanning(NFFT)
    mag = np.log1p(10 * np.abs(np.fft.rfft(frames, axis=1)))
    rise = np.maximum(0.0, np.diff(mag, axis=0))
    kick = int(150 * NFFT / SR)
    flux, low = rise.sum(1), rise[:, 1:kick + 1].sum(1)
    flux = flux - np.convolve(flux, np.ones(31) / 31, "same")  # remove the slow loudness trend
    return np.maximum(flux, 0) / (flux.std() or 1), low


def beat_grid(path: Path, prefer: tuple[float, float]) -> dict:
    """The track's beats: spectral-flux onsets; tempo from their autocorrelation over 70-180 bpm,
    weighted toward 120 bpm (one octave wide, as in librosa) so an eighth-note or triplet relation does
    not win; a double or half tempo inside the playbook's `prefer` range replaces a pulse outside it
    when nearly as strong (64 and 128 bpm are the same pulse); then dynamic-programming beat tracking
    (Ellis 2007), which follows small tempo drifts instead of laying a rigid grid. Bars start on the
    beat phase with the strongest low end. Checked on three CC0 tracks against their inter-onset
    intervals (references/audio-and-music.md)."""
    import numpy as np
    fps = SR / STEP
    flux, low = onset_strength(path)
    head = flux[: int(90 * fps)] - flux[: int(90 * fps)].mean()
    ac = np.correlate(head, head, "full")[len(head) - 1:] / np.arange(len(head), 0, -1)
    lags = np.arange(int(fps * 60 / 180), int(fps * 60 / 70) + 1)
    weight = np.exp(-0.5 * np.log2(60 * fps / lags / 120) ** 2)
    # A real pulse is usually subdivided into eighths: count half-period evidence too. Without it a
    # 110 bpm track scored as 73 bpm (a 2:3 relation), measured on a CC0 track.
    half = (ac[lags // 2] + ac[(lags + 1) // 2]) / 2
    best = lags[np.argmax((ac[lags] + 0.5 * np.maximum(half, 0)) * weight)]
    bpm = 60 * fps / best
    if not prefer[0] <= bpm <= prefer[1]:
        for alt in (best // 2, best * 2):
            if lags[0] <= alt <= lags[-1] and prefer[0] <= 60 * fps / alt <= prefer[1] and ac[alt] >= 0.6 * ac[best]:
                best = alt
                break
    period = float(best)
    # Dynamic programming: score[t] = onset[t] + best previous beat at a distance near one period.
    n, alpha = len(flux), 100.0
    score, back = flux.astype(float).copy(), np.full(n, -1)
    lo_d, hi_d = int(period / 2), int(period * 2)
    span = np.arange(lo_d, hi_d + 1)
    penalty = -alpha * np.log(span / period) ** 2
    for t in range(lo_d, n):
        prev = t - span
        ok = prev >= 0
        cand = score[prev[ok]] + penalty[ok]
        i = int(np.argmax(cand))
        score[t] += cand[i]
        back[t] = prev[ok][i]
    t = int(np.argmax(score[-int(period * 2):])) + n - int(period * 2)
    path_ = []
    while t >= 0:
        path_.append(t)
        t = back[t]
    frames = sorted(path_)
    beats = [round(f / fps + NFFT / SR / 2, 3) for f in frames if f / fps > 0.05]
    bar = max(range(4), key=lambda q: float(sum(low[min(len(low) - 1, int((b - NFFT / SR / 2) * fps))] for b in beats[q::4])))
    on = float(np.mean([flux[min(n - 1, int((b - NFFT / SR / 2) * fps))] for b in beats])) if beats else 0.0
    return {"bpm": round(60 * fps / period, 1), "beats": beats, "downbeats": beats[bar::4],
            "confidence": round(on / (float(flux.mean()) or 1) - 1, 2)}


def beat_candidates(grid: dict, end: float) -> list[tuple[float, float]]:
    down = set(grid["downbeats"])
    return [(b, 0.0 if b in down else 1.0) for b in grid["beats"] if 0 < b < end]


def snap_to_beats(cuts: list[float], grid: dict, words: list[dict], tol: float = 4 / 30) -> list[float]:
    out = []
    for c in cuts:
        b = min(grid["beats"], key=lambda x: abs(x - c))
        inside = any(w["start"] + 0.03 < b < w["end"] - 0.03 for w in words)
        out.append(b if abs(b - c) <= tol and not inside else c)
    return out


def candidates(words: list[dict], prefer: list[float]) -> list[tuple[float, float]]:
    """(time, cost) for every gap between two words; lower cost is a better place to cut. A gap within
    0.25 s of a `prefer` time (say the end of a sentence that starts a new shot) gets a bonus."""
    out = []
    for a, b in zip(words, words[1:]):
        gap = b["start"] - a["end"]
        t = (a["end"] + b["start"]) / 2 if gap > 0 else a["end"]
        end_mark = a["text"].rstrip()[-1:] in ",.!?…:;"
        cost = 0.0 if gap >= 0.25 else 0.8 if gap >= 0.12 else 1.5 if end_mark else 6.0
        if any(abs(t - p) < 0.25 for p in prefer):
            cost -= 3.0
        out.append((round(t, 3), cost))
    return out


def solve(cands, target, lo, hi, hook_beats, hook_len, hook_lo, hook_hi, end):
    cands = [(0.0, 0.0)] + [c for c in cands if min(0.9, hook_lo) < c[0] < end - min(1.0, lo)]
    n = len(cands)
    INF = float("inf")
    max_k = max(24, int(end / max(0.3, lo)) + 2)
    # best[i][k]: cheapest way to reach candidate i having made k scenes
    best = [[(INF, -1)] * (max_k + 1) for _ in range(n)]
    best[0][0] = (0.0, -1)
    for i in range(1, n):
        for j in range(i):
            length = cands[i][0] - cands[j][0]
            for k in range(max_k):
                prev = best[j][k][0]
                if prev == INF:
                    continue
                is_hook = k < hook_beats
                a, b, want = (hook_lo, hook_hi, hook_len) if is_hook else (lo, hi, target)
                if not a <= length <= b:
                    continue
                cost = prev + cands[i][1] + ((length - want) / want) ** 2 * 3
                if cost < best[i][k + 1][0]:
                    best[i][k + 1] = (cost, j)
    result = None
    for i in range(1, n):
        tail = end - cands[i][0]
        if not lo - 0.2 <= tail <= hi:  # the last scene obeys the same ceiling as the others
            continue
        for k in range(1, max_k + 1):
            c = best[i][k][0]
            if c == INF:
                continue
            total = c + ((tail - target) / target) ** 2 * 3
            if result is None or total < result[0]:
                result = (total, i, k)
    if result is None:
        sys.exit("no cut plan fits these constraints: loosen --min/--max or give a longer --end")
    _, i, k = result
    cuts = []
    while i > 0:
        cuts.append(cands[i][0])
        i = best[i][k][1]
        k -= 1
    return sorted(cuts)


def main() -> int:
    ap = argparse.ArgumentParser(description="Suggest scene cuts on pauses of the voice or beats of the music.")
    ap.add_argument("words", type=Path, nargs="?", help="words.json from align_captions.py --words-out")
    ap.add_argument("--music", type=Path, help="music track: cut on its beats (or snap voice cuts onto them)")
    ap.add_argument("--playbook", help="playbook id[:variant] for the default lengths (default product-demo)")
    ap.add_argument("--target", type=float, help="aimed scene length in seconds")
    ap.add_argument("--min", type=float, dest="lo", help="shortest normal scene")
    ap.add_argument("--max", type=float, dest="hi", help="longest scene")
    ap.add_argument("--hook-beats", type=int, help="how many opening scenes are short hook beats")
    ap.add_argument("--hook-len", type=float, help="aimed hook beat length")
    ap.add_argument("--hook-min", type=float, help="shortest hook beat")
    ap.add_argument("--hook-max", type=float, help="longest hook beat")
    ap.add_argument("--end", type=float, help="video length; default last word end + 0.8 (required with --music alone)")
    ap.add_argument("--prefer", default="", help="comma-separated times (s) where a cut is wanted, e.g. the ends of the sentences that change the shot")
    ap.add_argument("--beats-out", type=Path, help="write the beat grid (bpm, beats, downbeats) as JSON")
    ap.add_argument("--json", action="store_true", help="print the scenes as JSON")
    a = ap.parse_args()
    if not a.words and not a.music:
        sys.exit("give words.json (cut on pauses) and/or --music track (cut on beats)")

    pb = playbooks.load(a.playbook)
    hk, sc = pb["hook"], pb["scenes"]
    target = a.target or sc["target"]
    lo, hi = a.lo or sc["min"], a.hi or sc["max"]
    hook_beats = hk["beats"] if a.hook_beats is None else a.hook_beats
    hook_len = a.hook_len or hk["beat"]
    hook_lo = a.hook_min or max(hk["minBeat"], round(hook_len * 0.85, 2))
    hook_hi = a.hook_max or max(hook_len * 1.4, hook_len + 0.4)

    words = json.loads(a.words.read_text(encoding="utf-8-sig")) if a.words else []
    end = a.end or (round(words[-1]["end"] + 0.8, 2) if words else None)
    if end is None:
        sys.exit("--music without words needs --end (the video length in seconds)")
    if a.music:
        ensure_numpy()
    grid = beat_grid(a.music, tuple(pb["music"]["bpm"])) if a.music else None
    if grid and grid["confidence"] < 0.3:
        print(f"warning: weak beat ({grid['confidence']}): the cuts may not sit on the music; check them against the track",
              file=sys.stderr)
    if grid and not pb["music"]["bpm"][0] <= grid["bpm"] <= pb["music"]["bpm"][1]:
        print(f"note: the track runs at {grid['bpm']} bpm, outside {pb['name']}'s {pb['music']['bpm']} range for its mood",
              file=sys.stderr)
    if grid and a.beats_out:
        a.beats_out.write_text(json.dumps(grid, indent=1), encoding="utf-8")
    prefer = [float(x) for x in a.prefer.split(",") if x.strip()]
    cands = candidates(words, prefer) if words else beat_candidates(grid, end)
    cuts = solve(cands, target, lo, hi, hook_beats, hook_len, hook_lo, hook_hi, end)
    if words and grid:
        cuts = snap_to_beats(cuts, grid, words)
    bounds = [0.0] + cuts + [end]
    scenes = []
    for s, e in zip(bounds, bounds[1:]):
        text = " ".join(w["text"] for w in words if s - 0.001 <= (w["start"] + w["end"]) / 2 < e)
        scenes.append({"start": round(s, 2), "end": round(e, 2), "text": text})
    if a.json:
        print(json.dumps(scenes, ensure_ascii=False, indent=1))
        return 0
    head = f"{len(scenes)} scenes, {end:.2f}s, playbook {pb['name']}"
    print(head + (f", music {grid['bpm']} bpm" if grid else ""))
    for i, s in enumerate(scenes, 1):
        print(f"{i:2}  {s['start']:6.2f} - {s['end']:6.2f}  ({s['end'] - s['start']:.2f}s)  {s['text']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
