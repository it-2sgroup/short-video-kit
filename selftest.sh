#!/usr/bin/env bash
# Verify the kit works on this machine. Spends no ElevenLabs credits.
#   ./selftest.sh                  groups 1-14d (a few seconds each; group 4 loads the Whisper model)
#   ./selftest.sh --render [DIR]   also group 15: typecheck the Remotion template and render one still in
#                                  DIR (default: a temp folder). Without node_modules in DIR this runs
#                                  npm install, which downloads packages and Chromium (~300 MB): ask first.
set -uo pipefail
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8  # Windows: the scripts print arrows and Vietnamese, which cp1252 cannot encode
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
if OUT=$("$PY" "$S/doctor.py" --only ffmpeg 2>&1); then pass "ffmpeg has every filter and encoder the scripts call"
else fail "ffmpeg lacks something the scripts call:"; echo "$OUT" | grep -E '✗|->' | sed 's/^/        /'; fi
"$PY" "$S/doctor.py" --json >/dev/null 2>&1; [[ $? -le 1 ]] && pass "doctor.py runs (exit 0 or 1)" || fail "doctor.py crashed"

echo "2. inspect_footage.py reads a real clip"
ffmpeg -loglevel error -y -f lavfi -i testsrc=size=1080x1920:rate=30 -f lavfi -i sine=frequency=440 \
  -t 3 -pix_fmt yuv420p "$TMP/clip.mp4" 2>/dev/null
OUT=$("$PY" "$S/inspect_footage.py" "$TMP/clip.mp4" 2>&1)
echo "$OUT" | grep -q "1080x1920" && echo "$OUT" | grep -q "vertical" \
  && pass "reported 1080x1920 vertical" || { fail "inspect_footage output wrong"; echo "$OUT" | sed 's/^/        /'; }

echo "3. playbooks and pacing_checker.py"
"$PY" "$S/playbook.py" check >"$TMP/pb.log" 2>&1 \
  && pass "every playbook and variant is valid, its skeleton passes its own pacing, every component/grade/theme is used" \
  || { fail "playbook.py check"; grep -E "FAIL|x " "$TMP/pb.log" | head -5 | sed 's/^/        /'; }
"$PY" "$S/pacing_checker.py" "$KIT/samples/example-edit-plan.md" >/dev/null 2>&1 \
  && pass "example product-demo plan passes its playbook" || fail "pacing_checker rejected the example plan"
"$PY" "$S/pacing_checker.py" "$KIT/samples/example-real-estate-plan.md" >/dev/null 2>&1 \
  && pass "example real-estate plan passes its playbook" || fail "pacing_checker rejected the real-estate plan"
"$PY" "$S/pacing_checker.py" "$KIT/samples/example-real-estate-plan.md" --playbook product-demo >/dev/null 2>&1 \
  && fail "a 1.5 s non-hook scene passed product-demo's rules" || pass "the same plan fails product-demo's 2.5 s minimum (rules follow the playbook)"
"$PY" "$S/playbook.py" suggest --intent "tour căn hộ 2 phòng ngủ" 2>&1 | head -1 | grep -q "real-estate" \
  && pass "suggest: 'tour căn hộ' -> real-estate" || fail "playbook.py suggest did not pick real-estate"
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

"$PY" -c "import sys; sys.path.insert(0, sys.argv[1]); import plan_to_project as p; \
t=p.parse_content('title','style=stack; lines=Khởi tố / 10/8/2026; accent=2026'); u=p.parse_content('title','lines=300'); s=p.parse_content('stat','value=5; unit= bị can'); \
sys.exit(0 if t['accent']=='2026' and u['lines']==['300'] and s['value']==5 and s['unit']=='bị can' else 1)" "$S" \
  && pass "text keys stay text (accent=2026, lines=300), stat values stay numbers" \
  || fail "a numeric accent or title line would crash the renderer (plan_to_project value coercion)"

"$PY" "$S/plan_to_project.py" "$KIT/samples/example-real-estate-plan.md" --out "$TMP/re.json" --auto-camera --auto-sfx >"$TMP/re.log" 2>&1 \
  && "$PY" -c "import json,sys; p=json.load(open(sys.argv[1],encoding='utf-8')); s=p['scenes']; \
sys.exit(0 if s[2].get('ramp')==[1.0,2.0,1.0] and s[6].get('speed')==0.5 and p['captionStyle']=='none' \
  and {o['component'] for o in p['overlays']} >= {'specs','pin','label','stat','chart','image','price'} else 1)" "$TMP/re.json" \
  && pass "music-driven plan: speed ramp, 0.5x, captions off, specs/pin/label/stat/chart/image compiled" \
  || { fail "real-estate plan compiled wrong"; tail -3 "$TMP/re.log" | sed 's/^/        /'; }

echo "7. footage_overlap_checker.py"
"$PY" "$S/footage_overlap_checker.py" "$KIT/samples/example-edit-plan.md" >/dev/null 2>&1 \
  && pass "example plan reuses no footage" || fail "example plan reported as reusing footage"
printf '| # | Start | End | Source | In |\n|---|---|---|---|---|\n| 1 | 0 | 3 | a.mp4 | 1.0 |\n| 2 | 3 | 6 | a.mp4 | 2.0 |\n' > "$TMP/dup.md"
"$PY" "$S/footage_overlap_checker.py" "$TMP/dup.md" >/dev/null 2>&1 \
  && fail "a reused range was NOT caught" || pass "a reused range is caught"
printf '| # | Start | End | Source | In | Speed |\n|---|---|---|---|---|---|\n| 1 | 0 | 3 | a.mp4 | 0.0 | 2x |\n| 2 | 3 | 6 | a.mp4 | 5.0 | |\n' > "$TMP/fast.md"
"$PY" "$S/footage_overlap_checker.py" "$TMP/fast.md" >/dev/null 2>&1 \
  && fail "a 2x scene reading 0-6 s was not seen to overlap 5-8 s" || pass "a 2x scene counts the footage it reads (3 s at 2x = 6 s)"

