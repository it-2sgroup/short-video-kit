# short-video-kit — instructions for Claude

The user works in **Vietnamese**: reply in Vietnamese. This repo is a toolkit for making short vertical
videos of **many kinds** (TikTok, TikTok Shop, Reels; product demos, property tours, food, talking heads,
tutorials, fashion/beauty, montages, promos): the Claude skill `skill/short-video-editing` with one
**playbook** per genre (`playbooks/`), Python scripts (footage measurement and correction, contact sheets,
voice cleanup and mastering, jump cuts, cuts on pauses or beats, ElevenLabs voiceover, Whisper-aligned
captions, plan checkers, plan → project compiler) and a data-driven Remotion render template.

**Everything a new machine needs is in this repo.** A chat, a Claude memory or an installed skill on
another computer is not shared: if a rule or a fix matters, it belongs here (this file, `docs/`, or the
skill), not in someone's head.

## First thing in every session

Run `./setup.sh --check` (changes nothing; lists what is installed and what is missing). For the deep
check run `python skill/short-video-editing/scripts/doctor.py`: it also tests every ffmpeg filter the scripts
call (vidstab, zscale, haldclut, afftdn…), numpy in the venv, and free disk. The same script ships inside the
skill, so a chat opened **outside** this repo can run it too (SKILL.md step 0). On Windows run
bash through Git Bash — `& "C:\Program Files\Git\bin\bash.exe" ./setup.sh --check` from PowerShell. If
anything is missing, or the skill copy is out of date after a `git pull`, follow the setup steps below.

## When the user says "setup", "cài đặt", or has just cloned this repo

Do these in order. Show real output; never summarise a failure as success.

0. **Prerequisites** (Windows: `winget install Git.Git Python.Python.3.12 OpenJS.NodeJS.LTS Gyan.FFmpeg`,
   then open a **new** terminal so PATH refreshes; macOS: `brew install python node ffmpeg`; Ubuntu:
   `apt install python3 python3-venv nodejs ffmpeg`). Cloning this private repo needs
   `gh auth login --web` and `gh auth setup-git` once per machine. **Ask before installing anything.**
1. **Run `./setup.sh`** (bash; on Windows use Git Bash) and read all of it. It builds a venv under
   `~/.local/share/short-video-kit`, fetches the Whisper model (~460 MB), installs the key file if
   present, and installs the skill into `~/.claude/skills/short-video-editing`. Re-run it after every
   `git pull` so the installed skill matches the repo (`./setup.sh --check` shows drift).
2. **ffmpeg missing?** Let the user choose: `brew install ffmpeg` / `apt install ffmpeg` /
   `winget install Gyan.FFmpeg`, or `./setup.sh --download-ffmpeg` (Linux static build, ~40 MB).
   **Ask before any download.**
3. **No ElevenLabs key?** Only needed to synthesize a voice; a supplied voice works without one. The
   user runs **`./setup.sh --set-key` themselves** (typed hidden). **Never** ask for the key in chat;
   never read, print, log, commit it or put it on a command line. It lives at
   `~/.config/short-video-kit/env` (mode 600). Verify with `make_voiceover.py --quota`.
4. **Rendering needs Node 20+.** `./selftest.sh --render [DIR]` typechecks the template and renders one
   still; without `node_modules` in DIR it runs `npm install` (npm packages + Remotion's Chromium,
   ~300 MB), so ask first.
5. **Run `python skill/short-video-editing/scripts/doctor.py`** and read all of it: a build of ffmpeg without
   libvidstab or libzimg passes "ffmpeg on PATH" and then fails mid-encode. Fix every `✗`; low disk space is a
   stop sign for 4K work (put the venv, model and work folders on another drive).
6. **Run `./selftest.sh`** and report each PASS / FAIL / SKIP (a SKIP on group 5 is fine without a key).
7. Confirm `~/.claude/skills/short-video-editing/SKILL.md` exists and tell the user to start a **new**
   Claude Code session so the skill loads.

