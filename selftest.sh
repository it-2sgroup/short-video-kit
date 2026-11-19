#!/usr/bin/env bash
# Verify the kit works on this machine. Spends no ElevenLabs credits.
#   ./selftest.sh                  groups 1-16 (a few seconds each; group 4 loads the Whisper model)
#   ./selftest.sh --render [DIR]   also group 17: typecheck the Remotion template and render one still in
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
# SKILL.md frontmatter: a plain "description: ... edit: ..." (colon + space) breaks YAML parsers (VS Code, skill loaders); the text must be a folded block or quoted, and <= 1024 chars.
if OUT=$("$PY" -I - "$KIT/skill/short-video-editing/SKILL.md" << 'PY' 2>&1
import re, sys
fm = open(sys.argv[1], encoding="utf-8").read().split("---")[1].split("\n")
i = next(k for k, l in enumerate(fm) if l.startswith("description:"))
head = fm[i][len("description:"):].strip()
body = [l.strip() for l in fm[i + 1:] if l.startswith(" ")] if head[:1] in ("", ">", "|") or head.startswith((">-", "|-")) else [head]
text = " ".join(body)
if head[:1] not in ("", ">", "|", '"', "'") and ": " in head:
    sys.exit("description is a plain scalar containing ': ' (YAML error): use '>-' or quotes")
if len(text) > 1024:
    sys.exit(f"description is {len(text)} chars (limit 1024)")
print(f"SKILL.md description parses and is {len(text)} chars")
PY
); then pass "$OUT"; else fail "$OUT"; fi
# What setup.sh installs must cover what the scripts import: a new third-party import without a line in requirements*.txt fails here, not on someone else's machine.
if OUT=$("$PY" -I - "$S" "$KIT" << 'PY' 2>&1
import ast, re, sys, pathlib
scripts, kit = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
std, local = set(sys.stdlib_module_names), {p.stem for p in scripts.glob("*.py")}
alias = {"cv2": "opencv-python-headless", "faster_whisper": "faster-whisper"}
need = {}
for f in scripts.glob("*.py"):
    for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
        mods = [a.name for a in n.names] if isinstance(n, ast.Import) else [n.module] if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module else []
        for m in mods:
            m = m.split(".")[0]
            if m not in std and m not in local and m != "__future__":
                need.setdefault(alias.get(m, m).lower().replace("_", "-"), f.name)
have = set()
for r in kit.glob("requirements*.txt"):
    for line in r.read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if line:
            have.add(re.split(r"[=<>!~\[ ]", line)[0].lower().replace("_", "-"))
missing = {k: v for k, v in need.items() if k not in have}
if missing:
    sys.exit("imported but in no requirements*.txt: " + ", ".join(f"{k} ({v})" for k, v in sorted(missing.items())))
print(f"{len(need)} third-party packages imported, all in requirements*.txt")
PY
); then pass "$OUT"; else fail "$OUT"; fi

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
"$PY" "$S/playbook.py" suggest --intent "apartment tour" 2>&1 | head -1 | grep -q "real-estate"   && pass "suggest: 'apartment tour' -> real-estate" || fail "playbook.py suggest did not pick real-estate for an English request"
# Vietnamese on purpose: playbook.py keeps Vietnamese keywords, and "tour căn hộ" ("apartment tour") must still pick real-estate.
"$PY" "$S/playbook.py" suggest --intent "tour căn hộ" 2>&1 | head -1 | grep -q "real-estate" \
  && pass "suggest: 'tour căn hộ' -> real-estate" || fail "playbook.py suggest did not pick real-estate"
printf '| # | Start | End | Type |\n|---|---|---|---|\n| 1 | 0.0 | 6.5 | HOOK |\n' > "$TMP/bad.md"
"$PY" "$S/pacing_checker.py" "$TMP/bad.md" >/dev/null 2>&1 \
  && fail "a 6.5s hook scene was NOT rejected" || pass "a 6.5s opening scene is rejected"

echo "4. align_captions.py (Whisper timing, script spelling)"
if "$PY" "$S/align_captions.py" "$KIT/samples/line_00.mp3" --script "$KIT/samples/line_00.txt" \
     --out "$TMP/c.srt" >"$TMP/align.log" 2>&1; then
  "$PY" -c "import sys; srt=open(sys.argv[1],encoding='utf-8').read(); \
txt=' '.join(b.split('\n',2)[2].strip() for b in srt.strip().split('\n\n') if b.count('\n')>=2); \
sys.exit(0 if txt.split()==open(sys.argv[2],encoding='utf-8-sig').read().split() else 1)" "$TMP/c.srt" "$KIT/samples/line_00.txt" \
    && pass "captions carry the script's own words, in order (Whisper gives the timing only)" \
    || fail "caption text differs from the script (Whisper's misheard text leaked through)"
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
t=p.parse_content('title','style=stack; lines=Text A / 10/8/2026; accent=100'); u=p.parse_content('title','lines=300'); s=p.parse_content('stat','value=5; unit= items'); \
sys.exit(0 if t['accent']=='100' and u['lines']==['300'] and s['value']==5 and s['unit']=='items' else 1)" "$S" \
  && pass "text keys stay text (accent=100, lines=300), stat values stay numbers" \
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
    {"clip": "A", "kind": "ACTION", "start": 0, "end": 60, "focus": [0.5, 0.5], "size": "medium"},
    {"clip": "B", "kind": "ACTION", "start": 0, "end": 60, "focus": [0.5, 0.5], "size": "medium"}]}, open(f"{tmp}/lib.json", "w"))
PYEOF
"$PY" "$S/suggest_cuts.py" "$TMP/w.json" --json > "$TMP/cuts.json" 2>"$TMP/cuts.err" \
  && "$PY" -c "import json,sys; c=json.load(open(sys.argv[1])); sys.exit(0 if len(c)>=5 and all(1.2<=x['end']-x['start']<=4.0 for x in c) else 1)" "$TMP/cuts.json" \
  && pass "scene cuts: every scene 1.2-4.0 s" || { fail "suggest_cuts output wrong"; sed 's/^/        /' "$TMP/cuts.err" | head -3; }
N=$("$PY" -c "import json,sys; print(len(json.load(open(sys.argv[1]))))" "$TMP/cuts.json" 2>/dev/null || echo 0)
KINDS=$(printf 'ACTION,%.0s' $(seq 1 "$N")); KINDS=${KINDS%,}; TYPES=$(printf 'DEMO,%.0s' $(seq 1 "$N")); TYPES=${TYPES%,}
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

if ffmpeg -v error -y -f lavfi -i "color=c=0xD9A98B:s=320x180:d=1:r=25" -pix_fmt yuv420p "$TMP/skin.mp4" >/dev/null 2>&1 \
   && OUT=$("$PY" "$S/skin_check.py" "$TMP/skin.mp4" --patch 0.4,0.3,0.2,0.2 --grade all 2>&1) \
   && echo "$OUT" | grep -q "mono .*WARN: skin turned grey" && echo "$OUT" | grep -q "warm-food"; then
  pass "skin_check.py measures a skin patch under every look and warns when a look turns it grey"
else fail "skin_check.py"; echo "$OUT" | tail -4 | sed 's/^/        /'; fi

