#!/usr/bin/env bash
# Set up short-video-kit on this machine. Safe to run more than once.
#
#   ./setup.sh --check            report what is installed and what is missing, change nothing
#   ./setup.sh                    full setup
#   ./setup.sh --download-ffmpeg  also fetch a static ffmpeg if none is installed (Linux, ~40 MB)
#   ./setup.sh --no-model         skip the Whisper model (it then downloads on first use)
#   ./setup.sh --no-skill         do not install the skill into ~/.claude/skills
#   ./setup.sh --set-key          type the ElevenLabs key (hidden) and store it, then exit
#   ./setup.sh --package          build dist/short-video-editing.skill (for the Claude desktop app), then exit
#
# Works in bash on macOS, Linux and Windows (Git Bash): the venv's bin/ or Scripts/ is detected.
#
# Everything lands under $HOME (venv, key, model, skill), never in this folder, so the folder can
# be moved or deleted afterwards without breaking the install. Override HOME for a trial run:
#   HOME=/tmp/trial ./setup.sh
set -euo pipefail

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARE="$HOME/.local/share/short-video-kit"
VENV="$SHARE/venv"
MODEL_DIR="${WHISPER_MODEL_DIR:-$HOME/.cache/short-video-kit/models}"   # same override align_captions.py reads
KEYDIR="$HOME/.config/short-video-kit"; KEYFILE="$KEYDIR/env"

INSTALL_SKILL=1; GET_MODEL=1; GET_FFMPEG=0; SET_KEY=0; PACKAGE=0; CHECK=0
for a in "$@"; do
  case "$a" in
    --check) CHECK=1 ;;
    --no-skill) INSTALL_SKILL=0 ;;
    --no-model) GET_MODEL=0 ;;
    --download-ffmpeg) GET_FFMPEG=1 ;;
    --set-key) SET_KEY=1 ;;
    --package) PACKAGE=1 ;;
    -h|--help) sed -n '2,/^set -euo/{/^set -euo/!p}' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $a (try --help)" >&2; exit 2 ;;
  esac
done

ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; }
bad()  { printf '  \033[31m✗\033[0m %s\n' "$*"; }
step() { printf '\n\033[1m%s\033[0m\n' "$*"; }
PROBLEMS=0

# ------------------------------------------------------------------ --set-key (and exit)
if [[ $SET_KEY -eq 1 ]]; then
  [[ -t 0 ]] || { echo "--set-key needs an interactive terminal (the key is typed hidden)." >&2; exit 1; }
  read -rsp "ElevenLabs API key (hidden, nothing is echoed): " k; echo
  [[ -n "$k" ]] || { echo "empty — nothing saved." >&2; exit 1; }
  mkdir -p "$KEYDIR"; chmod 700 "$KEYDIR"
  ( umask 077; printf 'ELEVENLABS_API_KEY=%s\n' "$k" > "$KEYFILE" )
  chmod 600 "$KEYFILE"; unset k
  echo "Saved to $KEYFILE (mode 600). Check it with:  python3 skill/short-video-editing/scripts/make_voiceover.py --quota"
  exit 0
fi

# A real Python 3 (on Windows "python3" can be the Microsoft Store stub, which fails to run).
PY=""; for cand in python3 python; do
  if command -v "$cand" >/dev/null 2>&1 && "$cand" -c 'import sys' >/dev/null 2>&1; then PY="$cand"; break; fi
done