Machine-specific locations are overridable: `SVK_PYTHON` (the venv's python), `WHISPER_MODEL_DIR`
(folder holding `faster-whisper-small/`), `SVK_MODEL_DIR` (where `u2net_human_seg.onnx` is looked for first). If drive C: is small, put the venv, model and work folders on
another drive and set these two variables for the user.

## When the user asks for a video

Follow `docs/WORKFLOW.md` (Vietnamese) and the skill's `SKILL.md`. In short:

1. `./setup.sh --check`. A script PDF: open it with the Read tool (`pages` up to 20 at a time) and copy
   the spoken lines into one `script.txt` per video (no PDF library is installed).
2. **Analyse, then choose the playbook**: `inspect_footage.py CLIPS --measure --json analysis.json`,
   `contact_sheet.py CLIPS --out clips.png` (**look** at it), `playbook.py suggest --intent "<the user's
   words>" --analysis analysis.json`, then read `playbooks/<id>.md`. Say which playbook and why in one
   line; when the request and the footage disagree or facts are missing, ask **at most three** questions,
   each with a default. For a batch, **budget the footage** first (`references/policy.md` §4.1).
3. Footage: `new_remotion_project.py RENDER --playbook <id> --proxies CLIPS` (corrected, graded proxies;
   look at `corrections.json` and a contact sheet of the proxies).
4. Sound: a supplied voice → `trim_voice.py` if longer than the playbook allows, `process_audio.py voice`,
   transcribe, correct the script **by hand**, `align_captions.py`; a talking head → `trim_voice.py
   --jumpcut`; no voice → ElevenLabs (after `--quota`) or music only (`process_audio.py music`).
5. Plan: `suggest_cuts.py` (pauses, or `--music` for beats) → `playbook.py skeleton <id> --cuts` →
   `plan_scenes.py --plan` → fill Scenes and Overlays; `pacing_checker.py`, `footage_overlap_checker.py`
   (all plans together); `plan_to_project.py --auto-camera --analysis --auto-sfx` (read the sync report);
   render (Remotion, or HyperFrames with `project_to_hyperframes.py`: choose per video, `references/hyperframes-flow.md`
   §1); `process_audio.py master`; `contact_sheet.py VIDEO --project …` and **look** at it.
6. Report in Vietnamese: playbook and why, runtime, scenes, hook, footage corrections, what the sync report
   still flags, claims that need the human, the publishing checklist, and what was **not** verified (never
   say "listened" unless it was).

Keep work files **outside this repo** (e.g. `<work>/v1/{script.txt,captions.srt,words.json,edit-plan.md}`,
`<work>/analysis.json` and one render project `<work>/render`); only the toolkit lives here.

## When the user hands over a reference video ("make it like this") or a presenter's takes with a voice

`skill/short-video-editing/references/agency-pitch-recipe.md` is the full recipe (steps 0-10, every tool and flag, the pitfalls met). In short: `analyze_reference.py sample.mp4 --out ref/` and
**look** at its sheets before planning; `match_voice_takes.py` when the voice is the takes' own sound; `find_cutaways.py`, `person_matte.py` (needs the 168 MB person model: ask, then
`./setup.sh --person-model`), `agency_plan.py` for the draft plan; build with `plan_to_project.py`; check with `node stills.mjs` + `montage.py`; render Remotion with `--concurrency=5`;
finish with `finish_video.py`; prove with `check_lipsync.py` and `mix_report.py`. A technique the kit lacks is researched and added (component + doc row + selftest), not faked. Say what was not
verified: nobody has listened to the sound bank or the music, and a sentence guessed from a poor transcript or a logo keyed from a sample frame is the human's to confirm.

## Growing the kit: the technique catalogue

The kit is a framework, not a record of past videos. Every technique it can do is one card in `skill/short-video-editing/assets/techniques.json`
(`python skill/short-video-editing/scripts/technique.py list | kinds | show ID | search "words"`; the search knows the names editors use). When a request
or a reference needs something the kit lacks: search first (it may exist under another name), then follow `references/adding-techniques.md`
(research with sources and licences, implement where its kind lives, card, doc, selftest, `technique.py check`). What was researched but not built is in
`references/technique-backlog.md`. Nothing client-specific (names, footage names, slogans, dates) goes into `skill/`, the template, scripts, examples or help
strings: use placeholders (`CLIP_A`, `BRAND`, `Text A`); the case itself is written in `docs/CASE-LOG.md`.

## Footage rights and duplicate content — read `references/policy.md` first

Before planning **any batch** of videos, and before using **any footage that is not the user's own or
licensed**, read `skill/short-video-editing/references/policy.md` (also in the installed skill). Short
version, with the evidence in that file:

- **Never download, crawl, cut or splice other people's videos** (Douyin, TikTok, YouTube, a competitor's) into
  product videos without a **written commercial licence**. Douyin's terms forbid commercial use and
  scraping; TikTok removes or demotes reused content and bans repeat infringers. Never run or adapt
  `crawl-video-douyin`-style download → re-dub → re-post pipelines for ads.
