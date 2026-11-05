# short-video-kit — instructions for Claude

The user works in **Vietnamese**: reply in Vietnamese. This repo is a toolkit for editing short
TikTok Shop product videos (30–40s): a Claude skill plus scripts for footage inspection, ElevenLabs
voiceover, and Whisper-aligned captions. Render stack: ffmpeg (cut/join) + Remotion (graphics).

## When the user says "setup", "cài đặt", or has just cloned this repo on a new machine

Do these in order. Show the user real output; do not summarise a failure as success.

1. **Run `./setup.sh`** and read all of it. It builds a venv under `~/.local/share/short-video-kit`,
   fetches the Whisper model (~460 MB), installs the key file if present, and installs the skill into
   `~/.claude/skills/short-video-editing`.
2. **ffmpeg missing?** Tell the user and let them choose: `apt install ffmpeg` / `brew install ffmpeg`,
   or `./setup.sh --download-ffmpeg` (static build from johnvansickle.com, ~40 MB, checksum-verified).
   **Ask before using `--download-ffmpeg`** — do not add the flag on your own.
3. **No ElevenLabs key?** Ask the user to run **`./setup.sh --set-key` themselves** in a terminal (in
   Claude Code they can type `! ./setup.sh --set-key`). The key is typed hidden.
   - **Never** ask them to paste the key into this chat. **Never** read, print, echo, log or commit it,
     and never put it on a command line (it lands in shell history and process listings).
   - It is stored at `~/.config/short-video-kit/env`, mode 600. Verify without revealing it:
     `python3 skill/short-video-editing/scripts/make_voiceover.py --quota`
4. **Run `./selftest.sh`.** Report each PASS / FAIL / SKIP. A SKIP on step 5 is fine while there is no key.
5. Confirm `~/.claude/skills/short-video-editing/SKILL.md` exists, then tell the user to **start a new
   Claude Code session** so the skill loads.

## Decisions that belong to the human — do not make them silently

- **ElevenLabs plan.** Free plan audio is *not licensed for commercial use* and the account may be out
  of credits. Run `--quota` and tell the user before synthesizing anything meant to ship.
- **Remotion licence.** Free only for individuals or companies of up to 3 employees; $25/seat/month
  above that, and having an AI write the Remotion code still counts as a seat.
- **Any download** of a file or binary. Name it, its source and size, and wait for a yes.

## Facts already learned the hard way — do not relearn them

- `eleven_multilingual_v2` does **not** support Vietnamese. Default is `eleven_turbo_v2_5`.
- Free ElevenLabs plans can only use `premade` voices via the API (library voices return HTTP 402).
- `[emotion]` tags only work on `eleven_v3`; other models read them aloud. The scripts strip them.
- Whisper mishears Vietnamese ("túi xách" → "tui sách"). Captions take their **words from the script**
  and only the **timing** from Whisper — always pass `--script` to `align_captions.py`.
- Don't sum `video_metrics_daily` in the campaign database; it repeats on a 7-day cycle.
- **Remotion has not been built or tested in this kit yet.** The two videos rendered so far used HyperFrames.
- The skill was evaluated *before* the ingest/ElevenLabs/Whisper/Remotion changes; it has not been re-evaluated.

## Read next

`README.md` → `docs/WORKFLOW.md` → `docs/DECISIONS.md` → `skill/short-video-editing/SKILL.md`.

## Working in this repo

- **Never commit** `.env*`, `bin/`, `models/`, `*.mp4`, `*.tar.gz`. `.gitignore` enforces it; still run
  `git status` and read the file list before every commit.
- **The repo must stay private.** `docs/` and `skill/…/niche-winning-patterns.md` hold real campaign
  GMV figures and creator handles. Do not make it public or paste those files into external services.
- After changing anything under `skill/short-video-editing/`, re-run `./selftest.sh`.
- Don't label a staged or designed graphic as a "real customer review" in any video you plan or build.
