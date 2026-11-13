# Agency pitch recipe (`talking-head:agency`): from raw takes to a finished video, step by step (steps 0-10)

A service pitch told to camera, edited the way hand-made social openers are: the speaker's own takes cut on the voice, loud text blocks that say what the speaker says,
portfolio cards over a wind-blown grid, a brand mark that lands on its name, sound design that changes with the picture. The numbers below were measured on a real run of
this recipe (a few dozen takes of one speaker, a voice of about a minute cut from them, checked against a hand-made reference edit).

## 0. Is this the right recipe?
- The speaker talks to camera and the voice is (or can be) the take's own sound. If the voice is a fresh recording over B-roll, use `food-fnb`/`product-demo`.
- If there is B-roll of the brand's work, use it on the cards instead of cutaways (step 5 shrinks). If there is none, the pitch cannot show work: say so.
- Ask only what the files cannot answer: the brand name as spoken, the logo file (a vector or PNG; keying it out of a video frame is a last resort), the call to
  action, the figures the voice states (they are the brand's claims), whether customer work shown on screen has consent, the platform and account type (music).

## 1. Prepare the machine
`doctor.py`; a render project (`new_remotion_project.py DIR --playbook talking-head:agency`: theme `crimson`; link an existing `node_modules` or ask before `--install`);
for the opening flash and the beauty light the person-segmentation model `u2net_human_seg.onnx` (168 MB, outside the repo, **ask before downloading**, then `./setup.sh --person-model`;
`person_matte.py` finds it in `$SVK_MODEL_DIR`, `$WHISPER_MODEL_DIR` or `~/.cache/short-video-kit/models`). On Windows a second drive for the venv, model and work folders
(`SVK_PYTHON`, `WHISPER_MODEL_DIR`) keeps a 4K batch off a small C:.

## 2. Read the sample and the footage
**The sample** (if a reference edit was given): `analyze_reference.py sample.mp4 --out ref/ --dense 0-3,15-20` and **look** at `scenes.png`, every `dense_*.png` and `spectrum_*.png`. What a
reference of this kind gave: about 30 shots (median 1.3 s), a white silhouette on frames 0, 2, 4 at 30 fps (shots of 0.03 s), cards over a coloured grid from the middle of the video, transitions of 5-12 frames, -14 LUFS.
List every technique before building anything; each one is a kit component or a gap to close (`capcut-techniques.md`).
Choose the `--dense` ranges from `report.md`: the first 3 s (the opening), and every motion run it lists (start, frames) with half a second of margin, then run it again on those ranges.
**The footage**: `inspect_footage.py DIR --measure --json analysis.json`, `contact_sheet.py DIR --out sheet.png` and look; `prepare_footage.py DIR <work>/render/public/clips --playbook talking-head:agency
--analysis analysis.json` (proxies are made without sound; keep the render project OUTSIDE the clips folder: `prepare_footage.py` reads every video below its input, so a re-run would take the proxies for sources;
`new_remotion_project.py RENDER --proxies DIR` does the same in one go. If `node_modules` exists elsewhere, link it: Windows `mklink /J RENDER\node_modules <existing>`, macOS/Linux `ln -s`). Transcribe every take with the brand and domain words (`align_captions.py take.mp4 --prompt "BRAND, domain words"`) and correct by
hand (Whisper `small` mishears Vietnamese business talk): the takes that repeat a line are the cutaway pool, not extra A-roll.

## 3. Match the voice to the takes (the lips)
`match_voice_takes.py voice.mp3 DIR --out matches.json` prints `clip time = voice time + lag` per take. Each talking scene uses that take with `In = start + lag`. A second lag inside one
take is a splice: cut there. Stretches no take covers are the card sections. Verify at the end with `check_lipsync.py` (all scenes within one frame).

## 4. Script and word timings
Transcribe the voice with `align_captions.py voice.mp3 --prompt "BRAND, domain words" --out draft.srt`, correct it by hand into `script.txt` (one sentence per line, numbers as digits; a sentence you
could not hear well is flagged to the user, not guessed), then `align_captions.py voice.wav --script script.txt --out captions.srt --words-out words.json --words 6`.
Order: first `process_audio.py voice voice_raw.mp3 --out RENDER/public/audio/voice.wav --denoise off` (the processed voice is what the video plays, and the plan says `--voice audio/voice.wav`),
then transcribe and align on THAT file, so the timings are the ones heard. `--denoise off` when the splices are already clean (`mix_report.py voice.wav --words words.json` prints the level in the pauses:
pauses near -50 dBFS need no gate); check the first 2 seconds. Flag every claim in the voice (customers served, delivery days, volumes, "this month only").

## 5. Pictures for the stretches no take holds
`find_cutaways.py DIR --avoid matches.json --min 0.8 --margin 0.1 --pre-roll --json cutaways.json` lists silent stretches (pre-roll, walk-offs, empty establishing shots). **Look at each range**
on a contact sheet: the lips must be closed or it must be a place; reject blinks, mid-word frames and a hand over the lens. Never use another take of the same line.

## 6. The plan, first draft
`agency_plan.py --words words.json --matches matches.json --cutaways cutaways.json --brand NAME --flash CLIP --voice-stem VOICE [--cta "INBOX NGAY" --cta-word inbox] --out edit-plan.md`
writes the mechanical half: talking scenes cut on pauses (`In = start + lag`), cards, transitions, cameras, a block per spoken clause, the logo on the brand word (a phrase that would share the
top strip drops to y 0.285; a counter that collides with a logo is left out and reported), caption bands, a closing card with the logo and the call to action. It also writes `edit-plan.face-keys.txt`: the
CLIP@seconds list the next step measures. `--voice-stem` is the voice file's name without extension when it sits in the clips folder (it matches itself and is skipped).

## 7. Opening and light, then the plan again
- Silhouette flash: scene 1's source is in the plan. `person_matte.py RENDER/public/clips/CLIP.mp4 --at <scene 1 In> --frames 0,2,4 --out RENDER/public/mattes/CLIP` (use the 9:16 proxy, not the original: the
  matte is squashed to a square model input and stretched back, so the frame must be the one that will be shown); the plan's `Subject` cell (`references/subject-effects.md`) `0,2,4 @ mattes/CLIP` is already there from `--flash CLIP`. White frames 0, 2, 4, then the video: measured on the sample.