- **Reshuffling one source into many videos is the pattern TikTok Shop names as repetitive content**
  ("re-posting the same video at high volume with only order of clips changed"). Changing music, voice or
  background does not fix it. The default is **no source range reused across videos of a batch**
  (`footage_overlap_checker.py` over all plans). Count what the footage supports (a scene takes a whole short clip; about 40 s of usable
  footage per video) before promising a batch size. When the footage runs out,
  stop and say so with these numbers and propose shooting more, hiring KOCs with licences, or consented
  customer video; do not reshuffle.
- The footage must show **the advertised product's own result**; never another product's.
- Ask the market and check its posting limits (Vietnam's rules were not found; US and Malaysia limits are in
  the file).

## Decisions that belong to the human — do not make them silently

- **ElevenLabs plan.** Free-plan audio is not licensed for commercial use, ever. Run `--quota` and say
  so before synthesizing anything meant to ship.
- **Remotion licence.** Free only for individuals or companies of up to 3 employees; $25/seat/month
  above that, and an AI writing Remotion code still counts as a seat. HyperFrames (the second renderer,
  `references/hyperframes-flow.md`) is Apache-2.0: say so when a client is above the Remotion limit. Its first
  `npx hyperframes` downloads a package: ask first.
- **Any download** (packages, models, binaries, stock media). Name it, its source and size; wait for yes.
- **Third-party footage of any kind**, and **how many videos** a batch should have when the footage cannot
  support it: put the numbers to the user (see the rights section above); never decide by reshuffling.
- **Trimming a supplied voiceover** or dropping a claim: say exactly which sentences/claims.
- **Claims already inside a supplied voice** (absolute results, instant effect, savings, scarcity pressure):
  flag them against `references/claims-and-compliance.md`; keep the on-screen text clear of them.
- **The playbook**, when the request and the footage disagree: ask, do not force footage into a genre.
- **Facts on screen** (prices, areas, legal status of a property, offer dates): only what the user or the
  documents give; never invented or rounded.

## Facts already learned the hard way — do not relearn them

- `eleven_multilingual_v2` does **not** support Vietnamese. Default is `eleven_turbo_v2_5`.
- Free ElevenLabs plans can only use `premade` voices (library voices return HTTP 402).
- `[emotion]` tags only work on `eleven_v3`; other models read them aloud. The scripts strip them.
- Whisper mishears Vietnamese ("túi xách" → "tui sách"): captions take **words from the script**,
  **timing from Whisper**. Supplied voice files often differ from the written script — transcribe,
  correct by hand, then align.
- A client's house style (e.g. scenes 3–4 s with soft transitions, no text in boxes) belongs to the playbook it was
  given for (`product-demo`), not to every genre (food, fashion and montages cut on the beat at 1–2 s): say so if
  the same client asks for another genre.
- Rules that depend on the kind of video live in `playbooks/<id>.json`; the scripts read the plan's
  `**Playbook:**` line. Never hard-code a genre's number in a script; add or change a playbook (or a
  variant) and run `playbook.py check`. The kit is a library: a technique no playbook recommends is allowed
  (`playbook.py check` lists it as a note); what keeps the library honest is `technique.py check` (every technique has a card, a doc and a test).
- Footage correction (measured, `references/image-processing.md`): white balance only from near-neutral
  pixels (a green bowl fooled grey-world); denoise only when dark or very noisy (texture fools the
  meter); an RGB filter right after `vidstabtransform` segfaults ffmpeg 7.0 (the script inserts
  `scale=iw:ih`); colour steps are baked into one 3D LUT (113 s → 45 s for 6 s of 4K60); a BEFORE and an
  AFTER get the same correction (`correction: shared`). Run one heavy 4K ffmpeg job at a time: two
  together exhausted 14 GB and were killed.
- Audio (measured, `references/audio-processing.md`): the noise floor is the 5th percentile of 100 ms
  windows (the 10th "cleaned" a clean TTS line and raised its floor 15 dB); the compressor threshold
  follows the voice; `afftdn` delays 25 ms and `alimiter` adds gain by default — the script handles both.
  Neither TikTok nor Instagram publishes a loudness target: −14 LUFS / −1 dBTP is common practice.
- Captions: whole phrases, the spoken word highlighted (`karaoke`, `pop`); never one word at a time
  (research: viewers read ahead; Vietnamese words are syllables).
- Speed ramps in Remotion re-time the source frame by frame inside `<Freeze>` (animating `playbackRate`
  does not work); slow motion needs a 60 fps proxy (`prepare_footage.py --slowmo`).
- Reels ads keep the bottom 35% clear (Meta): `plan_to_project.py --platform reels-ad`; there is no
  TikTok Shop product bar on Reels, so no cart arrow there.
