---
name: short-video-editing
description: >-
  Plan, edit and render short vertical videos (TikTok, TikTok Shop, Reels, Shorts; 10–90 s) of any kind: product demos and reviews, before/after, unboxing, real-estate tours, food, talking heads and testimonials, tutorials, fashion and beauty, travel/event montages, sale promos. It analyses the footage and the request, picks a genre playbook, then does the edit: footage correction (white balance, grade, stabilisation, denoise), voice cleanup and loudness, cuts on voice pauses or music beats, speed ramps, transitions, camera moves, captions, motion graphics, sound effects, a Remotion or HyperFrames render and export. It also rebuilds a reference video the user supplies, including an agency pitch cut from a presenter's takes, lip-synced. Use it whenever someone asks to make, edit, cut, script, caption, colour, mix or improve a short-form video, or several from one batch of footage, even for a small part of the job ('just add captions', 'fix the colour', 'cut this to the music').
---

# Short Video Editing

Make short vertical videos that get watched to the end, say one thing clearly, and survive platform
review. The kit is **genre-agnostic**: what depends on the kind of video (rhythm, structure, look,
sound, graphics, compliance) lives in a **playbook** (`playbooks/`); what does not (safe zones,
caption alignment, the renderer, the rights policy) is shared. Read `playbooks/README.md` once.

The data behind the defaults: reach, not persuasion, is the bottleneck on short-form feeds (16,242
measured TikTok Shop videos: the top 20% by views earned 95% of revenue, and low-reach videos converted
at the same rate when seen). Both TikTok and Instagram say they rank on watching to the end and on
shares. So every playbook spends its care on the first three seconds, the rhythm, and a frame that
keeps the subject visible.

---

## Rules for every video

Checked mechanically where a tool exists. Do not deliver a plan that breaks them.

1. **Analyse before planning.** Look at the footage (contact sheet) and measure it (`inspect_footage.py
   --measure`); know the user's goal. Choose the playbook from both and say which and why.
2. **The hook resolves within 3 s**; frame 0 is the thumbnail and never empty. Picture, on-screen text
   and sound each do a different job.
3. **The playbook's pacing holds**: scene lengths, runtime band, hook beats (`pacing_checker.py`, which
   reads the plan's `**Playbook:**` line). Push back, with the playbook's reason, on lengths outside its band.
4. **Every plan carries explicit timestamps** in the tables of `assets/edit-plan-template.md`.
5. **Claims are checked before anything is voiced or written** against the playbook's checklist and
   `references/claims-and-compliance.md`. Claims inside a supplied voice are flagged, never silently kept.
6. **Footage is owned or licensed, and videos are not reshuffles of each other.** Never download or
   splice other people's videos (Douyin, TikTok, YouTube, competitors) without a written commercial
   licence; no source range is used twice in a batch (`footage_overlap_checker.py`). When the footage
   cannot reach the batch size, say so with the numbers and propose shooting or licensed creators.
   Read `references/policy.md` before planning a batch.
7. **Graphics respect the frame**: nothing over a face; nothing in the platform UI zones; titles hug the
   top (y ≈ 236–420), captions the lower third (y ≈ 1340, ≤ 2 lines); the middle belongs to the footage;
   at most two informational elements at once. Reels ads need `--platform reels-ad`.
8. **A demonstration is never faked**: no hidden cut between a BEFORE and an AFTER, the same grade on
   both, time compression labelled on screen.
9. **Say what was not verified.** A tool cannot hear: never say "listened" unless someone did.

## Decisions that belong to the human — ask, do not decide silently

Any download (packages, models, music, stock): name, source, size; that includes the first
`npx hyperframes` (it fetches the package). The ElevenLabs plan (free-plan audio
is never commercial). The Remotion licence (free up to 3 employees; HyperFrames is Apache-2.0, so a studio
above the limit can render with it: `references/hyperframes-flow.md` §1). Third-party footage. The batch size
when footage runs short. Trimming a supplied voice or dropping a claim (say which sentences). Whether
the video will be boosted as an ad (no before/after in ads).

---

## Workflow