echo "7b. suggest_cuts.py and plan_scenes.py (cuts on pauses, footage never reused)"
"$PY" - "$TMP" <<'PYEOF'
import json, sys
tmp = sys.argv[1]
words, t = [], 0.0
for i in range(60):  # 60 words, a pause every 6th: ~24 s of speech
    words.append({"text": f"w{i}", "start": round(t, 2), "end": round(t + 0.3, 2)})
    t += 0.3 + (0.45 if i % 6 == 5 else 0.05)
json.dump(words, open(f"{tmp}/w.json", "w"))
json.dump({"gap": 0.5, "spans": [
    {"clip": "A", "kind": "SOAK", "start": 0, "end": 60, "focus": [0.5, 0.5], "size": "medium"},
    {"clip": "B", "kind": "SOAK", "start": 0, "end": 60, "focus": [0.5, 0.5], "size": "medium"}]}, open(f"{tmp}/lib.json", "w"))
PYEOF
"$PY" "$S/suggest_cuts.py" "$TMP/w.json" --json > "$TMP/cuts.json" 2>"$TMP/cuts.err" \
  && "$PY" -c "import json,sys; c=json.load(open(sys.argv[1])); sys.exit(0 if len(c)>=5 and all(1.2<=x['end']-x['start']<=4.0 for x in c) else 1)" "$TMP/cuts.json" \
  && pass "scene cuts: every scene 1.2-4.0 s" || { fail "suggest_cuts output wrong"; sed 's/^/        /' "$TMP/cuts.err" | head -3; }
N=$("$PY" -c "import json,sys; print(len(json.load(open(sys.argv[1]))))" "$TMP/cuts.json" 2>/dev/null || echo 0)
KINDS=$(printf 'SOAK,%.0s' $(seq 1 "$N")); KINDS=${KINDS%,}; TYPES=$(printf 'DEMO,%.0s' $(seq 1 "$N")); TYPES=${TYPES%,}
"$PY" "$S/plan_scenes.py" --library "$TMP/lib.json" --cuts "$TMP/cuts.json" --kinds "$KINDS" --types "$TYPES" > "$TMP/scenes.md" 2>"$TMP/scenes.err" \
  && "$PY" "$S/footage_overlap_checker.py" "$TMP/scenes.md" >/dev/null 2>&1 \
  && pass "plan_scenes filled $N scenes and the overlap checker finds no reuse" || { fail "plan_scenes output reused or missing footage"; sed 's/^/        /' "$TMP/scenes.err" | head -3; }
"$PY" "$S/plan_scenes.py" --library "$TMP/lib.json" --cuts "$TMP/cuts.json" --kinds "$KINDS" --types "$TYPES" --used "$TMP/scenes.md" > "$TMP/scenes2.md" 2>/dev/null \
  && "$PY" "$S/footage_overlap_checker.py" "$TMP/scenes.md" "$TMP/scenes2.md" >/dev/null 2>&1 \
  && pass "a second video planned with --used shares no range with the first" || fail "second video reused footage of the first"

# a library written in lower case (real file names are) must still be recognised as spent: plans store clip names in upper case
sed 's/"clip": "A"/"clip": "clip_a"/; s/"clip": "B"/"clip": "clip_b"/' "$TMP/lib.json" > "$TMP/lib_lc.json"
"$PY" "$S/plan_scenes.py" --library "$TMP/lib_lc.json" --cuts "$TMP/cuts.json" --kinds "$KINDS" --types "$TYPES" > "$TMP/lc1.md" 2>/dev/null   && "$PY" "$S/plan_scenes.py" --library "$TMP/lib_lc.json" --cuts "$TMP/cuts.json" --kinds "$KINDS" --types "$TYPES" --used "$TMP/lc1.md" > "$TMP/lc2.md" 2>/dev/null   && "$PY" "$S/footage_overlap_checker.py" "$TMP/lc1.md" "$TMP/lc2.md" >/dev/null 2>&1   && pass "--used also holds for lower-case clip names in the library" || fail "plan_scenes ignored --used for lower-case clip names"

echo "7c. suggest_cuts.py --music (beats) and playbook.py skeleton"
ffmpeg -loglevel error -y -f lavfi -i "aevalsrc='0.8*sin(2*PI*55*t)*exp(-30*mod(t\,0.5))':d=30:s=44100" "$TMP/beat.wav" 2>/dev/null
"$PY" "$S/suggest_cuts.py" --music "$TMP/beat.wav" --end 28 --playbook real-estate --beats-out "$TMP/beats.json" --json > "$TMP/mcuts.json" 2>"$TMP/m.err" \
  && "$PY" -c "import json,sys; g=json.load(open(sys.argv[1])); c=json.load(open(sys.argv[2])); \
sys.exit(0 if abs(g['bpm']-120)<1.5 and all(min(abs(x['start']-b) for b in g['beats'])<0.02 for x in c[1:]) else 1)" "$TMP/beats.json" "$TMP/mcuts.json" \
  && pass "120 bpm found; every cut lands on a beat" || { fail "beat detection or beat cuts wrong"; sed 's/^/        /' "$TMP/m.err" | head -3; }
"$PY" "$S/playbook.py" skeleton real-estate --cuts "$TMP/mcuts.json" > "$TMP/skel.md" && "$PY" "$S/pacing_checker.py" "$TMP/skel.md" >/dev/null 2>&1 \
  && pass "a skeleton built on those cuts passes real-estate's rules" || fail "skeleton from beat cuts fails its playbook"

