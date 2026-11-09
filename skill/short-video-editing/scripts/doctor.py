#!/usr/bin/env python3
"""Check that this machine can run every part of the skill, and say exactly how to fix what it cannot.

Standard library only, so it runs on a machine where nothing else is installed yet. Changes nothing.

    python scripts/doctor.py              all checks, human-readable
    python scripts/doctor.py --json       the same, machine-readable
    python scripts/doctor.py --only ffmpeg   one group: python | venv | ffmpeg | model | node | key | disk

Exit code: 0 when everything REQUIRED is present, 1 otherwise. "Optional" items (Node for rendering,
the ElevenLabs key) only warn, because a video can be planned and graded without them.

Why filters are checked, not just `ffmpeg` on PATH: a distro build can lack libvidstab (stabilisation),
libzimg (HDR tone mapping) or the audio filters the voice chain uses, and the failure then appears
halfway through a 4K encode as "No such filter". Each filter below is the one a named script calls.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
SHARE = HOME / ".local" / "share" / "short-video-kit"
KIT_PYTHON = SHARE / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
MODEL_DIR = Path(os.environ.get("WHISPER_MODEL_DIR") or HOME / ".cache" / "short-video-kit" / "models")
KEYFILE = HOME / ".config" / "short-video-kit" / "env"
REPO_URL = "https://github.com/it-2sgroup/short-video-kit.git"   # private: needs `gh auth login --web`

# filter -> what stops working without it (every one is called by a script in this skill)
FILTERS = {
    "vidstabdetect": "stabilisation (prepare_footage, inspect_footage --measure)",
    "vidstabtransform": "stabilisation (prepare_footage)",
    "zscale": "HDR tone mapping (prepare_footage, inspect_footage)",
    "tonemap": "HDR tone mapping (prepare_footage, inspect_footage)",
    "haldclut": "colour grade and white balance (prepare_footage)",
    "haldclutsrc": "colour grade and white balance (prepare_footage)",
    "lenscorrection": "lens distortion (prepare_footage)",
    "hqdn3d": "denoise and its measurement (prepare_footage, inspect_footage)",
    "colorchannelmixer": "white balance (prepare_footage)",
    "signalstats": "light and colour measurement (inspect_footage)",
    "unsharp": "final sharpening (prepare_footage)",
    "afftdn": "noise reduction (process_audio)",
    "acompressor": "voice compression (process_audio)",
    "agate": "noise gate (process_audio)",
    "deesser": "sibilance (process_audio)",
    "alimiter": "loudness limiter (process_audio)",
    "ebur128": "loudness measurement (process_audio)",
    "asendcmd": "noise print (process_audio)",
}
ENCODERS = {"libx264": "H.264 video (every proxy and render)", "aac": "AAC audio"}

DISK_WARN_GB = 5.0   # a 4K batch writes proxies, a Chromium download and renders
DISK_BAD_GB = 1.5


def os_name() -> str:
    s = platform.system()
    return {"Windows": "windows", "Darwin": "macos"}.get(s, "linux")


def hint(kind: str) -> str:
    o = os_name()
    table = {
        "python": {"windows": "winget install Python.Python.3.12, then open a NEW terminal",
                   "macos": "brew install python", "linux": "sudo apt install python3 python3-venv"},
        "ffmpeg": {"windows": "winget install Gyan.FFmpeg (the full build), then open a NEW terminal",
                   "macos": "brew install ffmpeg",
                   "linux": "sudo apt install ffmpeg, or ./setup.sh --download-ffmpeg (static build with every filter, ~40 MB)"},
        "node": {"windows": "winget install OpenJS.NodeJS.LTS, then open a NEW terminal",
                 "macos": "brew install node", "linux": "install Node 20+ (nodejs.org or your package manager)"},
    }
    return table[kind][o]


def run(cmd: list[str], timeout: int = 20) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, errors="replace")
        return (r.stdout or "") + (r.stderr or "")
    except (OSError, subprocess.SubprocessError):
        return ""


def repo_path() -> Path | None:
    """Where setup.sh last ran from (it writes this file); None on a machine that never ran it."""
    try:
        p = Path((SHARE / "repo-path").read_text().strip())
    except OSError:
        return None
    return p if (p / "setup.sh").exists() else None


def setup_hint() -> str:
    repo = repo_path()
    if repo:
        return f"cd {repo} && ./setup.sh"
    return (f"get the kit: gh auth login --web && gh auth setup-git && git clone {REPO_URL}, "
            "then run its ./setup.sh (Windows: through Git Bash)")


def venv_python() -> str | None:
    for c in (os.environ.get("SVK_PYTHON"), str(KIT_PYTHON)):
        if c and Path(c).exists():
            return c
    return None


class Report:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def add(self, group: str, name: str, status: str, detail: str = "", fix: str = "") -> None:
        # status: ok | missing (required) | warn (optional or advisory)
        self.rows.append({"group": group, "name": name, "status": status, "detail": detail, "fix": fix})


def check_python(rep: Report) -> None:
    v = sys.version_info
    if v >= (3, 10):
        rep.add("python", "Python 3.10+", "ok", f"{v.major}.{v.minor}.{v.micro}")
    else:
        rep.add("python", "Python 3.10+", "missing", f"found {v.major}.{v.minor}", hint("python"))


def check_venv(rep: Report) -> None:
    vpy = venv_python()
    if not vpy:
        rep.add("venv", "kit virtualenv", "missing", f"not found at {KIT_PYTHON} and $SVK_PYTHON is unset",
                setup_hint())
        return
    for mod, pin in (("faster_whisper", "faster-whisper==1.2.1"), ("numpy", "numpy")):
        out = run([vpy, "-c", f"import {mod}; print(getattr({mod}, '__version__', 'ok'))"])
        if out.strip() and "Error" not in out:
            rep.add("venv", f"{pin.split('==')[0]} in the venv", "ok", out.strip().splitlines()[-1])
        else:
            rep.add("venv", f"{pin.split('==')[0]} in the venv", "missing", "import failed",
                    f"{vpy} -m pip install {pin}   (or {setup_hint()})")


def check_ffmpeg(rep: Report) -> None:
    ff, fp = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not (ff and fp):
        rep.add("ffmpeg", "ffmpeg and ffprobe on PATH", "missing", "not found", hint("ffmpeg"))
        return
    ver = (run([ff, "-version"]).splitlines() or ["?"])[0]
    rep.add("ffmpeg", "ffmpeg and ffprobe on PATH", "ok", ver[:70])
    m = re.search(r"version\s+n?(\d+)", ver)
    if m and int(m.group(1)) < 6:
        rep.add("ffmpeg", "ffmpeg 6 or newer", "warn", ver[:70],
                "older builds lack some filter options this kit uses; the kit was tested on 7.0")
    filters = run([ff, "-hide_banner", "-filters"])
    have = {ln.split()[1] for ln in filters.splitlines() if len(ln.split()) >= 2 and ln[:3].strip()}
    lacking = {f: why for f, why in FILTERS.items() if f not in have}
    if lacking:
        by_use: dict[str, list[str]] = {}
        for f, why in lacking.items():
            by_use.setdefault(why.split(" (")[0], []).append(f)
        for use, names in by_use.items():
            rep.add("ffmpeg", f"ffmpeg lacks {', '.join(names)}", "missing", f"needed for {use}",
                    "use a full ffmpeg build: " + hint("ffmpeg"))
    else:
        rep.add("ffmpeg", f"all {len(FILTERS)} filters the scripts call", "ok", "vidstab, zscale, haldclut, afftdn, ...")
    enc = run([ff, "-hide_banner", "-encoders"])
    for e, why in ENCODERS.items():
        if re.search(rf"\s{e}\s", enc):
            rep.add("ffmpeg", f"encoder {e}", "ok", why)
        else:
            rep.add("ffmpeg", f"encoder {e}", "missing", why, "use a full ffmpeg build: " + hint("ffmpeg"))


def check_model(rep: Report) -> None:
    f = MODEL_DIR / "faster-whisper-small" / "model.bin"
    if f.exists():
        rep.add("model", "Whisper model (captions)", "ok", f"{f.stat().st_size // 2**20} MB at {MODEL_DIR}")
    else:
        rep.add("model", "Whisper model (captions)", "missing", f"not at {MODEL_DIR}",
                f"{setup_hint()} downloads ~460 MB (ask the user first)")


def check_node(rep: Report) -> None:
    node = shutil.which("node")
    if not node:
        rep.add("node", "Node 20+ (rendering only)", "warn", "not found", hint("node"))
        return
    ver = run([node, "-v"]).strip()
    major = int(re.sub(r"\D.*", "", ver.lstrip("v")) or 0)
    if major >= 20:
        rep.add("node", "Node 20+ (rendering only)", "ok", ver)
    else:
        rep.add("node", "Node 20+ (rendering only)", "warn", f"{ver} is too old for Remotion 4", hint("node"))
    if major >= 22:
        rep.add("node", "Node 22+ (HyperFrames renderer, optional)", "ok", ver)
    else:
        rep.add("node", "Node 22+ (HyperFrames renderer, optional)", "warn", f"{ver}: HyperFrames needs Node 22 or newer; Remotion does not",
                hint("node"))
    if not shutil.which("npm"):
        rep.add("node", "npm", "warn", "not found", "comes with Node")


def check_key(rep: Report) -> None:
    if KEYFILE.exists() or os.environ.get("ELEVENLABS_API_KEY"):
        rep.add("key", "ElevenLabs key", "ok", "present (value not shown)")
    else:
        rep.add("key", "ElevenLabs key", "warn", "absent: only needed to synthesize a voice; a supplied voice works without it",
                "the USER runs ./setup.sh --set-key (typed hidden; never paste a key into a chat)")


def check_disk(rep: Report) -> None:
    for label, p in (("home", HOME), ("temp", Path(os.environ.get("TMPDIR") or "/tmp" if os.name != "nt" else os.environ.get("TEMP", ".")))):
        try:
            free = shutil.disk_usage(p).free / 2**30
        except OSError:
            continue
        msg = f"{free:.1f} GB free on {label} ({p})"
        if free < DISK_BAD_GB:
            rep.add("disk", f"free space on {label}", "warn", msg + ": 4K proxies and renders will fail",
                    "free space or point work folders at another drive (SVK_PYTHON, WHISPER_MODEL_DIR for the venv and model)")
        elif free < DISK_WARN_GB:
            rep.add("disk", f"free space on {label}", "warn", msg + ": enough for one video, not a batch", "")
        else:
            rep.add("disk", f"free space on {label}", "ok", msg)


GROUPS = {"python": check_python, "venv": check_venv, "ffmpeg": check_ffmpeg, "model": check_model,
          "node": check_node, "key": check_key, "disk": check_disk}


def main() -> int:
    ap = argparse.ArgumentParser(description="Check this machine against everything the skill needs.")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--only", choices=sorted(GROUPS), help="run one group of checks")
    a = ap.parse_args()
    rep = Report()
    for name, fn in GROUPS.items():
        if a.only in (None, name):
            fn(rep)
    missing = [r for r in rep.rows if r["status"] == "missing"]
    if a.json:
        print(json.dumps({"os": os_name(), "ok": not missing, "checks": rep.rows}, indent=2, ensure_ascii=False))
        return 1 if missing else 0
    mark = {"ok": "✓", "missing": "✗", "warn": "!"}
    print(f"short-video-kit doctor ({os_name()}, Python {platform.python_version()})")
    for r in rep.rows:
        line = f"  {mark[r['status']]} {r['name']}" + (f"  ({r['detail']})" if r["detail"] else "")
        print(line)
        if r["status"] != "ok" and r["fix"]:
            print(f"      -> {r['fix']}")
    n_warn = sum(r["status"] == "warn" for r in rep.rows)
    if missing:
        print(f"\n{len(missing)} required item(s) missing. Fix them, ask before any download, then re-run.")
        return 1
    print("\nEverything required is in place" + (f" ({n_warn} optional note(s) above)." if n_warn else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
