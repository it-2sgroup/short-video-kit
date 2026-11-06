#!/usr/bin/env python3
"""Suggest scene cut points from word timings: on pauses, never inside a word, 3-4 s per scene.

    python scripts/suggest_cuts.py words.json                       # table of scenes and the words in each
    python scripts/suggest_cuts.py words.json --json > cuts.json    # [{"start":..,"end":..,"text":..}]
    python scripts/suggest_cuts.py words.json --hook-beats 2 --hook-len 1.4 --target 3.3

words.json comes from `align_captions.py --words-out`. A cut candidate sits between two words: a pause
(>= 0.25 s) is best, a shorter pause or a punctuation mark is acceptable, a plain word boundary is a last
resort. The cuts are chosen together (dynamic programming) so every scene is close to the target length:
the first `--hook-beats` scenes are short (hook beats, `--hook-min`..`--hook-max`), the rest aim for
`--target` seconds and stay within [--min, --max]. The last scene ends at `--end` (default: the last word
plus 0.8 s).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


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


def solve(words, target, lo, hi, hook_beats, hook_len, hook_lo, hook_hi, end, prefer):
    cands = [(0.0, 0.0)] + [c for c in candidates(words, prefer) if 0.9 < c[0] < end - 1.0]
    n = len(cands)
    INF = float("inf")
    max_k = 24
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
    ap = argparse.ArgumentParser(description="Suggest scene cuts on pauses of the voice.")
    ap.add_argument("words", type=Path)
    ap.add_argument("--target", type=float, default=3.3, help="aimed scene length in seconds (default 3.3)")
    ap.add_argument("--min", type=float, default=2.5, dest="lo", help="shortest normal scene (default 2.5)")
    ap.add_argument("--max", type=float, default=4.0, dest="hi", help="longest scene (default 4.0)")
    ap.add_argument("--hook-beats", type=int, default=2, help="how many opening scenes are short hook beats (default 2)")
    ap.add_argument("--hook-len", type=float, default=1.5, help="aimed hook beat length (default 1.5)")
    ap.add_argument("--hook-min", type=float, default=1.3, help="shortest hook beat (default 1.3; pacing_checker needs 1.2)")
    ap.add_argument("--hook-max", type=float, default=2.9, help="longest hook beat (default 2.9)")
    ap.add_argument("--end", type=float, help="video length; default last word end + 0.8")
    ap.add_argument("--prefer", default="", help="comma-separated times (s) where a cut is wanted, e.g. the ends of the sentences that change the shot")
    ap.add_argument("--json", action="store_true", help="print the scenes as JSON")
    a = ap.parse_args()

    words = json.loads(a.words.read_text(encoding="utf-8-sig"))
    end = a.end or round(words[-1]["end"] + 0.8, 2)
    prefer = [float(x) for x in a.prefer.split(",") if x.strip()]
    cuts = solve(words, a.target, a.lo, a.hi, a.hook_beats, a.hook_len, a.hook_min, a.hook_max, end, prefer)
    bounds = [0.0] + cuts + [end]
    scenes = []
    for s, e in zip(bounds, bounds[1:]):
        text = " ".join(w["text"] for w in words if s - 0.001 <= (w["start"] + w["end"]) / 2 < e)
        scenes.append({"start": round(s, 2), "end": round(e, 2), "text": text})
    if a.json:
        print(json.dumps(scenes, ensure_ascii=False, indent=1))
        return 0
    print(f"{len(scenes)} scenes, {end:.2f}s")
    for i, s in enumerate(scenes, 1):
        print(f"{i:2}  {s['start']:6.2f} - {s['end']:6.2f}  ({s['end'] - s['start']:.2f}s)  {s['text']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
