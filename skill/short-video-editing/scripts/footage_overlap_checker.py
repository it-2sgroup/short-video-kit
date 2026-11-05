#!/usr/bin/env python3
"""Check that edit plans do not reuse the same stretch of raw footage.

One folder of raw clips usually has to feed SEVERAL videos. The expensive mistake is spending the
best moments on the first video and then repeating them in the next, or repeating a moment inside
one video. This reads the scene table of each edit plan (columns Start, End, Source, In), turns every
scene into a source interval [In, In + (End - Start)] and reports any overlap, inside one plan and
across plans.

    python scripts/footage_overlap_checker.py plan_a.md plan_b.md [--gap 0.5] [--clips DIR]

--gap   minimum clean margin, in seconds, required between two used intervals of the same clip
        (default 0.5: cross-dissolves borrow ~0.2s of footage before and after each scene, so a
        tighter margin would show the neighbour's frames inside the transition).
--clips DIR  also lists the FREE ranges left in every clip (needs ffprobe), so the next video can
        be planned from what remains.

Exit code 0 = no overlaps, 1 = overlaps found, 2 = bad input.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path


def parse_plan(path: Path):
    rows, header = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        low = [c.lower() for c in cells]
        if "start" in low and "end" in low and "source" in low and "in" in low:
            header = {name: i for i, name in enumerate(low)}
            continue
        if header is None or set("".join(cells)) <= set("-: "):
            continue
        try:
            n = cells[header.get("#", 0)]
            start, end = float(cells[header["start"]]), float(cells[header["end"]])
            src, in_t = cells[header["source"]], float(cells[header["in"]])
        except (ValueError, KeyError, IndexError):
            continue
        rows.append({"scene": n, "src": Path(src).stem.upper(), "a": in_t, "b": in_t + (end - start)})
    return rows


def clip_durations(root: Path):
    out = {}
    for p in root.rglob("*"):
        if p.suffix.lower() in {".mov", ".mp4", ".m4v", ".mkv"}:
            try:
                d = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                    capture_output=True, text=True, check=True).stdout.strip()
                out[p.stem.upper()] = float(d)
            except Exception:
                pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plans", nargs="+")
    ap.add_argument("--gap", type=float, default=0.5)
    ap.add_argument("--clips")
    a = ap.parse_args()

    used = []  # (plan, scene, src, a, b)
    for p in a.plans:
        path = Path(p)
        rows = parse_plan(path)
        if not rows:
            print(f"{p}: no scene table with Source/In columns found", file=sys.stderr)
            sys.exit(2)
        for r in rows:
            used.append((path.parent.name + "/" + path.name, r["scene"], r["src"], r["a"], r["b"]))

    problems = 0
    for i in range(len(used)):
        for j in range(i + 1, len(used)):
            p1, s1, c1, a1, b1 = used[i]
            p2, s2, c2, a2, b2 = used[j]
            if c1 != c2:
                continue
            gap = max(a1, a2) - min(b1, b2)  # negative = overlap
            if gap < a.gap:
                problems += 1
                kind = "OVERLAP" if gap < 0 else "TOO CLOSE"
                print(f"{kind:9} {c1}: {p1} scene {s1} [{a1:.1f}-{b1:.1f}]  vs  {p2} scene {s2} [{a2:.1f}-{b2:.1f}]"
                      f"  (margin {gap:+.1f}s, need {a.gap:.1f}s)")

    per_clip = {}
    for _, _, c, x, y in used:
        per_clip.setdefault(c, []).append((x, y))
    print(f"\nScenes read: {len(used)} across {len(a.plans)} plan(s); clips touched: {len(per_clip)}")

    if a.clips:
        durs = clip_durations(Path(a.clips))
        print("\nFree ranges (>=1.5s) left per clip:")
        for c in sorted(durs):
            iv = sorted(per_clip.get(c, []))
            free, cur = [], 0.0
            for x, y in iv:
                if x - a.gap > cur:
                    free.append((cur, x - a.gap))
                cur = max(cur, y + a.gap)
            if durs[c] > cur:
                free.append((cur, durs[c]))
            free = [(round(x, 1), round(y, 1)) for x, y in free if y - x >= 1.5]
            total = sum(y - x for x, y in free)
            print(f"  {c}: {durs[c]:5.1f}s long, {total:5.1f}s free  " + ", ".join(f"{x}-{y}" for x, y in free))

    if problems:
        print(f"\nFAIL — {problems} reused/too-close stretch(es).")
        sys.exit(1)
    print("\nPASS — no footage is reused within or between these plans.")


if __name__ == "__main__":
    main()