- Beauty light: `person_matte.py --faces "$(cat edit-plan.face-keys.txt)" --clips RENDER/public/clips --faces-out faces.json` (the keys are `CLIP@seconds` with one decimal: three per talking scene), then
  run `agency_plan.py` again with `--faces faces.json`: each scene gets a `Face` cell (x, y, r of the head) and the camera's `focus` follows it. Build with `--face-glow 1.26,0.88,1.0,1.15,0,0.07`
  (brightness, saturation, blur, size, warm, veil; matched against a hand-made reference edit).
- Global look: `--look 1.10,1.05,1.04,0.06` (saturate, contrast, brightness, warm).
- Then edit the plan by hand (re-running `agency_plan.py` overwrites it, so do this last): choose which words become the loud line (the draft takes the last ~28 characters, at most 5 words, of each clause; a clause
  that is only a connective gets none), spend each effect once or twice (`layout-and-motion-graphics.md`, "Text effects"), put the tags (`SẢN PHẨM`, `DỊCH VỤ`...) on the right cards (`at=0.5,0.235`, over the
  card's top edge: the card is 690 x 1227 with its top at y 360), add the counter, the circled promise, the RAW | FINAL pair (`raw` = the same take, ungraded: a plain re-encode of the original,
  `ffmpeg -i ORIGINAL_TAKE -vf scale=1620:2880 -an -c:v libx264 -crf 23 -r 30 RENDER/public/raw/CLIP.mp4`, beside `final=clips/CLIP.mp4`), the script phrase. Rules that held: one block at a time;
  cuts on word boundaries (the sync report lists any inside a word); text never starts or ends within 3 frames of a cut; `pacing_checker.py` and `footage_overlap_checker.py --gap 0`
  (jump cuts inside one take touch by design) pass.