# ------------------------------------------------------------------ --check (and exit)
# Honours the same overrides the scripts do: SVK_PYTHON (venv python) and WHISPER_MODEL_DIR.
if [[ $CHECK -eq 1 ]]; then
  VPY=""; for cand in "${SVK_PYTHON:-}" "$VENV/bin/python" "$VENV/Scripts/python.exe"; do
    if [[ -n "$cand" && -x "$cand" ]]; then VPY="$cand"; break; fi
  done
  py_ok()     { [[ -n "$PY" ]] && "$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)'; }
  venv_ok()   { [[ -n "$VPY" ]] && "$VPY" -c 'import faster_whisper'; }
  ffmpeg_ok() { command -v ffmpeg && command -v ffprobe; }
  model_ok()  { [[ -f "$MODEL_DIR/faster-whisper-small/model.bin" ]]; }
  node_ok()   { command -v node && [[ "$(node -v | sed 's/^v//; s/\..*//')" -ge 20 ]]; }
  skill_ok()  { diff -rq -x evals -x __pycache__ "$KIT/skill/short-video-editing" "$HOME/.claude/skills/short-video-editing"; }
  MISSING=0
  chk() { local label="$1" hint="$2"; shift 2
    if "$@" >/dev/null 2>&1; then ok "$label"; else bad "$label  ->  $hint"; MISSING=$((MISSING+1)); fi; }
  step "short-video-kit on this machine (nothing is changed)"
  chk "Python 3.10+"                        "install Python 3.10+ (Windows: winget install Python.Python.3.12)" py_ok
  chk "kit venv with faster-whisper"        "run ./setup.sh" venv_ok
  chk "ffmpeg and ffprobe on PATH"          "macOS: brew install ffmpeg | Ubuntu: sudo apt install ffmpeg | Windows: winget install Gyan.FFmpeg, then open a NEW terminal" ffmpeg_ok
  chk "Whisper model"                       "run ./setup.sh (downloads ~460 MB: ask the user first)" model_ok
  chk "Node 20+ (rendering only)"           "install Node 20+ (Windows: winget install OpenJS.NodeJS.LTS, then open a NEW terminal)" node_ok
  chk "skill installed and identical to this repo" "run ./setup.sh (after every git pull), then start a NEW Claude Code session" skill_ok
  if [[ -f "$KEYFILE" || -n "${ELEVENLABS_API_KEY:-}" ]]; then ok "ElevenLabs key present (value not shown)"
  elif [[ -f "$KIT/.env.local" ]] && grep -q '^ELEVENLABS_API_KEY=.\+' "$KIT/.env.local"; then
    ok "ElevenLabs key found in .env.local (value not shown; ./setup.sh installs it for every folder)"
  else warn "no ElevenLabs key. Optional: only needed to synthesize a voice; a supplied voice works without it. ./setup.sh --set-key"; fi
  echo
  if [[ $MISSING -eq 0 ]]; then printf '\033[1mEverything required is in place.\033[0m Verify with ./selftest.sh\n'; exit 0; fi
  printf '\033[1;33m%d item(s) missing.\033[0m Run ./setup.sh (it fixes what it can and says what it cannot).\n' "$MISSING"; exit 1
fi

# ------------------------------------------------------------------ --package (and exit)
if [[ $PACKAGE -eq 1 ]]; then
  [[ -n "$PY" ]] || { echo "python not found" >&2; exit 1; }
  mkdir -p "$KIT/dist"
  "$PY" - "$KIT/skill/short-video-editing" "$KIT/dist/short-video-editing.skill" << 'PY'
import sys, zipfile, pathlib
src, out = pathlib.Path(sys.argv[1]), sys.argv[2]
skip = {"evals", "__pycache__", "node_modules"}
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(src.rglob("*")):
        rel = p.relative_to(src.parent)
        if p.is_file() and not skip.intersection(rel.parts):
            z.write(p, rel.as_posix())
print(f"wrote {out}")
PY
  exit 0
fi

# ------------------------------------------------------------------ 1. Python + venv
step "1/6  Python environment"
[[ -n "$PY" ]] || { bad "Python not found. Install Python 3.10 or newer (Windows: winget install Python.Python.3.12, then open a NEW terminal)."; exit 1; }
PYV=$("$PY" -c 'import sys; print("%d.%d" % sys.version_info[:2])')
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' \
  && ok "$PY $PYV" || { bad "$PY $PYV is too old (need 3.10+)"; exit 1; }
vbin() { if [[ -d "$VENV/Scripts" ]]; then echo "$VENV/Scripts"; else echo "$VENV/bin"; fi; }
if [[ ! -d "$VENV" ]]; then
  mkdir -p "$SHARE"; "$PY" -m venv "$VENV" && ok "created venv at $VENV" \
    || { bad "could not create a venv (on Debian/Ubuntu: sudo apt install python3-venv)"; exit 1; }
else ok "venv already exists"; fi
VBIN="$(vbin)"
"$VBIN/python" -m pip install --quiet --upgrade pip >/dev/null 2>&1 || true
if "$VBIN/python" -m pip install --quiet -r "$KIT/requirements.txt"; then
  ok "installed $(grep -v '^#' "$KIT/requirements.txt" | grep -v '^$' | tr '\n' ' ')"
else bad "pip install failed (needs internet)"; PROBLEMS=$((PROBLEMS+1)); fi

# ------------------------------------------------------------------ 2. ffmpeg / ffprobe
download_ffmpeg() {
  local arch base dest tmp want got
  case "$(uname -s)-$(uname -m)" in
    Linux-x86_64) arch=amd64 ;;
    Linux-aarch64|Linux-arm64) arch=arm64 ;;
    *) bad "no static build for $(uname -sm). macOS: brew install ffmpeg"; return 1 ;;
  esac
  command -v xz >/dev/null || { bad "need 'xz' to unpack (sudo apt install xz-utils)"; return 1; }
  base="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-$arch-static.tar.xz"
  dest="$SHARE/bin"; tmp="$(mktemp -d)"; mkdir -p "$dest"
  echo "      downloading $base"
  # A progress bar is only useful on a terminal. Captured by a script or by Claude it becomes
  # thousands of characters of noise, so fall back to quiet mode (errors still show).
  local quiet=-sS; [[ -t 1 ]] && quiet=--progress-bar
  curl -fL --retry 3 $quiet -o "$tmp/ff.tar.xz" "$base" || { bad "download failed"; rm -rf "$tmp"; return 1; }
  if curl -fsSL -o "$tmp/ff.md5" "$base.md5"; then
    want=$(cut -d' ' -f1 "$tmp/ff.md5"); got=$(md5sum "$tmp/ff.tar.xz" | cut -d' ' -f1)
    [[ "$want" == "$got" ]] || { bad "checksum mismatch (expected $want, got $got) — not installed"; rm -rf "$tmp"; return 1; }
    ok "checksum matches the one published alongside the file"
  else warn "no checksum published to compare against"; fi
  tar -xJf "$tmp/ff.tar.xz" -C "$tmp" --strip-components=1
  install -m 755 "$tmp/ffmpeg" "$tmp/ffprobe" "$dest/"
  mkdir -p "$HOME/.local/bin"
  ln -sf "$dest/ffmpeg" "$HOME/.local/bin/ffmpeg"; ln -sf "$dest/ffprobe" "$HOME/.local/bin/ffprobe"
  rm -rf "$tmp"; ok "installed ffmpeg + ffprobe to $dest, linked into ~/.local/bin"
}

