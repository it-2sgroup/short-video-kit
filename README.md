# short-video-kit

Tooling for producing short vertical videos (TikTok, TikTok Shop, Instagram Reels, Shorts; 10–90 s)
of many kinds with Claude: product demos, property tours, food, talking heads, tutorials, fashion and
beauty, montages, promos. A Claude Code skill analyses the footage and the request, picks a **genre
playbook** and runs the edit; Python utilities measure and correct footage and sound, cut on voice
pauses or music beats and check the plan; a data-driven Remotion template renders the video.

> **Private repository.** `docs/CASE-LOG.md`, `docs/niche-data-queries.sql` and `skill/short-video-editing/references/niche-winning-patterns.md`
> contain client names and real campaign figures. Do not make this repository public, and do not hand `dist/short-video-editing.skill`
> outside the company: it carries `niche-winning-patterns.md`.

## Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [A framework that grows](#a-framework-that-grows)
- [Project structure](#project-structure)
- [Testing](#testing)
- [Licensing and third-party terms](#licensing-and-third-party-terms)
- [Versions and releases](#versions-and-releases)
- [Known limitations](#known-limitations)
- [Contributing](#contributing)

## Overview

Everything that depends on the **kind** of video lives in a playbook (`skill/short-video-editing/playbooks/`):
runtime band, hook, scene lengths, whether cuts follow the voice or the music, the beat structure,
transitions, camera moves, captions, colour theme and grade, sound-design overrides, recommended
graphics and the compliance checklist. The scripts read the playbook named in the plan, so adding a
genre is adding a JSON and a Markdown file, validated by `playbook.py check`.

An edit is described once, as a Markdown **edit plan** (a Scenes table and an Overlays table), checked
by scripts, compiled into `project.json` and rendered by one Remotion composition. No video content is
written into code.

```
raw clips ─► inspect --measure + contact sheet ─┐            ┌─► prepare_footage (correct + grade proxies)
request ────────────────────────────────────────┴► playbook ─┤
voice ─► trim / jumpcut ─► process_audio ─► align_captions ──┤
music ─► process_audio ─► suggest_cuts --music ──────────────┘
           skeleton ─► plan_scenes ─► edit plan ─► checkers ─► plan_to_project ─► Remotion ─► master
```

## Features

- **Genre playbooks**: `product-demo` (+ unboxing, listicle), `real-estate` (+ voiceover), `food-fnb`
  (+ review), `talking-head` (+ testimonial), `tutorial`, `fashion-beauty`, `montage-recap`,
  `promo-sale`, and `reference` ("make it like this sample": the sample's own numbers instead of a genre's); `playbook.py suggest` ranks them from the request and the footage measurements;
  `playbook.py skeleton` writes a plan that already meets the genre's rules.
- **Footage analysis and correction**: HDR tone-mapping, white balance from neutral pixels, exposure,
  stabilisation (vid.stab), denoise, levelling, lens correction and one grade per genre baked into a
  3D LUT (`inspect_footage.py --measure`, `prepare_footage.py`).
- **Sound**: voice cleanup with a noise print, presence EQ, de-essing, voice-relative compression and
  an expander; music levelling; a −14 LUFS / −1 dBTP master with a phone copy (`process_audio.py`).
- **Cutting**: on pauses of the voice or on beats of the music (built-in beat detection), jump cuts for
  talking heads, speed changes and speed ramps (`suggest_cuts.py`, `trim_voice.py --jumpcut`).
- **Rules enforced in code** per playbook: hook within 3 s, scene lengths, runtime (`pacing_checker.py`);
  no footage reused across a batch, counting fast scenes (`footage_overlap_checker.py`).
- **Word-accurate Vietnamese captions**: timing from Whisper, spelling from the script; karaoke, pop
  (one bold line) and plain styles.
- **Sync report**: cuts inside words, text on cuts, UI-zone collisions (TikTok and Reels ads),
  components a genre avoids, slow motion that would stutter, missing files (`plan_to_project.py`).
- **Render template**: 47 transitions centred on the cut (the shader ones need WebGL); a virtual camera that holds still on footage
  that already moves; per-scene speed and eased ramps; four colour themes; five title styles; 40 overlay
  components including information graphics (specs with icons, map pin, labels, count-up
  stats, bar charts, images, prices, steps, checklists, before/after card, cart arrow at TikTok Shop's
  measured product bar).
- **Sound design** from an editable table with per-genre overrides; CC0 and synthesized sounds only.
- **Compliance and platform guidance**: claims by category (household, real estate, food, cosmetics,
  finance; Vietnamese law researched to Nov 2026), TikTok vs Reels formats, safe zones, ranking
  signals, originality policy (`references/`).
- **ElevenLabs voiceover** with quota checks that refuse to spend credits the plan cannot cover.

## Requirements

| Component | Version | Needed for |
|---|---|---|
| Python | 3.10+ | All scripts |
| ffmpeg / ffprobe | 6+ (libvidstab for stabilisation) | Analysis, correction, proxies, audio |
| Node.js | 20.19+ | Rendering with Remotion |
| bash | macOS/Linux shell, or Git Bash on Windows | `setup.sh`, `selftest.sh` |
| Claude Code | current | Using the skill |
| ElevenLabs account | optional | Synthesising voiceovers |

## Installation

```bash
gh repo clone <owner>/short-video-kit
cd short-video-kit
./setup.sh --check          # what is installed and what is missing; changes nothing
./setup.sh                  # venv, Python deps, Whisper model (~460 MB), skill install
./setup.sh --set-key        # optional: store the ElevenLabs key (typed hidden)
./selftest.sh               # 16 groups of checks, no credits spent
./selftest.sh --render DIR  # also typecheck the template and render stills (downloads ~300 MB once)
```

`setup.sh` installs everything under `$HOME` (venv in `~/.local/share/short-video-kit`, model in
`~/.cache/short-video-kit`, key in `~/.config/short-video-kit/env`, skill in
`~/.claude/skills/short-video-editing`) and can be re-run safely. Options: `--download-ffmpeg`
(Linux static build), `--no-model`, `--person-model` (the 168 MB person-segmentation model the agency recipe needs; ask first), `--ocr` (RapidOCR + OpenCV for `analyze_reference.py`, ~85 MB; ask first), `--all` (every optional download that needs no typing: OCR, person model, static ffmpeg), `--no-skill`, `--package` (builds
`dist/short-video-editing.skill` for the Claude desktop app).

**Windows:** run `setup.sh` and `selftest.sh` from Git Bash. Install prerequisites with
`winget install Git.Git Python.Python.3.12 OpenJS.NodeJS.LTS Gyan.FFmpeg` and open a new terminal so
PATH refreshes. If the venv lives elsewhere, set `SVK_PYTHON` to its `python.exe` and
`WHISPER_MODEL_DIR` to the folder containing `faster-whisper-small/`.

**Moving to another computer:** clone, `./setup.sh --check`, `./setup.sh`, start a new Claude Code
session. Claude reads `CLAUDE.md` and the skill from the repository; nothing depends on a chat or a
local memory. After every `git pull`, re-run `./setup.sh` so the installed skill matches.

**What `./setup.sh` does not install, and what is not verified yet.** `setup.sh` installs the Python venv and packages, the Whisper model
and the skill; with `--ocr`, `--person-model`, `--download-ffmpeg` (or `--all`) the optional extras. It cannot, or must not, do these:

| Needs a person or the OS package manager | How |
|---|---|
| Git, Python 3.10+, Node 20+ (22+ for HyperFrames), a **full** ffmpeg build | `apt`, `brew` or `winget` (commands above); `./setup.sh --check` and `doctor.py` name what is missing |
| GitHub login to clone this private repo | `gh auth login --web && gh auth setup-git`, once per machine |
| ElevenLabs key | `./setup.sh --set-key`, typed hidden by the person; never in a chat |
| npm packages and Chromium of each render project (~450 MB) | `new_remotion_project.py DIR --install`, or `./selftest.sh --render DIR`; ask first |
| HyperFrames renderer (optional) | Node 22+, Chrome; the first `npx hyperframes` downloads a package, ask first |
| Internet at render time | Remotion fetches the Google Fonts a video uses |

Verified on Windows 11 (Git Bash, 2026-11-16): `./setup.sh --check`, `doctor.py` and `./selftest.sh` (every check passed) on a machine that already had
the tools; the Remotion template typechecked and rendered with the committed lockfile.

Not verified: macOS; a first run on a machine that has none of the tools; the Whisper download from Hugging Face and `--download-ffmpeg` on a machine
that has neither (only a clean `HOME` on Linux, reusing the existing model and ffmpeg). A new machine's `./setup.sh --check`, `doctor.py` and
`./selftest.sh` output is the evidence to bring back.

## Usage

### With Claude

Ask for a video in your own words; the skill analyses the clips, picks the playbook (or asks up to three
questions when the request and the footage disagree) and runs the edit:

> The raw clips are in `~/clips/villa-thao-dien`, a 3-bedroom unit priced at 28.5 billion VND: make a 40-second tour video with music for TikTok and Reels.

> Here are the raw clips in `~/clips/product-a` and the voiceover `voice.mp3`. Make a 35-second TikTok Shop
> video for the stain remover combo, and keep enough footage for three more videos.

### Command line

```bash
cd skill/short-video-editing

# 1. Analyse and choose
python scripts/inspect_footage.py CLIPS --measure --json analysis.json
python scripts/contact_sheet.py CLIPS --out clips.png
python scripts/playbook.py suggest --intent "tour of a 2-bedroom apartment" --analysis analysis.json
python scripts/playbook.py show real-estate

# 2. Render project with corrected, graded proxies (--install downloads npm packages and Chromium)
python scripts/new_remotion_project.py ~/renders/batch --playbook real-estate --install --proxies CLIPS

# 3. Sound
python scripts/process_audio.py voice voice.mp3 --out ~/renders/batch/public/audio/v1.wav
python scripts/process_audio.py music track.mp3 --out ~/renders/batch/public/audio/music.wav
python scripts/align_captions.py ~/renders/batch/public/audio/v1.wav --script script.txt --out captions.srt --words-out words.json

# 4. Cuts, plan, checks
python scripts/suggest_cuts.py --music ~/renders/batch/public/audio/music.wav --end 40 --playbook real-estate --json > cuts.json
python scripts/playbook.py skeleton real-estate --cuts cuts.json --title "Villa Thao Dien" > edit-plan.md
python scripts/plan_scenes.py --library library.json --plan edit-plan.md --kinds "VIEW,ROOM,..."
python scripts/pacing_checker.py edit-plan.md
python scripts/footage_overlap_checker.py plan-a.md plan-b.md --clips CLIPS

# 5. Compile, render, master, look
python scripts/plan_to_project.py edit-plan.md --out ~/renders/batch/v1.json --music audio/music.wav \
    --auto-camera --analysis analysis.json --auto-sfx
cd ~/renders/batch && npx remotion render src/index.ts Short out/v1.mp4 --props=v1.json
python <skill>/scripts/process_audio.py master out/v1.mp4 --out out/v1_final.mp4 --phone
python <skill>/scripts/contact_sheet.py out/v1_final.mp4 --project v1.json --out out/sheet.png
```

`npm run studio` in a render project opens `project.example.json`, a footage-free gallery of every
title style and component. The plan format is in `skill/short-video-editing/assets/edit-plan-template.md`;
the workflow in `docs/WORKFLOW.md`; a file-by-file map in `docs/STRUCTURE.md`.

## A framework that grows

Every technique the kit can do (47 transitions, 22 text effects, 8 subject effects shaped by a matte, 31 fonts, 15 colour grades, camera
moves and options, speed curves, looks, graphics, themes) is one card in `skill/short-video-editing/assets/techniques.json`.

```bash
python skill/short-video-editing/scripts/technique.py search "glitch rgb split"   # find a technique by the names editors use
python skill/short-video-editing/scripts/technique.py check                       # cards <-> code <-> docs <-> selftest, both ways
python skill/short-video-editing/scripts/analyze_reference.py sample.mp4 --out ref/   # measure a reference video's edit techniques
python skill/short-video-editing/scripts/reference_to_plan.py ref/report.json --out edit-plan.md --words words.json --texts texts.txt   # a first-draft plan with the sample's rhythm, transitions, camera and text slots
python skill/short-video-editing/scripts/editor.py RENDER_DIR                     # fix a project by hand on a browser timeline
python skill/short-video-editing/scripts/concept.py example > concept.json          # the idea of a video: feeling, tension, motif, one signature move, restraint
python skill/short-video-editing/scripts/directions.py edit-plan.md --concept concept.json --out-dir dirs   # three different directions + compare.md
python skill/short-video-editing/scripts/style_ledger.py check edit-plan.md --ledger style-ledger.json     # is this the last video again?
```

A video starts from an idea, not from a genre's defaults: `concept.py` (feeling, tension, a returning motif, ONE signature move, the restraint of the vocabulary), `directions.py` (three different directions built from it, with a table of how
they differ), `style_ledger.py` (the style of finished videos, so the next one is not the same). `references/creative-direction.md` explains the loop and what it cannot judge.

Handed a reference video, Claude measures it, writes a draft plan from the measurements (`reference_to_plan.py`: the sample's shots, transitions, camera moves and text slots; your footage and words; checked with `pacing_checker.py --reference`),
finds each technique it sees in the catalogue, and adds the ones the kit lacks by one loop
(`references/adding-techniques.md`): research with sources and licences, implement where its kind lives, a card, a doc row, a selftest.
Nothing about the video that revealed a technique (client, footage, slogans) is written into the skill; the case goes in `docs/CASE-LOG.md`.

## Project structure

```
.
├── CLAUDE.md                      Agent instructions for this repository
├── CHANGELOG.md · LICENSE         Release history; the proprietary notice
├── docs/
│   ├── WORKFLOW.md                Step-by-step workflow
│   ├── STRUCTURE.md               Every folder and file, tools and techniques
│   ├── PROMPT-VIDEO.md            Generic prompt template for any genre
│   ├── PROMPT-BATCH-VIDEO.md      Prompt structure for a production batch
│   ├── DECISIONS.md               Tool choices, technical pitfalls, sources, licence notes
│   ├── CASE-LOG.md                History of the jobs done for clients (private; not a guide)
│   └── niche-data-queries.sql     Reproduces the campaign figures behind the product-demo defaults (private)
├── samples/                       Fixtures used by selftest.sh (a product-demo and a real-estate plan, a voice line)
├── setup.sh · selftest.sh · requirements.txt · requirements-ocr.txt · .env.example
└── skill/short-video-editing/
    ├── SKILL.md                   Universal rules and workflow loaded by Claude
    ├── VERSION                    The kit's version (installed and packaged with the skill)
    ├── playbooks/                 One JSON (rules the scripts read) + one MD (craft) per genre; README = how to choose and add
    ├── references/                Shared craft and policy: platforms, claims and compliance, content-rights policy
    │                              (policy.md), hooks, cutting and pacing, transitions, camera, image processing,
    │                              typography, layout and motion graphics, captions, sync, footage ingest, voiceover,
    │                              audio and music, audio processing, sound design, before/after, campaign data, Remotion,
    │                              HyperFrames flow, CapCut techniques, adding techniques (how the kit grows), technique
    │                              backlog, transition pack, subject effects, reference analysis, editor
    ├── scripts/                   doctor, playbook, inspect_footage, contact_sheet, prepare_footage, trim_voice, process_audio,
    │                              make_voiceover, make_sfx, make_music, match_voice_takes, align_captions, suggest_cuts, plan_scenes, pacing_checker,
    │                              footage_overlap_checker, plan_to_project, new_remotion_project, project_to_hyperframes,
    │                              analyze_reference (+ ref_measure), montage, mix_report, find_cutaways, find_occluders, reverse_clip, match_cut, skin_check, person_matte, object_cutout, agency_plan, reference_to_plan, layout_check, concept, directions, style_ledger, finish_video,
    │                              check_lipsync, technique (the technique catalogue), editor (browser timeline editor)
    ├── assets/
    │   ├── edit-plan-template.md  The plan format
    │   ├── grades.json            15 colour looks (5 used by the playbooks, 9 in the library)
    │   ├── techniques.json        The technique catalogue: one card per technique (technique.py checks it against the code)
    │   ├── editor/                The browser editor's page (HTML, CSS, JS; no dependencies)
    │   ├── shot-library.example.json  Shot library format for plan_scenes.py
    │   ├── sfx/                   CC0 sound effects, their sources, the event → sound table
    │   ├── remotion-template/     Render project: theme, engine, components
    │   └── hyperframes-template/  The HyperFrames renderer's kit.js and kit.css (second renderer, Apache-2.0)
    └── evals/                     Evaluation cases for the skill
```

## Testing

`./selftest.sh` runs 16 groups without spending ElevenLabs credits: tools; footage inspection;
playbooks (every playbook and variant valid, its own skeleton passing its own pacing, every component,
grade, theme and caption style used by some playbook) and pacing per playbook; caption alignment; the
ElevenLabs key (read-only); plan compilation (product demo and a music-driven property tour with speed
ramps and information graphics); footage reuse (including fast scenes); cuts on pauses and on beats;
voice trimming and jump cuts; contact sheets; scaffolding; sound effects; voice cleanup and mastering;
footage measurement and correction; the HyperFrames project build (baked speed ramps, unsupported overlays
reported); the technique catalogue; packaging (version, changelog, pins, lockfile, a document for every script).
`./selftest.sh --render DIR` adds group 17: typecheck the Remotion template and render stills,
including the information graphics.

## Licensing and third-party terms

This repository is proprietary and unlicensed for redistribution. Third-party terms that affect use:

| Dependency | Terms |
|---|---|
| Remotion | Free for individuals and companies of up to 3 employees; otherwise $25/month per seat, and an AI agent writing Remotion code counts as a seat ([licence](https://www.remotion.dev/license)). |
| HyperFrames (second renderer) | Apache-2.0 ([licence](https://github.com/heygen-com/hyperframes/blob/main/LICENSE)): free commercially, no seat count. The fonts, footage and music you add keep their own terms. Node 22+ and Chrome; the first `npx hyperframes` downloads the package. |
| ElevenLabs | Free-plan audio cannot be used commercially, including after upgrading. |
| Google Fonts used by the template | SIL Open Font License. |
| Sound effects in `assets/sfx` | 68 recordings under CC0, each with its source in `assets/sfx/SOURCES.md`; the others are synthesized by `make_sfx.py`. Add only CC0 or self-made sounds. |
| faster-whisper | MIT. |
| ffmpeg | The static builds used here are GPL (libvidstab, x264); the kit calls ffmpeg as a program and ships none of it. |
| Music on commercial content | The platform's commercial library (TikTok CML, Meta Sound Collection) or an explicit commercial licence only. |

Design references: `remotion-dev/skills`, `iart-ai/tiktok-video-skills` (MIT),
`browser-use/video-use` (MIT), `heygen-com/hyperframes` (Apache-2.0). Rules were adapted; no code
was copied. Details in `docs/DECISIONS.md`.

## Versions and releases

The version (MAJOR.MINOR.PATCH) is in `skill/short-video-editing/VERSION`, which is installed and packaged with the skill; `CHANGELOG.md` says what
changed. `doctor.py` and `./setup.sh --check` show the version of this repository and of the installed skill and warn when they differ.

To release:

1. `./selftest.sh` passes (and `./selftest.sh --render DIR` when the template changed).
2. Raise `VERSION` and put a `## [x.y.z] - date` entry on top of `CHANGELOG.md` (selftest group 15 fails when they disagree).
3. Commit, tag (`git tag -a vX.Y.Z -m "..."`) and push with `--follow-tags`.
4. On every machine: `git pull`, `./setup.sh`, start a new Claude Code session. For the Claude desktop app: `./setup.sh --package`.

The Remotion template's `package-lock.json` pins every npm package for every platform. Regenerate it only on purpose: change `package.json`, run
`npm install --package-lock-only` in a copy of the template, check it with `npm ci --dry-run`, then typecheck and render a still
(`./selftest.sh --render DIR`) before committing.

## Known limitations

- Neither TikTok nor Instagram publishes organic UI safe-zone pixels; the template uses a measured
  TikTok layout and Meta's documented Reels-ad zone. Confirm with a private test post.
- Footage measurements are heuristics checked on synthetic clips and one real iPhone clip (daylight,
  tripod), plus an HLG copy and a simulated night copy of it; no real handheld, night or 0.5× footage
  yet. Confirm on the contact sheet. Speech on camera is a guess until `align_captions.py` confirms it.
- Proxy creation is slow on small machines (4K60 HEVC decodes at ~4 s per second of footage on a
  4-core laptop); use `--proxy-height 1920` for drafts.
- Beat detection is a suggestion: on three real CC0 tracks 88–95% of beats landed on strong onsets, but a
  compound-feel track was read at 73 bpm where 110 is equally defensible.
- Nothing has been judged by ear by the tools: the measured numbers (−14 LUFS, true peak, bed level) are
  checks, not a listening test.
- Shader transitions (`crossZoom`) and light leaks need WebGL (`angle` renderer); verified on
  Windows and in headless Chromium on Linux.
- The evaluation cases have no automated harness; the two genre cases were run once by hand with fresh
  agents (results in `docs/DECISIONS.md`).

## Contributing

- Keep the repository clean: no unused files or dead code, and no video content in the template.
- A new genre or a client's house style → a playbook or a variant (`playbooks/README.md`).
- New look → `theme.ts` or `assets/grades.json`, used by a playbook. New graphic → a component in
  `components/graphics/`, registered in `registry.tsx`, documented in
  `references/layout-and-motion-graphics.md`, and listed by the playbooks that use it.
- Run `./selftest.sh` after changing the skill (and `--render DIR` after changing the template), and
  read `git status` before every commit; secrets and media are ignored but must never be forced in.
