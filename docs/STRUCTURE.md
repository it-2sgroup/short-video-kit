# Repo structure, tools and techniques

This document answers three questions: **what each folder and file does**, **which tools the repo uses**, and **which techniques
make a video match its sound, flow smoothly and not repeat footage**. The step-by-step way of working is in
[`WORKFLOW.md`](WORKFLOW.md); the reasons for choosing tools and the pitfalls met are in [`DECISIONS.md`](DECISIONS.md).

## 1. What this repo does

A toolkit for making short vertical videos (TikTok, TikTok Shop, Reels, Shorts; 10–90 seconds) **of many genres**: product
reviews, real estate, food, talking to camera, tutorials, fashion/beauty, event/travel montages, sale
promos. Everything that depends on the genre lives in a **playbook**; the shared parts (safe zones, caption placement, rendering, the copyright
policy) live in `references/` and `scripts/`. A video is described **once** by an *edit plan* (Markdown with
two tables, with `**Playbook:**` at the top), passes the checking gates and is rendered by **one** Remotion composition.

```
raw clips ─► inspect_footage --measure + contact_sheet ─┐
user request ────────────────────────────────────────────┴─► playbook.py suggest/show ─► playbook
raw clips ─► prepare_footage (HDR, frame, denoise, stabilise, white balance, exposure, grade) ─► proxy
voice ─► trim_voice (cut sentences / jump cut) ─► process_audio voice ─► align_captions ─► captions.srt + words.json
music ─► process_audio music ─► suggest_cuts --music (beats)          voice ─► suggest_cuts (pauses)
            ─► playbook.py skeleton ─► plan_scenes ─► edit-plan.md (Scenes + Overlays)
            ─► pacing_checker + footage_overlap_checker (the playbook's checking gates)
            ─► plan_to_project ─► project.json + sync report ─► Remotion ─► process_audio master ─► contact_sheet
```

## 2. Folder tree

```
short-video-kit/
├── CLAUDE.md                 Instructions for Claude when the repo is opened (Claude reads it first by itself)
├── README.md                 Introduction, installation, usage
├── setup.sh · selftest.sh    Machine setup and check
├── requirements.txt          Python libraries (faster-whisper, numpy, onnxruntime)
├── requirements-ocr.txt      Optional OCR libraries (rapidocr, opencv), installed with setup.sh --ocr
├── .env.example              Template of the ElevenLabs key file (contains no key)
├── .gitignore · .gitattributes
├── docs/                     Documents for readers
├── samples/                  Sample data for the selftest
└── skill/short-video-editing/   ← this is the "skill" that Claude loads
    ├── SKILL.md              General rules + the 9-step workflow (analyse → playbook → edit → master → report)
    ├── playbooks/            One JSON per genre (machine-read rules) + one MD (craft); README = how to choose and add a genre
    ├── references/           Shared knowledge by topic (Claude reads it when needed)
    ├── scripts/              Python command-line tools
    ├── assets/               Plan template + Remotion template
    └── evals/                Quality test cases for the skill
```

## 3. Repo root

| File | Function |
|---|---|
| `CLAUDE.md` | Instructions for Claude: check the machine at the start of a session, the setup steps, the workflow when the user asks for a video, what must be asked of the user (downloads, ElevenLabs plan, Remotion licence), lessons paid for the hard way. |
| `README.md` | Overview, system requirements, installation (including Windows), usage, third-party licences, known limits. |
| `setup.sh` | Installs everything under `$HOME`: the Python venv, libraries, the Whisper model (~460 MB), the ElevenLabs key (if `.env.local` exists), copies the skill into `~/.claude/skills`. Safe to re-run. Options: `--check` (report only), `--set-key` (hidden key entry), `--no-model`, `--person-model` (also downloads the 168 MB person-segmentation model for the agency workflow; ask the user first), `--ocr` (RapidOCR + OpenCV ~85 MB for analyze_reference.py; ask first), `--all` (every optional thing that can be downloaded without typing: OCR, the person model, static ffmpeg), `--no-skill`, `--download-ffmpeg` (Linux), `--package` (packs a `.skill` for the desktop app). |
| `selftest.sh` | 13 groups of checks that cost no credits: tools; inspecting clips; playbooks (every playbook/variant valid, its skeleton passes its own pacing rules, every component/grade/theme/caption style is used by at least one playbook) and the per-playbook pacing rules; caption alignment; the ElevenLabs key; compiling plans (a product review + a property tour with speed ramps and information graphics); footage overlap (counting sped-up scenes too); cutting on pauses and on beats; voice cutting and jump cut; contact sheets; project skeleton building; sound effects; voice cleanup + master; measuring and correcting footage. `--render [DIR]` adds group 14: typechecking the template and rendering stills (including the information graphics). |
| `requirements.txt` | `faster-whisper==1.2.1`, `numpy`, `onnxruntime`. |
| `requirements-ocr.txt` | `rapidocr` and `opencv-python-headless` (version-pinned). Optional. Group 1 of `selftest.sh` checks that every third-party package the scripts import is in some `requirements*.txt` file. |
| `.env.example` | Only the line `ELEVENLABS_API_KEY=`. The real key lives in `.env.local` (blocked by `.gitignore`) or `~/.config/short-video-kit/env`. |
| `.gitignore` | Blocks keys (`.env*`), media (`*.mp4`, `*.mp3`), `models/`, `bin/`, `dist/`, `node_modules/`, `out/`, `renders/`. |
| `.gitattributes` | Forces LF for text files, so that Git for Windows does not turn `.sh` into CRLF and break bash. |