Run scripts from this skill's folder (`~/.claude/skills/short-video-editing` once installed). They
need Python 3 and a full ffmpeg; the scripts that need faster-whisper or numpy (`align_captions.py`, `suggest_cuts.py --music`,
`match_voice_takes.py`, `find_cutaways.py`, `find_occluders.py`, `person_matte.py`, `object_cutout.py`, `check_lipsync.py`, `mix_report.py`, `make_music.py`, `analyze_reference.py`)
re-launch themselves in the kit's venv (`$SVK_PYTHON`, or the one `setup.sh` built).

### 0. Is this machine ready? (first time in a chat, and whenever a tool is "not found")

```bash
python scripts/doctor.py          # changes nothing; names every missing item and how to install it
```

It checks Python, the venv (faster-whisper, numpy, onnxruntime), ffmpeg **and the filters the scripts call**
(vidstab, zscale, haldclut, afftdn, loudnorm, tile, …), the Whisper model, the optional person-segmentation
model (only the agency recipe needs it), Node (rendering only), the ElevenLabs key (presence only) and free disk. If something required is missing, set it up before any video work:

- The kit repo is on this machine (doctor prints its path) → `cd <repo> && ./setup.sh`, then
  `./selftest.sh`. On a machine without it: `gh auth login --web && gh auth setup-git`, clone
  `https://github.com/it-2sgroup/short-video-kit.git`, read its `CLAUDE.md` (the setup steps), run `./setup.sh`.
  Windows: through Git Bash.
- **Ask before any download or install** (Whisper model ~460 MB, ffmpeg, npm + Chromium ~300 MB, the person
  model 168 MB via `./setup.sh --person-model`) and name it. Never ask for the ElevenLabs key in chat: the user runs `./setup.sh --set-key` themselves.
- Show doctor's real output; a failure is never "probably fine". Low disk space is a stop sign for a
  4K batch, not a footnote.
- A new chat must be started after the skill is installed or updated so it loads.

### 1. Analyse the footage and the request, choose the playbook

```bash
python scripts/inspect_footage.py CLIPS --measure --json analysis.json   # light, colour cast, noise, shake, motion, speech, HDR, fps
python scripts/contact_sheet.py CLIPS --out clips.png                     # one row per clip: OPEN AND LOOK at it
python scripts/playbook.py suggest --intent "<the user's words>" --analysis analysis.json
python scripts/playbook.py show <id>                                      # the rules you will be held to
```

Then read `playbooks/<id>.md`. If the request and the footage agree, state the choice in one line and
go on. If they disagree, or two playbooks are close, or facts the video needs are missing (price,
address, offer dates, the voice), ask **at most three** questions in one message, each with your
default (`playbooks/README.md` → Questions). For a batch: budget the footage first
(`references/footage-ingest.md` §1b, `policy.md` §4.1).

### 1b. A reference video to copy ("make it like this sample")

```bash
python scripts/analyze_reference.py sample.mp4 --out ref/ --dense 0-3,15-20   # shots, transitions (and their family), camera paths, speed, flashes, grade, loudness, sheets
python scripts/technique.py search "glitch rgb split"                        # is it already in the kit, under the name editors use?
```

Open `ref/report.md`, `scenes.png`, every `dense_*.png` (every 2nd frame of a range: a flash on frames 0, 2, 4, a text pile
assembling) and every `spectrum_*.png` (a click is a vertical streak, a whoosh a slanted band) and **look**. The numbers give the
frame-exact timing; the sheets give the technique; `references/reference-analysis.md` says which keys are measured and which are Claude's reading.
Write down every technique you see in neutral words (text effects, card layouts, transitions, camera moves, grade, subject effects, sound on each cut), then
**find each one in the catalogue** (`technique.py search`, `list`, `show`). Found: use it. Almost found: a new parameter, not a new technique. Not found: **research it,
implement it where its kind lives, write its card, document it, prove it in selftest.sh** (`references/adding-techniques.md`: one loop for every kind; what
was researched but not built is in `references/technique-backlog.md`), never fake it with a lookalike. A presenter talking to camera with a service pitch →
`references/agency-pitch-recipe.md`, step by step. The sample's logo, and any customer work shown on its cards, belong to their owners: ask for the vector
logo and for consent. Do not copy the sample's music, footage or typeface; the case itself (client, dates, numbers) goes in `docs/CASE-LOG.md`, never in the skill.

