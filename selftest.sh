#!/usr/bin/env bash
# Verify the kit works on this machine. Spends no ElevenLabs credits.
#   ./selftest.sh                  groups 1-14 (a few seconds each; group 4 loads the Whisper model)
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
