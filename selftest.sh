#!/usr/bin/env bash
# Verify the kit works on this machine. Spends no ElevenLabs credits.
#   ./selftest.sh                  groups 1-11 (a few seconds each; group 4 loads the Whisper model)
#   ./selftest.sh --render [DIR]   also group 12: typecheck the Remotion template and render one still in
#                                  DIR (default: a temp folder). Without node_modules in DIR this runs
#                                  npm install, which downloads packages and Chromium (~300 MB): ask first.
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
RENDER=0; RENDER_DIR="$TMP/render"
if [[ "${1:-}" == "--render" ]]; then RENDER=1; RENDER_DIR="${2:-$TMP/render}"; fi
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
sys.exit(0 if len(p['scenes'])==11 and len(p['overlays'])==11 and all('camera' in s for s in p['scenes']) \
  and any(o['component']=='compare' and o['props']['before']['clip']=='CLIP_05' for o in p['overlays']) \
  and any(o['component']=='thumbs' and o['props']['cards'][0]['focus']==[0.3,0.4] and o['props']['cards'][1]['delay']==1.2 for o in p['overlays']) else 1)" "$TMP/project.json"; then
  pass "11 scenes, 11 overlays (a before/after compare, a framed three-photo strip), every scene has a camera move"
else
  fail "plan_to_project output wrong"; tail -4 "$TMP/p2p.log" | sed 's/^/        /'
fi

echo "7. footage_overlap_checker.py"
"$PY" "$S/footage_overlap_checker.py" "$KIT/samples/example-edit-plan.md" >/dev/null 2>&1 \
  && pass "example plan reuses no footage" || fail "example plan reported as reusing footage"
printf '| # | Start | End | Source | In |\n|---|---|---|---|---|\n| 1 | 0 | 3 | a.mp4 | 1.0 |\n| 2 | 3 | 6 | a.mp4 | 2.0 |\n' > "$TMP/dup.md"
"$PY" "$S/footage_overlap_checker.py" "$TMP/dup.md" >/dev/null 2>&1 \
  && fail "a reused range was NOT caught" || pass "a reused range is caught"

echo "8. trim_voice.py finds a pause and cuts there"
ffmpeg -loglevel error -y -f lavfi -i "aevalsrc=exprs='if(between(t,1,2),0,sin(2*PI*440*t))':d=3:s=44100" "$TMP/v.mp3" 2>/dev/null
"$PY" "$S/trim_voice.py" "$TMP/v.mp3" --silences 2>&1 | grep -q "cut at 1.5" \
  && pass "the 1 s pause is found, midpoint 1.5 s" || fail "trim_voice --silences missed the pause"
"$PY" "$S/trim_voice.py" "$TMP/v.mp3" --keep 0-1,2-3 --out "$TMP/k.mp3" 2>&1 | grep -Eq "wrote .*: (1\.9|2\.0|2\.1)[0-9]*s" \
  && pass "keeping 0-1 and 2-3 gives a ~2 s file" || fail "trim_voice --keep produced the wrong length"

echo "9. contact_sheet.py"
printf '{"scenes":[{"start":0,"end":1.5},{"start":1.5,"end":3.0}]}' > "$TMP/mini.json"
"$PY" "$S/contact_sheet.py" "$TMP/clip.mp4" --project "$TMP/mini.json" --out "$TMP/sheet.png" 2>&1 | grep -q "3 frames" \
  && [[ -s "$TMP/sheet.png" ]] && pass "3 frames (2 scene middles + 1 cut) tiled into a PNG" || fail "contact_sheet produced no sheet"
mkdir "$TMP/clips" && cp "$TMP/clip.mp4" "$TMP/clips/"
"$PY" "$S/contact_sheet.py" "$TMP/clips" --out "$TMP/clips.png" 2>&1 | grep -q "1 clip(s)" \
  && [[ -s "$TMP/clips.png" ]] && pass "a folder of raw clips becomes one row per clip" || fail "folder mode produced no sheet"

