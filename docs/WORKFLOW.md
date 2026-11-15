# Workflow: from raw clips to a finished video, for any genre

Run the commands from `skill/short-video-editing/` (or `~/.claude/skills/short-video-editing/` after installing).
Claude runs these steps when you ask; this document is here so you can understand and double-check them.

**Before starting, on every machine:** `./setup.sh --check` (Windows: Git Bash's bash). If anything is missing, run
`./setup.sh`; after every `git pull` run `./setup.sh` again so the installed skill matches the repo.

**Python:** `python3` means any Python 3. On Windows use `python` or
`~/.local/share/short-video-kit/venv/Scripts/python.exe` (the `python3` command may be the Microsoft Store stub).

## The main idea: a playbook per genre

Everything that depends on the **kind of video** lives in one *playbook* (`playbooks/<id>.json` for machines +
`playbooks/<id>.md` for people/Claude to read): length, hook, scene length, cutting on the voice or on the music, the
structure of the beats, transitions, camera moves, caption style, colour palette, colour "look", sound effects, graphics to
use or avoid, the compliance list. The edit plan carries `**Playbook:** <id>` at the top; every script reads the rules from there.

| Playbook | Used for | Cut on |
|---|---|---|
| `product-demo` (`:unboxing`, `:listicle`) | TikTok Shop product reviews/demos, before/after | voice |
| `real-estate` (`:voiceover`) | tours of apartments, townhouses, villas, homestays, land | music |
| `food-fnb` (`:review`) | dishes, restaurants, drinks | music |
| `talking-head` (`:testimonial`, `:agency`) | experts, sharing, stories, customer impressions; `:agency` = a service-intro video cut from the presenter's takes | on-camera voice (jump cut) |
| `tutorial` | how-tos, recipes, step by step | voice |
| `fashion-beauty` | try-ons, lookbooks, makeup, skincare | music |
| `montage-recap` | travel, events, openings, behind the scenes | music |
| `promo-sale` | discounts, launches, announcements | music |

Keep the working folder **outside the repo**:

```
<work-folder>/
├── v1/  script.txt  captions.srt  words.json  edit-plan.md      (one folder per video; keep every edit-plan.md)
├── analysis.json  clips.png  library.json
└── render/                                                       (one Remotion project for the whole batch)
    ├── public/clips   corrected proxies + corrections.json
    ├── public/audio   cleaned voice, levelled music
    └── public/images  logo, floor plan, packshot (if any)
```

## Steps

### 1. Analyse the source and the intent → choose the playbook
```bash
python3 scripts/inspect_footage.py /path/to/clips --measure --json analysis.json   # brightness, colour cast, noise, shake, camera movement, speech present, HDR, fps
python3 scripts/contact_sheet.py /path/to/clips --out clips.png                     # OPEN IT AND LOOK
python3 scripts/playbook.py suggest --intent "your request in your own words" --analysis analysis.json
python3 scripts/playbook.py show real-estate
```
If the request and the footage agree, Claude says which playbook it chose and why (one line) and carries on. If they
disagree or facts are missing (price, area, address, promotion dates, voice or music only), Claude asks **at most 3
questions**, each with a default. For a batch of several videos: budget the footage first
(`references/footage-ingest.md` §1b, `references/policy.md` §4.1).

### 1b. The client supplies a sample video ("make it like this")
```bash
python3 scripts/analyze_reference.py sample.mp4 --out ref/ --dense 0-3,15-20   # measures: scene count, transitions, flashes, colour, noise + summary images
```
Open `ref/report.md`, `scenes.png`, every `dense_*.png` (one image every 2 frames within the range: a flash on frames 0, 2, 4,
a pile of text being assembled) and `spectrum_*.png` (a click is a vertical line, a whoosh is a diagonal band), then **look**.
The numbers give the timing to the exact frame; the images tell you which technique it is. List every technique you can see,
find it in `references/capcut-techniques.md` and `references/layout-and-motion-graphics.md`; a technique the kit does not have
yet is **researched and added as a component** (with a documentation row and a selftest), not imitated. A presenter speaking
to camera to introduce a service → `references/agency-pitch-recipe.md` (10 steps).
The logo and the product the client puts on a card belong to the client: ask for the vector file and for consent. Do not use the sample video's music or footage.

### 2. Prepare the footage (correction + colour)
```bash
python3 scripts/new_remotion_project.py ~/renders/batch1 --playbook real-estate --proxies /path/to/clips   # --install the first time (ask first: ~300 MB)
python3 scripts/contact_sheet.py ~/renders/batch1/public/clips --out proxies.png
```
`prepare_footage.py` (called by `--proxies`) automatically: converts iPhone HDR to SDR, crops the 9:16 frame, denoises when the scene is
dark and noisy, stabilises when shaky, balances white (measured on neutral pixels), adjusts exposure, applies the playbook's colour
"look" (baked into one 3D LUT). A before/after video (`correction: shared`) uses the **same** correction for every clip.
To straighten the horizon: `--fix "CLIP_A:rotate=-1.2"`. For 0.5x slow motion add `--slowmo` (keeps 60 fps).
Read `corrections.json` to see what was done to which clip.

### 3. Sound
**A supplied voice:**
```bash
python3 scripts/trim_voice.py voice.mp3 --silences                                   # too long for the playbook: list the pauses
python3 scripts/trim_voice.py voice.mp3 --keep 0-3.8,8.3-16.1 --out voice_short.mp3   # drop whole sentences, say exactly which
python3 scripts/process_audio.py voice voice_short.mp3 --out ~/renders/batch1/public/audio/v1.wav   # denoise (if needed), EQ, de-ess, compress, −16 LUFS
python3 scripts/align_captions.py ~/renders/batch1/public/audio/v1.wav --out draft.srt # draft transcript → correct by hand → script.txt
python3 scripts/align_captions.py ~/renders/batch1/public/audio/v1.wav --script script.txt --out captions.srt --words-out words.json
```
**A presenter speaking to camera (talking head):**
```bash
python3 scripts/trim_voice.py talk.mp4 --jumpcut --out talk_cut.wav --scenes-out cuts.json   # drop every pause > 0.35 s; each segment kept is one scene
python3 scripts/process_audio.py voice talk_cut.wav --out ~/renders/batch1/public/audio/v1.wav
```
**A voice synthesized with ElevenLabs:** check the claims first, then `make_voiceover.py --quota` → `--dry-run` → synthesize →
`process_audio.py voice … --no-clean`.
**Music** (commercially licensed for the platform): `process_audio.py music track.mp3 --out ~/renders/batch1/public/audio/music.wav`.

### 4. Cut the scenes and make the plan
```bash
python3 scripts/suggest_cuts.py words.json --playbook product-demo --json > cuts.json                        # cut on the voice's pauses
python3 scripts/suggest_cuts.py --music ~/renders/batch1/public/audio/music.wav --end 40 --playbook real-estate --json > cuts.json   # cut on the beats
python3 scripts/playbook.py skeleton real-estate --cuts cuts.json --title "Villa Thảo Điền" > v1/edit-plan.md
python3 scripts/plan_scenes.py --library library.json --plan v1/edit-plan.md --kinds "VIEW,ROOM,EXTERIOR,..." --used v0/edit-plan.md
```
The skeleton comes with Type, Transition, Speed, a hint for each beat and the compliance list filled in. Complete the **Scenes** table
(Source/In, Camera or leave empty for `--auto-camera`, Speed: `2x` for waiting passages, `ramp 1>2>1` through a door,
`0.5x` for the "money shot" at 60 fps) and the **Overlays** table (text and graphics: `title`, `specs`, `pin`, `label`,
`stat`, `chart`, `price`, `step`, `checklist`, `thumbs`, `compare`, `image`, `cart`…; anchored to a word with
`@"phrase"`). The on-screen text says something **different** from the spoken line; every number comes from the user/the documents.

### 5. Check the plan
```bash
python3 scripts/pacing_checker.py v1/edit-plan.md                          # the playbook's rules, as recorded in the plan
python3 scripts/footage_overlap_checker.py v1/edit-plan.md v0/edit-plan.md --clips /path/to/clips
```

### 6. Compile and render
```bash
python3 scripts/plan_to_project.py v1/edit-plan.md --out ~/renders/batch1/v1.json --voice audio/v1.wav --music audio/music.wav \
    --captions captions.srt --words words.json --auto-camera --analysis analysis.json --auto-sfx [--platform reels-ad]
cd ~/renders/batch1
node stills.mjs v1.json out/s --cuts                                  # bundle once: a still after every cut and in the middle of every scene (or --every 0.5 --from 0 --to 8, or list the seconds)
python3 scripts/montage.py "out/s_*.jpg" --cols 6 --out out/sheet.jpg  # LOOK at every transition, text effect and card on one image
npx remotion render src/index.ts Short out/v1.mp4 --props=v1.json --codec=h264 --crf=18 --concurrency=5
```
`--concurrency=5`: 8 workers report "No frame found at position" with 2880-tall proxies. Read the "wrote …" line after every compile: an argument
rejected by argparse (`--music-levels -6,-6` must be written with `=`) can leave the old project in place, and the video renders without music.
Read the **sync report**: cuts in the middle of a word, text appearing/disappearing right at a cut, graphics overlapping the UI zones (TikTok, Reels ads),
components the playbook advises against, slow motion that will stutter, files missing from `public/`.

### 6b. (Optional) Render with HyperFrames instead of Remotion
The same `project.json`, a second renderer (Apache-2.0, no per-seat fee as with Remotion). Choose per video and say why:
HyperFrames suits a studio above Remotion's 3-employee limit, or a wish for CapCut-style effects (`+shake`, `+glitch`,
`+rgb`, `+pulse` in the Transition cell; `--look vignette,grain`). It does **not** draw `magnifier`, `thumbs`, `compare`, `ranking`: a video
that needs the before/after card uses Remotion.
```bash
python3 scripts/new_remotion_project.py ~/renders/batch1 --playbook <id> --proxies /path/to/clips     # NO --install: only the proxies + SFX
python3 scripts/plan_to_project.py … --out ~/renders/batch1/v1.json …                                    # as in step 6
python3 scripts/project_to_hyperframes.py ~/renders/batch1/v1.json --out ~/hf/v1 --playbook <id> [--look vignette=0.3,grain=0.05]
cd ~/hf/v1
npx hyperframes@0.9.26 check                       # ask the user before the first npx (it downloads a package); needs Node 22+, Chrome
npx hyperframes@0.9.26 snapshot --at 0.5,4,9,28    # LOOK at the contact image
npx hyperframes@0.9.26 render --quality high --output final.mp4
```
`check` must give 0 errors; a `line_unread` warning on captions for fast speech is normal. Measured: a 28.5 s video renders in ~55 s,
with loudness −16.3 LUFS and a duration identical to Remotion's, and the picture looks the same side by side. Continue with step 7 using `final.mp4`.
Details, pitfalls, extensions: `references/hyperframes-flow.md`; catalogue of CapCut techniques: `references/capcut-techniques.md`.