## 4. `docs/`: documents for readers

| File | Content |
|---|---|
| `WORKFLOW.md` | The flow from raw clips to a finished video, every command, the standard working folder. |
| `PROMPT-VIDEO.md` | A general sample prompt (every genre): brief, invariant rules, workflow, the catalogue of techniques, acceptance criteria, delivery. |
| `PROMPT-BATCH-VIDEO.md` | A frame for writing a request for a batch of videos posted for real (several sources, voice speed-up, delivery into a synced folder), with the places where prompts are often ambiguous. |
| `DECISIONS.md` | The **technical** part only: licences (Remotion, ElevenLabs), technical pitfalls met, the reasons for the architecture, the second renderer, camera keyframes, the tools surveyed. The work done for each client is in `CASE-LOG.md`. |
| `CASE-LOG.md` | **History**, not a guide: niche figures, the jobs done for clients (client names, file names, measured results, what was not checked), the analysis of one batch's prompt. Reusable lessons have been turned into techniques in the skill. It contains client names and campaign figures, so the repo must be private. |
| `STRUCTURE.md` | This file. |
| `niche-data-queries.sql` | The queries that reproduce the figures in `niche-winning-patterns.md` (the `videos` table; `video_metrics_daily` is not summed because it repeats on a 7-day cycle). Data of one real campaign: only in `docs/`, never in the skill. |

## 5. `samples/`: sample data

| File | Used in |
|---|---|
| `example-edit-plan.md` | A sample `product-demo` plan with 11 scenes + 11 graphic layers; the selftest uses it to try `pacing_checker`, `plan_to_project`, `footage_overlap_checker`. |
| `example-real-estate-plan.md` | A sample `real-estate` plan (cut on music, speed ramp, 0.5x, `specs`/`pin`/`label`/`stat`/`chart`/`image`/`price`); the selftest uses it to try the per-playbook rules and to compile the new features. |
| `line_00.mp3` + `line_00.txt` | One line of voice and its exact words; the selftest uses it to try `align_captions` (checks that the spelling "túi xách" (handbag) is kept). |

## 6. `skill/short-video-editing/`: the skill

### 6.1 `SKILL.md`

The entry point that Claude loads. It holds 9 **general rules** for every video (analyse before planning; a hook within 3 seconds;
pacing as the playbook says; timestamps; check claims; footage that is yours/licensed, not reused, not reshuffled; graphics
respect the frame; no faking before/after; say clearly what was not checked), the decisions that belong to humans, the
9-step workflow, the document index table and the "honesty about evidence" section.

### 6.2 `playbooks/`: rules per genre

| File | Content |
|---|---|
| `README.md` | The table of 8 playbooks; how to choose (a table "what the footage shows + what the user wants → playbook"; at most 3 questions); the meaning of each JSON key and which script reads it; how to add a genre or a client's "house style" (a variant). |
| `<id>.json` | Machine-read rules: duration, hook, scene length, `drive` (voice/music), beat structure, transitions, camera, caption style, theme, grade, correction style (`shared`/`per-clip`), music tempo (bpm), graphics to use/avoid, sound-effect overrides, the compliance checklist, documents to read, variants. |
| `<id>.md` | The genre's craft: when to use it, questions to clarify, structure, shots needed, editing, sound, colour, graphics, hook, compliance (Vietnamese law), commands to run. |

The eight playbooks: `product-demo` (+`unboxing`, `listicle`), `real-estate` (+`voiceover`), `food-fnb` (+`review`),
`talking-head` (+`testimonial`), `tutorial`, `fashion-beauty`, `montage-recap`, `promo-sale`.

### 6.3 `references/`: shared knowledge

