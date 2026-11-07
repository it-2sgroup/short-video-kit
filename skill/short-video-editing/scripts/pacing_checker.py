#!/usr/bin/env python3
"""Check a short-video edit plan against the pacing rules of its playbook.

Distribution on short-form platforms follows early retention, so a plan that drifts past its genre's
rhythm tends to lose viewers before the point is made; it is cheaper to catch on paper than after a
render. The numbers come from the plan's playbook (playbooks/<id>.json, named by the plan's
`**Playbook:**` line or --playbook), not from this file:

  1. The hook resolves by `hook.deadline` (3 s in every playbook); frame 0 is never empty.
  2. No scene is longer than `scenes.max`; outside the hook none is shorter than `scenes.min`
     (hook beats may go down to `hook.minBeat`).
  3. Scenes tile the timeline with no gaps and no overlaps.
  4. Runtime lands in `runtime.min`-`runtime.max`, ideally in `runtime.ideal`.

Usage:
    python pacing_checker.py <edit-plan.md> [--playbook ID] [--min 25] [--max 45] [--min-scene 2.5] [--json]

Exit code is 0 when every rule passes and 1 otherwise, so this can gate a build. The parser reads any
markdown table with columns for the scene number, start and end, and tolerates extra columns.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import playbook as playbooks  # noqa: E402

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


def is_hook(s: Scene, deadline: float) -> bool:
    """A HOOK-typed scene (not RE-HOOK). With no type column, anything inside the hook window."""
    kind = s.kind.strip().upper()
    if kind:
        return kind == "HOOK"
    return s.start < deadline - EPSILON


def check(scenes: list[Scene], pb: dict) -> Report:
    """Check scenes against a loaded playbook (playbook.load); the CLI may have overridden its numbers."""
    report = Report(scenes=scenes)
    deadline, hook_min = pb["hook"]["deadline"], pb["hook"]["minBeat"]
    lo, hi, target = pb["scenes"]["min"], pb["scenes"]["max"], pb["scenes"]["target"]
    rmin, rmax = pb["runtime"]["min"], pb["runtime"]["max"]
    ideal_lo, ideal_hi = pb["runtime"]["ideal"]
    why = pb["runtime"].get("why", "")

    if not scenes:
        report.errors.append("No scenes to check.")
        return report

    ordered = sorted(scenes, key=lambda s: s.start)

    # Rule: outside the hook, scenes last at least `lo`; hook beats at least `hook_min`.
    for s in ordered:
        if s.duration <= 0:
            continue
        if is_hook(s, deadline):
            if s.duration < hook_min - EPSILON:
                report.errors.append(
                    f"Hook scene {s.index} ({s.start:g}-{s.end:g}s) is only {s.duration:.1f}s. "
                    f"Even hook beats need {hook_min:g}s to read."
                )
        elif s.duration < lo - EPSILON:
            report.errors.append(
                f"Scene {s.index} ({s.start:g}-{s.end:g}s) is only {s.duration:.1f}s; outside the hook "
                f"a {pb['name']} scene lasts at least {lo:g}s (aim {target:g}s). Merge it with a "
                "neighbour or hold the shot longer."
            )

    # Rule: each scene must have positive length, and none may exceed `hi`.
    for s in ordered:
        if s.duration <= 0:
            report.errors.append(
                f"Scene {s.index} ({s.start:g}-{s.end:g}s): end must come after start."
            )
        elif s.duration > hi + EPSILON:
            report.errors.append(
                f"Scene {s.index} ({s.start:g}-{s.end:g}s) runs {s.duration:.1f}s, over the "
                f"{hi:g}s limit of {pb['name']}. Split it, punch in, or cut to a B-roll insert."
            )

    # Rule: the hook must land inside the deadline. What matters is that something has changed on
    # screen by then, so the viewer has a reason to stay.
    first = ordered[0]
    if first.start > EPSILON:
        report.errors.append(
            f"Timeline starts at {first.start:g}s, not 0. The first frame is the thumbnail — "
            "it cannot be empty."
        )
    if first.end > deadline + EPSILON:
        report.errors.append(
            f"The opening scene runs to {first.end:g}s, so the hook is not resolved within "
            f"{deadline:g}s. Cut it shorter or split it."
        )

    hook_scenes = [s for s in ordered if s.start < deadline - EPSILON]
    if len(hook_scenes) < pb["hook"]["beats"]:
        report.warnings.append(
            f"Only {len(hook_scenes)} scene(s) in the first {deadline:g}s; the {pb['name']} hook "
            f"is {pb['hook']['beats']} beats of ~{pb['hook']['beat']:g}s ({pb['hook'].get('purpose', '')})."
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
    if runtime < rmin - EPSILON:
        report.errors.append(f"Runtime {runtime:.1f}s is under the {rmin:g}s floor of {pb['name']}. {why}".strip())
    elif runtime > rmax + EPSILON:
        report.errors.append(f"Runtime {runtime:.1f}s is over the {rmax:g}s ceiling of {pb['name']}.")
    elif not (ideal_lo - EPSILON <= runtime <= ideal_hi + EPSILON):
        report.warnings.append(
            f"Runtime {runtime:.1f}s is allowed but outside the ideal {ideal_lo:g}-{ideal_hi:g}s of {pb['name']}."
        )

    # Advisory: the average body scene against the playbook's target.
    body = [s for s in ordered if not is_hook(s, deadline)] or ordered
    avg = sum(s.duration for s in body) / len(body)
    if avg > target * 1.2:
        report.warnings.append(f"Average non-hook scene is {avg:.1f}s against a target of {target:g}s; it will feel slow.")
    elif avg < target * 0.8:
        report.warnings.append(f"Average non-hook scene is {avg:.1f}s against a target of {target:g}s; it may read as choppy.")
    return report


def format_text(report: Report, path: Path, pb: dict) -> str:
    out: list[str] = []
    out.append(f"Pacing check: {path.name}  (playbook {pb['name']})")
    out.append("=" * (15 + len(path.name)))

    if report.scenes:
        ordered = sorted(report.scenes, key=lambda s: s.start)
        runtime = ordered[-1].end
        avg = sum(s.duration for s in ordered) / len(ordered)
        longest = max(ordered, key=lambda s: s.duration)
        out.append(f"  Scenes        : {len(ordered)}")
        out.append(f"  Runtime       : {runtime:.1f}s  (window {pb['runtime']['min']:g}-{pb['runtime']['max']:g}s)")
        out.append(f"  Avg scene     : {avg:.1f}s  (target {pb['scenes']['target']:g}s)")
        out.append(
            f"  Longest scene : {longest.duration:.1f}s "
            f"(scene {longest.index}, limit {pb['scenes']['max']:g}s)"
        )
        out.append(f"  Hook resolves : {ordered[0].end:.1f}s (deadline {pb['hook']['deadline']:g}s)")
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
    ap = argparse.ArgumentParser(description="Check an edit plan against its playbook's pacing rules.")
    ap.add_argument("plan", type=Path, help="Path to the edit plan markdown file")
    ap.add_argument("--playbook", help="playbook id[:variant]; default: the plan's **Playbook:** line")
    ap.add_argument("--min", type=float, help="override the minimum runtime (s)")
    ap.add_argument("--max", type=float, help="override the maximum runtime (s)")
    ap.add_argument("--min-scene", type=float, help="override the minimum non-hook scene length (s)")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = ap.parse_args()

    if not args.plan.exists():
        print(f"File not found: {args.plan}", file=sys.stderr)
        return 1

    text = args.plan.read_text(encoding="utf-8")
    pb = playbooks.resolve(args.playbook, text)
    if args.min is not None:
        pb["runtime"]["min"] = args.min
    if args.max is not None:
        pb["runtime"]["max"] = args.max
    if args.min_scene is not None:
        pb["scenes"]["min"] = args.min_scene
    scenes, parse_problems = parse_plan(text)
    report = check(scenes, pb)
    report.errors = parse_problems + report.errors

    if args.json:
        ordered = sorted(scenes, key=lambda s: s.start)
        print(
            json.dumps(
                {
                    "file": str(args.plan),
                    "playbook": pb["name"],
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
        print(format_text(report, args.plan, pb))

    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