echo "14. project_to_hyperframes.py builds a HyperFrames project (no Node needed)"
mkdir -p "$TMP/hfpub/clips"; cp "$TMP/clip.mp4" "$TMP/hfpub/clips/CLIP.mp4"
"$PY" - "$TMP/hf.json" <<'PYEOF'
import json, sys
sc = lambda a, b, **k: dict(clip="CLIP", **{"in": 0.2}, start=a, end=b, type="DEMO", **k)
# The caption is Vietnamese on purpose: it proves non-ASCII text survives the HyperFrames build.
json.dump({"duration": 3.0, "captionStyle": "plain", "captions": [{"text": "xin chào", "start": 0.2, "end": 1.4}],
           "scenes": [sc(0, 1.0, fx=["shake"]), sc(1.0, 2.0, transition={"type": "slide", "direction": "up"}, speed=2),
                      sc(2.0, 3.0, transition={"type": "whip"}, ramp=[1, 2, 1], fx=["rgb"])],
           "overlays": [{"component": "title", "start": 0, "end": 1.5, "props": {"style": "outline", "lines": ["Title text"]}},
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
| 1 | 0.0 | 1.4 | phrase | top | – | lead=Text A; emph=TEXT B; emphAt=0.5; y=0.2 |
| 2 | 1.6 | 2.6 | counter | – | – | from=5; to=10; label=DAYS; at=0.5,0.18 |
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
for i, w in enumerate("Hello friends, we make videos. Please reach out to ACME today!".split()):
    words.append({"text": w, "start": round(t, 2), "end": round(t + 0.35, 2)})
    t += 0.42 + (0.25 if w.endswith((",", ".")) else 0)
(T / "w.json").write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
(T / "m.json").write_text(json.dumps({"TKX": [{"lag": 0.0, "clip_from": 3.2, "clip_to": 8.4, "voice_from": 3.2, "voice_to": 8.4, "corr": 0.99}]}), encoding="utf-8")
(T / "c.json").write_text(json.dumps([{"clip": "TKX", "start": 0.2, "end": 2.8, "length": 2.6, "person": None, "score": 2.6}, {"clip": "TKX", "start": 9.2, "end": 11.8, "length": 2.6, "person": None, "score": 2.6}]), encoding="utf-8")
r = subprocess.run([sys.executable, str(Path(S) / "agency_plan.py"), "--words", str(T / "w.json"), "--matches", str(T / "m.json"), "--cutaways", str(T / "c.json"), "--brand", "ACME", "--out", str(T / "ap.md")], capture_output=True, text=True)
print(r.stdout, r.stderr)
assert r.returncode == 0, "agency_plan failed"
md = (T / "ap.md").read_text(encoding="utf-8")
assert "talking-head:agency" in md and "phrase" in md and "logo" in md and "card" in md, "plan lacks talking scenes, blocks or cards"
assert "fx=neon" not in md and "| pill |" not in md, "without --cta there is no call to action block and no closing pill"
r = subprocess.run([sys.executable, str(Path(S) / "plan_to_project.py"), str(T / "ap.md"), "--out", str(T / "ap.json"), "--words", str(T / "w.json")], capture_output=True, text=True)
print(r.stdout, r.stderr)
assert r.returncode == 0, "the drafted plan does not compile"
p = json.load(open(T / "ap.json", encoding="utf-8"))
talk = [s for s in p["scenes"] if s["clip"] == "TKX" and not s.get("layout")]
assert talk and abs(talk[0]["in"] - talk[0]["start"]) < 0.01, "In must equal start + lag (lag 0 here)"
PYEOF
"$PY" -X utf8 - "$KIT/skill/short-video-editing/assets/remotion-template/src" <<'PYEOF' >/dev/null 2>&1 \
  && pass "text effects: every effect named in Fx.tsx has a duration (FRAMES) and, but for the calm ones, a sound-design key" || fail "text effect names out of step"
import json, re, sys
from pathlib import Path
src = Path(sys.argv[1])
fx = re.search(r'FX_NAMES: FxName\[\] = \[(.*?)\]', (src / "components/text/Fx.tsx").read_text(encoding="utf-8"), re.S).group(1)
names = re.findall(r'"(\w+)"', fx)
fx_src = (src / "components/text/Fx.tsx").read_text(encoding="utf-8")
frames = re.search(r'const FRAMES.*?=\s*\{\n(.*?)\n\};', fx_src, re.S).group(1)
missing = [n for n in names if not re.search(r'(^|\s)' + n + r':', frames)]
assert not missing, ("no duration in FRAMES", missing)
sfx = json.loads((src.parent.parent / "sfx/sfx-map.json").read_text(encoding="utf-8"))
raw = json.dumps(sfx)
nosound = [n for n in names if f'"phrase:{n}"' not in raw]
assert set(nosound) <= {"scatter", "split", "typewriter", "rise"}, ("effects with no sound key (only the calm defaults may have none)", nosound)
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
  && pass "project_to_hyperframes.py names every Remotion-only feature (card layout, subject, face, look, bands, cardSlide)" || { fail "project_to_hyperframes.py warnings"; tail -4 "$TMP/hfw.log" | sed 's/^/        /'; }
import sys
sys.path.insert(0, sys.argv[1])
import project_to_hyperframes as hf
p = {"scenes": [{"layout": "card", "transition": {"type": "cardSlide"}}, {"subject": {"mode": "behind", "frames": [0]}, "face": {"x": .5, "y": .3, "r": .1}}],
     "faceGlow": {"brightness": 1.2}, "look": {"saturate": 1.1}, "captionBands": [{"hide": True}], "captionHighlight": "box"}
out = " ".join(hf.remotion_only(p))
for word in ("layout", "subject", "face", "faceGlow", "look", "caption band", "cardSlide", "captionHighlight"):
    assert word in out, (word, out)
assert hf.remotion_only({"scenes": [{"transition": {"type": "fade"}}], "look": {"vignette": 0.3}}) == []
PYEOF
# The first request is Vietnamese on purpose (playbook.py matches Vietnamese keywords); the English twin follows it.
"$PY" "$S/playbook.py" suggest --intent "Tôi có thư mục clip thô quay một người dẫn, một file giọng (voice) cắt từ chính các take đó, và một video mẫu. Hãy dựng lại video giống bản mẫu" 2>&1 | head -1 | grep -q "talking-head:agency" \
  && pass "playbook.py suggest: the words a user uses for this job (người dẫn, video mẫu, các take) pick talking-head:agency" || fail "playbook.py suggest does not pick talking-head:agency for the agency-pitch request"
"$PY" "$S/playbook.py" suggest --intent "I have a folder of raw clips of one presenter, a voice file cut from those same takes, and a reference video. Rebuild the video like the reference" 2>&1 | head -1 | grep -q "talking-head:agency"   && pass "playbook.py suggest: the English request for the same job also picks talking-head:agency" || fail "playbook.py suggest does not pick talking-head:agency for the English agency-pitch request"
"$PY" "$S/agency_plan.py" --words "$TMP/w.json" --matches "$TMP/m.json" --cutaways "$TMP/c.json" --brand "we make" --cta "CALL NOW" --cta-word reach --out "$TMP/ap2.md" >"$TMP/ap2.log" 2>&1 \
  && grep -q "emph=CALL NOW" "$TMP/ap2.md" && grep -q "text=CALL NOW" "$TMP/ap2.md" && grep -q "| logo |" "$TMP/ap2.md" && [[ -s "$TMP/ap2.face-keys.txt" ]] \
  && pass "agency_plan.py: --cta with --cta-word reaches the neon block and the closing card, a two-word brand gets its logo, the face-keys file is written" \
  || { fail "agency_plan.py --cta / multi-word brand / face keys"; tail -4 "$TMP/ap2.log" | sed 's/^/        /'; }
"$PY" "$S/agency_plan.py" --words "$TMP/w.json" --matches "$TMP/m.json" --cutaways "$TMP/c.json" --cta-word reach --out "$TMP/ap3.md" >/dev/null 2>&1 \
  && fail "agency_plan.py accepted --cta-word without --cta" || pass "agency_plan.py: --cta-word without --cta is refused (no content default)"
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

echo "14e. reference mode: reference_to_plan.py, the reference playbook, pacing_checker.py --reference"
"$PY" -X utf8 - "$TMP" <<'PYEOF'
import json, sys
from pathlib import Path
tmp = Path(sys.argv[1])
cam = lambda drv, z, ease: {"quality": "ok", "driver": drv, "zoom_end": z, "pan_x": 0.06, "pan_y": 0.0, "ease": ease, "shake": {"level": "locked"}}
unk = {"quality": "unknown", "reason": "flat picture"}
shot = lambda a, b, enter, c: {"start": a, "end": b, "length": round(b - a, 3), "enter": enter, "edge": "blue", "centre": "green", "camera": c, "speed": {"ramp": "none", "frozen_runs": []}}
shots = [shot(0, 1.0, "start", cam("zoom-in", 1.2, "ease-out")), shot(1.0, 2.6, "crossfade", cam("static", 1.0, "linear")),
         shot(2.6, 4.2, "mask-wipe", cam("pan-left", 1.0, "linear")), shot(4.2, 6.0, "hard-cut", unk)]
ev = lambda i, t0, t1, txt, box, fill, mot: {"id": f"tx{i:02d}", "text": txt, "bbox": box, "t_in": t0, "t_out": t1, "conf": 0.9, "precision": "frame",
     "motion_in": {"family": mot}, "style": {"fill": fill}}
events = [ev(1, 0.2, 1.4, "SAMPLE HEADLINE ONE", [0.1, 0.12, 0.8, 0.06], "#ffd21a", "pop"), ev(2, 2.8, 4.0, "Sample wording that must not be copied", [0.1, 0.40, 0.8, 0.1], "#ffffff", "fade")] + \
         [ev(3 + j, 0.3 + j * 0.9, 1.0 + j * 0.9, f"caption {j}", [0.2, 0.74, 0.6, 0.04], "#ffffff", "cut") for j in range(6)]
rep = {"video": "sample.mp4", "duration": 6.0, "shots": shots, "shot_length": {"count": 4, "median": 1.6, "shortest": 1.0, "longest": 1.8, "cuts_per_minute": 30.0},
       "transitions": [{"t": 0.84, "kind": "run", "frames": 12, "seconds": 0.4, "family": "crossfade", "direction": None, "needs_look": False},
                       {"t": 2.45, "kind": "run", "frames": 9, "seconds": 0.3, "family": "mask-wipe", "direction": "left", "needs_look": True},
                       {"t": 4.2, "kind": "cut", "family": "hard-cut"}], "flashes": [], "text_events": events, "text": {"available": True},
       "grade": {"nearest": [{"look": "natural"}]}, "loudness": {"lufs": -14.0}}
(tmp / "refrep.json").write_text(json.dumps(rep), encoding="utf-8")
(tmp / "reftexts.txt").write_text("MY OWN HEADLINE\n", encoding="utf-8")
words, t = [], 0.1
for w in "this is my own spoken line about the product and why it works well for you".split():
    words.append({"text": w, "start": round(t, 2), "end": round(t + 0.3, 2)}); t += 0.45
(tmp / "refwords.json").write_text(json.dumps(words), encoding="utf-8")
PYEOF
"$PY" "$S/reference_to_plan.py" "$TMP/refrep.json" --out "$TMP/refplan.md" --duration 7.2 --texts "$TMP/reftexts.txt" --words "$TMP/refwords.json" --genre product-demo >"$TMP/refplan.log" 2>&1 \
  && grep -c "^| [0-9]* | [0-9.]* | [0-9.]* | \[CLIP\]" "$TMP/refplan.md" | grep -qx 4 \
  && grep -q "| fade 12f |" "$TMP/refplan.md" && grep -q "| wipe left 9f |" "$TMP/refplan.md" && grep -q "| keys 0=1.00 ; 1=1.20 out |" "$TMP/refplan.md" \
  && pass "reference_to_plan.py: one scene per sample shot, its transitions (fade 12f, wipe left 9f) and eased push as a camera key" || { fail "reference_to_plan.py scenes, transitions or camera wrong"; sed 's/^/        /' "$TMP/refplan.log" | tail -5; }
grep -q "textbox | – | – | text=MY OWN HEADLINE; box=0.060,0.112,0.880,0.075" "$TMP/refplan.md" && ! grep -qi "SAMPLE HEADLINE\|must not be copied" <(sed -n '/## Overlays/,/Notes on the overlays/p' "$TMP/refplan.md") \
  && grep -q "color=#ffd21a" "$TMP/refplan.md" && grep -q "in=elastic" "$TMP/refplan.md" \
  && pass "reference_to_plan.py: the text slot is a textbox in the sample's own box, ink colour and entry effect, at its time; the words are the user's, never the sample's OCR string" || fail "reference_to_plan.py overlay text"
grep -q "^## Caption bands" "$TMP/refplan.md" && grep -q "Compliance check (from \`product-demo\`" "$TMP/refplan.md" && grep -q "No antibacterial" "$TMP/refplan.md" \
  && pass "reference_to_plan.py: six short lines low in the frame become a caption band; --genre copies only the compliance list" || fail "reference_to_plan.py caption band or --genre"
"$PY" "$S/pacing_checker.py" "$TMP/refplan.md" --reference "$TMP/refrep.json" >"$TMP/refpace.log" 2>&1 \
  && pass "pacing_checker.py --reference passes a plan made from the sample" || { fail "pacing_checker --reference rejected the plan"; tail -6 "$TMP/refpace.log" | sed 's/^/        /'; }
"$PY" - "$TMP" <<'PYEOF'
import re, sys
from pathlib import Path
tmp = Path(sys.argv[1])
lines = (tmp / "refplan.md").read_text(encoding="utf-8").splitlines()
rows = [i for i, l in enumerate(lines) if re.match(r"\| \d+ \| [\d.]+ \| [\d.]+ \| \[CLIP\]", l)]
def set_cell(ls, i, col, val):
    c = ls[i].split("|"); c[col] = f" {val:.2f} "; ls[i] = "|".join(c)      # col 2 = Start, col 3 = End
start3 = float(lines[rows[2]].split("|")[2])
short = list(lines)                                   # scene 3 (outside the hook) shrinks to 0.2 s, scene 4 starts right after it: no gap, only a rhythm break
set_cell(short, rows[2], 3, start3 + 0.2); set_cell(short, rows[3], 2, start3 + 0.2)
(tmp / "refplan_short.md").write_text("\n".join(short), encoding="utf-8")
gap = list(short)                                     # scene 4 starts 0.5 s late: a hole in the timeline
set_cell(gap, rows[3], 2, start3 + 0.7)
(tmp / "refplan_gap.md").write_text("\n".join(gap), encoding="utf-8")
PYEOF
"$PY" "$S/pacing_checker.py" "$TMP/refplan_short.md" --reference "$TMP/refrep.json" >"$TMP/refshort.log" 2>&1 && grep -q "only 0.2s" "$TMP/refshort.log" \
  && ! "$PY" "$S/pacing_checker.py" "$TMP/refplan_short.md" --playbook product-demo >/dev/null 2>&1 \
  && pass "a scene shorter than the sample's is a warning with --reference (an error under a genre playbook)" || fail "--reference did not soften the rhythm rules"
"$PY" "$S/pacing_checker.py" "$TMP/refplan_gap.md" --reference "$TMP/refrep.json" >/dev/null 2>&1 \
  && fail "a gap between scenes passed --reference" || pass "a gap between scenes is still an error with --reference"
sed 's/\[CLIP\]/CLIP_A/; s/| \[s\] |/| 0.5 |/' "$TMP/refplan.md" > "$TMP/refplan_filled.md"
"$PY" "$S/plan_to_project.py" "$TMP/refplan_filled.md" --out "$TMP/refproj.json" --words "$TMP/refwords.json" >"$TMP/refproj.log" 2>&1 \
  && "$PY" -c "import json,sys; p=json.load(open(sys.argv[1])); assert len(p['scenes'])==4 and any(o['component']=='textbox' and len(o['props']['box'])==4 for o in p['overlays'])" "$TMP/refproj.json" \
  && pass "plan_to_project.py compiles a reference plan once its footage cells are filled" || { fail "plan_to_project.py could not compile the reference plan"; tail -5 "$TMP/refproj.log" | sed 's/^/        /'; }
"$PY" - "$S" <<'PYEOF' >"$TMP/tb.log" 2>&1 && pass "textbox plan syntax (box, escaped ; | and slash) and layout_check.py: overlap, captions, head, right rail, frame edge" || { fail "textbox plan syntax or layout_check.py"; tail -6 "$TMP/tb.log" | sed 's/^/        /'; }
import sys
sys.path.insert(0, sys.argv[1])
import plan_to_project as P, layout_check as L
BS = chr(92)
assert P.split_cells(f"| 1 | text=A {BS}| B; x=1 |") == ["1", "text=A | B; x=1"], "an escaped pipe stays in its cell"
c = P.parse_content("textbox", f"box=0.1,0.4,0.8; text=Line one / Line {BS}/ two; color=#FFD21A")
assert c["box"] == [0.1, 0.4, 0.8] and c["text"] == ["Line one", "Line / two"], c
c = P.parse_content("textbox", f"box=0.1,0.4,0.8,0.2; text=50% off {BS}; today")
assert c["box"] == [0.1, 0.4, 0.8, 0.2] and c["text"] == "50% off ; today", c
tb = lambda s0, e0, box, **k: {"component": "textbox", "start": s0, "end": e0, "props": {"text": "Sample text", "box": box, **k}}
proj = {"captionStyle": "plain", "layout": "feed", "captions": [{"start": 0, "end": 5, "text": "x"}], "captionBands": [], "words": [],
        "scenes": [{"start": 0, "end": 5, "face": {"x": 0.5, "y": 0.3, "r": 0.08}}]}
def n(*ov, **extra):
    return len(L.check({**proj, **extra, "overlays": list(ov)}))
assert n(tb(0, 2, [0.1, 0.1, 0.4, 0.05]), tb(1, 3, [0.15, 0.1, 0.4, 0.05])) == 1, "two boxes in one place at one time"
assert n(tb(0, 2, [0.1, 0.1, 0.4, 0.05]), tb(2.5, 4, [0.15, 0.1, 0.4, 0.05])) == 0, "the same place at another time is fine"
assert n(tb(0, 2, [0.1, 0.1, 0.4, 0.05]), tb(1, 3, [0.1, 0.5, 0.4, 0.05])) == 0, "two boxes apart"
assert n(tb(0, 2, [0.1, 0.70, 0.5, 0.08])) == 1, "a box on the captions (y 1340)"
assert n(tb(0, 2, [0.1, 0.70, 0.5, 0.08]), captionBands=[{"start": 0, "end": 5, "top": 0, "hide": True}]) == 0, "captions hidden by a band"
assert n(tb(0, 2, [0.35, 0.25, 0.3, 0.1])) == 1, "a box over the speaker's head"
assert n(tb(0, 2, [0.6, 0.5, 0.35, 0.05])) == 1, "the right rail (x > 900)"
assert n(tb(0, 2, [0.8, 0.1, 0.4, 0.05])) >= 1, "outside the frame"
PYEOF
"$PY" - "$S" "$TMP" <<'PYEOF' >"$TMP/tcmp.log" 2>&1 && pass "analyze_reference.py --compare: text events paired by time (when, where, how big, how it enters; never the strings)" || { fail "--compare text rows"; tail -5 "$TMP/tcmp.log" | sed 's/^/        /'; }
import copy, json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import analyze_reference as A
tmp = Path(sys.argv[2])
rep = json.loads((tmp / "refrep.json").read_text(encoding="utf-8"))
rep["grade"] = {"global": {"warmth_b": 0, "chroma": 10, "luma": {"p1": 5, "p99": 240}}}
rep["loudness"] = {"lufs": -14, "true_peak_db": -1}
for t in rep["transitions"]:
    t.setdefault("frames", 0)
for e in rep["text_events"]:
    e["bbox"] = list(e["bbox"])
mine = copy.deepcopy(rep)
mine["video"] = "mine.mp4"
mine["text_events"] = mine["text_events"][:2]
mine["text_events"][0]["bbox"][1] += 0.03
A.write_diff(rep, mine, tmp / "diff.md")
t = (tmp / "diff.md").read_text(encoding="utf-8")
assert "## Text events, paired by time" in t and "| text events | 8 | 2 |" in t and "+0.030" in t and "missing" in t, t[-900:]
assert "SAMPLE HEADLINE" not in t, "the strings are not compared"
PYEOF
"$PY" "$S/playbook.py" suggest --intent "làm giống video mẫu này" 2>&1 | head -1 | grep -q "reference" \
  && "$PY" "$S/playbook.py" suggest --intent "tour căn hộ" --reference 2>&1 | head -1 | grep -q "reference" \
  && pass "suggest: a request that names a sample (or --reference) picks the reference playbook first" || fail "playbook.py suggest did not pick the reference playbook"

echo "14f. creative layer: style-axes.json, concept.py, directions.py, style_ledger.py"
"$PY" - "$S" "$KIT" <<'PYEOF' >"$TMP/axes.log" 2>&1 && pass "style-axes.json names only things the catalogue has (transitions, fonts, text effects, grades), every option has a feel, every signature kind is built" || { fail "style-axes.json against the catalogue"; tail -5 "$TMP/axes.log" | sed 's/^/        /'; }
import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import playbook, directions
skill = Path(sys.argv[2]) / "skill" / "short-video-editing"
ax = json.loads((skill / "assets" / "style-axes.json").read_text(encoding="utf-8"))
trans = set(playbook.transition_types())
fonts = set(json.loads((skill / "assets" / "fonts.json").read_text(encoding="utf-8"))["fonts"])
grades = set(json.loads((skill / "assets" / "grades.json").read_text(encoding="utf-8"))["grades"])
fx = {c["id"] for c in json.loads((skill / "assets" / "techniques.json").read_text(encoding="utf-8"))["techniques"] if c["kind"] == "text-fx"}
for o in ax["axes"]["transitions"]:
    assert set(o["ids"]) <= trans, (o["id"], set(o["ids"]) - trans)
for o in ax["axes"]["type"]:
    assert set(o["fonts"]) <= fonts and set(o["fx"]) <= fx, (o["id"], set(o["fonts"]) - fonts, set(o["fx"]) - fx)
for o in ax["axes"]["colour"]:
    assert o["grade"] in grades, o["id"]
for name, opts in ax["axes"].items():
    assert len(opts) >= 4, f"{name} has too few options to vary"
    for o in opts:
        assert set(o["feel"]) <= set(ax["dimensions"]), o["id"]
for k in ax["signatures"]:
    assert k in {"flash-cut", "hold-then-burst", "speed-hit", "zoom-through", "text-takeover"}, k
assert set(ax["axes"]) == set(directions.AXIS_NAMES)
PYEOF
"$PY" "$S/concept.py" example > "$TMP/c_ok.json" && "$PY" "$S/concept.py" check "$TMP/c_ok.json" >/dev/null 2>&1 \
  && "$PY" - "$TMP" <<'PYEOF' && ! "$PY" "$S/concept.py" check "$TMP/c_flat.json" >/dev/null 2>&1 && ! "$PY" "$S/concept.py" check "$TMP/c_id.json" >/dev/null 2>&1 && ! "$PY" "$S/concept.py" check "$TMP/c_why.json" >/dev/null 2>&1 \
  && pass "concept.py: the example is valid; a flat energy curve, an unknown technique and a missing 'why' are refused" || fail "concept.py validation"
import json, sys
from pathlib import Path
tmp = Path(sys.argv[1])
c = json.loads((tmp / "c_ok.json").read_text(encoding="utf-8"))
c["energy"] = [[0, 0.5], [0.5, 0.55], [1, 0.5]]
(tmp / "c_flat.json").write_text(json.dumps(c), encoding="utf-8")
c = json.loads((tmp / "c_ok.json").read_text(encoding="utf-8")); c["restraint"]["use"] = ["cut", "fade", "no-such-technique"]
(tmp / "c_id.json").write_text(json.dumps(c), encoding="utf-8")
c = json.loads((tmp / "c_ok.json").read_text(encoding="utf-8")); c["signature"]["why"] = ""
(tmp / "c_why.json").write_text(json.dumps(c), encoding="utf-8")
PYEOF
"$PY" - "$S" "$TMP" "$KIT" <<'PYEOF' >"$TMP/dir.log" 2>&1 && pass "directions.py: three directions that differ on most axes, the same seed gives the same plans, another seed other ones, the signature and the motif are in every plan" || { fail "directions.py"; tail -8 "$TMP/dir.log" | sed 's/^/        /'; }
import hashlib, json, subprocess, sys
from pathlib import Path
S, tmp, kit = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
sys.path.insert(0, S)
import style_ledger as SL
plan = kit / "samples" / "example-edit-plan.md"
def run(out, seed, *extra):
    r = subprocess.run([sys.executable, "-X", "utf8", f"{S}/directions.py", str(plan), "--concept", str(tmp / "c_ok.json"), "--out-dir", str(out), "--seed", str(seed), *extra], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr + r.stdout
    return [(out / d / "edit-plan.md").read_text(encoding="utf-8") for d in "ABC"]
a, a2, b = run(tmp / "d1", 1), run(tmp / "d1b", 1), run(tmp / "d2", 2)
assert a == a2, "the same seed must give the same directions"
assert a != b, "another seed must give other directions"
fps = [SL.fingerprint(t) for t in a]
sims = [SL.similarity(x, y)[0] for i, x in enumerate(fps) for y in fps[i + 1:]]
assert max(sims) < 0.6, f"the three directions are too alike: {sims}"
for t in a:
    assert t.count("[signature]") == 1 and t.count("[motif]") >= 3, "signature once, motif at least three times"
    assert "**Direction:**" in t and "**Grade:**" in t
dirs = {tuple(json.loads((tmp / "d1" / d / "direction.json").read_text(encoding="utf-8"))["axes"].values()) for d in "ABC"}
assert len(dirs) == 3
PYEOF
"$PY" - "$S" "$TMP" <<'PYEOF' >"$TMP/lock.log" 2>&1 && pass "concept lock + plan check: a direction's vocabulary becomes the restraint, its own plan passes, another direction's plan is refused; every direction passes pacing_checker and compiles" || { fail "concept lock / plan check"; tail -6 "$TMP/lock.log" | sed 's/^/        /'; }
import json, subprocess, sys
from pathlib import Path
S, tmp = sys.argv[1], Path(sys.argv[2])
py = [sys.executable, "-X", "utf8"]
def sh(*cmd):
    return subprocess.run([*py, *cmd], capture_output=True, text=True)
assert sh(f"{S}/concept.py", "lock", str(tmp / "c_ok.json"), "--direction", str(tmp / "d1" / "A" / "direction.json")).returncode == 0
assert sh(f"{S}/concept.py", "check", str(tmp / "c_ok.json"), "--plan", str(tmp / "d1" / "A" / "edit-plan.md")).returncode == 0, "its own vocabulary must pass"
refused = [d for d in "BC" if sh(f"{S}/concept.py", "check", str(tmp / "c_ok.json"), "--plan", str(tmp / "d1" / d / "edit-plan.md")).returncode != 0]
assert refused, "a plan of another direction uses techniques outside the locked vocabulary"
for d in "ABC":
    plan = str(tmp / "d1" / d / "edit-plan.md")
    assert sh(f"{S}/pacing_checker.py", plan).returncode == 0, f"pacing {d}"
    r = sh(f"{S}/plan_to_project.py", plan, "--out", str(tmp / f"proj_{d}.json"))
    assert r.returncode == 0, r.stderr + r.stdout
PYEOF
"$PY" - "$S" "$TMP" "$KIT" <<'PYEOF' >"$TMP/led.log" 2>&1 && pass "style_ledger.py: a plan is identical to itself (1.0), different directions score lower, and directions.py steers away from a remembered video" || { fail "style_ledger.py"; tail -6 "$TMP/led.log" | sed 's/^/        /'; }
import json, subprocess, sys
from pathlib import Path
S, tmp, kit = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
sys.path.insert(0, S)
import style_ledger as SL
py = [sys.executable, "-X", "utf8"]
ledger = tmp / "ledger.json"
a = (tmp / "d1" / "A" / "edit-plan.md")
assert subprocess.run([*py, f"{S}/style_ledger.py", "add", str(a), "--ledger", str(ledger), "--name", "v1"], capture_output=True).returncode == 0
fa = SL.fingerprint(a.read_text(encoding="utf-8"))
assert SL.similarity(fa, fa)[0] == 1.0
assert SL.similarity(fa, SL.fingerprint((tmp / "d1" / "B" / "edit-plan.md").read_text(encoding="utf-8")))[0] < 0.6
assert subprocess.run([*py, f"{S}/style_ledger.py", "check", str(a), "--ledger", str(ledger), "--strict"], capture_output=True).returncode == 1, "the same style is a repeat"
c = json.loads((tmp / "c_ok.json").read_text(encoding="utf-8")); c["restraint"]["use"] = []
(tmp / "c_open.json").write_text(json.dumps(c), encoding="utf-8")
r = subprocess.run([*py, f"{S}/directions.py", str(kit / "samples" / "example-edit-plan.md"), "--concept", str(tmp / "c_open.json"), "--out-dir", str(tmp / "d3"), "--seed", "1", "--ledger", str(ledger)], capture_output=True, text=True)
assert r.returncode == 0, r.stderr
for d in "ABC":
    s = SL.similarity(SL.fingerprint((tmp / "d3" / d / "edit-plan.md").read_text(encoding="utf-8")), fa)[0]
    assert s < 0.8, f"direction {d} repeats the remembered video ({s})"
PYEOF

echo "15. packaging: version, changelog, pins, lockfile, documents"
"$PY" -X utf8 - "$KIT" <<'PYEOF' >"$TMP/pack.log" 2>&1 \
  && pass "$(head -1 "$TMP/pack.log")" || { fail "packaging is out of step"; sed 's/^/        /' "$TMP/pack.log" | tail -14; }
import json, re, sys
from pathlib import Path

kit = Path(sys.argv[1])
skill = kit / "skill" / "short-video-editing"
tpl = skill / "assets" / "remotion-template"
bad = []

ver = (skill / "VERSION").read_text(encoding="utf-8").strip()
if not re.fullmatch(r"\d+\.\d+\.\d+", ver):
    bad.append(f"VERSION {ver!r} is not MAJOR.MINOR.PATCH")
m = re.search(r"^## \[(\d+\.\d+\.\d+)\]", (kit / "CHANGELOG.md").read_text(encoding="utf-8"), re.M)
if not m or m.group(1) != ver:
    bad.append(f"the newest CHANGELOG.md entry ({m.group(1) if m else 'none'}) is not VERSION ({ver})")
if not (kit / "LICENSE").read_text(encoding="utf-8").strip():
    bad.append("LICENSE is empty")

for line in (kit / "requirements.txt").read_text(encoding="utf-8").splitlines():
    s = line.split("#")[0].strip()
    if s and not re.search(r"(==|>=|~=|<)", s):
        bad.append(f"requirements.txt: {s!r} has no version limit")

pj = json.loads((tpl / "package.json").read_text(encoding="utf-8"))
lock = json.loads((tpl / "package-lock.json").read_text(encoding="utf-8"))
root = lock["packages"][""]
for k in ("dependencies", "devDependencies"):
    if root.get(k, {}) != pj.get(k, {}):
        bad.append(f"package-lock.json is out of step with package.json ({k}): regenerate it (README, Versions and releases)")
if lock.get("lockfileVersion", 0) < 3:
    bad.append("package-lock.json: lockfileVersion is below 3")
loose = [k for k, v in lock["packages"].items() if k and not v.get("link") and not (v.get("resolved") and v.get("integrity"))]
if loose:
    bad.append(f"package-lock.json: {len(loose)} package(s) without resolved or integrity, e.g. {loose[0]}")
if len([k for k in lock["packages"] if "/compositor-" in k]) < 5:
    bad.append("package-lock.json lacks the other platforms' Remotion binaries (generate it with npm install --package-lock-only)")

struct = (kit / "docs" / "STRUCTURE.md").read_text(encoding="utf-8")
for folder in ("scripts", "references", "playbooks"):
    for f in sorted((skill / folder).iterdir()):
        named = f.stem if folder == "playbooks" else f.name  # the playbooks are described by genre, the others file by file
        if f.is_file() and f.suffix in (".py", ".md") and named not in struct:
            bad.append(f"docs/STRUCTURE.md does not name {folder}/{f.name}")

pat = re.compile(r"`((?:references|scripts|assets|playbooks|docs|samples)/[A-Za-z0-9_./-]+\.[a-z]{1,5})`")
for doc in ("README.md", "CLAUDE.md", "docs/STRUCTURE.md", "docs/WORKFLOW.md", "docs/DECISIONS.md", "skill/short-video-editing/SKILL.md"):
    where = (kit / doc).parent
    for p in sorted(set(pat.findall((kit / doc).read_text(encoding="utf-8")))):
        if any(c in p for c in "*<>{}"):
            continue
        if not any(c.exists() for c in (kit / p, skill / p, skill / "assets" / p, where / p, tpl / p)):
            bad.append(f"{doc} names {p}, which does not exist")

cards = json.loads((skill / "assets" / "techniques.json").read_text(encoding="utf-8"))["techniques"]
n = {}
for c in cards:
    n[c["kind"]] = n.get(c["kind"], 0) + 1
readme = (kit / "README.md").read_text(encoding="utf-8")
sfx = sorted((skill / "assets" / "sfx").glob("*.wav"))
groups = len(re.findall(r'^echo "\d+\. ', (kit / "selftest.sh").read_text(encoding="utf-8"), re.M))
for text, what in ((f"{n['transition']} transitions", "README.md"), (f"{n['text-fx']} text effects", "README.md"),
                   (f"{n['subject-fx']} subject effects", "README.md"), (f"{n['font']} fonts", "README.md"),
                   (f"{n['grade']} colour grades", "README.md"), (f"{len(sfx)} recordings", "README.md"),
                   (f"{groups} groups", "README.md"), (f"{groups} groups", "docs/STRUCTURE.md")):
    if text not in (kit / what).read_text(encoding="utf-8"):
        bad.append(f"{what} does not state the live count: {text}")
sources = (skill / "assets" / "sfx" / "SOURCES.md").read_text(encoding="utf-8")
for f in sfx:
    if f"`{f.name}`" not in sources:
        bad.append(f"assets/sfx/SOURCES.md has no row for {f.name} (a file without a row does not ship)")

if bad:
    print("\n".join(bad))
    sys.exit(1)
print(f"version {ver}: changelog, licence, version limits, lockfile ({len(lock['packages']) - 1} packages), documents and live counts agree")
PYEOF

echo "16. technique catalogue and the newer techniques"
"$PY" -X utf8 "$S/technique.py" check >"$TMP/tech.log" 2>&1 \
  && pass "technique.py check: every technique has a card, a doc and a test, and every card is in the code ($(head -1 "$TMP/tech.log" | cut -d' ' -f1) cards)" \
  || { fail "technique catalogue out of step with the code"; tail -14 "$TMP/tech.log" | sed 's/^/        /'; }
"$PY" -X utf8 "$S/technique.py" search "glitch rgb split" 2>&1 | grep -q "glitchSlice" \
  && pass "technique.py search finds a technique by the names editors use" || fail "technique.py search"
"$PY" -X utf8 - "$S" <<'PYEOF' >"$TMP/grades.log" 2>&1 \
  && pass "grades move a synthetic card the way they claim (teal shadows, lifted blacks, mono, warm, cold; strength mixes)" || { fail "grades move a synthetic card"; tail -4 "$TMP/grades.log" | sed 's/^/        /'; }
import json, subprocess, sys, tempfile
from pathlib import Path
import numpy as np

S = Path(sys.argv[1])  # scripts dir
sys.path.insert(0, str(S))
import prepare_footage as pf

GR = json.loads((S.parent / "assets" / "grades.json").read_text(encoding="utf-8"))["grades"]
tmp = Path(tempfile.mkdtemp())
W, H = 256, 64
# card: a grey ramp (top half) and a skin / sky / foliage / red row (bottom half)
patches = [(224, 172, 140), (90, 140, 210), (70, 130, 60), (200, 50, 50)]
row = np.zeros((H // 2, W, 3), np.uint8)
for i, c in enumerate(patches):
    row[:, i * W // 4:(i + 1) * W // 4] = c
ramp = np.repeat(np.linspace(0, 255, W, dtype=np.uint8)[None, :, None], H // 2, 0).repeat(3, 2)
card = np.concatenate([ramp, row], 0)
(tmp / "card.rgb").write_bytes(card.tobytes())


def graded(name):
    pf.colour_lut("", GR[name]["chain"], 1.0, tmp / f"{name}.png")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-i", str(tmp / "card.rgb"),
                        "-i", str(tmp / f"{name}.png"), "-filter_complex", "[0:v][1:v]haldclut=interp=tetrahedral", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       capture_output=True)
    assert r.returncode == 0, r.stderr[-200:]
    return np.frombuffer(r.stdout, np.uint8).reshape(H, W, 3).astype(float)


def sat(a):
    return float((a.max(2) - a.min(2)).mean())


base = card.astype(float)
ramp_in, row_in = base[:H // 2], base[H // 2:]
res = {}
for n in ("teal-orange", "cinematic-fade", "moody", "pastel", "vintage-film", "mono", "bleach-bypass", "golden-hour", "cold-blue"):
    res[n] = graded(n)
g = lambda n: (res[n][:H // 2], res[n][H // 2:])
rb = lambda a: float((a[..., 0] - a[..., 2]).mean())
shadows, highs = slice(0, W // 4), slice(3 * W // 4, W)
t = g("teal-orange")[0]
assert rb(t[:, shadows]) < rb(ramp_in[:, shadows]) - 2, "teal-orange: shadows should move toward teal (less red than blue)"
assert rb(t[:, highs]) > rb(ramp_in[:, highs]) + 2, "teal-orange: highlights should move toward orange"
assert g("cinematic-fade")[0][:, :4].mean() > 9, "cinematic-fade: black should be lifted"
assert g("moody")[0].mean() < ramp_in.mean() - 3, "moody: darker than the input"
assert g("pastel")[0][:, :4].mean() > 8 and sat(g("pastel")[1]) < sat(row_in), "pastel: blacks lifted, colour softer"
assert g("vintage-film")[0][:, :4].mean() > 8 and sat(g("vintage-film")[1]) < sat(row_in), "vintage-film: blacks lifted, colour muted"
assert sat(res["mono"]) < 2, "mono: no colour left"
assert sat(g("bleach-bypass")[1]) < 0.6 * sat(row_in), "bleach-bypass: strongly desaturated"
assert rb(res["golden-hour"]) > rb(base) + 4, "golden-hour: warmer than the input"
assert rb(res["cold-blue"]) < rb(base) - 4, "cold-blue: cooler than the input"
# strength: 0.5 lands between no grade and the full grade
pf.colour_lut("", GR["golden-hour"]["chain"], 0.5, tmp / "half.png")
r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-i", str(tmp / "card.rgb"),
                    "-i", str(tmp / "half.png"), "-filter_complex", "[0:v][1:v]haldclut=interp=tetrahedral", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
half = np.frombuffer(r.stdout, np.uint8).reshape(H, W, 3).astype(float)
assert rb(base) + 1 < rb(half) < rb(res["golden-hour"]) - 1, "grade strength 0.5 should land between the input and the full grade"
print("grades ok")
PYEOF
"$PY" -X utf8 - "$S" <<'PYEOF' >"$TMP/new.log" 2>&1 \
  && pass "camera shake parses; speed presets parse; look fx parses; subject cells parse; light, subject and speed techniques compile; every transition of project.ts is plannable" || { fail "newer plan features"; tail -6 "$TMP/new.log" | sed 's/^/        /'; }
import sys
sys.path.insert(0, sys.argv[1])
import plan_to_project as p, footage_overlap_checker as f
c = p.parse_camera("push 1.1>1.25 shake mild")
assert c["move"] == "push" and c["shake"]["amp"] == 6.0, c
assert p.parse_camera("shake 9") == {"move": "hold", "shake": {"amp": 9.0}}
k = p.parse_camera("keys 0=1.05 ; 1=1.3 shake strong")
assert k["move"] == "keys" and k["shake"]["amp"] == 14.0, k
assert f.parse_speed("hero") == (None, [2.0, 0.4, 2.0]) and f.parse_speed("Flash-In")[1] == [3.0, 1.0]
assert abs(f.speed_factor("montage") - 1.75) < 1e-9
try:
    f.parse_speed("sideways")
    raise SystemExit("an unknown speed name must be refused")
except ValueError:
    pass
s = p.parse_subject("0,2,4 @ mattes/CLIP_A")
assert s == {"frames": [0, 2, 4], "matte": "mattes/CLIP_A"}, s
s = p.parse_subject("outline 0-60 @ mattes/CLIP_A; color=#FFD23F; width=12; every=3")
assert s["mode"] == "outline" and s["show"] == [0, 60] and s["frames"][:3] == [0, 3, 6] and s["color"] == "#FFD23F", s
s = p.parse_subject("behind 0-80 @ mattes/CLIP_A; text=HELLO / WORLD; size=300")
assert s["mode"] == "behind" and s["text"] == "HELLO\nWORLD" and s["frames"] == [0], s
try:
    p.parse_subject("sparkle 0,2 @ m")
    raise SystemExit("an unknown subject mode must be refused")
except ValueError:
    pass
for t in ("blinds", "diamond", "doors", "glitchSlice", "spinZoom", "filmBurn", "zoomBlur", "whip", "cardSwirl"):
    assert t.lower() in p.CANON, t
# label: light, subject and speed techniques compile
assert {"sweep", "flare", "streak", "knockout"} <= set(p.KNOWN), "light overlays and knockout text must be in the registry"
assert f.parse_speed("freeze-hit") == (None, [1.0, 0.0, 0.0, 1.0]), "freeze-hit holds one frame in the middle"
assert p.parse_transition("cut +echo")[2] == ["echo"] and p.ECHO_HIT["copies"] == 2, "+echo is a transition hit"
for m in ("blur", "lift"):
    assert p.parse_subject(m + " 0-60 @ mattes/CLIP_A; every=3; width=5")["mode"] == m, m
PYEOF
"$PY" "$S/plan_to_project.py" "$KIT/samples/example-edit-plan.md" --out "$TMP/lookfx.json" --look-fx vignette=0.3,grain=0.06 >/dev/null 2>&1 \
  && "$PY" -c "import json,sys; l=json.load(open(sys.argv[1]))['look']; assert l=={'vignette':0.3,'grain':0.06}, l" "$TMP/lookfx.json" \
  && pass "plan_to_project.py --look-fx writes look.vignette and look.grain (look fx parses)" || fail "plan_to_project.py --look-fx"
# label: object drop: cutout script and overlays
mkdir -p "$TMP/od"
ffmpeg -hide_banner -v error -y -f lavfi -i "color=c=0x87CEEB:s=270x480,drawbox=x=60:y=200:w=150:h=160:color=0x333333@1:t=fill" -frames:v 1 "$TMP/od/frame.png" >/dev/null 2>&1
"$PY" "$S/object_cutout.py" "$TMP/od/frame.png" --size 270x480 --poly "0.222,0.4167 0.778,0.4167 0.778,0.75 0.222,0.75" --out "$TMP/od/public/objects/OBJ_A.png" >"$TMP/od/cut.log" 2>&1 \
  && "$PY" "$S/object_cutout.py" "$TMP/od/frame.png" --size 270x480 --grid "$TMP/od/grid.png" >/dev/null 2>&1 \
  && ffmpeg -hide_banner -v error -i "$TMP/od/public/objects/OBJ_A.png" -f rawvideo -pix_fmt rgba "$TMP/od/obj.rgba" \
  && "$PY" -X utf8 - "$TMP/od" "$S" <<'PYEOF' >"$TMP/od/check.log" 2>&1 \
  && pass "object_cutout.py: a hand outline cuts an opaque object with a clear background, prints the plan cell (src, at, width, aspect), writes a grid; objectDrop and impact are known overlays and sit on a cut without a warning" \
  || { fail "object drop: cutout script and overlays"; tail -6 "$TMP/od/check.log" | sed 's/^/        /'; }
import re, subprocess, sys
import numpy as np
d, s = sys.argv[1], sys.argv[2]
log = open(d + "/cut.log", encoding="utf8").read()
m = re.search(r"src=objects/OBJ_A\.png; at=([\d.]+),([\d.]+); width=(\d+); aspect=([\d.]+)", log)
assert m, log
ax, ay, w, asp = float(m[1]), float(m[2]), int(m[3]), float(m[4])
assert abs(ax - 0.5) < 0.01 and abs(ay - 0.75) < 0.01 and 150 <= w <= 160, (ax, ay, w)
h = round(w * asp)
a = np.fromfile(d + "/obj.rgba", np.uint8)
assert a.size == w * h * 4, (a.size, w, h)
a = a.reshape(h, w, 4)
assert a[h // 2, w // 2, 3] == 255 and a[0, 0, 3] == 0 and a[-1, -1, 3] == 0, "centre opaque, corners clear"
assert tuple(a[h // 2, w // 2, :3]) == (51, 51, 51), "the object keeps its own colour"
assert (a[..., 3] > 0).mean() > 0.85, "the PNG is cropped to the object"
assert subprocess.run([sys.executable, s + "/object_cutout.py", d + "/frame.png", "--size", "270x480", "--poly", "0.1,0.1 0.1,0.1 0.1,0.1", "--out", d + "/x.png"],
                      capture_output=True).returncode == 1, "an empty outline must be refused"
r = subprocess.run([sys.executable, s + "/object_cutout.py", d + "/frame.png", "--size", "270x480", "--model", "no-such-model.onnx", "--out", d + "/x.png"], capture_output=True)
assert r.returncode == 1 and b"ships and downloads no object model" in r.stderr + r.stdout, "a missing model must say the kit supplies none"
sys.path.insert(0, s)
import plan_to_project as p
assert {"objectDrop", "impact"} <= set(p.KNOWN) and {"objectDrop", "impact"} == set(p.LANDS_ON_CUT), "both overlays are registered and exempt from the cut-edge warning"
assert p.parse_transition("cut +jolt")[2] == ["jolt"] and p.JOLT_HIT == {"frames": 7, "blur": 36, "shake": 26}, "+jolt is a transition hit with its default"
PYEOF
# label: showreel transitions: six presentations, the occluder finder and the reverse tool
mkdir -p "$TMP/sr"
ffmpeg -hide_banner -v error -y -f lavfi -i "nullsrc=s=320x180:d=3:r=30,geq=lum='255*random(1)':cb=128:cr=128" -f lavfi -i "color=c=0x404040:s=640x180:d=3:r=30" \
  -filter_complex "[0:v][1:v]overlay=x='-640+1280*t/3':y=0,format=yuv420p" -c:v libx264 -crf 14 "$TMP/sr/pass.mp4" >/dev/null 2>&1 \
  && ffmpeg -hide_banner -v error -y -f lavfi -i "testsrc2=s=160x90:d=2:r=30" -c:v libx264 -crf 12 -pix_fmt yuv420p "$TMP/sr/src.mp4" >/dev/null 2>&1 \
  && "$PY" "$S/find_occluders.py" "$TMP/sr/pass.mp4" --json "$TMP/sr/occ.json" >"$TMP/sr/occ.log" 2>&1 \
  && "$PY" "$S/reverse_clip.py" "$TMP/sr/src.mp4" --from 0 --to 2 --out "$TMP/sr/rev.mp4" >"$TMP/sr/rev.log" 2>&1 \
  && ffmpeg -hide_banner -v error -y -sseof -0.1 -i "$TMP/sr/src.mp4" -frames:v 1 "$TMP/sr/src_last.png" \
  && ffmpeg -hide_banner -v error -y -i "$TMP/sr/rev.mp4" -frames:v 1 "$TMP/sr/rev_first.png" \
  && "$PY" -X utf8 - "$TMP/sr" "$S" "$KIT/skill/short-video-editing" <<'PYEOF' >"$TMP/sr/check.log" 2>&1 \
  && pass "six showreel transitions are in project.ts, timeline.ts, transitions.tsx and the HyperFrames fallback list and plannable; find_occluders.py finds a flat mass sweeping across a textured picture; reverse_clip.py writes the stretch backwards" \
  || { fail "showreel transitions: six presentations, the occluder finder and the reverse tool"; tail -6 "$TMP/sr/check.log" | sed 's/^/        /'; }
import json, re, subprocess, sys
import numpy as np
d, s, k = sys.argv[1], sys.argv[2], sys.argv[3]
NEW = ["gridFlash", "cropPop", "cropNegative", "flashWipe", "blackFlicker", "zoomFade"]
ts = open(k + "/assets/remotion-template/src/project.ts", encoding="utf8").read()
tl = open(k + "/assets/remotion-template/src/engine/timeline.ts", encoding="utf8").read()
tr = open(k + "/assets/remotion-template/src/engine/transitions.tsx", encoding="utf8").read()
hf = open(s + "/project_to_hyperframes.py", encoding="utf8").read()
for t in NEW:
    assert f'| "{t}"' in ts, f"{t} missing from TransitionType"
    assert re.search(rf"\b{t}: \d+,", tl), f"{t} missing from DEFAULT_FRAMES"
    assert f'case "{t}":' in tr, f"{t} has no case in presentationFor"
    assert f'"{t}"' in hf, f"{t} missing from the HyperFrames fallback list"
sys.path.insert(0, s)
import plan_to_project as p
for t in NEW:
    assert t.lower() in p.CANON, f"{t} is not a plannable transition"
occ = json.load(open(d + "/occ.json"))
assert occ and any(0.5 <= c["peak"] <= 2.0 and c["cover"] >= 0.9 for c in occ), occ
assert "timelinepanel" in {k.lower() for k in p.KNOWN}, "timelinePanel must be a plannable overlay"
assert "wrote" in open(d + "/rev.log", encoding="utf8").read(), "reverse_clip.py must say what it wrote"
def px(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
    return np.frombuffer(r.stdout, np.uint8).astype(float)
a, b = px(d + "/src_last.png"), px(d + "/rev_first.png")
assert a.size == b.size and np.abs(a - b).mean() < 10, "the first frame of the reversed clip is the last frame of the source"
PYEOF
SVK_SELFTEST_PY="$PY" bash -s "$KIT/skill/short-video-editing" <<'EDITORTEST' >"$TMP/editor.log" 2>&1 \
  && pass "editor.py: serves the project, saves with a history snapshot, restores, refuses traversal and foreign hosts" || { fail "editor.py"; grep FAIL "$TMP/editor.log" | head -6 | sed 's/^/        /'; }
#!/usr/bin/env bash
# Selftest snippet for scripts/editor.py (stdlib only; needs curl and a working Python 3: SVK_SELFTEST_PY, else python3). Usage: editor-selftest-snippet.sh [SKILL_DIR]
# SKILL_DIR defaults to skill/short-video-editing relative to the repo root. Prints PASS/FAIL lines, exits 1 on any FAIL.
set -u
PYX="${SVK_SELFTEST_PY:-python3}"   # on Windows "python3" may be the Microsoft Store stub: selftest.sh passes the Python it tested
SKILL="${1:-skill/short-video-editing}"
TMP="$(mktemp -d)"; PORT_FILE="$TMP/port"; FAILS=0; PID=""
cleanup() { [[ -n "$PID" ]] && kill "$PID" 2>/dev/null; rm -rf "$TMP"; }
trap cleanup EXIT
pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1"; FAILS=$((FAILS+1)); }
check() { if eval "$2"; then pass "$1"; else fail "$1"; fi; }

# a throw-away render folder: the example project, an empty public/ and out/
mkdir -p "$TMP/render/public/clips" "$TMP/render/out"
cp "$SKILL/assets/remotion-template/project.example.json" "$TMP/render/v1.json"

"$PYX" "$SKILL/scripts/editor.py" "$TMP/render" --project v1.json --port 0 --no-open >"$TMP/server.log" 2>&1 &
PID=$!
URL=""
for _ in $(seq 1 50); do
  URL="$(grep -o 'http://127.0.0.1:[0-9]*/' "$TMP/server.log" 2>/dev/null | head -1)"
  [[ -n "$URL" ]] && break; sleep 0.1
done
[[ -n "$URL" ]] || { echo "FAIL  editor.py did not start:"; cat "$TMP/server.log"; exit 1; }
B="${URL%/}"; J='Content-Type: application/json'
pass "editor.py started at $URL"

check "page is served"                  'curl -sf "$B/" | grep -q "Video editor"'
check "GET /api/project returns scenes" 'curl -sf "$B/api/project" | "$PYX" -c "import sys,json; d=json.load(sys.stdin); assert d[\"project\"][\"scenes\"] and d[\"name\"]==\"v1.json\""'

# edit one scene length through the API and save
"$PYX" - "$TMP/render/v1.json" "$TMP/edited.json" <<'EOF'
import json, sys
d = json.load(open(sys.argv[1])); d["scenes"][0]["type"] = "EDITED"; json.dump(d, open(sys.argv[2], "w"))
EOF
check "POST save is accepted"           'curl -sf -X POST -H "$J" --data-binary @"$TMP/edited.json" "$B/api/project?name=v1.json" | grep -q "\"ok\": true"'
check "saved file holds the edit"       'grep -q EDITED "$TMP/render/v1.json"'
check "history snapshot was written"    'ls "$TMP"/render/.editor-history/v1-*.json >/dev/null 2>&1 && ! grep -q EDITED "$TMP"/render/.editor-history/v1-*.json'
check "history API lists it"            'curl -sf "$B/api/history?name=v1.json" | "$PYX" -c "import sys,json; assert len(json.load(sys.stdin)[\"items\"])==1"'
check "invalid project is refused (400)" '[[ "$(curl -s -o /dev/null -w %{http_code} -X POST -H "$J" -d "{\"nope\":1}" "$B/api/project?name=v1.json")" == 400 ]]'
check "wrong Content-Type is refused (415)" '[[ "$(curl -s -o /dev/null -w %{http_code} -X POST -d "{}" "$B/api/project?name=v1.json")" == 415 ]]'

for p in "/media/../../etc/passwd" "/media/%2e%2e/%2e%2e/etc/passwd" "/out/../v1.json" "/media/.hidden"; do
  check "traversal refused: $p"         '[[ "$(curl -s --path-as-is -o /dev/null -w %{http_code} "$B$p")" =~ ^4 ]]'
done
check "foreign Host header refused"     '[[ "$(curl -s -o /dev/null -w %{http_code} -H "Host: evil.example" "$B/api/info")" == 403 ]]'

kill "$PID"; wait "$PID" 2>/dev/null; PID=""
check "server stopped"                  '! curl -sf -m 1 "$B/api/info" >/dev/null 2>&1'
[[ $FAILS -eq 0 ]] && echo "editor selftest: all PASS" || { echo "editor selftest: $FAILS FAIL"; exit 1; }
EDITORTEST
sed 's/accent=[^;|]*[^;| ]/&; font=no-such-font/' "$KIT/samples/example-edit-plan.md" >"$TMP/fontplan.md"
"$PY" "$S/plan_to_project.py" "$TMP/fontplan.md" --out "$TMP/fontplan.json" 2>&1 | grep -q "font=no-such-font is not in the font library" \
  && pass "plan_to_project.py warns about a font id the library does not have" || fail "plan_to_project.py unknown font warning"
cat >"$TMP/rep.json" <<'JSON'
{"transitions": [{"t": 2.4, "frames": 18, "family": "slide", "direction": "left"}, {"t": 5.0, "frames": 12, "family": "dip-to-black", "direction": null}],
 "shots": [{"start": 0, "end": 2.4, "camera": {"quality": "ok", "driver": "zoom-in", "ease": "ease-in-out", "shake": {"level": "handheld"}}, "speed": {"ramp": "none"}}],
 "grade": {"nearest": [{"look": "golden-hour"}]}}
JSON
"$PY" -X utf8 "$S/technique.py" match "$TMP/rep.json" >"$TMP/match.log" 2>&1 \
  && grep -q "transition:slide" "$TMP/match.log" && grep -q "camera-move:push" "$TMP/match.log" && grep -q "camera-option:shake" "$TMP/match.log" && grep -q "grade:golden-hour" "$TMP/match.log" \
  && grep -A1 "dip-to-black" "$TMP/match.log" | grep -q "NO CARD" \
  && pass "technique.py match maps an analyser report onto cards and says plainly where no card exists" || { fail "technique.py match"; cat "$TMP/match.log" | head -12 | sed 's/^/        /'; }
cat >"$TMP/analysis-test.sh" <<'ANALYSISTEST'
# Not part of selftest.sh. Needs ffmpeg (xfade, geq, zoompan, vidstabdetect) and numpy. Usage: bash analysis-selftest-snippet.sh [REPO] [WORKDIR]
set -euo pipefail
REPO=${1:?repo root}
WORK=${2:-$(mktemp -d)}
SCR=$REPO/skill/short-video-editing/scripts
PY=${SVK_PYTHON:-python3}
mkdir -p "$WORK" && cd "$WORK"
FF="ffmpeg -hide_banner -v error -y"

# ---- sources: three different smooth, colourful stills; a blurred-noise texture (corners to track) for camera tests
plasma() { $FF -f lavfi -i "nullsrc=s=360x640,geq=r='128+100*sin(X/$1+Y/$2)':g='128+90*sin(X/$3-Y/$4)':b='128+100*sin((X+Y)/$5)'" -frames:v 1 -update 1 "$6"; }
plasma 9 13 7 11 17 T1.png
plasma 23 5 31 9 13 T2.png
plasma 6 19 11 27 8 T3.png
# Texture for the camera tests: a hash of X and Y, not geq random(): random() keeps one state per filter slice, so with 16 threads the picture repeats every 120 rows
# and a zoom looks like a pan to vid.stab (the measured zoom came out inverted on a 16-core machine).
NOISE="255*((sin(X*12.9898+Y*78.233)*43758.5453)-floor(sin(X*12.9898+Y*78.233)*43758.5453))"
$FF -f lavfi -i "nullsrc=s=1200x640,geq=$NOISE:128:128,boxblur=2,eq=contrast=2.5" -frames:v 1 -update 1 pan_tex.png
$FF -f lavfi -i "nullsrc=s=1080x1920,geq=$NOISE:128:128,boxblur=3,eq=contrast=2.5" -frames:v 1 -update 1 zoom_tex.png

# ---- 1. transitions: A and B stills alternate, 0.6 s xfade each, 2.0 s hold: transition k starts at 1.4*k s
FAMS=(fade fadeblack fadewhite dissolve wipeleft wipeup slideleft slideright coverleft revealleft)
IN=(); FC=""; prev="[0:v]"
for i in $(seq 0 ${#FAMS[@]}); do
  [ $((i % 2)) -eq 0 ] && img=T1.png || img=T2.png
  IN+=(-loop 1 -framerate 30 -t 2.0 -i $img)
done
for k in "${!FAMS[@]}"; do
  n=$((k + 1)); off=$(awk -v n="$n" 'BEGIN { printf "%.1f", n * 1.4 }')
  FC+="${prev}[$n:v]xfade=transition=${FAMS[$k]}:duration=0.6:offset=$off[x$n];"; prev="[x$n]"
done
$FF "${IN[@]}" -filter_complex "${FC%;}" -map "$prev" -pix_fmt yuv420p -crf 14 xfades.mp4

# ---- 2. a push of known rate: z = 1 + 0.1 * seconds (1.0 -> 1.3 in 3 s), linear
$FF -i zoom_tex.png -vf "zoompan=z='1+0.1*on/30':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=90:s=360x640:fps=30" -pix_fmt yuv420p -crf 14 push.mp4

# ---- 3. speed: a pan of 1 px/frame for 60 frames, then every 3rd frame (3 px/frame): a 1x -> 3x change; and a 0.8 s freeze
$FF -loop 1 -framerate 30 -t 12 -i pan_tex.png -vf "crop=360:640:x='t*30':y=0,fps=30,select='if(lt(n,60),1,not(mod(n,3)))',setpts=N/30/TB" -pix_fmt yuv420p -crf 14 speed.mp4
$FF -loop 1 -framerate 30 -t 3 -i pan_tex.png -vf "crop=360:640:x='t*30':y=0,fps=30,loop=loop=24:size=1:start=45,setpts=N/30/TB" -pix_fmt yuv420p -crf 14 freeze.mp4

# ---- 4. grade: three different stills, warm / untouched / cold, hard cuts
$FF -loop 1 -framerate 30 -t 1.5 -i T1.png -loop 1 -framerate 30 -t 1.5 -i T2.png -loop 1 -framerate 30 -t 1.5 -i T3.png -filter_complex \
 "[0:v]colorchannelmixer=rr=1.2:bb=0.8[a];[1:v]null[b];[2:v]colorchannelmixer=rr=0.8:bb=1.2[c];[a][b][c]concat=n=3:v=1:a=0" -pix_fmt yuv420p -crf 14 grade.mp4

# ---- run the analyzer (grade.mp4 also exercises --compare against the push clip)
for c in xfades push speed freeze; do $PY "$SCR/analyze_reference.py" $c.mp4 --out out_$c --dense auto > log_$c.txt 2>&1 || { cat log_$c.txt; exit 1; }; done
$PY "$SCR/analyze_reference.py" grade.mp4 --out out_grade --compare push.mp4 > log_grade.txt 2>&1 || { cat log_grade.txt; exit 1; }

REPO_SCR=$SCR $PY - <<'PYEOF'
import json, sys
R = lambda n: json.load(open(f"out_{n}/report.json"))
fails = []
def check(ok, msg):
    print(("PASS  " if ok else "FAIL  ") + msg)
    if not ok: fails.append(msg)

# 1. transition families: (index k, accepted families, direction or None). Geometry of iris/circle/diagonal styles is NOT asserted: not separable.
rep = R("xfades")
runs = [t for t in rep["transitions"] if t["kind"] == "run"]
want = {1: ({"crossfade"}, None), 2: ({"dip-to-black"}, None), 3: ({"dip-to-white"}, None), 4: ({"dissolve"}, None),
        5: ({"mask-wipe"}, "left"), 6: ({"mask-wipe"}, "up"), 7: ({"slide"}, "left"), 8: ({"slide"}, "right"),
        9: ({"cover"}, "left"), 10: ({"reveal"}, "left")}
for k, (fams, d) in want.items():
    t = min(runs, key=lambda r: abs(r["t"] - 1.4 * k), default=None)
    ok = t is not None and abs(t["t"] - 1.4 * k) < 0.3
    check(ok and t["family"] in fams and 15 <= t["frames"] <= 20 and (d is None or t["direction"] == d),
          f"xfade #{k}: expected {sorted(fams)} {d or ''}, got {None if not ok else (t['family'], t['direction'], t['frames'], t['confidence'])}")
check(len(rep["evidence"]) >= 4 and all(__import__("os").path.exists(f"out_xfades/{e['file']}") for e in rep["evidence"]), f"evidence strips written ({len(rep['evidence'])})")

# 2. zoom push 1.0 -> 1.3 in 3 s, linear
sh = R("push")["shots"][0]["camera"]
check(sh["quality"] == "ok" and sh["driver"] == "zoom-in", f"push: driver {sh.get('driver')} (quality {sh['quality']})")
check(abs(sh.get("zoom_end", 0) - 1.29) <= 0.05, f"push: zoom_end {sh.get('zoom_end')} vs 1.29 (+-0.05)")
check(sh.get("ease") == "linear", f"push: ease {sh.get('ease')} (linear expected)")

# 3. speed: 1x -> 3x ramp; freeze of 0.8 s
sp = R("speed")["shots"][0]["speed"]
check(sp["ramp"] == "speed-up" and 2.0 <= (sp["ramp_factor"] or 0) <= 4.6, f"speed: {sp['ramp']} x{sp['ramp_factor']} (3x expected; vid.stab reads whole pixels at 480 px, so 1.33 px/frame reads 1 and the ratio up to 4: 2..4.6 accepted)")
cam = R("speed")["shots"][0]["camera"]
check(cam.get("quality") == "ok" and cam["driver"] == "pan-right", f"speed clip camera: {cam.get('driver')} (camera moves right = content moves left)")
fz = [z for sh in R("freeze")["shots"] for z in sh["speed"]["frozen_runs"]]
check(len(fz) == 1 and 0.7 <= fz[0]["seconds"] <= 0.95, f"freeze: {fz}")

# no clip with a pan, a push or a freeze may report a change of scene
for n in ("push", "speed", "freeze"):
    bad = [t for t in R(n)["transitions"] if t["family"] not in ("content-motion", "hard-cut")]
    check(not bad and len(R(n)["shots"]) == 1, f"{n}: one shot, no transition reported (got {[(t['t'], t['family']) for t in bad]})")

# 4. grade: warmth warm > untouched > cold, shots counted, compare written
g = R("grade")
w = [p["warmth_b"] for p in g["grade"]["per_shot"]]
check(len(g["shots"]) == 3 and w[0] > w[1] + 5 and w[1] > w[2] + 5, f"grade: 3 shots, warmth b* per shot {w}")
check(len(g["grade"]["global"]["palette"]) >= 3 and g["grade"]["nearest"], "grade: palette and nearest kit looks present")
import os
d = open("out_grade/diff.md", encoding="utf-8").read() if os.path.exists("out_grade/diff.md") else ""
check("| shots | 3 |" in d and "grade warmth" in d, "compare: diff.md lists shots and grade rows")
check(os.path.exists("out_grade/mine/report.json"), "compare: the recreation was analysed too")

# 5. no drawtext on this build: sheets exist and carry a tile index (labels are optional)
check(os.path.exists("out_xfades/scenes.png") and rep["sheet_times"].get("scenes.png"), "sheets: scenes.png written with its tile times")
print("\nFAILED: %d" % len(fails) if fails else "\nALL PASS")
sys.exit(1 if fails else 0)
PYEOF
ANALYSISTEST
SVK_PYTHON="$PY" bash "$TMP/analysis-test.sh" "$KIT" >"$TMP/analysis.log" 2>&1 \
  && pass "analyze_reference.py: transition families, camera zoom and pan, speed ramps, freezes, grade fingerprint, evidence strips and --compare on synthetic clips with known answers" || { fail "analyze_reference.py closed-loop check"; grep FAIL "$TMP/analysis.log" | head -6 | sed 's/^/        /'; tail -3 "$TMP/analysis.log" | sed 's/^/        /'; }

if [[ $RENDER -eq 1 ]]; then
  echo "17. Remotion render (--render)"
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
  # the newer techniques as stills: shader and CSS transitions at mid-cut, a subject outline, handheld shake (synthetic clips; no GPU needed)
  mkdir -p "$RENDER_DIR/public/clips" "$RENDER_DIR/public/mattes" "$RENDER_DIR/out"
  ffmpeg -hide_banner -v error -y -f lavfi -i "testsrc2=s=1080x1920:r=30:d=4" -c:v libx264 -pix_fmt yuv420p "$RENDER_DIR/public/clips/CLIP_A.mp4" \
    && ffmpeg -hide_banner -v error -y -f lavfi -i "smptebars=s=1080x1920:r=30:d=4" -c:v libx264 -pix_fmt yuv420p "$RENDER_DIR/public/clips/CLIP_B.mp4" \
    && ffmpeg -hide_banner -v error -y -f lavfi -i "color=c=white@0:s=1080x1920,format=rgba" -vf "geq=r=255:g=255:b=255:a='if(lt(pow((X-540)/300,2)+pow((Y-900)/700,2),1),255,0)'" -frames:v 1 "$RENDER_DIR/public/mattes/CLIP_A_0.png"
  "$PY" -X utf8 - "$RENDER_DIR/showcase.json" <<'PYEOF'
import json, sys
types = ["cut", "blinds", "diamond", "doors", "glitchSlice", "spinZoom", "filmBurn", "zoomBlur"]
scenes = []
for i, t in enumerate(types):
    sc = {"clip": "CLIP_A" if i % 2 == 0 else "CLIP_B", "in": 0, "start": float(i), "end": float(i + 1), "transition": {"type": t}}
    if i == 0:
        sc["subject"] = {"mode": "outline", "matte": "mattes/CLIP_A", "frames": [0], "show": [0, 40], "color": "#FFD23F", "width": 14}
    if i == 1:
        sc["camera"] = {"move": "push", "from": 1.1, "to": 1.25, "shake": {"amp": 14}}
    scenes.append(sc)
json.dump({"fps": 30, "width": 1080, "height": 1920, "duration": 8, "scenes": scenes, "overlays": [], "captions": [], "look": {"vignette": 0.3, "grain": 0.06}}, open(sys.argv[1], "w"))
PYEOF
  if (cd "$RENDER_DIR" && node stills.mjs showcase.json out/sh 0.5 1.5 2 3 4 5 6 7) >"$TMP/showcase.log" 2>&1 \
     && [[ "$(ls "$RENDER_DIR"/out/sh_*.jpg 2>/dev/null | wc -l)" -ge 8 ]] && [[ -z "$(find "$RENDER_DIR"/out -name 'sh_*.jpg' -size -4k)" ]]; then
    pass "rendered stills of the newer techniques: subject outline, shake, blinds, diamond, doors, glitchSlice, spinZoom, filmBurn, zoomBlur, vignette and grain (LOOK at out/sh_*.jpg)"
  else fail "the newer techniques did not render"; tail -6 "$TMP/showcase.log" | sed 's/^/        /'; fi
  ffmpeg -hide_banner -v error -y -f lavfi -i "color=c=black:s=1080x1920:r=30:d=4" -c:v libx264 -pix_fmt yuv420p "$RENDER_DIR/public/clips/BLACK.mp4"
  "$PY" -X utf8 - "$RENDER_DIR/textbox.json" <<'PYEOF'
import json, sys
sc = [{"clip": "BLACK", "in": 0, "start": 0.0, "end": 4.0, "transition": {"type": "cut"}}]
ov = [{"component": "textbox", "start": 0, "end": 4, "props": {"text": "SIEUCAPDAIDUONGKHONGLOSOSAU", "box": [0.1, 0.2, 0.3, 0.05], "size": 200, "color": "#ffffff", "in": "rise"}},
      {"component": "textbox", "start": 0, "end": 4, "props": {"text": "Một câu rất dài rất dài rất dài rất dài rất dài rất dài rất dài rất dài rất dài rất dài", "box": [0.1, 0.5, 0.5, 0.1], "size": 90, "color": "#ffffff", "in": "rise"}}]
json.dump({"fps": 30, "width": 1080, "height": 1920, "duration": 4, "scenes": sc, "overlays": ov, "captions": []}, open(sys.argv[1], "w"), ensure_ascii=False)
PYEOF
  if (cd "$RENDER_DIR" && node stills.mjs textbox.json out/tb 2) >"$TMP/tb_render.log" 2>&1 \
     && ffmpeg -hide_banner -v error -i "$RENDER_DIR/out/tb_0002.00.jpg" -f rawvideo -pix_fmt gray - 2>/dev/null | "$PY" -c "
import sys, numpy as np
a = np.frombuffer(sys.stdin.buffer.read(), np.uint8).reshape(1920, 1080) > 200
def cols(y0, y1):
    c = np.where(a[y0:y1].any(axis=0))[0]
    return (int(c.min()), int(c.max()), int(a[y0:y1].sum())) if len(c) else None
one, two = cols(300, 700), cols(900, 1250)
assert one and two, ('no text drawn', one, two)
assert 108 - 8 <= one[0] and one[1] <= 432 + 8, ('a long word left its box sideways', one)
assert 108 - 8 <= two[0] and two[1] <= 648 + 8, ('a long sentence left its box sideways', two)
print(one, two)
" >"$TMP/tb_px.log" 2>&1; then
    pass "textbox: measured fit (a 27-letter word and a long sentence stay inside their boxes, measured on the rendered pixels)"
  else fail "textbox: measured fit did not hold"; tail -4 "$TMP/tb_render.log" "$TMP/tb_px.log" | sed 's/^/        /'; fi
fi

echo
[[ $FAIL -eq 0 ]] && printf '\033[1;32mAll checks passed.\033[0m\n' || { printf '\033[1;31m%d check(s) failed.\033[0m\n' "$FAIL"; exit 1; }