### 2. Prepare the footage

```bash
python scripts/new_remotion_project.py RENDER --playbook <id> --proxies CLIPS   # theme + corrected, graded proxies
```

`prepare_footage.py` (called by `--proxies`) tone-maps HDR, frames to 9:16, denoises, stabilises,
white-balances, fixes exposure and applies the playbook's grade; `--fix "CLIP:rotate=-1.5"` levels a
horizon. Look at `contact_sheet.py RENDER/public/clips` and read `corrections.json`
(`references/image-processing.md`). Ask before `--install` (npm + Chromium, ~300 MB).

### 3. Sound: voice, music

- **Supplied voice**: several files → match by name and ask when unsure. Too long for the playbook's
  band → `trim_voice.py voice.mp3 --silences`, keep whole sentences with `--keep`, tell the user which
  were dropped. Then `process_audio.py voice voice.mp3 --out RENDER/public/audio/v1.wav`.
- **Landmarks that land (road trips, montages, tours):** `objectDrop` + `impact` overlays and `object_cutout.py`; the recipe is "The object drop" in
  `references/layout-and-motion-graphics.md` (cut the next shot's object out of its first frame, start the overlay `fall/fps` before the cut).
- **Showreel and montage techniques (grid reveal, frame click, teleport, black flash, zoom fade, mask and shape transitions, reverse, match-cut bursts):** `references/transition-pack.md` measures each one in frames and says how to build it: the transitions `gridFlash`, `cropPop`, `cropNegative`, `flashWipe`, `blackFlicker`, `zoomFade`; `find_occluders.py` finds the moments an object covers the lens (where to hide a cut); `reverse_clip.py` writes a stretch backwards; the rest are recipes.
- **Agency pitch end to end:** `references/agency-pitch-recipe.md` — `match_voice_takes.py` (lag per take), `find_cutaways.py`, `person_matte.py` (silhouette flash,
  head positions for the beauty light), `agency_plan.py` (draft plan), 14 text effects, caption highlights, `make_music.py`, a varied CC0 sound bank,
  `finish_video.py` (masters), `check_lipsync.py` and `mix_report.py` (proof).
- **Voice cut from the takes** (a presenter's camera audio, spliced): `match_voice_takes.py voice.mp3 clips/` prints `clip time = voice time + lag` per take, so each scene uses the take's own
  picture with `In = start + lag` and the lips are exact; stretches no take covers get cutaways. Used by `talking-head:agency` (service pitches: loud text blocks, card sections over an
  animated grid, theme `crimson`; `playbooks/talking-head.md`).
- **Talking head** (speech on camera): `trim_voice.py talk.mp4 --jumpcut --out voice.wav --scenes-out
  cuts.json` removes the pauses and gives the scenes with their source times; then `process_audio.py voice`.
- **Synthesized voice**: write to the word budget (~4.5–5 words/s), check claims, then
  `make_voiceover.py --quota`, `--dry-run`, synthesize (`references/voiceover-and-captions.md`;
  Vietnamese needs `eleven_turbo_v2_5`), and `process_audio.py voice --no-clean`.
- **Captions and word timings**: `align_captions.py voice.wav --out draft.srt [--prompt "BRAND, domain words"]`
  → correct the transcript by hand into `script.txt` → `align_captions.py voice.wav --script script.txt --out
  captions.srt --words-out words.json`. Whisper gives the timing, the script gives the words; `--prompt` primes it with
  brand names it would otherwise mishear. A sentence you could not hear well is **flagged to the user, not guessed**.
- **Music** (licensed for the platform and a business account; `references/audio-and-music.md`):
  `process_audio.py music track.mp3 --out RENDER/public/audio/music.wav`.

### 4. Cut and plan

```bash
python scripts/suggest_cuts.py words.json --playbook <id> --json > cuts.json                 # voice-driven: cut on pauses
python scripts/suggest_cuts.py --music RENDER/public/audio/music.wav --end 40 --playbook <id> --json > cuts.json   # music-driven: on beats
python scripts/playbook.py skeleton <id> --cuts cuts.json --title "…" > edit-plan.md          # Type, Transition, Speed, hints, checklist
python scripts/plan_scenes.py --library library.json --plan edit-plan.md --kinds "…" --used <other plans>   # Source/In without reuse
```

Fill the plan (`assets/edit-plan-template.md`): every scene a Source and In (a kept talking-head take
already has them), a transition from the playbook, a Camera cell or blank for `--auto-camera`
(`references/camera-moves.md`; for a scene with an action to follow or reveal, **keyframes**:
`keys 0=1.05 ; 0.4=1.38@0.34,0.5 out ; 1=1.38@0.32,0.54 soft`), a Speed where it earns its place (`2x` for waiting, `ramp 1>2.5>1`
through a doorway, `montage` / `hero` / `bullet` as named curves, `0.5x` on a 60 fps money shot: `references/cutting-and-pacing.md`; a handheld
`shake mild` on a locked-off take). Cut on pauses or beats, never inside a word, never across a reveal. The whole technique library is searchable by name:
`python scripts/technique.py list --kind transition` (31 transitions, text effects, subject effects, grades, camera options, speed curves, looks...), `show <id>`, `search "<words>"`.

### 5. Design the graphics layer

Fill the **Overlays** table with the playbook's components (`references/layout-and-motion-graphics.md`):
titles (`references/typography.md`: 3–4 styles, never the same twice in a row, one accent word), and
the information graphics the content needs — `specs` (area, rooms, direction), `pin` (place), `label`
(room, dish, item), `stat` (a counted-up number), `chart` (bars), `price`, `step`, `checklist`, `thumbs`
(a spoken list of three), `compare` (before/after), `image` (logo, floor plan), `cart` (TikTok Shop's real
product bar only), and effects shaped by a person matte (silhouette flash, outline, glow, spotlight, colour pop, text behind the subject: the `Subject` cell,
`references/subject-effects.md`). Anchor to words with `@"phrase"`. On-screen text says something **different** from
the voice. Every number on screen comes from the user or the documents.

### 6. Check the plan

```bash
python scripts/pacing_checker.py edit-plan.md                       # the playbook's rules; errors block delivery
python scripts/footage_overlap_checker.py plans/v1.md plans/v2.md --clips CLIPS   # every plan of the batch, named
```

### 7. Compile and render

```bash
python scripts/plan_to_project.py edit-plan.md --out RENDER/v1.json --voice audio/v1.wav --music audio/music.wav \
    --captions captions.srt --words words.json --auto-camera --analysis analysis.json --auto-sfx [--platform reels-ad]
cd RENDER && node stills.mjs v1.json out/s --cuts          # one bundle: a still after every cut and mid-scene; or --every 0.5 --from 0 --to 8; or seconds
python scripts/montage.py "out/s_*.jpg" --cols 6 --out out/sheet.jpg      # one labelled sheet: LOOK at every transition, effect and card
npx remotion render src/index.ts Short out/v1.mp4 --props=v1.json --codec=h264 --crf=18 --concurrency=5
```

`--concurrency=5`: 8 workers fail with "No frame found at position" on 2880-tall proxies. Read the "wrote …" line of every compile:
an argument argparse rejects (`--music-levels -6,-6` needs the `=`) can leave an older project in place, and the video then renders without its music.

Read the **sync report** (cuts inside words, text on cuts, UI-zone collisions, overlaps, flashing
captions, components the playbook avoids, slow motion that would stutter, missing files) and fix what it
flags. Sound effects come from `assets/sfx/sfx-map.json` with the playbook's overrides
(`references/sound-design.md`). A human editor can work from the plan and `captions.srt` instead.

**Alternative renderer: HyperFrames** (Apache-2.0; the same `project.json`; CapCut-style hits `+shake`
`+glitch` `+rgb` `+pulse` in the Transition cell and `--look vignette,grain`). Choose it per video and say why
(`references/hyperframes-flow.md` §1: it does not draw `magnifier`, `thumbs`, `compare`, `ranking`):

```bash
python scripts/project_to_hyperframes.py RENDER/v1.json --out HF/v1 --playbook <id> [--look vignette=0.3,grain=0.05]
cd HF/v1 && npx hyperframes@0.9.26 check && npx hyperframes@0.9.26 snapshot --at 0.5,4,9   # look at the sheet
npx hyperframes@0.9.26 render --quality high --output final.mp4                             # then step 8 on final.mp4
```

Ask before the first `npx` (package download; Node 22+ and Chrome). `check` should report 0 errors; its
`line_unread` warnings on fast-voice captions are expected (§5 of the reference). For "make it like a CapCut
edit", find the technique in `references/capcut-techniques.md` before inventing one.

### 8. Master and export

```bash
python scripts/process_audio.py master RENDER/out/v1.mp4 --out RENDER/out/v1_final.mp4 --phone      # the general path
python scripts/finish_video.py RENDER/out/v1.mp4 --name BRAND_v1 --out-dir RENDER/out/final --audio-nomusic nomusic.wav --cover-at 3 --preview720   # agency recipe
```

−14 LUFS, true peak ≤ −1 dBTP, AAC 192 kb/s, `+faststart`; `--phone` adds a small copy for sending (chat and web viewers
take ~30 MB). Remotion writes full-range `yuvj420p`: `finish_video.py` converts to limited-range BT.709 (`mix_report.py` flags a
file that still is). One clean master for every platform (`references/platforms.md`): never re-post a TikTok download. A business
account cannot bake in a licensed track: deliver a second master **without music** so the human adds a Commercial Music Library
track at upload (`make_music.py` writes the self-made bed).

### 9. Verify, then report

`contact_sheet.py out/v1_final.mp4 --project RENDER/v1.json --out sheet.png` (the middle of every scene
and every cut) and **look**: subject visible, text readable over the footage (white text on white
fabric: `outline`/`marker`), nothing in UI zones, before/after honest. Then the numbers:
`mix_report.py final.mp4 --project RENDER/v1.json --words words.json [--nomusic final_nomusic.mp4]` (format, range, duration
against the plan, LUFS, true peak, loudness by 10 s, pauses, cue count, music present) and, for a voice cut from takes,
`check_lipsync.py RENDER/v1.json final.mp4 --clips ORIGINALS` (every talking scene within a frame). Then report in the user's language: playbook and why, runtime, scenes, the hook, corrections
applied to the footage, what the sync report still flags, claims changed or flagged (name the rule),
the publishing checklist (`platforms.md` §6), and what was **not** verified (e.g. not listened to; sounds picked by name and
measurement; a sentence guessed from a poor transcript; a logo keyed from a sample frame). Facts on screen (figures, customer
names, prices) are the user's or the documents', never invented; claims a brand makes inside a voice need the brand's evidence.

---

## Reference files

Read as the task requires, not all at once.

| File | Read it when |
|---|---|
| `playbooks/README.md` | Choosing the playbook; the questions to ask; adding a genre or a house style. |
| `playbooks/<id>.md` | Always, for the chosen playbook: structure, shots needed, editing, sound, look, graphics, compliance, commands. |
| `references/adding-techniques.md` | A reference or a request needs a technique the kit lacks: the one loop (search, research, implement, card, doc, test), the kinds and where each lives. |
| `references/technique-backlog.md` | Before researching a new technique: what was already researched but not built (GL Transitions loader, match cut, rack focus, parallax, OCR...). |
| `references/subject-effects.md` | Effects shaped by a person matte: silhouette flash, outline, glow, spotlight, colour pop, text behind the subject; the `Subject` plan cell. |
| `references/reference-analysis.md` | Reading `analyze_reference.py`'s report: what each key means, its thresholds, what is measured and what Claude must read from the evidence images. |
| `references/editor.md` | Fixing a project by hand in the browser: `editor.py`, the timeline, what is saved where. |
| `references/agency-pitch-recipe.md` | A service or agency pitch, or any "recreate this sample" job where a presenter talks to camera and the voice is cut from their takes: every step, tool and flag, and the pitfalls met. |
| `references/policy.md` | **Before any batch or any footage that is not the user's own**: originality, duplicates, Douyin, how many videos footage supports. |
| `references/claims-and-compliance.md` | Writing any script or on-screen claim; category law (real estate, food, cosmetics, finance); before/after rules; the rewrite table. |
| `references/platforms.md` | TikTok vs Reels vs Shorts: formats, safe zones, ranking signals, music by platform, the publishing checklist. |
| `references/hook-library.md` | Choosing or writing the opening. |
| `references/cutting-and-pacing.md` | Rhythm per playbook, cut types (J/L, match, jump), cutting on beats, speed ramps, re-hooks. |
| `references/transitions.md` | The transition catalogue, centred-cut maths, shader transitions on Windows. |
| `references/transition-pack.md` | The showreel techniques measured frame by frame (grid, frame click, teleport, black flash, zoom fade, mask and shape transitions, reverse, match-cut bursts, phone green screen) and how to build each; the layout of a "technique breakdown" video. |
| `references/camera-moves.md` | Visible push/pull/pan/roll, shot-size ladder, focus, punch-ins, moving footage, proxies. |
| `references/image-processing.md` | HDR, white balance, exposure, grades, stabilisation, noise, lens, levelling. |
| `references/typography.md` | Fonts with Vietnamese, the five title styles, colour themes (cool, warm, luxe). |
| `references/layout-and-motion-graphics.md` | Safe zones, layout per content, every graphic component and its keys. |
| `references/captions-and-text.md` | Caption styles (karaoke, pop, plain), readability, grouping, placement, SRT. |
| `references/sync-and-timing.md` | Cutting on pauses, anchoring graphics to words, ducking, verification. |
| `references/footage-ingest.md` | Shot log, shot library, budgeting footage across a batch. |
| `references/voiceover-and-captions.md` | ElevenLabs voices and models, Whisper alignment, the supplied-voice path. |
| `references/audio-and-music.md` | Licensing, choosing and levelling music, cutting to it, J/L-cuts. |
| `references/audio-processing.md` | Noise reduction, the voice chain, loudness targets, ffmpeg traps. |
| `references/sound-design.md` | Sound effects: licence-safe sources, the bank, which sound on which event. |
| `references/before-after.md` | Showing a result honestly: techniques, the `compare` card, choosing the pair. |
| `references/niche-winning-patterns.md` | The evidence behind the product-demo playbook's defaults: what 16,242 measured TikTok Shop videos show. |
| `references/remotion-output.md` | The render pipeline and template. Read the licence section first. |
| `references/hyperframes-flow.md` | Rendering with HyperFrames instead: which renderer, the flow, `+shake`/`+glitch`/`+rgb`/`+pulse`, `--look`, what `check` says, parity measured, pitfalls. |
| `references/capcut-techniques.md` | The user wants "a CapCut look", or you need a technique (speed curve, glitch, freeze, text behind subject, auto captions…): where it lives in the kit, or why it does not. |

---

## Output

1. `edit-plan.md` with its `**Playbook:**` line, Scenes and Overlays tables, the compliance checklist
   ticked and the pacing output pasted in.
2. `captions.srt` + `words.json` when there is a voice.
3. A shot list when footage must be shot (the playbook's "Shots the footage needs").
4. The render project's `project.json`, the mastered MP4 (+ phone copy), the contact sheet; or editor
   instructions.
5. The report (step 9).

## Honesty about evidence

**Measured**: the duration/CTR relationship and reach-not-persuasion (product demos, one niche); the
audio and image thresholds in `audio-processing.md` and `image-processing.md` (synthetic and one real
clip). **Documented**: platform policy, law (as researched, not legal advice), ffmpeg and Remotion
behaviour, licence terms. **Craft convention or a playbook's house style**: rhythms, structures, transitions,
camera moves, grades, title styles, layout bands, mix levels. Present conventions as informed practice,
not measurement: several much-quoted short-form statistics turned out to be fabricated or misattributed
(`platforms.md` §3). If asked whether a hook or style will perform better, the honest answer is usually
that the data does not say; recommend on structural fit and test it (Trial Reels, two hooks).
