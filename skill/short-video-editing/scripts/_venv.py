"""Shared by the scripts that need numpy (and sometimes onnxruntime): re-run under the kit's virtualenv when this Python lacks them.

Skill docs say `python scripts/foo.py`, which on a fresh machine means the system Python. `ensure_venv()` finds the venv setup.sh
created (or $SVK_PYTHON) and hands over to it, like `align_captions.py` does for faster-whisper. Not a script: nothing to run here.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

KIT_PYTHON = Path.home() / ".local" / "share" / "short-video-kit" / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def ensure_venv(*modules: str) -> None:
    mods = modules or ("numpy",)
    try:
        for m in mods:
            __import__(m)
        return
    except ImportError:
        pass
    # a venv's python is a symlink to the system python, so a marker (not a path comparison) stops an exec loop
    if not os.environ.get("SVK_REEXEC"):
        for candidate in (os.environ.get("SVK_PYTHON"), str(KIT_PYTHON)):
            if candidate and Path(candidate).exists():
                os.environ["SVK_REEXEC"] = "1"
                os.execv(candidate, [candidate] + sys.argv)
    sys.exit(f"{', '.join(mods)} not installed for this Python. Run the kit's setup.sh (it builds the venv), or set SVK_PYTHON to the venv's python, "
             f"or `pip install {' '.join(mods)}`.")