| File | When to read |
|---|---|
| `policy.md` | **Before planning a batch of videos or using scenes that are not your own:** non-original content, repetition, copyright infringement; how many videos the footage at hand can make; the conclusion on Douyin crawling; the legitimate way to get large volume. |
| `claims-and-compliance.md` | Writing wording/text with an advertising character: general rules (Advertising Law 75/2025, the word "nhất" (the superlative "-est"), comparing competitors, matching prices), by sector (household goods + a table of replacement sentences, real estate: the 2023 Real Estate Business Law & Decree 339/2026, food/dietary supplements, cosmetics, finance, promotions), before/after rules. |
| `platforms.md` | TikTok vs Reels vs Shorts: formats, safe zones (TikTok measured in practice + Meta's Reels ad zone), ranking signals the platforms published, music per platform, TikTok Shop specifics, the posting checklist. |
| `hook-library.md` | The 3-channel hook structure, a ranking of hook types, hooks per playbook. |
| `cutting-and-pacing.md` | Pacing per playbook, the kinds of cut (J/L, match, jump, smash…), cutting on voice or on beat, speed-up/slow motion/speed ramp, re-hook, where not to cut. |
| `transitions.md` | The catalogue of 11 transitions, transition families per playbook, the maths of centring on the cut point, shaders on Windows. |
| `camera-moves.md` | Push/pull/pan/roll/hold, footage that already moves is kept still, the shot-size scale, movement per shot type in each playbook. |
| `image-processing.md` | HDR, white balance (neutral pixels), exposure, the grades, stabilisation, denoising, lens distortion correction, straightening; measured thresholds, ffmpeg pitfalls, speed. |
| `agency-pitch-recipe.md` | The full step-by-step recipe for a presenter's service-intro video: voice–take matching, cutaways, the silhouette flash, skin light, plan, sound, render, delivery, the pitfalls met. |
| `typography.md` | Fonts with Vietnamese support, the no-outlined-boxes rule, 5 title styles, "big" text for agency ads (`phrase`, `pill`, `arc`, `script`, `tag`), 4 colour themes (cool, warm, luxe, crimson). |
| `layout-and-motion-graphics.md` | Safe zones, layout per genre, the catalogue of 20 graphic components and their content keys, motion conventions. |
| `captions-and-text.md` | Caption styles (karaoke, pop, plain, none) and the reading-comprehension evidence, caption grouping, position, text that does a different job from the spoken line, SRT. |
| `sync-and-timing.md` | The shared clock (voice or music), cutting on pauses, anchoring graphics to words, ducking music under speech, sync checks. |
| `footage-ingest.md` | Inspecting and measuring clips, the shot log, the shot library, dividing the footage budget across several videos. |
| `voiceover-and-captions.md` | ElevenLabs (models, emotion tags, cost), caption alignment, **a supplied voice**. |
| `audio-and-music.md` | Music copyright, choosing music per genre, cutting on music, volume levels, location sound, J/L-cuts. |
| `audio-processing.md` | Denoising, the voice processing chain, loudness targets, the ffmpeg pitfalls measured. |
| `sound-design.md` | Sound effects: legitimate sources, the sound set, which sound for which event (with playbook overrides), level and timing. |
| `before-after.md` | Making a before/after result clear and honest: technique, the `compare` card, choosing the frame pair, advertising warnings. |
| `niche-winning-patterns.md` | Real figures over 16,242 household-product videos (for `product-demo`). *Internal figures, the repo must stay private.* |
| `remotion-output.md` | The Remotion licence, the render pipeline, the template layout, the ffmpeg ↔ Remotion boundary. |
| `hyperframes-flow.md` | The flow for rendering with **HyperFrames** (Apache-2.0): which renderer to choose, the steps, the `+shake/+glitch/+rgb/+pulse` syntax and `--look`, what `check` reports, the comparison with Remotion (measurements), pitfalls, how to extend. |
| `capcut-techniques.md` | The catalogue of CapCut techniques (cuts, speed, camera, transitions, effects, masks, colour, text, sound, AI) mapped onto the toolkit: where it is, with which command, or why not yet; a CapCut-style review recipe. |
| `adding-techniques.md` | **How the toolkit grows**: the single loop for adding a new technique (search first, research with sources and licence, implement in the right place by kind, card, documentation, test), the kinds of technique and the files each kind installs into. |
| `transition-pack.md` | The showreel techniques of two technique-breakdown videos measured in frames (grid reveal, frame click, crop with negative, teleport band, black flash, zoom fade, mask and shape transitions, reverse, match-cut burst, phone green screen, dolly zoom) with the kit transition, tool or recipe for each, the sound, and the breakdown layout. |
| `technique-backlog.md` | Techniques **researched but not built** (loading GL Transitions shaders, match cut, mask/ink reveal, rack focus, 2.5D parallax, OCR…), with how to build them, pitfalls, licences; delete a line once it is built. |
| `subject-effects.md` | Person-mask effects (the `Subject` column): silhouette flash, outline, glow, spotlight, colour pop, text behind the person; how to make the mask (`person_matte.py --frames/--range`), when to use it, pitfalls. |
| `reference-analysis.md` | How to read the report of `analyze_reference.py`: each measured key (transition family, camera path, speed, colour fingerprint, evidence, `--compare`), thresholds, what was measured and what Claude must read from the images itself. |
| `editor.md` | The browser-based video editor (`editor.py`): starting it, the screen areas, shortcuts, where it saves, limits. |

### 6.4 `scripts/`: command-line tools

Run from the skill folder. `align_captions.py` and `suggest_cuts.py --music` need the venv (they re-launch themselves inside the toolkit's
venv); the rest only need Python 3 and ffmpeg (a build with all the filters: `doctor.py` checks).

| Script | What it does | In → Out |
|---|---|---|
| `doctor.py` | **Run first on a new machine.** Checks everything the skill needs: Python, the venv (faster-whisper, numpy), ffmpeg and each filter/encoder the scripts call (vidstab, zscale, haldclut, afftdn…), the Whisper model, Node, the ElevenLabs key (never prints the value), disk space; says clearly what is missing and how to install it per operating system. Changes nothing; `--json`, `--only GROUP`. Uses only the standard library. | machine → report, exit code 0/1 |
| `playbook.py` | Loads a playbook (including `id:variant` variants); `list`, `show`, `suggest` (ranks playbooks by the request + footage measurements), `skeleton` (a plan skeleton obeying the genre's rules, from `cuts.json` if given), `check` (checks every playbook; the selftest runs it). Other scripts import it. | request/plan → playbook |
| `technique.py` | **The technique catalogue**: `list`, `kinds`, `show`, `search` (by name, CapCut/Premiere/After Effects aliases, tags), `scaffold KIND ID` (prints the files to edit to add a technique), `check` (compares the cards in `assets/techniques.json` with the code, documentation and selftest, both directions). | keyword → card; code ↔ card |
| `editor.py` | A locally running video editor (Python standard library only, listens on `127.0.0.1`): opens `project.json`, drag and drop scenes/text/captions on a timeline, edit properties, saves with history snapshots, re-renders. The UI is in `assets/editor/`. | project.json → project.json |
| `ref_measure.py` | The measurements for `analyze_reference.py` (no new libraries): transition family, camera path from vid.stab, speed and freeze frames, colour fingerprint. | clip → measurements |
| `inspect_footage.py` | Reads the real properties of a clip (duration, resolution, rotation, fps, sound, HDR), warns about landscape clips, missing sound, format mismatches; `--log` prints an empty shot log; `--measure` measures brightness, colour cast (on neutral pixels), noise, shake/camera movement (vid.stab), whether someone is speaking, then proposes corrections; `--json FILE` writes `analysis.json`. | clip folder → report / `analysis.json` |
| `prepare_footage.py` | Makes proxies: HDR conversion, 9:16 frame, denoise, 2-pass stabilisation, distortion correction/straightening (`--fix`), 30 or 60 fps (`--slowmo`), white balance + exposure + the playbook's grade baked into one 3D LUT, light sharpening; `correction: shared` gives every clip the same correction; writes `corrections.json`. | raw clips → `public/clips/*.mp4` |
| `process_audio.py` | `voice`: measures the noise floor/voice level, denoises with a noise profile when needed, EQ, de-ess, compression following the voice level, expander, −16 LUFS; `music`: levels to −14 LUFS; `master`: the whole video to −14 LUFS, peak ≤ −1 dBTP, AAC, `--phone` a light copy; `measure`. | audio/video → processed copy |
| `contact_sheet.py` | A contact image of frames: one row per raw clip; or the middle of every scene + every cut point of a rendered video. | clips/video → `.png` |
| `trim_voice.py` | `--silences` lists pauses and cut points; `--keep a-b,c-d` joins the kept segments; `--jumpcut` (talking head) drops every long pause, merges/splits segments by the playbook's scene length, writes the joined voice + `--scenes-out` (each scene has its source time). | voice/video → shorter voice, scenes |
| `_venv.py` | Not a command: the `ensure_venv()` function that scripts needing numpy/onnxruntime call at the top of the file to re-run themselves inside the toolkit's venv (`$SVK_PYTHON` or the venv `setup.sh` made) when the system Python lacks the libraries, as `align_captions.py` already does with faster-whisper. | — |
| `analyze_reference.py` | Measures a client's SAMPLE video before rebuilding it: splits scenes by frame change (scene count, shortest scene, scenes/minute), continuous-motion runs of 4+ frames (= transitions, length in frames), single-frame flashes, the edge/centre colour of each scene, loudness (LUFS, peak), the `scenes.png` image, dense images `dense_*.png` (one every n frames) and spectrogram images `spectrum_*.png`. It does not detect effect sounds automatically (tried, not reliable: `docs/DECISIONS.md`). | sample video → `ref/report.md` + `.json` + images |
| `montage.py` | Joins any images into one labelled image (the time comes from the file name, or `--labels`): images rendered by `stills.mjs`, a sample frame placed beside your own frame. | images → one image |
| `mix_report.py` | Measurements for a finished video: size, fps, colour range (flags an error if full-range), duration against the project, LUFS/peak, loudness per 10 s, the voice level and the level in the pauses, whether the music is really in the file (`--nomusic`), the number of effect sounds. Measures only, does not listen. | mp4/wav → report, exit code 1 on error |
| `agency_plan.py` | Writes a draft `edit-plan.md` for a service-intro video (`talking-head:agency`) from words.json + matches.json (match_voice_takes) + cutaways.json: presenter scenes cut on the gaps (In = start + lag), card scenes with unused cutaways, transitions, camera, the Face/Flash columns, a text block for each clause (effects alternating), a logo at the brand name, the caption strip. A draft to be adjusted by hand. | json → `edit-plan.md` |
| `finish_video.py` | From a Remotion render to the deliverable files: converts the full colour range → limited (BT.709), −14 LUFS audio master, a music-free version (`--audio-nomusic`), a phone copy, a cover, a 720p preview. | rendered mp4 → final folder |
| `check_lipsync.py` | Checks the FINAL video: for each presenter scene, compares the take's original audio at `In` with the final audio; more than 1 frame off is a timeline error. | project.json + mp4 + source clips → table |
| `person_matte.py` | Cuts a person from the background with the ONNX person-segmentation model (u2net_human_seg, ~168 MB, kept OUTSIDE the repo): outputs a white silhouette PNG for the opening flash; `--faces` measures the head position (x, y, r) for skin-brightening light. | clip + time → PNG / JSON |
| `object_cutout.py` | Cuts ONE object (a house, a gate, a vehicle, a product) out of a frame into a transparent-background PNG for the `objectDrop` overlay: a hand-drawn outline `--poly` (no model, nothing downloaded) or `--model` an ONNX model the user supplies (the kit ships no model); `--grid` prints the frame with a coordinate grid, `--preview` paints the background pink to check the edge; prints the ready plan cell `src, at, width, aspect`. | clip/image + time → PNG |
| `find_occluders.py` | Scans clips for the moments a foreground object (a sleeve, a handrail, a pillar) covers the lens after a textured picture: the places to hide a hard cut for a mask or shape transition. Lists start, peak, end, cover share and tone; look at each on a contact sheet. | clips -> candidates (JSON) |
| `reverse_clip.py` | Writes a stretch of a clip played backwards with ffmpeg (`trim`, `reverse`) for a reverse scene, refusing stretches whose raw frames would not fit in about 3 GB. | clip -> reversed mp4 |
| `find_cutaways.py` | Lists the silent stretches of the takes (the gaps before/after speech) as cutaways: ranked by length, with a person in frame (`--person`), excluding used ones (`--avoid`). | clip folder → table, JSON |
| `match_voice_takes.py` | When the voice was cut from the takes' own audio (presenter, interview): cross-correlates the voice with each clip, prints `clip time = voice time + lag` for each matched segment and the voice segments that no take has (where cutaways go). A scene starting at second T of the voice uses `In = T + lag`, so the mouth matches sample for sample. | voice + clip folder → table, `--out` JSON |
| `make_music.py` | Synthesizes copyright-free background music itself (numpy + ffmpeg): music sections that start exactly at the video's cuts (the beat grid restarts at each section), an intensity 0..1 picks the layers (pad, bass, kick + hat, chord, clap + arpeggio), `--hits` places a hit + riser. The final level is `process_audio.py music`'s job. | `--sections --hits` → `.wav` |
| `make_sfx.py` | Makes 6 effect sounds itself (pop, tick, ding, thud, swoosh, riser) with ffmpeg: nothing downloaded, no copyright issue; peak −3 dB like the CC0 files. | folder → `.wav` |
| `make_voiceover.py` | Synthesizes a voice with ElevenLabs, one file per line; `--quota`, `--dry-run` (spends no credits), refuses to run without enough credits. | `script.txt` → `.mp3` + `voice_manifest.json` |
| `align_captions.py` | Whisper for the **timing**, the script for the **words**; merges caption groups that are too short; `--words-out` writes per-word timing. | voice + script → `captions.srt`, `words.json` |
| `suggest_cuts.py` | Suggests cut points: on the pauses of `words.json`, or on the beats of the music (`--music`: spectral flux + tempogram + dynamic-programming beat tracking, favouring the start of a bar; `--beats-out`; needs numpy so it runs itself in the venv), or both (cut on the voice then pull to a beat within 4 frames); scene/hook length comes from the playbook (dynamic programming). | `words.json`/music → table/`cuts.json` |
| `plan_scenes.py` | Fills Source/In from the **shot library** so that no range is used twice (counting sped-up scenes too), keeps the skeleton's Type/Speed/Transition (`--plan`), picks Camera from the span's `move` → the playbook's `camera.byKind` → shot size; exits 1 when the footage runs out. | `library.json` + skeleton/`cuts.json` → Scenes table |
| `pacing_checker.py` | The gate that checks **the playbook's** pacing rules recorded in the plan (hook, scene length, continuity, total duration). Exits 1 on a violation. | `edit-plan.md` → report |
| `footage_overlap_checker.py` | Turns each scene into a source range `[In, In + length × speed]` and reports overlaps/near-touching ranges within and across plans; `--clips` lists the free ranges. | the `edit-plan.md` files → report |
| `plan_to_project.py` | Compiles the plan into `project.json` (including Speed/ramp); caption style, automatic camera (`--auto-camera`, keeps a moving clip still per `--analysis`), SFX overrides taken from the playbook; `--platform reels-ad`; prints the **sync report** (cuts mid-word, text next to a cut, UI zones, components the playbook avoids, slow motion that will stutter, missing files). | `edit-plan.md` + SRT + words → `project.json` |
| `project_to_hyperframes.py` | **The second renderer**: turns the same `project.json` into a HyperFrames project (Apache-2.0, no seat fee): lays out scenes like `timeline.ts`, **bakes** scenes with `speed`/`ramp` into separate clips with ffmpeg, mixes voice + self-ducking music + SFX into `audio/mix.wav` (the same level and ducking as `audio.tsx`), hard-links the proxies (no copy), writes `index.html`, `kit.js`, `kit.css`, `package.json` (pins `hyperframes@0.9.26`); `--look vignette=,grain=`; `--check`, `--render FILE --quality`; reports components not drawn (magnifier, thumbs, compare, ranking) and scenes where the source clip runs out first. | `project.json` → HyperFrames folder |
| `new_remotion_project.py` | Creates a render project from the template; `--playbook` sets the theme (and the grade for proxies); `--proxies` calls `prepare_footage.py`; `--slowmo`; `--install` runs npm; `--theme cool|warm|luxe|crimson`; `--update` copies the template again (repeat `--playbook`/`--theme`); always puts the SFX set into `public/sfx/`. | → project folder |

### 6.5 `assets/`

| Path | Function |
|---|---|
| `edit-plan-template.md` | The edit plan template: the header (Playbook, Platform, Drive, Look…), the **Scenes** table (Start, End, Source, In, Type, Transition, Camera, Speed, Shot, Audio), the **Overlays** table (Start, End, Component, Zone, Tone, Content), the compliance checklist. |
| `grades.json` | 15 colour "looks": 5 for the playbooks (natural, bright-interior, warm-food, soft-skin, vivid) and 9 library ones (teal-orange, cinematic-fade, moody, pastel, vintage-film, mono, bleach-bypass, golden-hour, cold-blue); the ffmpeg filter string contains only colour filters that can be baked into the 3D LUT + `wbStrength`; `--grade-strength 0..1` blends the look with the corrected picture. |
| `techniques.json` | **The technique catalogue**: one card per technique (transition, text effect, person-mask effect, grade, camera, speed, look, font, graphic, theme…): id, kind, how it looks, the syntax in the plan, renderer, documentation, test, source and licence. `technique.py check` keeps it matching the code. |
| `editor/` | `index.html`, `editor.css`, `editor.js`: the UI of `scripts/editor.py` (plain JavaScript, no CDN, no libraries). |
| `shot-library.example.json` | A sample shot library for `plan_scenes.py`: `kind`, `focus`, `size`, optional `move`. |
| `sfx/` | The sound-effect set: 5 CC0 recorded files (`whoosh`, `whip`, `switch`, `mouse-click`, `shutter-modern`), `SOURCES.md` (author, source, licence of each file), `sfx-map.json` (which sound for which event, dB level, lead time). |
| `remotion-template/` | The data-driven Remotion project (section 7). |
| `hyperframes-template/` | The painter for the HyperFrames renderer (section 7b): `kit.js`, `kit.css`. |

### 6.6 `evals/`: the skill's test cases

Five cases: `full-edit-plan-from-brief` (a full product-review plan, recording the right playbook), `pushes-back-on-too-short`
(pushes back on a 15-second video with figures), `rejects-banned-claims` (catches banned claims, proposes replacement sentences), `routes-real-estate-tour`
(recognises a property tour, uses the `real-estate` playbook, cuts on music, keeps the facts exact), `asks-when-ambiguous` (footage fits two
genres: ask at most 3 questions with defaults, or choose and give the reason). Each case has `prompt.md`, `case.yaml`, `graders/`. The two new cases were
run by hand once with a fresh agent (passed; results in `DECISIONS.md`); there is no automatic harness yet.

## 7. `assets/remotion-template/`: the render template

A single composition, `Short`, reads `project.json` through `--props`. **No video content text is in the code.**

| Path | Function |
|---|---|
| `stills.mjs` | Renders several stills of a project from ONE bundle (`--cuts`, `--every S --from A --to B`, or list the seconds): to look at every transition and effect before the full render; joined with `montage.py`. |
| `package.json` · `tsconfig.json` · `remotion.config.ts` | Dependencies pinned to exact versions; the TypeScript configuration; the default GL backend `swangle` (software, runs on any machine; `SVK_GL=angle` for a machine with a GPU) so that shader transitions and light leaks run. |
| `project.example.json` | A sample library that needs no footage: every text and graphic style (including `pin`, `label`, `chart`, `specs`, `stat`); open it with `npm run studio`. |
| `src/index.ts` · `src/Root.tsx` | Registers the composition; the length comes from `duration` and `fps` in the data (`calculateMetadata`). |
| `src/project.ts` | **The data contract**: the types `Project` (including `layout`), `Scene` (including `speed`, `ramp`), `Overlay`, `CaptionStyle`, `Word`, `Camera`… |
| `src/theme.ts` | **Every design token**: fonts, **four colour palettes** (`cool`: white, sky blue; `warm`: ivory white, yellow, red, brown for food/golden light; `luxe`: warm white, champagne gold, graphite for real estate/fashion; `crimson`: white, brand red, yellow, burgundy for agency ads; one `THEME` line decided by the playbook), a conditional font (Barlow Condensed) and a handwriting font (Pacifico), the video card size + grid (`card`, `grid`), the title text colour, layout zones, the caption strip per layout (feed / reels-ad), the cart point (112, 1677; measured from a real TikTok screenshot), the sizes of information graphics, motion curves, camera limits, the comparison card. Change the look here. |
| `src/engine/timeline.ts` | Lays out scenes with transitions **centred on the cut point**; recomputes the source frame for `speed` and `ramp` (the source frame at the cut is always `In`). |
| `src/engine/transitions.tsx` | The transition table (31 names): those built into Remotion (including the shader group `filmBurn`, `zoomBlur`, `crosswarp`…), `zoomThrough`, `blurDissolve`, a speed-matched `whip` (blur along the direction of motion), and 5 written in CSS (`blinds`, `diamond`, `doors`, `glitchSlice`, `spinZoom`). |
| `src/engine/Subject.tsx` | Person-mask effects (`Scene.subject`): silhouette fill/flash, outline, glow, dim, colorpop, behind (text between the background and the cut-out of the person); drawn inside the camera frame so it follows every push. |
| `src/fonts.ts` | A library of 31 Google fonts (OFL, with the Vietnamese subset) by mood, chosen with `font=<id>` on each text layer; only the fonts the project uses are loaded. |
| `src/engine/camera.ts` | The virtual camera: push, pull, pan, hold, keyword-driven zoom; and **keyframes** (`keys`): a list of frames (zoom, centre point, roll) with an easing per segment (`inOut soft out in snap back linear hold`), zoom interpolated by area, the frame edge is never exposed; plus `shake` (handheld shake: smooth noise on x, y, roll, one seed per axis). |
| `src/engine/audio.tsx` | The voice, background music that ducks under speech, sound effects; outside the transition chain so it is not shifted. |
| `src/engine/Short.tsx` | The composition: joins scenes, camera, speed (a ramp re-reads the source frame frame by frame inside `<Freeze>`), the graphics layer, captions, sound, the `look` layer (vignette, grain). |
| `src/components/registry.tsx` | The component names used in `project.json`; an unknown name raises an error. |
| `src/components/anim.ts` | Shared animation functions (in/out, spring, fit to frame). |
| `src/components/text/` | `Title.tsx` (5 styles: outline, stack, gradient, glass, marker), `Captions.tsx` (karaoke / pop / plain; caption strips `captionBands`, with `hide`), `primitives.tsx` (outlined text, gradient text, text rising through a mask), `Phrase.tsx` (`phrase`, `pill`, `arc`, `script`, `tag`, `burst`), `Fx.tsx` (14 text effects: scatter, slam, stamp, glitch, drop, elastic, wave, flip, maskwipe, split, shine, neon, typewriter, rise). |
| `src/components/graphics/Grid.tsx` | A red grid background moving like cloth in the wind (a pure function of the frame) for card scenes. |
| `src/components/graphics/Drop.tsx` | `objectDrop` (an object cut from the next scene falls from the top edge, a hard cut on touchdown) and `impact` (an explosion flash + dust drawn in SVG from a `seed`, no sprites). |
| `src/components/graphics/Brand.tsx`, `Glyph.tsx` | `logo` (blurred in motion then sharp, `tint`, `hold`), `counter` ("5 → 10"), `icon`, `circled`, `rawfinal` (RAW | FINAL of the same take) and the SVG icon set. |
| `src/components/graphics/` | 20 components: `Callout`, `Lists` (checklist, step), `Price` (count-up number, with decimals), `Pointers` (the TikTok Shop cart arrow, a circling ring, a sticker), `Media` (a magnifier, the 3-picture strip `thumbs`, the BEFORE/AFTER card `compare`, the picture `image`), `Ranking`, `Bars` (progress bar, name card), `Info` (**`specs`** a row of specifications with icons, **`pin`** a map pin, **`label`** a room/dish/item label, **`stat`** a counting-up number, **`chart`** a bar chart). |

## 7b. `assets/hyperframes-template/`: the painter for HyperFrames

Not a complete project: `project_to_hyperframes.py` copies these two files into the project and generates `index.html` around them.
The same `project.json` contract as section 7; the HyperFrames contract: a paused GSAP timeline registered at `window.__timelines["main"]`.

| Path | Function |
|---|---|
| `kit.js` | The whole painter: `render(frame)` is a **pure function of the frame** (sets the style of every element from data), GSAP only pushes the playhead through a setter so every seek is correct. It has the theme tokens (cool/warm/luxe, copied from `theme.ts`), easing and springs like Remotion, scene layout + centred transitions, the virtual camera (push/pull/pan/hold/roll, punch), 11 transitions, accent flash/light leak, **effects on the cut point** (`shake`, `pulse`, `rgb` channel split with an SVG filter, `glitch`), the **look** (vignette, film grain), karaoke/pop/plain captions, 5 title styles and 17 graphic components (`FACTORY`). Not drawn: `magnifier`, `thumbs`, `compare`, `ranking`. |
| `kit.css` | The background and the stacking layers (`z-index`), the fonts Be Vietnam Pro / Playfair Display / Anton (HyperFrames embeds Google Fonts at render time). |

How to use it, the comparison with Remotion, the real measurements and the pitfalls: `references/hyperframes-flow.md`. The catalogue of CapCut techniques
and where they sit in the toolkit: `references/capcut-techniques.md`.

## 8. Outside the repo (made by `setup.sh` and by working)

| Location | Content |
|---|---|
| `~/.local/share/short-video-kit/venv` | The Python environment (change with `SVK_PYTHON`). |
| `~/.cache/short-video-kit/models` | The Whisper `small` model (change with `WHISPER_MODEL_DIR`). |
| `~/.config/short-video-kit/env` | The ElevenLabs key, permission 600. |
| `~/.claude/skills/short-video-editing` | The installed copy of the skill (re-run `setup.sh` after every `git pull`). |
| `<work-folder>/<video>/` | `script.txt`, `captions.srt`, `words.json`, `edit-plan.md` of each video. |
| `<work-folder>/analysis.json` | Footage measurements (`inspect_footage.py --measure`). |
| `<work-folder>/render/` | One Remotion project for the whole batch (`public/clips` = corrected proxies + `corrections.json`, `public/audio` = processed voice/music, `public/images`). |

## 9. Tools in use

| Tool | Version | Role |
|---|---|---|
| Claude Code (skill + `CLAUDE.md`) | current | Orchestration: reads the instructions, plans, runs the tools, reports. |
| Python | 3.10+ (tried on 3.12 Windows, 3.14 Linux) | Every script. |
| faster-whisper (CTranslate2) | 1.2.1, model `small` | Gets the **timing** of each word of the voice. |
| numpy | — | Audio sample handling for Whisper; beat detection (`suggest_cuts.py --music` re-runs itself in the venv). |
| ffmpeg / ffprobe | 6+ (tried 7.0 static, with libvidstab) | Measuring footage (`signalstats`, `vidstabdetect`, `psnr`), correction and grading (`zscale/tonemap`, `hqdn3d`, `vidstabtransform`, `lenscorrection`, `rotate`, `haldclut`), audio (`afftdn`, `deesser`, `acompressor`, `agate`, `alimiter`, `loudnorm` for measuring), `silencedetect`, `atrim`/`concat`, contact images, decoding music to find beats. |
| ElevenLabs API | `eleven_turbo_v2_5` | Synthesizes a voice when none is supplied (the free plan is not for commercial use). |
| Node.js | 20.19+ | Runs Remotion. |
| Remotion | 4.0.540 (`@remotion/cli`, `transitions`, `light-leaks`, `paths`, `google-fonts`) | Renders video from data; transitions, effects, camera. Free for individuals or companies of ≤ 3 people. |
| React / TypeScript | 19.3.1 / 5.9.3 | Writing the graphic components; typecheck with `tsc --noEmit`. |
| Google Fonts | Be Vietnam Pro, Playfair Display Italic, Anton | Fonts checked to have the Vietnamese character set (OFL). |
| bash (Git Bash on Windows) | — | `setup.sh`, `selftest.sh`. |
| git + GitHub CLI | — | Source code (private repo), sign-in with `gh auth login --web`. |
| winget / brew / apt | — | Install Python, Node, ffmpeg per operating system. |
| Supabase (data side only) | — | The source of the niche figures; only the reproducing SQL file remains. |

## 10. Main techniques

1. **Playbook per genre.** Genre-dependent rules are data (`playbooks/<id>.json`) that every script reads; adding a
   genre = adding one JSON + one MD, and `playbook.py check` guarantees it is valid, its skeleton passes its own rules, and no
   component/grade/theme is left "lying around" unused by any playbook.
2. **Analyse first, choose after.** Measure the footage (`--measure`) + the request → `playbook.py suggest` proposes; Claude looks at the
   contact sheet to confirm, and asks at most 3 questions when ambiguous.
3. **Edit by data.** The plan (Markdown) → `project.json` → one composition. Changing the video = changing the table.
4. **Measured image correction.** White balance on neutral pixels (not every pixel: a green basin once fooled it),
   exposure by gamma, denoise only when dark and noisy, stabilise when shake > 4 px/frame, HDR to SDR; white balance +
   exposure + grade baked into one 3D LUT (~2.5 times faster, the difference not visible); before/after share one correction.
5. **Measured audio.** Noise floor = the 5th percentile of 100 ms windows; noise-profile denoising only when the voice is < 35 dB above the noise;
   compression following the voice level; an expander gives the silences back; −16 LUFS for the voice, −14 LUFS / −1 dBTP for the master.
6. **Text from the script, timing from Whisper.** Whisper mishears Vietnamese; the word sequences are matched and then the script's spelling
   is kept.
7. **Cut on voice or on music.** On pauses (`silencedetect`, the gap between words) or on beats (spectral flux, a weighted tempo
   + half-beat evidence, dynamic-programming beat tracking, the start of a bar from the bass band; 88–95% of beats on onsets on real music); dynamic programming picks the cut points for every scene within the playbook's length.
   Talking head: automatic jump cut, every kept segment is a scene with a source time, so picture and sound always match.
8. **Speed and speed ramp.** The Speed column (`2x`, `0.5x`, `ramp 1>2.5>1`); the source frame at the cut is always `In`; a ramp recomputes
   the source frame frame by frame (checked: off by ≤ 3 frames on a clip with a clock); the footage-overlap check counts speed;
   warns about slow-motion stutter when the proxy lacks fps.
9. **Transitions centred on the cut point.** `begin = cut − T/2`, `finish = nextCut + T/2`, so the cut lands exactly where it was set.
10. **A continuous virtual camera**, a perceptible scale ladder, no reset at cuts; a clip that already moves is kept still.
11. **Graphics anchored to words** (`@"phrase"`), kept on long enough to read, off ≥ 3 frames before a cut.
12. **Safe zones per platform.** TikTok (measured in practice) for the feed; Meta's Reels ad zone (`--platform reels-ad`);
    captions have their own strip; at most two information components at once.
13. **Dividing the footage budget.** Source ranges `[In, In + length × speed]`, a 0.5-second margin, listing the free ranges.
14. **The sync report** and the **check by eye** (`contact_sheet.py`): where flaws such as white text sinking into a white shirt show up.
15. **Sound effects by table**, with playbook overrides; only CC0 or self-made.
16. **Keep the repo clean.** No spare files, no dead code, no video content in the template; keys, media, models and work
    folders stay outside git; `playbook.py check` blocks "written but unused" techniques.