step "2/6  ffmpeg and ffprobe"
missing=0; for t in ffmpeg ffprobe; do command -v "$t" >/dev/null 2>&1 && ok "$t on PATH" || missing=1; done
if [[ $missing -eq 1 ]]; then
  if [[ -x "$KIT/bin/ffmpeg" ]] && "$KIT/bin/ffmpeg" -version >/dev/null 2>&1; then
    mkdir -p "$HOME/.local/bin"
    ln -sf "$KIT/bin/ffmpeg" "$HOME/.local/bin/ffmpeg"; ln -sf "$KIT/bin/ffprobe" "$HOME/.local/bin/ffprobe"
    ok "linked the bundled static ffmpeg (keep this folder in place)"
  elif [[ $GET_FFMPEG -eq 1 ]]; then
    download_ffmpeg || PROBLEMS=$((PROBLEMS+1))
  else
    bad "ffmpeg/ffprobe not found."
    echo "      macOS:   brew install ffmpeg"
    echo "      Ubuntu:  sudo apt install ffmpeg"
    echo "      Windows: winget install Gyan.FFmpeg   (then open a NEW terminal so PATH updates)"
    echo "      No sudo: ./setup.sh --download-ffmpeg   (static build from johnvansickle.com, ~40 MB)"
    PROBLEMS=$((PROBLEMS+1))
  fi
  case ":$PATH:" in *":$HOME/.local/bin:"*) ;; *)
    warn "~/.local/bin is not on PATH. Add:  export PATH=\"\$HOME/.local/bin:\$PATH\"" ;; esac