echo "10. new_remotion_project.py scaffolds a render project"
"$PY" "$S/new_remotion_project.py" "$TMP/render" >/dev/null 2>&1
if [[ -f "$TMP/render/package.json" && -f "$TMP/render/src/index.ts" && -d "$TMP/render/public/clips" ]]; then
  pass "template copied, public/clips and public/audio ready"
  echo "// local edit" >> "$TMP/render/src/theme.ts"; echo keep > "$TMP/render/public/clips/mine.txt"
  "$PY" "$S/new_remotion_project.py" "$TMP/render" --update >/dev/null 2>&1
  ! grep -q "local edit" "$TMP/render/src/theme.ts" && [[ -f "$TMP/render/public/clips/mine.txt" ]] \
    && pass "--update restores the template files and keeps public/" || fail "--update did not behave"
  "$PY" "$S/plan_to_project.py" "$KIT/samples/example-edit-plan.md" --out "$TMP/render/project.json" \
    --voice audio/none.mp3 2>&1 | grep -q "not in .*clips/" \
    && pass "plan_to_project reports clips and voice missing from public/" || fail "missing assets were not reported"
  [[ $(ls "$TMP/render/public/sfx"/*.wav 2>/dev/null | wc -l) -eq 11 ]] \
    && pass "11 sound effects installed in public/sfx" || fail "public/sfx is incomplete"
else fail "scaffold incomplete"; fi

echo "11. sound effects: make_sfx.py and plan_to_project.py --auto-sfx"
"$PY" "$S/make_sfx.py" "$TMP/sfx" >"$TMP/sfx.log" 2>&1 && [[ $(ls "$TMP/sfx"/*.wav | wc -l) -eq 6 ]] \
  && pass "6 sounds synthesized with ffmpeg" || { fail "make_sfx failed"; tail -3 "$TMP/sfx.log" | sed 's/^/        /'; }
if "$PY" "$S/plan_to_project.py" "$KIT/samples/example-edit-plan.md" --out "$TMP/sfx.json" --auto-sfx >/dev/null 2>&1 \
   && "$PY" -c "
import json, sys, pathlib
cues = json.load(open(sys.argv[1], encoding='utf-8'))['sfx']
have = {p.stem for p in pathlib.Path(sys.argv[2]).glob('*.wav')} | {p.stem for p in pathlib.Path(sys.argv[3]).glob('*.wav')}
ok = cues and all(pathlib.PurePosixPath(c['src']).stem in have and c['at'] >= 0 for c in cues)
sys.exit(0 if ok else 1)" "$TMP/sfx.json" "$KIT/skill/short-video-editing/assets/sfx" "$TMP/sfx"; then
  pass "automatic cues exist and every one names a sound in the bank"
else fail "--auto-sfx produced no cues, or a cue names a missing sound"; fi

if [[ $RENDER -eq 1 ]]; then
  echo "12. Remotion render (--render)"
  command -v node >/dev/null 2>&1 || fail "node not found (need 20+)"
  [[ -f "$RENDER_DIR/package.json" ]] || "$PY" "$S/new_remotion_project.py" "$RENDER_DIR" >/dev/null 2>&1
  if (cd "$RENDER_DIR" && { [[ -d node_modules ]] || npm install --no-audit --no-fund; } && npm run typecheck) >"$TMP/tsc.log" 2>&1; then
    pass "dependencies in place and the template typechecks"
  else fail "npm install / typecheck failed"; tail -5 "$TMP/tsc.log" | sed 's/^/        /'; fi
  if (cd "$RENDER_DIR" && npx remotion still src/index.ts Short "$TMP/still.png" --frame=30) >"$TMP/still.log" 2>&1 \
     && [[ -s "$TMP/still.png" ]]; then pass "rendered a still of the example project"
  else fail "remotion still failed"; tail -5 "$TMP/still.log" | sed 's/^/        /'; fi
fi

echo
[[ $FAIL -eq 0 ]] && printf '\033[1;32mAll checks passed.\033[0m\n' || { printf '\033[1;31m%d check(s) failed.\033[0m\n' "$FAIL"; exit 1; }
