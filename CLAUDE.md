# short-video-kit — instructions for Claude

The user works in **Vietnamese**: reply in Vietnamese. This repo is a toolkit for making short
TikTok Shop product videos (30–40 s): the Claude skill `skill/short-video-editing`, Python scripts
(footage inspection and contact sheets, voice trimming, ElevenLabs voiceover, Whisper-aligned captions,
plan checkers, plan → project compiler) and a data-driven Remotion render template.

**Everything a new machine needs is in this repo.** A chat, a Claude memory or an installed skill on
another computer is not shared: if a rule or a fix matters, it belongs here (this file, `docs/`, or the
skill), not in someone's head.

## First thing in every session

Run `./setup.sh --check` (changes nothing; lists what is installed and what is missing). On Windows run
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
5. **Run `./selftest.sh`** and report each PASS / FAIL / SKIP (a SKIP on group 5 is fine without a key).
6. Confirm `~/.claude/skills/short-video-editing/SKILL.md` exists and tell the user to start a **new**
   Claude Code session so the skill loads.

Machine-specific locations are overridable: `SVK_PYTHON` (the venv's python), `WHISPER_MODEL_DIR`
(folder holding `faster-whisper-small/`). If drive C: is small, put the venv, model and work folders on
another drive and set these two variables for the user.

## When the user asks for a video

Follow `docs/WORKFLOW.md` (Vietnamese) and the skill's `SKILL.md`. In short, for "make video KBn from
this script PDF, this clip folder and this voice":

1. `./setup.sh --check`, then read the script into one `script.txt` per video (a PDF: open it with the
   Read tool, `pages` up to 20 at a time, and copy the spoken lines; no PDF library is installed).
2. See the footage: `contact_sheet.py CLIPS_DIR --out overview.png`, `inspect_footage.py CLIPS_DIR --log`;
   build a shot log and **budget the batch** (every video gets its own source ranges).
3. Voice: supplied → `trim_voice.py` if over 45 s, transcribe, correct the script **by hand** to match
   what is said, `align_captions.py`. No supplied voice → ElevenLabs (after `--quota`).
4. Write `edit-plan.md` (Scenes + Overlays), cut **on pauses in the voice**, scenes 3–4 s.
5. `pacing_checker.py`, `footage_overlap_checker.py` (all plans together), `plan_to_project.py` (read the
   sync report), render, then `contact_sheet.py VIDEO --project …` and **look** at it.
6. Report in Vietnamese: runtime, scenes, hook, what the sync report still flags, claims in the supplied
   voice that need the human, and what was **not** verified (never say "listened" unless it was).

Keep work files **outside this repo** (e.g. `<work>/kb7/{script.txt,voice.mp3,captions.srt,words.json,
edit-plan.md}` and one render project `<work>/render`); only the toolkit lives here.

## Decisions that belong to the human — do not make them silently

- **ElevenLabs plan.** Free-plan audio is not licensed for commercial use, ever. Run `--quota` and say
  so before synthesizing anything meant to ship.
- **Remotion licence.** Free only for individuals or companies of up to 3 employees; $25/seat/month
  above that, and an AI writing Remotion code still counts as a seat.
- **Any download** (packages, models, binaries, stock media). Name it, its source and size; wait for yes.
- **Trimming a supplied voiceover** or dropping a claim: say exactly which sentences/claims.
- **Claims already inside a supplied voice** ("sạch tinh", "tiết kiệm tiền trăm tiền triệu", "Hết lại
  tiếc đó!"): flag them against `references/platform-specs.md`; keep the on-screen text clear of them.

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
- White text vanishes on white fabric: over white garments use the `outline` or `marker` title style, not
  `gradient` or `stack` (white→sky fills). Check every title on the contact sheet.
- Edit-plan tables are the footage ledger: keep every `edit-plan.md`, and pass them all (named, no
  shell glob) to `footage_overlap_checker.py`. A `project.json` cannot rebuild a lost plan.
- A render project is a **copy** of the template: after the template changes, run
  `new_remotion_project.py <render dir> --update` (replaces `src/` and config, keeps `public/`,
  `node_modules/` and your `*.json` projects).
- Don't sum `video_metrics_daily` in the campaign database; it repeats on a 7-day cycle.
- Windows PowerShell 5.1: `python -I` ignores `PYTHONIOENCODING`, use `python -X utf8`; the `python3`
  command may be the Microsoft Store stub (use the venv's `Scripts\python.exe`); a program installed by
  winget is not on PATH until a new terminal; `Get-Content` needs `-Encoding utf8` for Vietnamese files.
- Files sent to a phone or web viewer are limited to ~30 MB: make a compressed copy
  (`ffmpeg -i in.mp4 -c:v libx264 -crf 24 -c:a aac -b:a 128k -movflags +faststart out.mp4`).

## Read next

`README.md` → `docs/CAU-TRUC.md` (what every folder and file is) → `docs/WORKFLOW.md` → `docs/DECISIONS.md` →
`skill/short-video-editing/SKILL.md`. Adding, renaming or removing a file or script means updating
`docs/CAU-TRUC.md` and the structure tree in `README.md` in the same commit.

## Working in this repo

- **Never commit** `.env*`, `bin/`, `models/`, `dist/`, media files. `.gitignore` enforces it; still
  read `git status` before every commit.
- **The repo must stay private**: `docs/` and `niche-winning-patterns.md` hold real GMV figures and
  creator handles. Do not paste them into external services.
- **Keep it clean**: no dead code, no unused files, no video content hard-coded in the template (it
  belongs in the plan / `project.json`). New look → `theme.ts`; new graphic → a component plus a row
  in `references/layout-and-motion-graphics.md`.
- After changing anything under `skill/short-video-editing/`, run `./selftest.sh`; after changing the
  template, run `./selftest.sh --render <render project>` and look at stills.
- Never label a staged or designed graphic as a "real customer review".