fi

# ------------------------------------------------------------------ 3. Whisper model
step "3/6  Whisper model"
if [[ -f "$MODEL_DIR/faster-whisper-small/model.bin" ]]; then
  ok "model already present"
elif [[ -f "$KIT/models/faster-whisper-small/model.bin" ]]; then
  mkdir -p "$(dirname "$MODEL_DIR")"; ln -sfn "$KIT/models" "$MODEL_DIR"
  ok "linked bundled model (works offline; keep this folder in place)"
elif [[ $GET_MODEL -eq 0 ]]; then
  warn "skipped (--no-model); it will download the first time captions are aligned"
else
  echo "      downloading Systran/faster-whisper-small from Hugging Face (~460 MB)…"
  [[ -t 1 ]] || export HF_HUB_DISABLE_PROGRESS_BARS=1   # same reason as the curl bar above
  if "$VBIN/python" - "$MODEL_DIR/faster-whisper-small" << 'PY'
import sys
from huggingface_hub import snapshot_download
snapshot_download("Systran/faster-whisper-small", local_dir=sys.argv[1],
                  allow_patterns=["*.json", "*.txt", "model.bin"])
PY
  then
    [[ -f "$MODEL_DIR/faster-whisper-small/model.bin" ]] && ok "model downloaded to $MODEL_DIR" \
      || { bad "download finished but model.bin is missing"; PROBLEMS=$((PROBLEMS+1)); }
  else bad "model download failed (needs internet)"; PROBLEMS=$((PROBLEMS+1)); fi
fi

# ------------------------------------------------------------------ 4. ElevenLabs key
step "4/6  ElevenLabs key"
if [[ -f "$KEYFILE" ]]; then ok "key already installed at $KEYFILE"
elif [[ -f "$KIT/.env.local" ]] && grep -q '^ELEVENLABS_API_KEY=.\+' "$KIT/.env.local"; then
  mkdir -p "$KEYDIR"; chmod 700 "$KEYDIR"; install -m 600 "$KIT/.env.local" "$KEYFILE"
  ok "installed key from .env.local to $KEYFILE (mode 600; value not printed)"
else
  warn "no key yet. Run  ./setup.sh --set-key  in a terminal (typed hidden; never paste a key into a chat)"
fi

# ------------------------------------------------------------------ 5. Node (Remotion)
step "5/6  Node.js (needed only for Remotion rendering)"
if command -v node >/dev/null; then
  NV=$(node -v | sed 's/^v//'); [[ ${NV%%.*} -ge 20 ]] && ok "node $NV" || warn "node $NV is older than 20; the render template needs 20.19+"
else warn "node not found. Install Node 20+ before rendering (Windows: winget install OpenJS.NodeJS.LTS)."; fi

# ------------------------------------------------------------------ 6. Skill
step "6/6  Claude skill"
if [[ $INSTALL_SKILL -eq 1 ]]; then
  DEST="$HOME/.claude/skills/short-video-editing"
  mkdir -p "$HOME/.claude/skills"; rm -rf "$DEST"
  cp -r "$KIT/skill/short-video-editing" "$DEST"; rm -rf "$DEST/evals"
  ok "installed to $DEST"
  echo "      Start a NEW Claude Code session so it loads the skill."
  echo "      Claude desktop app: ./setup.sh --package, then open dist/short-video-editing.skill and click Save skill."
else warn "skipped (--no-skill)"; fi

echo
if [[ $PROBLEMS -eq 0 ]]; then printf '\033[1mSetup finished.\033[0m Next:  ./selftest.sh\n'
else printf '\033[1;33mSetup finished with %d problem(s) above.\033[0m Fix them, then re-run.\n' "$PROBLEMS"; exit 1; fi
