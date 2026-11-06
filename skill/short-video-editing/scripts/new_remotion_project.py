#!/usr/bin/env python3
"""Create a render project from assets/remotion-template and (optionally) make 1080x1920 proxies.

    python scripts/new_remotion_project.py ~/videos/saiza-render            # copy template only
    python scripts/new_remotion_project.py DEST --install                    # + npm install (downloads ~300 MB)
    python scripts/new_remotion_project.py DEST --proxies /path/to/raw_clips  # + ffmpeg proxies into public/clips
    python scripts/new_remotion_project.py DEST --update                      # re-copy the template over DEST

A render project is a copy of the template, so a template fix does not reach it by itself. --update
replaces the template's files (src/, config, package.json) and the sound effects in public/sfx, and keeps
the rest of public/, node_modules/, out/ and your own *.json projects. Local edits to the template's
files are overwritten.

Proxies: phone footage is usually 4K HEVC with rotation metadata; rendering from it is slow. This
writes H.264 30fps, audio-free copies named <STEM>.mp4 (ffmpeg applies the rotation), 1620x2880 by
default so camera moves up to ~1.5x stay sharp. Use --proxy-height 1920 for fast drafts (soft past
~1.15x) or 3840 for zooms up to 2x (see references/camera-moves.md).

Ask the user before --install: it downloads npm packages and Remotion's Chromium on first render.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL / "assets" / "remotion-template"
VIDEO_EXT = {".mov", ".mp4", ".m4v", ".mkv"}


def install_sfx(dest: Path) -> None:
    """public/sfx = the recorded CC0 files from assets/sfx + the ones make_sfx.py synthesizes."""
    out = dest / "public" / "sfx"
    out.mkdir(parents=True, exist_ok=True)
    for f in (SKILL / "assets" / "sfx").glob("*.wav"):
        shutil.copy2(f, out / f.name)
    r = subprocess.run([sys.executable, str(SKILL / "scripts" / "make_sfx.py"), str(out)], capture_output=True, text=True)
    print(f"sound effects in {out}" if r.returncode == 0 else f"could not synthesize sound effects (is ffmpeg on PATH?):\n{r.stderr.strip()}")


def make_proxies(src: Path, dest: Path, height: int) -> int:
    dest.mkdir(parents=True, exist_ok=True)
    width = height * 9 // 16
    clips = sorted(p for p in src.rglob("*") if p.suffix.lower() in VIDEO_EXT)
    for p in clips:
        out = dest / f"{p.stem.upper()}.mp4"
        if out.exists():
            continue
        print(f"proxy {p.name} -> {out.name}")
        subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-y", "-i", str(p),
             "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},fps=30",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-an", str(out)],
            check=True)
    return len(clips)


def set_theme(dest: Path, theme: str) -> None:
    """Rewrite the one `const THEME: ThemeName = "..."` line of the project's theme.ts."""
    path = dest / "src" / "theme.ts"
    text = path.read_text(encoding="utf8")
    new, n = re.subn(r'(const THEME: ThemeName = )"\w+"', lambda m: f'{m.group(1)}"{theme}"', text, count=1)
    if n != 1:
        sys.exit(f"could not find the THEME line in {path}")
    path.write_text(new, encoding="utf8", newline="\n")
    print(f"theme: {theme}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Scaffold a Remotion render project for this kit.")
    ap.add_argument("dest", type=Path)
    ap.add_argument("--install", action="store_true", help="run npm install in the new project")
    ap.add_argument("--update", action="store_true", help="re-copy the template over an existing render project")
    ap.add_argument("--theme", choices=["cool", "warm"],
                    help="colour theme written into the project's src/theme.ts: cool = kit default (white and sky blue), "
                         "warm = ivory, gold and torii red for amber, wood or candle-lit footage such as restaurants. "
                         "--update re-copies the template, so repeat --theme then")
    ap.add_argument("--proxies", type=Path, help="folder of raw clips to convert into public/clips")
    ap.add_argument("--proxy-height", type=int, default=2880, choices=[1920, 2880, 3840],
                    help="proxy height in pixels: 2880 (default) stays sharp to ~1.5x zoom, 1920 is smaller and faster, 3840 sharp to 2x")
    a = ap.parse_args()

    dest = a.dest.expanduser().resolve()
    if dest.exists() and any(dest.iterdir()) and not (dest / "package.json").exists():
        sys.exit(f"{dest} exists and is not a render project; choose an empty folder.")
    exists = (dest / "package.json").exists()
    if not exists or a.update:
        shutil.copytree(TEMPLATE, dest, dirs_exist_ok=True, ignore=shutil.ignore_patterns("node_modules", "out", "public"))
        print(f"{'updated' if exists else 'created'} {dest}")
    if a.theme:
        set_theme(dest, a.theme)
    for sub in ("public/clips", "public/audio"):
        (dest / sub).mkdir(parents=True, exist_ok=True)
    if not exists or a.update:
        install_sfx(dest)

    if a.proxies:
        n = make_proxies(a.proxies.expanduser(), dest / "public" / "clips", a.proxy_height)
        print(f"{n} clip(s) in {dest / 'public' / 'clips'}")

    if a.install:
        npm = shutil.which("npm")
        if not npm:
            sys.exit("npm not found: install Node 20+ first.")
        subprocess.run([npm, "install"], cwd=dest, check=True)

    print("next: put the voiceover in public/audio/, run plan_to_project.py --out "
          f"{dest / 'project.json'}, then  npx remotion render src/index.ts Short out/video.mp4 --props=project.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