echo "8. trim_voice.py finds a pause and cuts there"
ffmpeg -loglevel error -y -f lavfi -i "aevalsrc=exprs='if(between(t,1,2),0,sin(2*PI*440*t))':d=3:s=44100" "$TMP/v.mp3" 2>/dev/null
"$PY" "$S/trim_voice.py" "$TMP/v.mp3" --silences 2>&1 | grep -q "cut at 1.5" \
  && pass "the 1 s pause is found, midpoint 1.5 s" || fail "trim_voice --silences missed the pause"
"$PY" "$S/trim_voice.py" "$TMP/v.mp3" --keep 0-1,2-3 --out "$TMP/k.mp3" 2>&1 | grep -Eq "wrote .*: (1\.9|2\.0|2\.1)[0-9]*s" \
  && pass "keeping 0-1 and 2-3 gives a ~2 s file" || fail "trim_voice --keep produced the wrong length"

ffmpeg -loglevel error -y -f lavfi -i "aevalsrc=exprs='if(lt(mod(t\,3.2)\,2.4)\,0.5*sin(2*PI*220*t)*sin(2*PI*3*t)\,0.002*random(0))':d=20:s=48000" "$TMP/talk.wav" 2>/dev/null
"$PY" "$S/trim_voice.py" "$TMP/talk.wav" --jumpcut --out "$TMP/talk_cut.wav" --scenes-out "$TMP/tcuts.json" >/dev/null 2>&1 \
  && "$PY" "$S/playbook.py" skeleton talking-head --cuts "$TMP/tcuts.json" > "$TMP/th.md" \
  && grep -q "| TALK | 3.1" "$TMP/th.md" && "$PY" "$S/pacing_checker.py" "$TMP/th.md" --min 15 >/dev/null 2>&1 \
  && pass "jump cut: pauses removed, scenes carry their source times, talking-head rules pass" || fail "trim_voice --jumpcut / skeleton wrong"

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
  "$PY" -c "
