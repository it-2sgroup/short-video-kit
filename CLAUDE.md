# short-video-kit — instructions for Claude

The user works in **Vietnamese**: reply in Vietnamese. This repo is a toolkit for making short
TikTok Shop product videos (30–40 s): the Claude skill `skill/short-video-editing`, Python scripts
(footage inspection, ElevenLabs voiceover, Whisper-aligned captions, plan checkers, plan → project
compiler) and a data-driven Remotion render template.

## When the user says "setup", "cài đặt", or has just cloned this repo

Do these in order. Show real output; never summarise a failure as success.

1. **Run `./setup.sh`** (bash; on Windows use Git Bash) and read all of it. It builds a venv under
   `~/.local/share/short-video-kit`, fetches the Whisper model (~460 MB), installs the key file if
   present, and installs the skill into `~/.claude/skills/short-video-editing`.
2. **ffmpeg missing?** Let the user choose: `brew install ffmpeg` / `apt install ffmpeg` /
   `winget install Gyan.FFmpeg`, or `./setup.sh --download-ffmpeg` (Linux static build, ~40 MB).
   **Ask before any download.**
3. **No ElevenLabs key?** The user runs **`./setup.sh --set-key` themselves** (typed hidden).
   **Never** ask for the key in chat; never read, print, log, commit it or put it on a command line.
   It lives at `~/.config/short-video-kit/env` (mode 600). Verify with `make_voiceover.py --quota`.
4. **Rendering needs Node 20+.** `scripts/new_remotion_project.py <dir> --install` scaffolds a render
   project; `--install` downloads npm packages and Chromium, so ask first.
5. **Run `./selftest.sh`** and report each PASS / FAIL / SKIP (a SKIP on step 5 is fine without a key).
6. Confirm `~/.claude/skills/short-video-editing/SKILL.md` exists and tell the user to start a **new**
   Claude Code session so the skill loads.

## Decisions that belong to the human — do not make them silently

- **ElevenLabs plan.** Free-plan audio is not licensed for commercial use, ever. Run `--quota` and say
  so before synthesizing anything meant to ship.
- **Remotion licence.** Free only for individuals or companies of up to 3 employees; $25/seat/month
  above that, and an AI writing Remotion code still counts as a seat.
- **Any download** (packages, models, binaries, stock media). Name it, its source and size; wait for yes.
- **Trimming a supplied voiceover** or dropping a claim: say exactly which sentences/claims.

## Facts already learned the hard way — do not relearn them

- `eleven_multilingual_v2` does **not** support Vietnamese. Default is `eleven_turbo_v2_5`.
- Free ElevenLabs plans can only use `premade` voices (library voices return HTTP 402).
- `[emotion]` tags only work on `eleven_v3`; other models read them aloud. The scripts strip them.
- Whisper mishears Vietnamese ("túi xách" → "tui sách"): captions take **words from the script**,
  **timing from Whisper**. Supplied voice files often differ from the written script — transcribe,
  correct by hand, then align.
- Client rules (Phương, Nov 2026): scenes 3–4 s with soft transitions (1.5–2 s hard cuts felt jerky);
  no text in boxes on product demos; one batch of footage must feed many videos with no reused range.
- Shader transitions (`crossZoom`) and light leaks render on Windows with the `angle` GL renderer
  (set in the template's `remotion.config.ts`).
- iPhone footage is 4K HEVC with rotation metadata: render from ffmpeg proxies
  (`new_remotion_project.py --proxies`), not the originals.
- Don't sum `video_metrics_daily` in the campaign database; it repeats on a 7-day cycle.

## Read next

`README.md` → `docs/WORKFLOW.md` → `docs/DECISIONS.md` → `skill/short-video-editing/SKILL.md`.

## Working in this repo

- **Never commit** `.env*`, `bin/`, `models/`, `dist/`, media files. `.gitignore` enforces it; still
  read `git status` before every commit.
- **The repo must stay private**: `docs/` and `niche-winning-patterns.md` hold real GMV figures and
  creator handles. Do not paste them into external services.
- **Keep it clean**: no dead code, no unused files, no video content hard-coded in the template (it
  belongs in the plan / `project.json`). New look → `theme.ts`; new graphic → a component plus a row
  in `references/layout-and-motion-graphics.md`.
- After changing anything under `skill/short-video-editing/`, run `./selftest.sh`; after changing the
  template, run `npx tsc --noEmit` in a render project and look at stills.
- Never label a staged or designed graphic as a "real customer review".
