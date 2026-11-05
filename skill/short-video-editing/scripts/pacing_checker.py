#!/usr/bin/env python3
"""Check a short-video edit plan against the hard pacing rules.

The rules this enforces exist because distribution on short-form platforms is driven by early
retention. A plan that drifts past them tends to lose viewers before the product is ever seen,
so it is worth catching on paper rather than after a render.

Rules checked:
  1. The hook must be established within the first 3.0 seconds.
  2. No scene may run longer than 4.0 seconds, and outside the hook none may be shorter than
     2.5 seconds (client wants a cut about every 3-4s; hook beats of 1.2s+ are allowed).
  3. Scenes must tile the timeline with no gaps and no overlaps.
  4. Total runtime should land in the target window (default 25-45s, ideal 30-40s).

Usage:
    python pacing_checker.py <edit-plan.md> [--min 25] [--max 45] [--json]

Exit code is 0 when every rule passes and 1 otherwise, so this can gate a build.

The parser reads the scene table described in assets/edit-plan-template.md. It accepts any
markdown table whose header contains columns for the scene number, start, and end, and tolerates
extra columns, so the template can grow without breaking this script.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

HOOK_DEADLINE = 3.0
MAX_SCENE = 4.0
# Client requirement (Phuong, 2026-11): outside the hook, a scene should last about 3-4s. Cuts every
# 1.5-2s read as "bị ngắt" (jerky) and the transitions had no time to look smooth. Hook scenes are
# the one place a shorter beat is allowed, because the before/after must land in the first 3s.
MIN_SCENE = 2.5          # hard floor for non-hook scenes
PREFERRED_MIN_SCENE = 3.0
HOOK_MIN_SCENE = 1.2
DEFAULT_MIN_RUNTIME = 25.0
DEFAULT_MAX_RUNTIME = 45.0
IDEAL_MIN, IDEAL_MAX = 30.0, 40.0
# Timeline positions are compared with a small tolerance so that a plan written to one decimal
# place is not failed for floating-point noise.
EPSILON = 0.051


@dataclass
class Scene:
    index: int
    start: float
    end: float
    kind: str = ""
    description: str = ""
    row: int = 0

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class Report:
    scenes: list[Scene] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def parse_timecode(raw: str) -> float | None:
    """Accept 3, 3.5, 3s, 0:03, 00:03.5 and return seconds."""
    text = raw.strip().replace("s", "").replace(",", ".")
    if not text:
        return None
    if ":" in text:
        parts = text.split(":")
        try:
            nums = [float(p) for p in parts]
        except ValueError:
            return None
        seconds = 0.0
        for n in nums:
            seconds = seconds * 60 + n
        return seconds
    try:
        return float(text)
    except ValueError:
        return None


def split_row(line: str) -> list[str]:
    cells = line.strip().strip("|").split("|")
    return [c.strip() for c in cells]


def find_column(headers: list[str], *candidates: str) -> int | None:
    lowered = [h.lower() for h in headers]
    for cand in candidates:
        for i, h in enumerate(lowered):
            if cand in h:
                return i
    return None


def parse_plan(text: str) -> tuple[list[Scene], list[str]]:
    """Pull scenes out of the first markdown table that has start and end columns."""
    problems: list[str] = []
    lines = text.splitlines()

    header_idx = None
    cols: dict[str, int] = {}
    for i, line in enumerate(lines):
        if line.count("|") < 2:
            continue
        headers = split_row(line)
        start_i = find_column(headers, "start", "from", "bắt đầu")
        end_i = find_column(headers, "end", "to", "kết thúc")
        if start_i is not None and end_i is not None:
            header_idx = i
            cols = {
                "start": start_i,
                "end": end_i,
                "num": find_column(headers, "#", "no", "scene", "cảnh") or 0,
                "kind": find_column(headers, "type", "kind", "role", "loại"),
                "desc": find_column(headers, "shot", "visual", "action", "description", "hình"),
            }
            break

    if header_idx is None:
        problems.append(
            "No scene table found. Expected a markdown table with 'Start' and 'End' columns "
            "(see assets/edit-plan-template.md)."
        )
        return [], problems

    scenes: list[Scene] = []
    for offset, line in enumerate(lines[header_idx + 1 :], start=header_idx + 2):
        stripped = line.strip()
        if not stripped or stripped.count("|") < 2:
            if scenes:
                break
            continue
        # skip the |---|---| separator row
        if re.fullmatch(r"[|\s:\-]+", stripped):
            continue

        cells = split_row(line)

        def cell(key: str) -> str:
            i = cols.get(key)
            if i is None or i >= len(cells):
                return ""
            return cells[i]

        start = parse_timecode(cell("start"))
        end = parse_timecode(cell("end"))
        if start is None or end is None:
            problems.append(
                f"Row {offset}: could not read start/end "
                f"('{cell('start')}' / '{cell('end')}'). Use seconds like 3.5 or 0:03.5."
            )
            continue

        raw_num = cell("num")
        num_match = re.search(r"\d+", raw_num)
        index = int(num_match.group()) if num_match else len(scenes) + 1

        scenes.append(
            Scene(
                index=index,
                start=start,
                end=end,
                kind=cell("kind"),
                description=cell("desc"),
                row=offset,
            )
        )

    if not scenes:
        problems.append("Scene table found but no readable scene rows in it.")
    return scenes, problems


def is_hook(s: Scene) -> bool:
    """A HOOK-typed scene (not RE-HOOK). With no type column, anything inside the hook window."""
    kind = s.kind.strip().upper()
    if kind:
        return kind == "HOOK"
    return s.start < HOOK_DEADLINE - EPSILON


def check(scenes: list[Scene], min_runtime: float, max_runtime: float,
          min_scene: float = MIN_SCENE) -> Report:
    report = Report(scenes=scenes)

    if not scenes:
        report.errors.append("No scenes to check.")
        return report

    ordered = sorted(scenes, key=lambda s: s.start)

    # Rule: outside the hook, scenes last at least min_scene (client: cut every ~3-4s).
    for s in ordered:
        if s.duration <= 0:
            continue
        if is_hook(s):
            if s.duration < HOOK_MIN_SCENE - EPSILON:
                report.errors.append(
                    f"Hook scene {s.index} ({s.start:g}-{s.end:g}s) is only {s.duration:.1f}s. "
                    f"Even hook beats need {HOOK_MIN_SCENE:g}s to read."
                )
        elif s.duration < min_scene - EPSILON:
            report.errors.append(
                f"Scene {s.index} ({s.start:g}-{s.end:g}s) is only {s.duration:.1f}s; outside the "
                f"hook a scene must last at least {min_scene:g}s (aim for 3-4s). Merge it with a "
                "neighbour or hold the shot longer — cuts this fast feel jerky."
            )

    # Rule: each scene must have positive length, and none may exceed MAX_SCENE.
    for s in ordered:
        if s.duration <= 0:
            report.errors.append(
                f"Scene {s.index} ({s.start:g}-{s.end:g}s): end must come after start."
            )
        elif s.duration > MAX_SCENE + EPSILON:
            report.errors.append(
                f"Scene {s.index} ({s.start:g}-{s.end:g}s) runs {s.duration:.1f}s, over the "
                f"{MAX_SCENE:g}s limit. Split it, push in, or cut to a B-roll insert."
            )

    # Rule: the hook must land inside the first 3 seconds. A hook is whatever happens first;
    # what matters is that something has changed on screen by the deadline, so the viewer has
    # a reason to stay.
    first = ordered[0]
    if first.start > EPSILON:
        report.errors.append(
            f"Timeline starts at {first.start:g}s, not 0. The first frame is the thumbnail — "
            "it cannot be empty."
        )
    if first.end > HOOK_DEADLINE + EPSILON:
        report.errors.append(
            f"The opening scene runs to {first.end:g}s, so the hook is not resolved within "
            f"{HOOK_DEADLINE:g}s. Cut it shorter or split it."
        )

    hook_scenes = [s for s in ordered if s.start < HOOK_DEADLINE - EPSILON]
    if len(hook_scenes) < 2:
        report.warnings.append(
            f"Only {len(hook_scenes)} scene in the first {HOOK_DEADLINE:g}s. Hooks usually hold "
            "better with two ~1.5s beats (before -> after) rather than one static shot."
        )

    # Rule: scenes must tile the timeline.
    for prev, nxt in zip(ordered, ordered[1:]):
        gap = nxt.start - prev.end
        if gap > EPSILON:
            report.errors.append(
                f"Gap of {gap:.1f}s between scene {prev.index} (ends {prev.end:g}s) and "
                f"scene {nxt.index} (starts {nxt.start:g}s). Dead air loses viewers."
            )
        elif gap < -EPSILON:
            report.errors.append(
                f"Scene {prev.index} (ends {prev.end:g}s) overlaps scene {nxt.index} "
                f"(starts {nxt.start:g}s) by {-gap:.1f}s."
            )

    # Rule: total runtime.
    runtime = ordered[-1].end
    if runtime < min_runtime - EPSILON:
        report.errors.append(
            f"Runtime {runtime:.1f}s is under the {min_runtime:g}s floor. In the reference "
            "dataset, sub-25s videos had the lowest CTR and sale rate of any length band."
        )
    elif runtime > max_runtime + EPSILON:
        report.errors.append(
            f"Runtime {runtime:.1f}s is over the {max_runtime:g}s ceiling."
        )
    elif not (IDEAL_MIN - EPSILON <= runtime <= IDEAL_MAX + EPSILON):
        report.warnings.append(
            f"Runtime {runtime:.1f}s is inside the allowed window but outside the "
            f"{IDEAL_MIN:g}-{IDEAL_MAX:g}s band where CTR peaked in the reference data."
        )

    # Advisory: average scene length is a decent proxy for whether the edit feels alive.
    body = [s for s in ordered if not is_hook(s)] or ordered
    avg = sum(s.duration for s in body) / len(body)
    if avg > 3.8:
        report.warnings.append(
            f"Average non-hook scene is {avg:.1f}s. The edit will feel slow; aim for 3-3.7s."
        )
    elif avg < PREFERRED_MIN_SCENE - EPSILON:
        report.warnings.append(
            f"Average non-hook scene is {avg:.1f}s. The client asked for a cut about every 3-4s; "
            "this will read as choppy."
        )
    short = [s for s in body if s.duration < PREFERRED_MIN_SCENE - EPSILON]
    if short:
        report.warnings.append(
            "Scenes under 3s (allowed, but check they look smooth): "
            + ", ".join(f"#{s.index} {s.duration:.1f}s" for s in short)
        )

    return report


def format_text(report: Report, path: Path, min_rt: float, max_rt: float) -> str:
    out: list[str] = []
    out.append(f"Pacing check: {path.name}")
    out.append("=" * (15 + len(path.name)))

    if report.scenes:
        ordered = sorted(report.scenes, key=lambda s: s.start)
        runtime = ordered[-1].end
        avg = sum(s.duration for s in ordered) / len(ordered)
        longest = max(ordered, key=lambda s: s.duration)
        out.append(f"  Scenes        : {len(ordered)}")
        out.append(f"  Runtime       : {runtime:.1f}s  (window {min_rt:g}-{max_rt:g}s)")
        out.append(f"  Avg scene     : {avg:.1f}s")
        out.append(
            f"  Longest scene : {longest.duration:.1f}s "
            f"(scene {longest.index}, limit {MAX_SCENE:g}s)"
        )
        out.append(f"  Hook resolves : {ordered[0].end:.1f}s (deadline {HOOK_DEADLINE:g}s)")
    out.append("")

    if report.errors:
        out.append(f"FAIL — {len(report.errors)} error(s):")
        for e in report.errors:
            out.append(f"  x {e}")
    else:
        out.append("PASS — all hard rules satisfied.")

    if report.warnings:
        out.append("")
        out.append(f"{len(report.warnings)} warning(s):")
        for w in report.warnings:
            out.append(f"  ! {w}")

    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Check an edit plan against short-video pacing rules.")
    ap.add_argument("plan", type=Path, help="Path to the edit plan markdown file")
    ap.add_argument("--min", type=float, default=DEFAULT_MIN_RUNTIME, help="Minimum runtime (s)")
    ap.add_argument("--max", type=float, default=DEFAULT_MAX_RUNTIME, help="Maximum runtime (s)")
    ap.add_argument("--min-scene", type=float, default=MIN_SCENE,
                    help="Minimum length (s) of a non-hook scene (default 2.5; aim for 3-4)")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = ap.parse_args()

    if not args.plan.exists():
        print(f"File not found: {args.plan}", file=sys.stderr)
        return 1

    text = args.plan.read_text(encoding="utf-8")
    scenes, parse_problems = parse_plan(text)
    report = check(scenes, args.min, args.max, args.min_scene)
    report.errors = parse_problems + report.errors

    if args.json:
        ordered = sorted(scenes, key=lambda s: s.start)
        print(
            json.dumps(
                {
                    "file": str(args.plan),
                    "passed": report.ok,
                    "scene_count": len(ordered),
                    "runtime_s": round(ordered[-1].end, 2) if ordered else 0,
                    "avg_scene_s": (
                        round(sum(s.duration for s in ordered) / len(ordered), 2)
                        if ordered
                        else 0
                    ),
                    "longest_scene_s": (
                        round(max(s.duration for s in ordered), 2) if ordered else 0
                    ),
                    "hook_resolves_s": round(ordered[0].end, 2) if ordered else None,
                    "errors": report.errors,
                    "warnings": report.warnings,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(format_text(report, args.plan, args.min, args.max))

    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