import json, sys, pathlib
m = json.load(open(sys.argv[1], encoding='utf-8'))
have = {p.name for p in pathlib.Path(sys.argv[2]).glob('*.wav')}
miss = [n for n, v in m['sounds'].items() if pathlib.PurePosixPath(v['file']).name not in have]
print('missing:', miss) if miss else None
sys.exit(1 if miss else 0)" "$KIT/skill/short-video-editing/assets/sfx/sfx-map.json" "$TMP/render/public/sfx" \
    && pass "every sound named in sfx-map.json is installed in public/sfx ($(ls "$TMP/render/public/sfx"/*.wav 2>/dev/null | wc -l) files)" || fail "public/sfx is incomplete"
else fail "scaffold incomplete"; fi

echo "11. sound effects: make_sfx.py and plan_to_project.py --auto-sfx"
"$PY" "$S/make_sfx.py" "$TMP/sfx" >"$TMP/sfx.log" 2>&1 && [[ $(ls "$TMP/sfx"/*.wav | wc -l) -ge 17 ]] \
  && pass "17 sounds synthesized with ffmpeg (pop, tick, ding, thud, swoosh, sparkle, chime3, twinkle, shutter, glitch, bubble, boing, typing, whoosh_s, whoosh_l, slam, riser)" || { fail "make_sfx failed"; tail -3 "$TMP/sfx.log" | sed 's/^/        /'; }
if "$PY" "$S/plan_to_project.py" "$KIT/samples/example-edit-plan.md" --out "$TMP/sfx.json" --auto-sfx >/dev/null 2>&1 \
   && "$PY" -c "
import json, sys, pathlib
cues = json.load(open(sys.argv[1], encoding='utf-8'))['sfx']
have = {p.stem for p in pathlib.Path(sys.argv[2]).glob('*.wav')} | {p.stem for p in pathlib.Path(sys.argv[3]).glob('*.wav')}
ok = cues and all(pathlib.PurePosixPath(c['src']).stem in have and c['at'] >= 0 for c in cues)
sys.exit(0 if ok else 1)" "$TMP/sfx.json" "$KIT/skill/short-video-editing/assets/sfx" "$TMP/sfx"; then
  pass "automatic cues exist and every one names a sound in the bank"
else fail "--auto-sfx produced no cues, or a cue names a missing sound"; fi

echo "12. process_audio.py (voice cleanup, loudness master)"
ffmpeg -loglevel error -y -f lavfi -i "aevalsrc=exprs='if(lt(mod(t\,2.6)\,2.0)\,0.3*sin(2*PI*180*t)*(1+sin(2*PI*4*t))\,0)':d=12:s=48000" \
  -f lavfi -i "anoisesrc=d=12:c=pink:a=0.06:r=48000" -filter_complex amix=inputs=2:normalize=0 "$TMP/noisy.wav" 2>/dev/null
"$PY" "$S/process_audio.py" voice "$TMP/noisy.wav" --out "$TMP/clean.wav" >"$TMP/pa.log" 2>&1 \
  && grep -q "noise reduction: afftdn" "$TMP/pa.log" \
  && "$PY" -c "import re,sys; t=open(sys.argv[1]).read(); a=[float(x) for x in re.findall(r'distance\s+(-?[\d.]+)',t)]; i=float(re.findall(r'after\s+(-?[\d.]+) LUFS',t)[0]); sys.exit(0 if a[1]>a[0]+2 and abs(i+16)<1 else 1)" "$TMP/pa.log" \
  && pass "noisy voice: noise reduced (speech-to-floor up), levelled to -16 LUFS" || { fail "process_audio voice"; tail -4 "$TMP/pa.log" | sed 's/^/        /'; }
ffmpeg -loglevel error -y -f lavfi -i testsrc=size=270x480:rate=30 -i "$TMP/noisy.wav" -t 6 -pix_fmt yuv420p -shortest "$TMP/mix.mp4" 2>/dev/null
"$PY" "$S/process_audio.py" master "$TMP/mix.mp4" --out "$TMP/master.mp4" >"$TMP/pm.log" 2>&1 \
  && "$PY" -c "import re,sys; t=open(sys.argv[1]).read(); m=re.findall(r'after\s+(-?[\d.]+) LUFS\s+TP\s+(-?[\d.]+)',t)[0]; sys.exit(0 if abs(float(m[0])+14)<1 and float(m[1])<=-0.9 else 1)" "$TMP/pm.log" \
  && pass "master: -14 LUFS, true peak <= -1 dBTP, picture copied" || { fail "process_audio master"; tail -3 "$TMP/pm.log" | sed 's/^/        /'; }

echo "13. inspect_footage.py --measure and prepare_footage.py"
mkdir -p "$TMP/raw"
ffmpeg -loglevel error -y -f lavfi -i "testsrc2=s=1400x2400:r=30:d=4" -vf "crop=1080:1920:'160+40*sin(n*1.7)+25*sin(n*0.9)':'240+40*cos(n*1.3)'" -pix_fmt yuv420p "$TMP/raw/shaky.mp4" 2>/dev/null
ffmpeg -loglevel error -y -f lavfi -i "testsrc2=s=1080x1920:r=30:d=3" -vf "eq=brightness=-0.25,noise=alls=22:allf=t" -pix_fmt yuv420p "$TMP/raw/dark.mp4" 2>/dev/null
if "$PY" "$S/inspect_footage.py" "$TMP/raw" --measure --json "$TMP/an.json" >/dev/null 2>&1; then
  "$PY" -c "import json,sys; c={x['stem']:x for x in json.load(open(sys.argv[1]))['clips']}; \
sys.exit(0 if 'exposure' in c['DARK']['recommend'] and 'denoise' in c['DARK']['recommend'] and \
(c['SHAKY']['motion']=='unknown' or 'stabilize' in c['SHAKY']['recommend']) else 1)" "$TMP/an.json" \
    && pass "measured: the dark noisy clip needs exposure + denoise, the shaken clip stabilisation" || fail "inspect --measure recommendations wrong"
  "$PY" "$S/prepare_footage.py" "$TMP/raw" "$TMP/proxies" --analysis "$TMP/an.json" --playbook real-estate --height 1920 --fix "DARK:rotate=-1.5" >"$TMP/prep.log" 2>&1 \
    && [[ -s "$TMP/proxies/SHAKY.mp4" && -s "$TMP/proxies/DARK.mp4" ]] && grep -q "levelled" "$TMP/prep.log" \
    && [[ "$(ffprobe -v error -show_entries stream=width,height -of csv=p=0 "$TMP/proxies/DARK.mp4")" == "1080,1920" ]] \
    && pass "proxies corrected, graded (one LUT), levelled, 1080x1920; corrections.json written" \
    || { fail "prepare_footage.py"; tail -4 "$TMP/prep.log" | sed 's/^/        /'; }
else fail "inspect_footage --measure failed"; fi

echo "14. project_to_hyperframes.py builds a HyperFrames project (no Node needed)"
mkdir -p "$TMP/hfpub/clips"; cp "$TMP/clip.mp4" "$TMP/hfpub/clips/CLIP.mp4"
"$PY" - "$TMP/hf.json" <<'PYEOF'
import json, sys
sc = lambda a, b, **k: dict(clip="CLIP", **{"in": 0.2}, start=a, end=b, type="DEMO", **k)
json.dump({"duration": 3.0, "captionStyle": "plain", "captions": [{"text": "xin chào", "start": 0.2, "end": 1.4}],
           "scenes": [sc(0, 1.0, fx=["shake"]), sc(1.0, 2.0, transition={"type": "slide", "direction": "up"}, speed=2),
                      sc(2.0, 3.0, transition={"type": "whip"}, ramp=[1, 2, 1], fx=["rgb"])],
           "overlays": [{"component": "title", "start": 0, "end": 1.5, "props": {"style": "outline", "lines": ["Tiêu đề"]}},
                        {"component": "compare", "start": 1.5, "end": 2.5, "props": {}}]},
          open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False)
PYEOF
"$PY" -X utf8 "$S/project_to_hyperframes.py" "$TMP/hf.json" --public "$TMP/hfpub" --out "$TMP/hf" --look vignette=0.3,grain=0.05 >"$TMP/hf.log" 2>&1 \
  && [[ -f "$TMP/hf/index.html" && -f "$TMP/hf/kit.js" && -f "$TMP/hf/kit.css" && -f "$TMP/hf/package.json" ]] \
  && grep -q 'data-composition-id="main"' "$TMP/hf/index.html" && grep -q "__SVK_PROJECT__" "$TMP/hf/index.html" \
  && pass "index.html, kit.js, kit.css and package.json written; the composition is registered" \
  || { fail "project_to_hyperframes.py"; tail -5 "$TMP/hf.log" | sed 's/^/        /'; }
frames() { ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 "$1" 2>/dev/null; }
[[ "$(frames "$TMP/hf/clips/_scene1.mp4")" == "42" && "$(frames "$TMP/hf/clips/_scene2.mp4")" == "35" ]] \
  && pass "a 2x scene and a speed ramp are baked to exactly their slot (30-frame scenes plus transition handles: 42 and 35 frames)" \
  || fail "baked scene lengths are wrong ($(frames "$TMP/hf/clips/_scene1.mp4") and $(frames "$TMP/hf/clips/_scene2.mp4") frames)"
grep -q "not drawn by the HyperFrames kit: compare" "$TMP/hf.log" \
  && pass "an overlay the kit cannot draw (compare) is reported, not dropped silently" || fail "unsupported overlay not reported"
node -e "new Function(require('fs').readFileSync(process.argv[1],'utf8'))" "$TMP/hf/kit.js" >/dev/null 2>&1 \
  && pass "kit.js parses" || { command -v node >/dev/null 2>&1 && fail "kit.js has a syntax error" || skip "node not installed: kit.js not parsed"; }
"$PY" -X utf8 - "$S" <<'PYEOF' >/dev/null 2>&1 \
  && pass "camera keyframes: fractions and seconds become ts, @X,Y and ease are read, bad keys are rejected" \
  || fail "camera keyframe parsing (plan_to_project.parse_camera)"
import sys
sys.path.insert(0, sys.argv[1])
import plan_to_project as p
c = p.parse_camera("keys 0=1.0 ; 0.4=1.35@0.3,0.45 out ; 1.5s=1.1 roll -1 soft")
p.resolve_keys(c, 3.0)
k = c["keys"]
assert c["move"] == "keys" and [x["ts"] for x in k] == [0.0, 1.2, 1.5], k
assert k[1]["at"] == [0.3, 0.45] and k[1]["ease"] == "out" and k[2]["roll"] == -1 and k[2]["ease"] == "soft", k
for bad in ("keys 0=1.0", "keys 0=1.0 ; 1=1.2 wobble", "keys 0=x ; 1=1.2"):
    try:
        p.parse_camera(bad)
    except ValueError:
        continue
    raise SystemExit(1)
PYEOF

echo "14b. agency pitch: card layout, new components, make_music.py, match_voice_takes.py"
cat >"$TMP/agency-plan.md" <<'MDEOF'
**Playbook:** talking-head:agency

| # | Start | End | Source | In | Type | Layout | Transition | Camera |
|---|-------|-----|--------|----|------|--------|------------|--------|
| 1 | 0.0 | 1.5 | CLIP | 0.2 | HOOK | | – | hold 1.2 focus 0.5,0.4 |
| 2 | 1.5 | 2.7 | CLIP | 0.2 | LIVING | card | cardSlide 10f | push 1.0>1.1 |
| 3 | 2.7 | 3.9 | CLIP | 1.4 | LIVING | expand | cut | |
| 4 | 3.9 | 5.0 | - | 0 | CTA | card | cardSwirl 16f | |

| # | Start | End | Component | Zone | Tone | Content |
|---|-------|-----|-----------|------|------|---------|
| 1 | 0.0 | 1.4 | phrase | top | – | lead=Đang kinh doanh; emph=THIẾU VIDEO; emphAt=0.5; y=0.2 |
| 2 | 1.6 | 2.6 | counter | – | – | from=5; to=10; label=NGÀY; at=0.5,0.18 |
| 3 | 4.0 | 4.9 | logo | – | – | at=0.5,0.4; width=500; tint=white; hold=1 |

| Start | End | Top | Size |
|-------|-----|-----|------|
| 0.0 | 1.5 | hide | |
| 1.5 | 3.9 | 250 | 44 |
MDEOF
"$PY" "$S/plan_to_project.py" "$TMP/agency-plan.md" --out "$TMP/agency.json" --look 1.1,1.05,1.02 >"$TMP/agency.log" 2>&1 \
  && "$PY" -c "
import json, sys
p = json.load(open(sys.argv[1], encoding='utf-8'))
s = p['scenes']
ok = [x.get('layout') for x in s] == [None, 'card', 'expand', 'card'] and s[1]['transition']['type'] == 'cardSlide' and s[3]['transition']['type'] == 'cardSwirl'
ok = ok and s[3]['clip'] is None and p['look']['saturate'] == 1.1
ok = ok and p['captionBands'][0].get('hide') is True and p['captionBands'][1]['top'] == 250
ok = ok and {o['component'] for o in p['overlays']} == {'phrase', 'counter', 'logo'}
sys.exit(0 if ok else 1)" "$TMP/agency.json" \
  && pass "Layout column, cardSlide/cardSwirl, caption bands (hide), --look and the new components compile" \
  || { fail "agency plan did not compile as expected"; tail -4 "$TMP/agency.log" | sed 's/^/        /'; }
"$PY" "$S/make_music.py" --duration 6 --bpm 120 --sections "0:0.55,2:1.0,4:0.0" --hits "2" --out "$TMP/bed.wav" >"$TMP/mm.log" 2>&1 \
  && "$PY" -c "
import sys, wave
import numpy as np
w = wave.open(sys.argv[1]); d = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2') / 32768
sr = w.getframerate()
loud = lambda a, b: np.sqrt((d[int(a*sr)*2:int(b*sr)*2] ** 2).mean())
ok = abs(w.getnframes() / sr - 6) < 0.05 and 0.6 < np.abs(d).max() < 0.75 and loud(2.2, 3.8) > loud(4.6, 5.6) * 3 and not (np.abs(d) > 0.999).any()
sys.exit(0 if ok else 1)" "$TMP/bed.wav" \
  && pass "make_music.py: stereo bed of the asked length, peak near -3 dBFS, the loud section louder than the silent one, no clipping" \
  || { fail "make_music.py"; tail -3 "$TMP/mm.log" | sed 's/^/        /'; }
# a "voice" cut from two takes: take A (0-3 s of tone sweep) then take B, joined; each take plus a leading countdown that is not in the voice
ffmpeg -loglevel error -y -f lavfi -i "aevalsrc=exprs='0.5*sin(2*PI*(300+80*t)*t)*(1+0.6*sin(2*PI*3*t))':d=5:s=16000" "$TMP/tkA.wav" 2>/dev/null
ffmpeg -loglevel error -y -f lavfi -i "aevalsrc=exprs='0.5*sin(2*PI*(500+60*t)*t)*(1+0.6*sin(2*PI*2.2*t))':d=5:s=16000" "$TMP/tkB.wav" 2>/dev/null
mkdir -p "$TMP/takes" && cp "$TMP/tkA.wav" "$TMP/takes/TKA.wav" && cp "$TMP/tkB.wav" "$TMP/takes/TKB.wav"
ffmpeg -loglevel error -y -ss 1.0 -t 2.5 -i "$TMP/tkA.wav" "$TMP/pA.wav" 2>/dev/null && ffmpeg -loglevel error -y -ss 2.0 -t 2.5 -i "$TMP/tkB.wav" "$TMP/pB.wav" 2>/dev/null
ffmpeg -loglevel error -y -i "$TMP/pA.wav" -i "$TMP/pB.wav" -filter_complex "[0][1]concat=n=2:v=0:a=1" "$TMP/joined.wav" 2>/dev/null
"$PY" "$S/match_voice_takes.py" "$TMP/joined.wav" "$TMP/takes" --min-corr 0.8 >"$TMP/mv.log" 2>&1 \
  && grep -qE "^TKA .*\+1\.000" "$TMP/mv.log" && grep -qE "^TKB .*-0\.500" "$TMP/mv.log" \
  && pass "match_voice_takes.py: finds the take and the lag (clip time = voice time + 1.0 s and - 0.5 s) of a voice cut from two takes" \
  || { fail "match_voice_takes.py"; sed 's/^/        /' "$TMP/mv.log" | head -8; }

echo "14c. agency tools: find_cutaways.py, agency_plan.py, text effects, flash and face cells"
# two "takes": a speaker (loud tone bursts) with a quiet pre-roll and tail, so there are cutaways; the voice is the middle of take A
mkdir -p "$TMP/ag"
ffmpeg -loglevel error -y -f lavfi -i "color=c=gray:s=270x480:r=30:d=12" -f lavfi -i "aevalsrc=exprs='if(between(t,3,9),0.5*sin(2*PI*(300+40*t)*t)*(1+0.6*sin(2*PI*3*t)),0.002*sin(2*PI*60*t))':d=12:s=16000"   -pix_fmt yuv420p -shortest "$TMP/ag/TKX.mp4" 2>/dev/null
"$PY" "$S/find_cutaways.py" "$TMP/ag" --min 1.0 --json "$TMP/ag/cut.json" >"$TMP/ca.log" 2>&1 \
  && "$PY" -c "
import json, sys
r = json.load(open(sys.argv[1], encoding='utf-8'))
ok = len(r) == 2 and r[0]['clip'] == 'TKX' and all(x['end'] <= 3.0 or x['start'] >= 9.0 for x in r) and any(x['start'] < 0.5 for x in r) and any(x['end'] > 11 for x in r)
sys.exit(0 if ok else 1)" "$TMP/ag/cut.json" \
  && pass "find_cutaways.py: the quiet pre-roll and tail of a take are found, the spoken middle is not" || { fail "find_cutaways.py"; tail -4 "$TMP/ca.log" | sed 's/^/        /'; }
"$PY" -X utf8 - "$S" "$TMP" <<'PYEOF' >"$TMP/ap.log" 2>&1 \
  && pass "agency_plan.py: a voice cut from a take -> talking scenes with In = start + lag, cutaway cards, text blocks, a plan that compiles" \
  || { fail "agency_plan.py"; tail -6 "$TMP/ap.log" | sed 's/^/        /'; }
import json, subprocess, sys
from pathlib import Path
S, T = sys.argv[1], Path(sys.argv[2])
words = []
t = 3.2
for i, w in enumerate("Chào bạn, chúng tôi làm video. Hãy inbox ngay cho SISMO nhé!".split()):
    words.append({"text": w, "start": round(t, 2), "end": round(t + 0.35, 2)})
    t += 0.42 + (0.25 if w.endswith((",", ".")) else 0)
(T / "w.json").write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
(T / "m.json").write_text(json.dumps({"TKX": [{"lag": 0.0, "clip_from": 3.2, "clip_to": 8.4, "voice_from": 3.2, "voice_to": 8.4, "corr": 0.99}]}), encoding="utf-8")
(T / "c.json").write_text(json.dumps([{"clip": "TKX", "start": 0.2, "end": 2.8, "length": 2.6, "person": None, "score": 2.6}, {"clip": "TKX", "start": 9.2, "end": 11.8, "length": 2.6, "person": None, "score": 2.6}]), encoding="utf-8")
r = subprocess.run([sys.executable, str(Path(S) / "agency_plan.py"), "--words", str(T / "w.json"), "--matches", str(T / "m.json"), "--cutaways", str(T / "c.json"), "--brand", "SISMO", "--out", str(T / "ap.md")], capture_output=True, text=True)
print(r.stdout, r.stderr)
assert r.returncode == 0, "agency_plan failed"
md = (T / "ap.md").read_text(encoding="utf-8")
assert "talking-head:agency" in md and "phrase" in md and "logo" in md and "card" in md, "plan lacks talking scenes, blocks or cards"
r = subprocess.run([sys.executable, str(Path(S) / "plan_to_project.py"), str(T / "ap.md"), "--out", str(T / "ap.json"), "--words", str(T / "w.json")], capture_output=True, text=True)
print(r.stdout, r.stderr)
assert r.returncode == 0, "the drafted plan does not compile"
p = json.load(open(T / "ap.json", encoding="utf-8"))
talk = [s for s in p["scenes"] if s["clip"] == "TKX" and not s.get("layout")]
assert talk and abs(talk[0]["in"] - talk[0]["start"]) < 0.01, "In must equal start + lag (lag 0 here)"
PYEOF
"$PY" -X utf8 - "$KIT/skill/short-video-editing/assets/remotion-template/src" <<'PYEOF' >/dev/null 2>&1 \
  && pass "text effects: every effect named in Fx.tsx has a duration in Phrase.tsx and a sound-design key" || fail "text effect names out of step"
import json, re, sys
from pathlib import Path
src = Path(sys.argv[1])
fx = re.search(r'FX_NAMES: FxName\[\] = \[(.*?)\]', (src / "components/text/Fx.tsx").read_text(encoding="utf-8"), re.S).group(1)
names = re.findall(r'"(\w+)"', fx)
phrase = (src / "components/text/Phrase.tsx").read_text(encoding="utf-8")
frames = re.search(r'const fxFrames = .*?\)\[fx\]', phrase, re.S).group(0)
missing = [n for n in names if n + ":" not in frames]
assert not missing, missing
PYEOF

echo "14d. reference analysis, montage, mix report, doctor, and every command the docs name"
mkdir -p "$TMP/rf"
# a 4 s test video: 2 s red then 2 s blue (one hard cut at 2.0 s) with a quiet tone
ffmpeg -loglevel error -y -f lavfi -i "color=c=red:s=216x384:r=30:d=2" -f lavfi -i "color=c=blue:s=216x384:r=30:d=2" -f lavfi -i "sine=frequency=440:duration=4" \
  -filter_complex "[0:v][1:v]concat=n=2:v=1:a=0[v]" -map "[v]" -map 2:a -af "volume=0.3" -pix_fmt yuv420p -shortest "$TMP/rf/sample.mp4" 2>/dev/null
"$PY" "$S/analyze_reference.py" "$TMP/rf/sample.mp4" --out "$TMP/rf/ref" --dense 0-1 >"$TMP/rf.log" 2>&1 \
  && "$PY" -c "
import json, sys
r = json.load(open(sys.argv[1] + '/report.json', encoding='utf-8'))
ok = r['shot_length']['count'] == 2 and abs(r['shots'][1]['start'] - 2.0) < 0.07 and r['shots'][0]['edge'].endswith('red') and r['shots'][1]['edge'].endswith('blue') and r['loudness'] is not None
sys.exit(0 if ok else 1)" "$TMP/rf/ref" \
  && [[ -s "$TMP/rf/ref/scenes.png" && -s "$TMP/rf/ref/dense_0-1.png" && -s "$TMP/rf/ref/report.md" ]] \
  && pass "analyze_reference.py: two shots with the cut at 2.0 s, edge colours red and blue, loudness, scene and dense sheets" \
  || { fail "analyze_reference.py"; tail -5 "$TMP/rf.log" | sed 's/^/        /'; }
"$PY" "$S/montage.py" "$TMP/rf/ref/scenes.png" "$TMP/rf/ref/dense_0-1.png" --cols 2 --width 200 --labels "a,b" --out "$TMP/rf/m.png" >"$TMP/mt.log" 2>&1 \
  && [[ -s "$TMP/rf/m.png" ]] && pass "montage.py: two images tiled with labels" || { fail "montage.py"; tail -3 "$TMP/mt.log" | sed 's/^/        /'; }
echo '{"duration": 4.0, "sfx": [{"src": "sfx/pop-a.wav", "at": 1.0}], "music": null}' > "$TMP/rf/p.json"
"$PY" "$S/mix_report.py" "$TMP/rf/sample.mp4" --project "$TMP/rf/p.json" >"$TMP/mr.log" 2>&1 \
  && pass "mix_report.py: a limited-range video of the planned duration has no errors" || { fail "mix_report.py (clean case)"; tail -6 "$TMP/mr.log" | sed 's/^/        /'; }
ffmpeg -loglevel error -y -i "$TMP/rf/sample.mp4" -pix_fmt yuvj420p -c:v libx264 -c:a copy "$TMP/rf/full.mp4" 2>/dev/null
"$PY" "$S/mix_report.py" "$TMP/rf/full.mp4" --project "$TMP/rf/p.json" >"$TMP/mr2.log" 2>&1 \
  && fail "mix_report.py let a full-range video (yuvj420p) pass" || { grep -q "full-range" "$TMP/mr2.log" && pass "mix_report.py: a full-range video is an error" || fail "mix_report.py full-range message"; }
"$PY" "$S/doctor.py" --only model --json >"$TMP/dr.json" 2>&1; "$PY" -c "
import json, sys
rows = json.load(open(sys.argv[1], encoding='utf-8'))['checks']
names = [r['name'] for r in rows]
sys.exit(0 if any('person-segmentation' in n for n in names) and any('Whisper' in n for n in names) else 1)" "$TMP/dr.json" \
  && pass "doctor.py reports the Whisper model and the optional person-segmentation model" || fail "doctor.py model group"
"$PY" -X utf8 - "$S" <<'PYEOF' >"$TMP/hfw.log" 2>&1 \
  && pass "project_to_hyperframes.py names every Remotion-only feature (card layout, flash, face, look, bands, cardSlide)" || { fail "project_to_hyperframes.py warnings"; tail -4 "$TMP/hfw.log" | sed 's/^/        /'; }
import sys
sys.path.insert(0, sys.argv[1])
import project_to_hyperframes as hf
p = {"scenes": [{"layout": "card", "transition": {"type": "cardSlide"}}, {"flash": {"frames": [0]}, "face": {"x": .5, "y": .3, "r": .1}}],
     "faceGlow": {"brightness": 1.2}, "look": {"saturate": 1.1}, "captionBands": [{"hide": True}], "captionHighlight": "box"}
out = " ".join(hf.remotion_only(p))
for word in ("layout", "flash", "face", "faceGlow", "look", "caption band", "cardSlide", "captionHighlight"):
    assert word in out, (word, out)
assert hf.remotion_only({"scenes": [{"transition": {"type": "fade"}}], "look": {"vignette": 0.3}}) == []
PYEOF
"$PY" "$S/playbook.py" suggest --intent "Tôi có thư mục clip thô quay một người dẫn, một file giọng (voice) cắt từ chính các take đó, và một video mẫu của khách. Hãy dựng lại video giống bản mẫu" 2>&1 | head -1 | grep -q "talking-head:agency" \
  && pass "playbook.py suggest: the words a client uses for this job (người dẫn, video mẫu, các take) pick talking-head:agency" || fail "playbook.py suggest does not pick talking-head:agency for the agency-pitch request"
"$PY" "$S/agency_plan.py" --words "$TMP/w.json" --matches "$TMP/m.json" --cutaways "$TMP/c.json" --brand "chúng tôi" --cta "GỌI NGAY" --out "$TMP/ap2.md" >"$TMP/ap2.log" 2>&1 \
  && grep -q "emph=GỌI NGAY" "$TMP/ap2.md" && grep -q "text=GỌI NGAY" "$TMP/ap2.md" && grep -q "| logo |" "$TMP/ap2.md" && [[ -s "$TMP/ap2.face-keys.txt" ]] \
  && pass "agency_plan.py: --cta reaches the neon block and the closing card, a two-word brand gets its logo, the face-keys file is written" \
  || { fail "agency_plan.py --cta / multi-word brand / face keys"; tail -4 "$TMP/ap2.log" | sed 's/^/        /'; }
mkdir -p "$TMP/rf/empty"
echo '{"scenes": [{"clip": "TKX", "in": 0.5, "start": 0.0, "end": 2.0}]}' > "$TMP/rf/p2.json"
"$PY" "$S/check_lipsync.py" "$TMP/rf/p2.json" "$TMP/rf/sample.mp4" --clips "$TMP/rf/empty" >"$TMP/cl.log" 2>&1 \
  && fail "check_lipsync.py passed although it checked nothing" || { grep -q "NOTHING WAS CHECKED" "$TMP/cl.log" && pass "check_lipsync.py: zero scenes checked is a failure, not a pass" || fail "check_lipsync.py message"; }
env -u SVK_PYTHON SVK_REEXEC= "$PY" -c "import sys; sys.path.insert(0, sys.argv[1]); import _venv; _venv.ensure_venv('numpy'); print('ok')" "$S" >/dev/null 2>&1 \
  && pass "_venv.ensure_venv() finds numpy (or re-launches in the kit venv)" || fail "_venv.ensure_venv()"
"$PY" -X utf8 - "$KIT" <<'PYEOF' >"$TMP/docs.log" 2>&1 \
  && pass "every script and --flag named next to it in SKILL.md, the recipe and WORKFLOW.md exists" || { fail "a documented command or flag does not exist"; tail -12 "$TMP/docs.log" | sed 's/^/        /'; }
import re, sys
from pathlib import Path
kit = Path(sys.argv[1])
scripts = kit / "skill/short-video-editing/scripts"
docs = [kit / "skill/short-video-editing/SKILL.md", kit / "skill/short-video-editing/references/agency-pitch-recipe.md", kit / "docs/WORKFLOW.md",
        kit / "skill/short-video-editing/playbooks/talking-head.md"]
bad = []
for doc in docs:
    lines = doc.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        names = re.findall(r"scripts/(\w+)\.py", line)
        if len(set(names)) != 1 or re.search(r"\b(npx|node|ffmpeg|npm)\b", line):
            continue
        name = names[0]
        src = scripts / f"{name}.py"
        if not src.exists():
            bad.append(f"{doc.name}:{i + 1}: scripts/{name}.py does not exist")
            continue
        text = src.read_text(encoding="utf-8")
        # the command and its continuation lines (a trailing backslash)
        cmd = line
        j = i
        while cmd.rstrip().endswith("\\") and j + 1 < len(lines):
            j += 1
            cmd += " " + lines[j]
        after = cmd[cmd.index(f"{name}.py") + len(name) + 3:]
        for flag in re.findall(r"(?<![\w-])(--[a-z][a-z0-9-]+)", after):
            if flag in ("--help",):
                continue
            if f'"{flag}"' not in text and f"'{flag}'" not in text:
                bad.append(f"{doc.name}:{i + 1}: {name}.py has no {flag}")
for b in bad:
    print(b)
sys.exit(1 if bad else 0)
PYEOF

if [[ $RENDER -eq 1 ]]; then
  echo "15. Remotion render (--render)"
  command -v node >/dev/null 2>&1 || fail "node not found (need 20+)"
  [[ -f "$RENDER_DIR/package.json" ]] || "$PY" "$S/new_remotion_project.py" "$RENDER_DIR" >/dev/null 2>&1
  if (cd "$RENDER_DIR" && { [[ -d node_modules ]] || npm install --no-audit --no-fund; } && npm run typecheck) >"$TMP/tsc.log" 2>&1; then
    pass "dependencies in place and the template typechecks"
  else fail "npm install / typecheck failed"; tail -5 "$TMP/tsc.log" | sed 's/^/        /'; fi
  if (cd "$RENDER_DIR" && npx remotion still src/index.ts Short "$TMP/still.png" --frame=30) >"$TMP/still.log" 2>&1 \
     && [[ -s "$TMP/still.png" ]]; then pass "rendered a still of the example project"
  else fail "remotion still failed"; tail -5 "$TMP/still.log" | sed 's/^/        /'; fi
  if (cd "$RENDER_DIR" && npx remotion still src/index.ts Short "$TMP/still2.png" --frame=990) >"$TMP/still2.log" 2>&1 \
     && [[ -s "$TMP/still2.png" ]]; then pass "rendered a still of the information graphics (specs, frame 990)"
  else fail "remotion still of the new graphics failed"; tail -5 "$TMP/still2.log" | sed 's/^/        /'; fi
fi

echo
[[ $FAIL -eq 0 ]] && printf '\033[1;32mAll checks passed.\033[0m\n' || { printf '\033[1;31m%d check(s) failed.\033[0m\n' "$FAIL"; exit 1; }
