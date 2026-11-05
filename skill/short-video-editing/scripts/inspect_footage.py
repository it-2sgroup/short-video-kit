#!/usr/bin/env python3
"""Inspect raw source clips before planning an edit.

Planning a timeline without knowing what the footage actually is produces plans that cannot be
cut: a scene calling for a 3-second locked macro is worthless if every clip is handheld and
shot landscape. This reads the real properties off each file so the plan is built against
reality, and emits a shot-log skeleton for the editor to fill in with usable moments.

Usage:
    python inspect_footage.py <folder-or-files...> [--json] [--log]

    --json  machine-readable output
    --log   emit a blank shot-log table to paste into the edit plan

Requires ffprobe on PATH (ships with ffmpeg).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv", ".hevc", ".3gp"}


def probe(path: Path) -> dict:
    cmd = [
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", str(path),
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60).stdout
    except subprocess.CalledProcessError as e:
        return {"error": (e.stderr or "ffprobe failed").strip().splitlines()[-1][:120]}
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return {"error": str(e)[:120]}

    data = json.loads(out)
    v = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    a = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    if not v:
        return {"error": "no video stream"}

    w, h = int(v.get("width", 0)), int(v.get("height", 0))
    # Phones write rotation metadata rather than rotating pixels, so a clip that reads as
    # landscape here may actually play vertical. Check before concluding it needs reframing.
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = abs(int(sd["rotation"])) % 180
    if rot == 90:
        w, h = h, w

    fps = 0.0
    raw_fps = v.get("avg_frame_rate") or v.get("r_frame_rate") or "0/1"
    try:
        num, den = raw_fps.split("/")
        fps = round(float(num) / float(den), 2) if float(den) else 0.0
    except (ValueError, ZeroDivisionError):
        pass

    dur = float(data.get("format", {}).get("duration") or v.get("duration") or 0)

    return {
        "duration_s": round(dur, 2),
        "width": w,
        "height": h,
        "orientation": "vertical" if h > w else ("square" if h == w else "LANDSCAPE"),
        "fps": fps,
        "has_audio": a is not None,
        "vcodec": v.get("codec_name", "?"),
        "size_mb": round(path.stat().st_size / 1_048_576, 1),
        "rotated": rot == 90,
    }


def collect(targets: list[str]) -> list[Path]:
    files: list[Path] = []
    for t in targets:
        p = Path(t)
        if p.is_dir():
            files += [f for f in sorted(p.iterdir()) if f.suffix.lower() in VIDEO_EXT]
        elif p.is_file():
            files.append(p)
        else:
            print(f"Skipped (not found): {t}", file=sys.stderr)
    return files


def main() -> int:
    ap = argparse.ArgumentParser(description="Inspect raw clips before planning an edit.")
    ap.add_argument("targets", nargs="+", help="Folder(s) or video file(s)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--log", action="store_true", help="Emit a blank shot-log table")
    args = ap.parse_args()

    if not shutil.which("ffprobe"):
        print("ffprobe not found on PATH. It ships with ffmpeg.", file=sys.stderr)
        return 1

    files = collect(args.targets)
    if not files:
        print("No video files found.", file=sys.stderr)
        return 1

    results = []
    for f in files:
        info = probe(f)
        info["file"] = f.name
        info["path"] = str(f.resolve())
        results.append(info)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0

    ok = [r for r in results if "error" not in r]
    bad = [r for r in results if "error" in r]

    print(f"{len(files)} clip(s)\n")
    print(f"{'File':<34}{'Dur':>8}{'Resolution':>12}{'FPS':>7}{'Audio':>7}  Orientation")
    print("-" * 84)
    for r in ok:
        res = f"{r['width']}x{r['height']}"
        audio = "yes" if r["has_audio"] else "NO"
        print(
            f"{r['file'][:33]:<34}"
            f"{r['duration_s']:>7.1f}s"
            f"{res:>12}"
            f"{r['fps']:>7.0f}"
            f"{audio:>7}"
            f"  {r['orientation']}"
            + ("  (rotation metadata)" if r.get("rotated") else "")
        )
    for r in bad:
        print(f"{r['file'][:33]:<34}  ERROR: {r['error']}")

    if ok:
        total = sum(r["duration_s"] for r in ok)
        print(f"\nTotal source: {total:.1f}s across {len(ok)} clip(s)")

        # Flag the things that will break a plan if discovered late.
        notes = []
        land = [r["file"] for r in ok if r["orientation"] == "LANDSCAPE"]
        if land:
            notes.append(
                f"{len(land)} clip(s) are landscape — they need reframing or a blurred-fill "
                f"backdrop for a 1080x1920 frame: {', '.join(land[:3])}"
            )
        silent = [r["file"] for r in ok if not r["has_audio"]]
        if silent:
            notes.append(
                f"{len(silent)} clip(s) have no audio track — no diegetic sound to use, so the "
                f"demo will lean entirely on voiceover: {', '.join(silent[:3])}"
            )
        fpsset = {r["fps"] for r in ok if r["fps"]}
        if len(fpsset) > 1:
            notes.append(f"Mixed frame rates ({sorted(fpsset)}) — conform before cutting.")
        sizes = {(r["width"], r["height"]) for r in ok}
        if len(sizes) > 1:
            notes.append(f"Mixed resolutions ({len(sizes)} different) — conform before cutting.")
        if total < 45:
            notes.append(
                f"Only {total:.0f}s of source for a 30-40s cut. That leaves almost no room to "
                "choose moments; expect to reuse shots via punch-ins, or shoot pickups."
            )
        if notes:
            print("\nWorth knowing before planning:")
            for n in notes:
                print(f"  ! {n}")

    if args.log:
        print("\n## Shot log\n")
        print("| Clip | In | Out | What happens | Usable for |")
        print("|------|----|----|--------------|------------|")
        for r in ok:
            print(f"| {r['file']} | 0.0 | {r['duration_s']} | [describe] | [hook/problem/demo/reveal] |")
        print(
            "\nSplit a clip into several rows where several usable moments sit inside it. "
            "The In/Out columns are source timecodes; the edit plan's Start/End are timeline "
            "positions. They are not the same thing."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
