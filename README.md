# short-video-kit

Tooling for producing short vertical product videos (TikTok Shop, Reels, Shorts; 30–40 s) with
Claude: a Claude Code skill that plans and checks the edit, Python utilities for footage, voiceover
and captions, and a data-driven Remotion template that renders the final video.

> **Private repository.** `docs/` and `skill/short-video-editing/references/niche-winning-patterns.md`
> contain real campaign figures and creator handles. Do not make this repository public.

## Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Project structure](#project-structure)
- [Testing](#testing)
- [Licensing and third-party terms](#licensing-and-third-party-terms)
- [Known limitations](#known-limitations)
- [Contributing](#contributing)

## Overview

An edit is described once, as a Markdown **edit plan** (a Scenes table and an Overlays table). The
plan is checked by scripts, compiled into `project.json`, and rendered by a single Remotion
composition. No video content is written into code, so changing a video means changing its plan,
not prompting an AI to rewrite components.

```
raw clips ─► inspect / shot log ─► edit plan ─► checkers ─► plan_to_project ─► Remotion render
voiceover ─► align_captions (captions.srt + words.json) ───────────┘
```

## Features

- **Pacing rules enforced in code**: hook within 3 s; 3–4 s scenes (never > 4 s, never < 2.5 s
  outside the hook); 25–45 s runtime (`pacing_checker.py`).
- **Footage budgeting across videos**: one batch of raw clips feeds many videos with no reused range
  (`footage_overlap_checker.py`, which also lists the footage still free).
- **Word-accurate Vietnamese captions**: timing from Whisper, spelling from the script; word-level
  timings for karaoke captions and word-anchored graphics (`align_captions.py`).
- **Sync report**: flags cuts inside words, text appearing on a cut, graphics under TikTok's UI, zone
  collisions and flashing captions (`plan_to_project.py`).
- **Render template** (`assets/remotion-template`):
  - 11 transitions, each centred on the planned cut so the voiceover never drifts, plus flash and
    light-leak accents;
  - a virtual camera (push, pull, pan, hold, keyword punch-ins) with perceptual easing that never
    resets on a cut;
  - five title styles (outline, stack with serif-italic accent, gradient, frosted glass, marker) with
    fonts verified for Vietnamese;
  - twelve motion-graphic components (callouts with leader lines, steps, checklists, count-up price,
    cart pointer, hand-drawn highlights, stickers, magnifier, thumbnail recap, ranking podium,
    progress bar, lower third);
  - karaoke captions, music ducked under speech, sound-effect cues.
- **Sound design**: `--auto-sfx` places licence-safe sound effects (CC0 recordings plus sounds
  synthesized with ffmpeg) on moving transitions and selected graphics from an editable table
  (`assets/sfx/sfx-map.json`), thinned so they never crowd the voice; nothing across the reveal.
- **Commercial-claim guidance** for TikTok Shop (banned phrasing and compliant rewrites) and
  before/after demonstration rules.
- **ElevenLabs voiceover** with quota checks that refuse to spend credits the plan cannot cover.

## Requirements

| Component | Version | Needed for |
|---|---|---|
| Python | 3.10+ | All scripts |
| ffmpeg / ffprobe | any recent | Inspection, proxies, audio trimming |
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
./selftest.sh               # 11 groups of checks, no credits spent
./selftest.sh --render      # also typecheck the template and render one still (downloads ~300 MB once)
```

`setup.sh` installs everything under `$HOME` (venv in `~/.local/share/short-video-kit`, model in
`~/.cache/short-video-kit`, key in `~/.config/short-video-kit/env`, skill in
`~/.claude/skills/short-video-editing`) and can be re-run safely. Options: `--download-ffmpeg`
(Linux static build), `--no-model`, `--no-skill`, `--package` (builds
`dist/short-video-editing.skill` for the Claude desktop app).

**Windows:** run `setup.sh` and `selftest.sh` from Git Bash. Install prerequisites with
`winget install Git.Git Python.Python.3.12 OpenJS.NodeJS.LTS Gyan.FFmpeg` and open a new terminal so
PATH refreshes. If the venv lives elsewhere, set `SVK_PYTHON` to its `python.exe` and
`WHISPER_MODEL_DIR` to the folder containing `faster-whisper-small/`.

**Moving to another computer:** clone the repository, run `./setup.sh --check`, then `./setup.sh`, then
start a new Claude Code session. Claude reads `CLAUDE.md` and the skill from the repository, so it follows
the same rules and workflow; nothing depends on a chat or a local memory. After every `git pull`, re-run
`./setup.sh` so the installed skill matches the repository.

## Usage

### With Claude

The skill activates when you ask for a short video, for example:

> Here are the raw clips in `~/clips/saiza` and the voiceover `kb7.mp3`. Make a 35-second TikTok Shop
> video for the SAIZA stain remover combo, and keep enough footage for three more videos.

Claude inspects the clips, budgets the footage, writes the edit plan, runs the checkers, compiles the
project and renders, reporting what the sync report still flags.

### Command line

```bash
cd skill/short-video-editing

# 1. Footage
python scripts/inspect_footage.py /path/to/clips --log
python scripts/contact_sheet.py /path/to/clips --out clips.png        # one row of frames per clip

# 2. Voice and captions (a supplied recording: list pauses, keep ranges, then align)
python scripts/trim_voice.py voice.mp3 --silences
python scripts/trim_voice.py voice.mp3 --keep 0-3.8,8.3-16.1 --out voice_short.mp3
python scripts/align_captions.py voice.mp3 --script script.txt --out captions.srt --words-out words.json

# 3. Checks
python scripts/pacing_checker.py edit-plan.md
python scripts/footage_overlap_checker.py plan-a.md plan-b.md --clips /path/to/clips

# 4. Render project (once per batch; --install downloads npm packages and Chromium)
python scripts/new_remotion_project.py ~/renders/batch --install --proxies /path/to/clips
cp voice.mp3 ~/renders/batch/public/audio/kb7.mp3

# 5. Compile and render
python scripts/plan_to_project.py edit-plan.md --out ~/renders/batch/kb7.json \
    --voice audio/kb7.mp3 --captions captions.srt --words words.json --auto-camera --auto-sfx
cd ~/renders/batch
npx remotion still src/index.ts Short out/check.png --frame=45 --props=kb7.json
npx remotion render src/index.ts Short out/kb7.mp4 --props=kb7.json
python <skill>/scripts/contact_sheet.py out/kb7.mp4 --project kb7.json --out out/sheet.png   # look at it
```

`npm run studio` in a render project opens `project.example.json`, a footage-free gallery of every
title style and component.

The edit-plan format is documented in `skill/short-video-editing/assets/edit-plan-template.md`;
the full workflow (in Vietnamese) in `docs/WORKFLOW.md`; a file-by-file map of the repository, the tools
and the techniques it uses (in Vietnamese) in `docs/CAU-TRUC.md`.

## Project structure

```
.
├── CLAUDE.md                      Agent instructions for this repository
├── docs/
│   ├── WORKFLOW.md                Step-by-step workflow (Vietnamese)
│   ├── CAU-TRUC.md                Every folder and file, tools and techniques (Vietnamese)
│   ├── DECISIONS.md               Tool choices, pitfalls, sources, licence notes
│   └── niche-data-queries.sql     Reproduces every campaign figure used by the skill
├── samples/                       Fixtures used by selftest.sh
├── setup.sh · selftest.sh · requirements.txt · .env.example
└── skill/short-video-editing/
    ├── SKILL.md                   Rules and workflow loaded by Claude
    ├── references/                Topic guides (pacing, transitions, camera, typography,
    │                              layout and motion graphics, sync, captions, voiceover,
    │                              audio, platform policy, hooks, campaign data, Remotion)
    ├── scripts/                   inspect_footage, contact_sheet, trim_voice, make_voiceover,
    │                              make_sfx, align_captions, pacing_checker,
    │                              footage_overlap_checker, plan_to_project, new_remotion_project
    ├── assets/
    │   ├── edit-plan-template.md  The plan format
    │   ├── sfx/                   CC0 sound effects, their sources, the event → sound table
    │   └── remotion-template/     Render project: theme, engine, components
    └── evals/                     Evaluation cases for the skill
```

## Testing

`./selftest.sh` runs eleven groups without spending ElevenLabs credits: tool availability, footage
inspection, pacing rules, caption alignment (spelling preserved), the ElevenLabs key (read-only),
plan compilation, footage-reuse detection, voice trimming, contact sheets, render-project scaffolding
(including the missing-asset report) and sound effects. `./selftest.sh --render [DIR]` adds a 12th group: typecheck the
template and render a still. Template changes are also checked by eye on stills at transition frames.

## Licensing and third-party terms

This repository is proprietary and unlicensed for redistribution. Third-party terms that affect use:

| Dependency | Terms |
|---|---|
| Remotion | Free for individuals and companies of up to 3 employees; otherwise $25/month per seat, and an AI agent writing Remotion code counts as a seat ([licence](https://www.remotion.dev/license)). |
| ElevenLabs | Free-plan audio cannot be used commercially, including after upgrading. |
| Google Fonts used by the template | SIL Open Font License. |
| Sound effects in `assets/sfx` | Five recordings under CC0 (sources in `assets/sfx/SOURCES.md`); the rest are synthesized by `make_sfx.py`. Add only CC0 or self-made sounds. |
| faster-whisper | MIT. |
| Music on TikTok Shop content | TikTok Commercial Music Library or an explicit commercial licence only. |

Design references: `remotion-dev/skills`, `iart-ai/tiktok-video-skills` (MIT),
`browser-use/video-use` (MIT), `heygen-com/hyperframes` (Apache-2.0). Rules were adapted; no code
was copied. Details in `docs/DECISIONS.md`.

## Known limitations

- TikTok does not publish UI safe-zone pixels; the template uses conservative third-party
  measurements. Confirm with a private test post.
- Renders from 1080×1920 proxies soften above ~1.15× zoom; use `--proxy-height 3840` for heavy
  punch-ins.
- Shader transitions (`crossZoom`) and light leaks need WebGL (`angle` renderer); verified on
  Windows, not yet on macOS/Linux.
- The skill's evaluation cases were updated for the current rules but have not been re-run.

## Contributing

- Keep the repository clean: no unused files or dead code, and no video content in the template.
- New visual style → `theme.ts`. New graphic → a component in `components/graphics/`, registered in
  `registry.tsx` and documented in `references/layout-and-motion-graphics.md`.
- Run `./selftest.sh` after changing the skill, and read `git status` before every commit; secrets
  and media are ignored but must never be forced in.