### 7. Audio master and export
```bash
python3 scripts/process_audio.py master out/v1.mp4 --out out/v1_final.mp4 --phone    # −14 LUFS, peak ≤ −1 dBTP + a light copy to send to a phone
python3 scripts/finish_video.py out/v1.mp4 --name NAME_v1 --out-dir out/final --audio-nomusic nomusic.wav --cover-at 3 --preview720   # agency flow
```
Remotion exports the full colour range (`yuvj420p`): `finish_video.py` converts it back to limited BT.709. A TikTok business account cannot "bake" copyrighted music
into a video: deliver an extra **music-free** version so the user can attach a track from the Commercial Music Library when posting (`make_music.py` writes a self-made music bed).
One clean master serves every platform; do **not** download a video from TikTok and re-post it on Reels (it carries a watermark).

### 8. Final check and report
```bash
python3 scripts/contact_sheet.py out/v1_final.mp4 --project ~/renders/batch1/v1.json --out out/sheet.png
python3 scripts/mix_report.py out/v1_final.mp4 --project ~/renders/batch1/v1.json --words words.json [--nomusic out/v1_nomusic.mp4]   # measures: colour range, duration, LUFS, peak, whether the music is really in the file
python3 scripts/check_lipsync.py ~/renders/batch1/v1.json out/v1_final.mp4 --clips /path/to/source-clips   # voice cut from the takes: every scene off by ≤ 1 frame
```
**Really look**: the subject is not covered, the text is readable (white text on white fabric), nothing overlaps the UI zones, before/after
is honest. Listen to the whole video. Report: the playbook and why, the duration, the number of scenes, the hook, the corrections applied to the footage,
what the sync report still flags, the claims fixed/flagged, the publishing checklist (`references/platforms.md` §6), and what was **not**
checked (for example, the whole video was not listened to).

## General rules (SKILL.md)

1. Analyse the footage + the intent before planning; say which playbook was chosen and why.
2. The hook is done within the first 3 seconds; the first frame is not empty.
3. Pacing as the playbook says (scene length, total duration): `pacing_checker.py` checks it.
4. Every plan has a timestamp for each scene.
5. Check the claims against the playbook and `references/claims-and-compliance.md` before speaking/writing.
6. Footage is your own or licensed; no range is reused within a batch; never reshuffle one source into several videos.
7. Graphics respect the frame and the platform's safe zones.
8. Never hide the cut between before and after; the same colour for before and after; say clearly when the footage is sped up.
9. Say clearly what was not checked.