- Shader transitions (`crossZoom`, `filmBurn`, `zoomBlur`...) and light leaks need WebGL in headless Chrome; without it the render throws
  ("Failed to create WebGL2 context"). The template defaults to the software renderer `swangle` (works with or without a GPU); `SVK_GL=angle` selects the GPU path.
- iPhone footage is 4K HEVC with rotation metadata: render from ffmpeg proxies
  (`new_remotion_project.py --proxies`), not the originals.
- White text vanishes on white fabric: over white garments use the `outline` or `marker` title style, not
  `gradient` or `stack` (white→sky fills). Check every title on the contact sheet.
- TikTok Shop's cart (the yellow bag tile of the product bar) is at frame (112, 1677), **not** (300, 1440):
  measured on a phone screenshot of the feed, details and how to re-measure in
  `references/layout-and-motion-graphics.md`. The `cart` arrow curves onto it; check any change with a
  mockup of the frame scaled to a real phone screen. When the voice lists three things, use the
  `thumbs` strip (three-photo header) with `+@"word"` timing and `~x,y,zoom` framing.
- Before/after: the reveal gets a `compare` card (TRƯỚC/SAU frames of the same garment from ranges
  already on screen, with an honest time note); TikTok's **ad** policy bars before-and-after
  comparisons, so ask whether the video will be boosted. Details: `references/before-after.md`.
- Viewer-first layout (default for the feed playbooks; the `talking-head:agency` variant deliberately puts captions in a strip above its cards instead): titles hug the top edge (y 236–420), captions are the
  lower third (y ≈ 1340, 58 px, ≤ 2 lines), the middle ~900 px belongs to the footage. Title/caption blocks
  in the middle made viewers read instead of watch. Camera moves must be visible (≥ ~12% scale or ~8% pan,
  `focus` on the action, shot size alternating); render from 2880-tall proxies so the zoom stays sharp.
  Overlay targets (`highlight`, `callout`) are in screen space: re-check them on a still after the camera changes.
- Batches: `suggest_cuts.py` (cuts on pauses or beats) + `playbook.py skeleton` + `plan_scenes.py`
  (non-overlapping footage from a shot library, counting fast scenes) make the allocation;
  `plan_scenes.py` exiting 1 means the footage ran out: report the shortfall.
- Remotion: show a still of a clip with `trimBefore` and `<Freeze frame={0}>`; `Freeze frame={N}` with a
  large N inside a short overlay shows the wrong moment.
- Sound effects: only CC0 or self-made sounds go into `assets/sfx/` (row in `SOURCES.md` for each file);
  never the meme sounds in `@remotion/sfx` (`vine-boom`, `windows-xp-error`, `bruh`: no licence stated).
  Nothing across the reveal. A tool cannot hear: say whether you listened. Details:
  `references/sound-design.md`.
- Edit-plan tables are the footage ledger: keep every `edit-plan.md`, and pass them all (named, no
  shell glob) to `footage_overlap_checker.py`. A `project.json` cannot rebuild a lost plan.
- A render project is a **copy** of the template: after the template changes, run
  `new_remotion_project.py <render dir> --update` (replaces `src/` and config, keeps `public/`,
  `node_modules/` and your `*.json` projects).
