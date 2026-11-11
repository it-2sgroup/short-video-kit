#!/usr/bin/env python3
"""Create a render project from assets/remotion-template and (optionally) make its proxies.

    python scripts/new_remotion_project.py ~/videos/brand-render --playbook real-estate   # template + the playbook's theme
    python scripts/new_remotion_project.py DEST --install                    # + npm install (downloads ~300 MB)
    python scripts/new_remotion_project.py DEST --proxies /path/to/raw_clips  # + corrected, graded proxies (prepare_footage.py)
    python scripts/new_remotion_project.py DEST --update                      # re-copy the template over DEST

A render project is a copy of the template, so a template fix does not reach it by itself. --update
replaces the template's files (src/, config, package.json) and the sound effects in public/sfx, and keeps
the rest of public/, node_modules/, out/ and your own *.json projects. Local edits to the template's
files are overwritten.

Proxies: phone footage is usually 4K HEVC with rotation metadata (sometimes HDR); rendering from it is
slow and wrong-coloured. --proxies hands the folder to prepare_footage.py, which measures every clip,
corrects it (tone-mapping, white balance, exposure, stabilisation, noise) and applies the playbook's
grade, writing H.264 <STEM>.mp4 at 1620x2880 by default so camera moves up to ~1.5x stay sharp
(--proxy-height 1920 for fast drafts, 3840 for zooms up to 2x; references/image-processing.md).

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


def install_sfx(dest: Path) -> None:
    """public/sfx = the recorded CC0 files from assets/sfx + the ones make_sfx.py synthesizes."""
    out = dest / "public" / "sfx"
    out.mkdir(parents=True, exist_ok=True)
    for f in (SKILL / "assets" / "sfx").glob("*.wav"):
        shutil.copy2(f, out / f.name)
    r = subprocess.run([sys.executable, str(SKILL / "scripts" / "make_sfx.py"), str(out)], capture_output=True, text=True)
    print(f"sound effects in {out}" if r.returncode == 0 else f"could not synthesize sound effects (is ffmpeg on PATH?):\n{r.stderr.strip()}")


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
    ap.add_argument("--playbook", help="playbook id[:variant]: sets the theme and the proxies' grade (playbooks/<id>.json)")
    ap.add_argument("--theme", choices=["cool", "warm", "luxe", "crimson"],
                    help="override the playbook's colour theme in src/theme.ts: cool (white, sky blue), warm (ivory, gold, "
                         "vermilion: food, amber light), luxe (ivory, champagne, charcoal: property, fashion), crimson (white, brand red, "
                         "yellow, maroon: agency pitches with cards on an animated grid). "
                         "--update re-copies the template, so repeat --playbook/--theme then")
    ap.add_argument("--proxies", type=Path, help="folder of raw clips to correct, grade and convert into public/clips")
    ap.add_argument("--slowmo", action="store_true", help="with --proxies: keep 60 fps sources at 60 (for 0.5x slow motion)")
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
    theme = a.theme
    if a.playbook and not theme:
        sys.path.insert(0, str(SKILL / "scripts"))
        import playbook as playbooks
        theme = playbooks.load(a.playbook)["theme"]
    if theme:
        set_theme(dest, theme)
    for sub in ("public/clips", "public/audio"):
        (dest / sub).mkdir(parents=True, exist_ok=True)
    if not exists or a.update:
        install_sfx(dest)

    if a.proxies:
        cmd = [sys.executable, str(SKILL / "scripts" / "prepare_footage.py"), str(a.proxies.expanduser()),
               str(dest / "public" / "clips"), "--height", str(a.proxy_height)]
        if a.playbook:
            cmd += ["--playbook", a.playbook]
        if a.slowmo:
            cmd.append("--slowmo")
        if subprocess.run(cmd).returncode:
            sys.exit("prepare_footage.py failed")

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
