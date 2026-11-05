#!/usr/bin/env bash
# Verify the kit works on this machine. Spends no ElevenLabs credits.
#   ./selftest.sh
set -uo pipefail
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
S="$KIT/skill/short-video-editing/scripts"
# Prefer the kit's venv (setup.sh), then any working Python 3. On Windows "python3" may be the
# Microsoft Store stub, so every candidate is test-run.
PY=""; VENV="$HOME/.local/share/short-video-kit/venv"
for cand in "${SVK_PYTHON:-}" "$VENV/bin/python" "$VENV/Scripts/python.exe" python3 python; do
  if [[ -n "$cand" ]] && "$cand" -c 'import sys' >/dev/null 2>&1; then PY="$cand"; break; fi
done
[[ -n "$PY" ]] || { echo "No working Python found; run ./setup.sh first." >&2; exit 1; }
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
FAIL=0
pass() { printf '  \033[32mPASS\033[0m  %s\n' "$*"; }
fail() { printf '  \033[31mFAIL\033[0m  %s\n' "$*"; FAIL=$((FAIL+1)); }
skip() { printf '  \033[33mSKIP\033[0m  %s\n' "$*"; }

echo "1. tools"
ffmpeg -version >/dev/null 2>&1 && pass "ffmpeg runs" || fail "ffmpeg not runnable"
ffprobe -version >/dev/null 2>&1 && pass "ffprobe runs" || fail "ffprobe not runnable"

echo "2. inspect_footage.py reads a real clip"
ffmpeg -loglevel error -y -f lavfi -i testsrc=size=1080x1920:rate=30 -f lavfi -i sine=frequency=440 \
  -t 3 -pix_fmt yuv420p "$TMP/clip.mp4" 2>/dev/null
OUT=$("$PY" "$S/inspect_footage.py" "$TMP/clip.mp4" 2>&1)
echo "$OUT" | grep -q "1080x1920" && echo "$OUT" | grep -q "vertical" \
  && pass "reported 1080x1920 vertical" || { fail "inspect_footage output wrong"; echo "$OUT" | sed 's/^/        /'; }

echo "3. pacing_checker.py"
"$PY" "$S/pacing_checker.py" "$KIT/samples/example-edit-plan.md" >/dev/null 2>&1 \
  && pass "example plan passes the hard rules" || fail "pacing_checker rejected the example plan"
printf '| # | Start | End | Type |\n|---|---|---|---|\n| 1 | 0.0 | 6.5 | HOOK |\n' > "$TMP/bad.md"
"$PY" "$S/pacing_checker.py" "$TMP/bad.md" >/dev/null 2>&1 \
  && fail "a 6.5s hook scene was NOT rejected" || pass "a 6.5s opening scene is rejected"

echo "4. align_captions.py (Whisper timing, script spelling)"
if "$PY" "$S/align_captions.py" "$KIT/samples/line_00.mp3" --script "$KIT/samples/line_00.txt" \
     --out "$TMP/c.srt" >"$TMP/align.log" 2>&1; then
  grep -q "túi xách" "$TMP/c.srt" && pass "caption keeps the script's spelling: 'túi xách'" \
    || fail "caption lost the script spelling (Whisper's misheard text leaked through)"
  N=$(grep -cE -- '-->' "$TMP/c.srt"); [[ $N -ge 5 ]] && pass "$N caption groups written" || fail "only $N caption groups"
else
  fail "align_captions failed"; tail -4 "$TMP/align.log" | sed 's/^/        /'
fi

echo "5. make_voiceover.py (read-only, no credits)"
"$PY" "$S/make_voiceover.py" --quota >"$TMP/q.log" 2>&1; RC=$?
if [[ $RC -eq 0 ]]; then
  pass "ElevenLabs accepted the key and returned the plan"; sed 's/^/        /' "$TMP/q.log" | head -3
elif grep -q "invalid" "$TMP/q.log"; then
  fail "a key is installed but ElevenLabs REJECTS it — re-enter with ./setup.sh --set-key"
elif grep -q "not found" "$TMP/q.log"; then
  skip "no key installed yet (run ./setup.sh --set-key)"
else
  skip "key could not be verified (offline, or it cannot read the plan)"; sed 's/^/        /' "$TMP/q.log" | head -2
fi

echo "6. plan_to_project.py compiles a plan into project.json"
if "$PY" "$S/plan_to_project.py" "$KIT/samples/example-edit-plan.md" --out "$TMP/project.json" \
     --auto-camera >"$TMP/p2p.log" 2>&1 \
   && "$PY" -c "import json,sys; p=json.load(open(sys.argv[1],encoding='utf-8')); \
sys.exit(0 if len(p['scenes'])==11 and len(p['overlays'])==9 and all('camera' in s for s in p['scenes']) else 1)" "$TMP/project.json"; then
  pass "11 scenes, 9 overlays, every scene has a camera move"
else
  fail "plan_to_project output wrong"; tail -4 "$TMP/p2p.log" | sed 's/^/        /'
fi

echo "7. footage_overlap_checker.py"
"$PY" "$S/footage_overlap_checker.py" "$KIT/samples/example-edit-plan.md" >/dev/null 2>&1 \
  && pass "example plan reuses no footage" || fail "example plan reported as reusing footage"
printf '| # | Start | End | Source | In |\n|---|---|---|---|---|\n| 1 | 0 | 3 | a.mp4 | 1.0 |\n| 2 | 3 | 6 | a.mp4 | 2.0 |\n' > "$TMP/dup.md"
"$PY" "$S/footage_overlap_checker.py" "$TMP/dup.md" >/dev/null 2>&1 \
  && fail "a reused range was NOT caught" || pass "a reused range is caught"

echo
[[ $FAIL -eq 0 ]] && printf '\033[1;32mAll checks passed.\033[0m\n' || { printf '\033[1;31m%d check(s) failed.\033[0m\n' "$FAIL"; exit 1; }
