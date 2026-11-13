#!/usr/bin/env python3
"""Check that edit plans do not reuse the same stretch of raw footage.

One folder of raw clips usually has to feed SEVERAL videos. The expensive mistake is spending the
best moments on the first video and then repeating them in the next, or repeating a moment inside
one video. This reads the scene table of each edit plan (columns Start, End, Source, In, and Speed when
present), turns every scene into a source interval [In, In + (End - Start) x average speed] and reports
any overlap, inside one plan and across plans. A scene at 2x reads twice its length of footage.

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


# Named speed curves: the points of a ramp, spread evenly across the scene and eased between. The names are the editor's
# vocabulary (CapCut's "velocity" presets); CapCut publishes no numbers for them, so these are the kit's own approximations.
SPEED_PRESETS = {
    "montage": [1.0, 2.5, 1.0],        # slow-fast-slow: a push through the middle
    "hero": [2.0, 0.4, 2.0],           # fast-slow-fast: a slow moment held in the middle (needs a 60 fps proxy)
    "bullet": [1.0, 0.15, 0.15, 1.6],  # a sudden near-freeze, then release (needs a 60 fps proxy)
    "flash-in": [3.0, 1.0],            # starts fast and settles
    "flash-out": [1.0, 3.0],           # runs normal then whips away
    "freeze-hit": [1.0, 0.0, 0.0, 1.0],  # runs, holds one frame for the middle third of the scene, runs again (pair it with +flash and a camera punch)
}


def parse_speed(cell: str):
    """Speed cell -> (speed, ramp): blank = (None, None); "2x" or "0.5" = (2.0, None);
    "ramp 1>2.5>1" = (None, [1.0, 2.5, 1.0]); a preset name (montage, hero, bullet, flash-in, flash-out, freeze-hit) = its ramp."""
    cell = (cell or "").strip().lower().replace("×", "x")
    if not cell or cell in "-–":
        return None, None
    if cell in SPEED_PRESETS:
        return None, list(SPEED_PRESETS[cell])
    m = re.fullmatch(r"ramp\s+([\d.]+(?:\s*>\s*[\d.]+)+)", cell)
    if m:
        return None, [float(x) for x in m.group(1).split(">")]
    m = re.fullmatch(r"([\d.]+)\s*x?", cell)
    if m and float(m.group(1)) > 0:
        return float(m.group(1)), None
    raise ValueError(f"cannot read speed '{cell}' (write 2x, 0.5x, ramp 1>2.5>1 or a preset: {', '.join(SPEED_PRESETS)})")


def speed_factor(cell: str) -> float:
    """Average speed of a scene: source seconds read per timeline second. A ramp's points are spread
    evenly and eased symmetrically between, so each segment averages the mean of its two ends."""
    speed, ramp = parse_speed(cell)
    if ramp:
        return sum((a + b) / 2 for a, b in zip(ramp, ramp[1:])) / (len(ramp) - 1)
    return speed or 1.0


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
        if src in ("", "-", "–"):  # a graphics-only scene (a card or end card with no footage) uses no source
            continue
        try:
            factor = speed_factor(cells[header["speed"]]) if "speed" in header and header["speed"] < len(cells) else 1.0
        except ValueError as e:
            sys.exit(f"{path}: scene {n}: {e}")
        rows.append({"scene": n, "src": Path(src).stem.upper(), "a": in_t, "b": round(in_t + (end - start) * factor, 3)})
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
            if gap < a.gap - 1e-6:  # tolerance: 0.5 s margins computed from decimals land at 0.49999…
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