## 8. Sound
- Music: a licensed track the human adds at upload (a business TikTok account: the Commercial Music Library), or a self-made bed:
  `make_music.py --duration <video seconds> --sections "0:0.55,6.4:1.0,14.7:0.9,19.7:0.5,..." --hits "6.4,45.9,62.4" --bpm 120 --out music.wav`. Sections are TIME:INTENSITY on the plan's section starts
  (talking sections 0.45-0.6, the first card section after the hook 0.9-1.0, a calm proof section 0.45-0.5, the offer and call to action 0.9-1.0, 0 after the last hit for silence under the closing card);
  an impact (`--hits`) goes on the biggest changes only (the brand's entrance, the offer, the end). Then `process_audio.py music music.wav --out RENDER/public/audio/music.wav`.
  `--music-levels=VOLUME,DUCK` (the `=` is needed for negatives): the bed's level in the pauses, then the extra dip under speech. The default `-10,-8` was too quiet for a loud, fast voice: `-6,-6` (bed -6 dB in the pauses, -12 dB under speech) held up. Check `mix_report.py ... --nomusic` (it prints how far the bed sits above the voice-only pauses), and say the music was not listened to.
- Effects: `--auto-sfx`; the bank (`assets/sfx`, `references/sound-design.md`) holds 63 recorded CC0 files (5 core and 58 added for variety) and the 17 sounds `make_sfx.py` synthesizes into every render project;
  events rotate through alternatives so no sound repeats in a row, a text effect has its own (slam, stamp, glitch, boing...), the silhouette flash is a camera click, a burst of copies pops.
  `rules` of the variant allow 5 sounds per 3 s.

## 9. Build, look, render
(`--caption-keywords`: the brand and the two or three nouns the speaker repeats, always marked in the captions.)
`plan_to_project.py edit-plan.md --out RENDER/project.json --voice audio/voice.wav --captions captions.srt --words words.json --analysis analysis.json --look ... --face-glow ... --caption-highlight box
--caption-keywords "BRAND,word2,word3" --music audio/music.wav --music-levels=-6,-6 --auto-sfx`. Read the sync report. Render stills at every transition and every effect with one bundle
(`node stills.mjs project.json out/s --cuts`, or `--every 0.25 --from 15.8 --to 17` for a transition; ~8 s a still; the script is in the render project) and tile them
(`python scripts/montage.py "out/s_*.jpg" --cols 6 --out out/sheet.jpg`), then **look**. Put a sample frame beside yours at the same second:
`montage.py sample_12.5.png mine_12.5.png --cols 2 --labels "sample,mine" --out cmp.png`. Full render: `npx remotion render src/index.ts Short out/video.mp4 --props=project.json --codec=h264 --crf=18 --concurrency=5`
(8 workers fail with `No frame found at position` on 2880-tall proxies; ~20 min for 64 s).

## 10. Finish and check
`npx remotion render ... out/audio_nomusic.wav --codec=wav` from a copy of the project with `"music": null` (4 min), then `finish_video.py out/video.mp4 --name NAME --out-dir out/final --audio-nomusic
out/audio_nomusic.wav --cover-at 3.9 --preview720`. It writes `out/final/NAME_music.mp4`, `NAME_nomusic.mp4` (+ `_phone` copies), `NAME_cover.jpg` and the 720p previews; the cover frame is one where the
logo or the loud block is fully formed and the face has open eyes (read it off the contact sheet; ~3-4 s here). Then the proof:
`check_lipsync.py project.json out/final/NAME_music.mp4 --clips ORIGINALS` (clips = the original takes: proxies have no sound; it exits 1 when nothing could be checked) and
`mix_report.py out/final/NAME_music.mp4 --project project.json --words words.json --nomusic out/final/NAME_nomusic.mp4` (limited range, -15..-13 LUFS, true peak, music really present, cue count).
Look at a contact sheet and frames 0-5 (the flash). Report in the user's language: runtime, what was measured (LUFS, TP, lip-sync), claims and consents that need the human,
what nobody has listened to or watched in full (sounds chosen by name and measurement; the music; a sentence guessed from a poor transcript; the logo keyed from a sample frame).
This recipe is Remotion only: `project_to_hyperframes.py` lists what HyperFrames does not draw (cards, flash, face light, the agency components) and tells you to use Remotion.

## Logo from a frame (last resort: ask for the vector or a transparent PNG first)
A saturated red mark on a LIGHT background can be keyed out of a frame of the sample: crop the logo, then alpha = (R - G + 55) / 260 with ffmpeg `geq`, enlarged 4x with Lanczos:
`ffmpeg -ss T -i sample.mp4 -frames:v 1 -vf crop=W:H:X:Y crop.png`, then
`ffmpeg -i crop.png -vf "scale=iw*4:ih*4:flags=lanczos,format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='clip(255*(r(X,Y)-g(X,Y)+55)/260,0,255)'" render/public/images/logo.png`.
Put the result on a grey and on a white backdrop and look. On a DARK red frame (the card background) the same formula leaves a dark veil around the mark, so use a frame where
the logo sits on sky or white. A logo made this way is an approximation of the brand's mark: say so in the report.

## Pitfalls met
- A negative number after `--music-levels` must be `--music-levels=-6,-6`; the failed build silently kept the old project (read the "wrote ..." line every time).
- A decorative ring around a stamped line crossed the speaker's face: effects must stay inside their text box.
- Counters and karaoke captions fight for the same strip: hide the captions while the counter shows.
- A circular import between two component files broke the first build: shared pieces live in `Fx.tsx` and `Glyph.tsx`.
- Light from a backdrop filter needs a mask feather of ~45% or it draws a visible ellipse.