- Windows PowerShell 5.1: `python -I` ignores `PYTHONIOENCODING`, use `python -X utf8`; the `python3`
  command may be the Microsoft Store stub (use the venv's `Scripts\python.exe`); a program installed by
  winget is not on PATH until a new terminal; `Get-Content` needs `-Encoding utf8` for Vietnamese files.
- HyperFrames renderer (measured on Windows, 0.9.26): same `project.json`, a pure function of the frame in `kit.js`;
  `check` gives 0 errors and `line_unread` warnings on fast-voice captions (normal); it does not draw `magnifier`,
  `thumbs`, `compare`, `ranking`; `+shake +glitch +rgb +pulse` and `--look` exist only there; an RGB split needs an
  SVG filter (a `drop-shadow` on an opaque frame only paints the edges); Python's `round()` is not JS `Math.round`
  (use the half-up helper); Remotion's `perceptual-scale` eases zoom in area (`√(a²+t(b²−a²))`), not geometrically
  (the first port got it wrong: SSIM 0.946 → 0.987 once fixed); `selftest.sh` needs `PYTHONUTF8=1` on Windows (it now exports it).
- Footage for a batch (measured): a scene uses a whole short clip (a 4 s clip hosts one scene of <= 3.2 s; two ranges of one clip need 0.5 s between them), so supply is about one scene per clip. Allocate **round-robin over all videos** (scene 1 of every video, then scene 2...; product beats before drinking shots), or the last video gets every leftover. Reserve one closing-shot clip per video. File names must not contain a dot (`…` becomes `...` and `Path.stem` cuts it: two clips collapse into one name). `plan_scenes.py --used` is case-insensitive; plans store clip names in upper case. A client's "X% new footage" is limited by the same arithmetic: say so with the numbers.
- A supplied voice that is the camera audio of the chosen takes, spliced, matches each take sample for sample (normalised correlation 0.98-1.0): `match_voice_takes.py` gives the lag per take; use the take's own picture with `In = start + lag` and the lips are exact. Lines no take holds get cutaways from the silent pre-roll and walk-off of the other takes, never another take of the same line; the other takes of a line are for cutaways only. Whisper `small` mishears Vietnamese company talk: give it `initial_prompt` with the brand and domain words, and correct by hand.
- Card layouts over the animated grid (`talking-head:agency`, theme `crimson`): `cardSlide`/`cardSwirl` transitions, `phrase`/`pill`/`arc`/`logo`. A logo keyed out of a sample frame (alpha = (R-G+55)/260 with ffmpeg `geq`, 4x Lanczos) is the last resort: ask the owner for the vector. 8 render workers fail with `No frame found at position` on 2880-tall proxies; `--concurrency=5` passes.
- A silhouette flash opener fills the speaker's outline with white on a few early frames (e.g. 0, 2, 4 at 30 fps), then plays the video; "hidden letters jumping up" is a pile of tilted copies (grey ghosts under, colour copies larger and nearer the edge): `burst`. A backlit face is grey beside a hand edit: `faceGlow` (brightness 1.26, saturate 0.88, blur 1, size 1.15, veil 0.07, head from `person_matte.py --faces`) matches it; a ring or ellipse effect must never cross the face. The person model `u2net_human_seg.onnx` (168 MB) is not in the repo: `./setup.sh --person-model` downloads it next to the Whisper model (ask first); `doctor.py` checks it. Full recipe: `references/agency-pitch-recipe.md`; draft the plan with `agency_plan.py`, finish with `finish_video.py`, prove the lips with `check_lipsync.py`.
- Sound bank: 63 recorded CC0 files in `assets/sfx` (Kenney, OpenGameArt, Remotion's CDN) + 17 sounds `make_sfx.py` synthesizes into each render project, rotated per event so nothing repeats; nobody listened to them: say so. `--music-levels=-6,-6` needs the `=`.
- No licensed track is bakeable into a business-account video (TikTok: Commercial Music Library only, not reachable by a render): `make_music.py` writes a self-made bed that follows the cuts;
  deliver a second master without music so the human can add a CML track at upload.
- Files sent to a phone or web viewer are limited to ~30 MB: `process_audio.py master … --phone` writes a
  CRF 24 copy beside the master.

## Read next

`README.md` → `docs/CAU-TRUC.md` (what every folder and file is) → `docs/WORKFLOW.md` → `docs/DECISIONS.md` →
`skill/short-video-editing/SKILL.md` → `skill/short-video-editing/playbooks/README.md` (genres: how to choose and add) →
`skill/short-video-editing/references/policy.md` (content-rights and duplicate-content policy) → `references/hyperframes-flow.md` (the second renderer) and
`references/capcut-techniques.md` (where each CapCut technique lives in the kit) → `references/adding-techniques.md` (how the kit grows) → `docs/CASE-LOG.md` (the history of jobs done: not a guide). Adding, renaming or removing a file or script means updating
`docs/CAU-TRUC.md` and the structure tree in `README.md` in the same commit.

## Working in this repo

- **Never commit** `.env*`, `bin/`, `models/`, `dist/`, media files. `.gitignore` enforces it; still
  read `git status` before every commit.
- **The repo must stay private**: `docs/CASE-LOG.md` and `docs/niche-data-queries.sql` hold client names and real campaign figures.
  Do not paste them into external services. Nothing under `skill/` (the part that is installed and shared) may name a client, a person or a
  real footage file: describe techniques, use placeholders (`CLIP_A`, `BRAND`, `Text A`) in every comment, example and help string.
- **Keep it clean**: no dead code, no unused files, no video content hard-coded in the template (it
  belongs in the plan / `project.json`). New genre or house style → a playbook or a variant
  (`playbooks/README.md`); any new technique (transition, text effect, subject effect, grade, camera option, speed curve, look, graphic) →
  the loop in `references/adding-techniques.md`: implement where its kind lives, a card in `assets/techniques.json`, a doc row, a selftest —
  `technique.py check` fails otherwise.
- After changing anything under `skill/short-video-editing/`, run `./selftest.sh`; after changing the
  template, run `./selftest.sh --render <render project>` and look at stills.
- Never label a staged or designed graphic as a "real customer review".
