# Standard prompt: edit a short video with the `short-video-editing` skill (any genre)

This prompt is **not tied to one genre or one fixed workflow**. Everything that depends on the kind of video (length, pacing,
cutting on the voice or on the music, structure, colour, text, sound, graphics, compliance) lives in the kit's **playbooks**
(`product-demo`, `real-estate`, `food-fnb`, `talking-head`, `tutorial`, `fashion-beauty`, `montage-recap`,
`promo-sale` and the variants `:unboxing :listicle :voiceover :review :testimonial`). The prompt only states **intent,
constraints, the technique catalogue and the acceptance standard**; Claude takes the concrete numbers from the playbook
(`playbook.py show <id>`), the prompt does not hard-code them.

**Language:** you may write this prompt, and talk to Claude, in any language; Claude answers in the language you write in
(the user normally writes Vietnamese). The caption and voice-over language is a separate decision: say which one the video uses.

How to use it: copy the **PROMPT** block (sections 1-6), fill in the `[...]` fields, delete the lines you do not need. Any field
you leave empty gets the playbook default, or Claude asks (at most 3 questions, each with a default answer). Section 7 is a
short version with examples for a few genres. Open a **new chat** after installing or updating the skill (`./setup.sh`) so that
the skill loads.

---

## PROMPT

Use the skill `short-video-editing`. Answer in the language I write in. Edit **[number] vertical 9:16 video(s)** for me,
**[desired length, or "per the playbook"]**, to be posted on **[TikTok / TikTok Shop / Reels / Shorts]**
(**[organic / paid ads]**). Finish level: **[demo version for the client / real version to post]**, with picture,
colour, light, pacing, text and sound all polished.

### 1. Brief (fill in what you already know)

- **Subject / audience:** `[product, house, restaurant, dish, speaker, event...]`, named exactly as on the packaging,
  the menu, the documents: `[..]`.
- **Genre:** `[the playbook name if you know it, or "let Claude propose"]`. If left empty: run
  `playbook.py suggest` with the footage and this request, say which one was chosen and why; if the request and the footage
  disagree, ask, do not force the footage into a genre it cannot carry.
- **Goal / CTA:** `[sell through the cart · book a viewing · visit the shop · gain followers · save the post · brand awareness...]`.
- **Raw footage:** `[folder]` (camera/phone, possibly 4K, HEVC, 10-bit, HDR, 60 fps).
- **Voice:** `[file already exists: path · generate a voice (ElevenLabs) · speaker on camera · music only]`.
- **Music:** `[file already exists with a licence · ask Claude to find one (ask me before downloading) · no music]`.
- **Style reference video:** `[path or "none"]`: if there is one, analyse it first (pacing, transitions,
  camera, colour, text, music, opening and closing shots, and which parts of the footage it already used).
- **Facts that must appear on screen** (only from me or from documents, never invented, never rounded): price, floor
  area (clear internal area or wall-to-wall), address, opening hours, promotion deadline, discount code, the
  speaker's name and title... `[..]`. If there are none, none are shown.
- **The client's own style requests** (they take priority over the playbook default, and are written into the plan):
  `[for example: keep the tilting-pan opening shot · scenes 3-4 s long with soft transitions · no text in boxes · no
  transition sounds · text colour matching the video · logo at the end]`.
- **Batch of several videos:** `[number of videos; which scenes may be shared between videos (for example the opening and the closing
  shot); videos already made]`.

### 2. Invariant rules (breaking one is a failure; where a tool exists, the tool checks it)

1. **Analyse before planning:** look at the contact sheet with your own eyes and measure the footage (`inspect_footage.py
   --measure`); know my goal; choose the playbook from both.
2. **The hook is done within the first 3 seconds**, and the first frame is not empty. Picture, text and sound each do a different
   job (`references/hook-library.md`).
3. **Pacing per the playbook** (scene length, total duration, number of hook beats): `pacing_checker.py` must PASS. If I ask
   for a length outside the playbook's range, state that range and the reason, then let me decide.
4. **Every plan has a timestamp for each scene**, following `assets/edit-plan-template.md`, and carries a `**Playbook:**` line.
5. **Check the claims** (on-screen text, spoken lines, captions) against the playbook's checklist and
   `references/claims-and-compliance.md`. A claim already inside the voice I hand over is **flagged, not kept
   silently**; the on-screen text does not repeat that claim.
6. **Footage that is mine or has a commercial licence. No video from other people. No source range used
   twice across the whole batch**, no reshuffling of one source into many videos (`footage_overlap_checker.py` over **all**
   plans, including plans rebuilt from a reference video). When the scenes run out, stop, report the numbers and propose shooting more.
   Read `references/policy.md` before planning a batch.
7. **Graphics respect the frame:** do not cover faces, do not sit on platform UI areas, titles in the top band
   (y ≈ 236-420), captions in the lower third (y ≈ 1340, ≤ 2 lines), the middle belongs to the footage, at most two
   information elements at the same time. Reels ads use `--platform reels-ad`; there is no cart arrow on Reels.
8. **Do not fake a proof:** do not hide the cut between BEFORE and AFTER, give both the same colour correction,
   say on screen when time has been compressed. Paid ads carry no before/after comparison.
9. **State plainly what was not verified.** A tool cannot hear: do not write "listened" if nobody listened.
10. **Things to ask me about, not decide yourself:** every download (npm packages, models, **music**, stock, binaries: give the name,
    source, licence, size), the ElevenLabs plan (the free plan is not for commercial use), the Remotion licence
    (free up to 3 employees) versus HyperFrames, third-party footage, the number of videos when the footage is not enough, cutting an existing
    voice or dropping a claim (say exactly which sentence), the genre when the request and the footage disagree, whether ads will run.
11. **No commit and no push** until I say so. Work files live **outside the repo**
    (`<work>/<video>/{script.txt,edit-plan.md,captions.srt,words.json}`, `analysis.json`, one `render/` for the whole batch).

### 3. Workflow (in this order; give real results, a failure is not called a success)

Run the scripts in `~/.claude/skills/short-video-editing/scripts`. Windows: `python -X utf8`, put paths with spaces
in double quotes, run one heavy ffmpeg job at a time.

0. **Is the machine ready:** `doctor.py` (ask before installing anything that is missing). After a `git pull`, run `./setup.sh` again.
1. **Analyse and choose the playbook:** `contact_sheet.py` (open and look), `inspect_footage.py --measure --json
   analysis.json`, `playbook.py suggest/show`, read `playbooks/<id>.md`. State the choice in one line.
2. **Choose the scenes:** build a table of scenes by type (see "Shots the footage needs" in the playbook). Look at the
   first, middle and last frame of **each** range before putting it in the plan. Reject scenes that are pitch dark, shaky, with an
   obstruction in the frame, a face looking straight into the lens without permission, or two scenes that look alike. For a batch: work out the
   footage budget first (`footage-ingest.md` §1b), use `plan_scenes.py` with `--used` and `--reserve`.
3. **Prepare the picture:** `new_remotion_project.py RENDER --playbook <id> --proxies CLIPS` (or `prepare_footage.py`
   with `--analysis`): HDR tone-mapping, conversion to 9:16, denoise when dark or noisy, stabilise when shaky, white balance
   from neutral pixels, exposure correction, the playbook's grade merged into one LUT; `--fix "CLIP:rotate=-1.5"`,
   `--slowmo` when 0.5x slow motion is needed. Read `corrections.json` and look at the proxy contact sheet: dark scenes must be
   brightened, the picture must not take on a strange cast; if no clip was corrected although some look dark, suspect the measurement and check by eye.
4. **Sound:**
   - *Existing voice:* `process_audio.py measure`, `trim_voice.py --silences`/`--keep` if it is longer than the playbook's range
     (drop whole sentences, report which ones), `process_audio.py voice`. **Check the measured first 2 seconds and the pauses:**
     if hiss, crackle or breath sounds remain (the normalisation step can amplify them), block the parts without speech with an
     energy threshold and a soft 25-30 ms gate, take the speech start from the real audio and not from Whisper, keep the original file.
   - *Speaker on camera:* `trim_voice.py --jumpcut --scenes-out`, then `process_audio.py voice`.
   - *Generated voice:* check the claims, `make_voiceover.py --quota`, `--dry-run`, generate (`eleven_turbo_v2_5` for
     Vietnamese), `process_audio.py voice --no-clean`.
   - *Captions:* `align_captions.py` without `--script` gives a draft, **correct it by hand** to match the speech, run it again with
     `--script --words-out`. Whisper gives the timing, the script gives the words.
   - *Music:* only CC0, self-made or licensed for the platform and the account type (the commercial music library lives inside
     the TikTok/Meta app and a render cannot fetch it; read each track's licence, record the source in `SOURCES.md`). Ask me before
     downloading. `process_audio.py music`; the bpm range and mood come from the playbook.
5. **Cut:** per the playbook's `drive`: voice (`suggest_cuts.py words.json`, cut at pauses, never in the middle of a word),
   music (`suggest_cuts.py --music --beats-out`, cut on the beat, prefer the start of a bar), or both (cut on the voice, nudge
   onto the beat within 4 frames). For music with a quiet part and then a high-energy part: detect the "drop" moment by energy, choose the music
   segment so that the drop coincides with a deliberate cut (a hero scene or a change of pace). Short fade-in, 2-3 s fade-out.
   Do not cut across a before/after proof scene.
6. **Plan:** `playbook.py skeleton <id> --cuts cuts.json --title "…"` then fill in Source/In, Transition, Camera,
   Speed, Overlays (`plan_scenes.py` helps). `pacing_checker.py` PASS; `footage_overlap_checker.py` with all plans.
   A shared exception (opening shot, closing shot) applies only when I wrote it down in section 1; still take different ranges and report it.
7. **Compile:** `plan_to_project.py … --voice --music --captions --words --auto-camera --analysis` (add
   `--auto-sfx` **only if** the playbook/client wants transition sounds; add `--caption-style`, `--punch-keywords`,
   `--platform reels-ad` when needed). Read the **sync report** and fix every warning (a cut inside a word, text too close to a cut, UI zones,
   overlapping graphics, an element the playbook avoids, jerky slow motion, missing files). Set the music level in `project.json`
   according to whether there is a voice (section 4 below).
8. **Render:** `npx remotion still` for a few key frames (hook, change of pace, every title, the end card) and **look** at them before
   rendering in full (`--codec=h264 --crf=18`). Choose Remotion or HyperFrames per video and give the reason
   (`hyperframes-flow.md` §1: HyperFrames does not draw `magnifier`, `thumbs`, `compare`, `ranking`; it has `+shake +glitch
   +rgb +pulse`, `--look`). Ask before the first `npx hyperframes`.
9. **Master:** `process_audio.py master … --phone` (−14 LUFS, peak ≤ −1 dBTP, AAC, `+faststart`; the phone copy
   under ~30 MB). Measure the level of each part: opening, drop, pauses, ending.
10. **Final check:** `contact_sheet.py … --project …` and look at every scene; `ffprobe` duration matches the plan; compare against
    section 5 below.

### 4. Technique catalogue (choose by genre and footage; do not use them all, do not use extras)

| Group | Techniques available in the kit (source) | Use when |
|---|---|---|
| **Hook** | 3 channels doing different jobs; prefer social proof, a product/place reveal, a visible transformation; avoid an authority opening and a bare command (`hook-library.md`) | always |
| **Scene choice** | per-clip contact sheet, a shot log by type (BEFORE/AFTER/POUR/HERO/...), a footage budget for a batch | always |
| **Picture** | HDR tone-mapping, neutral-pixel white balance, gamma exposure, conditional denoise, vid.stab stabilisation, lens distortion fix and straightening, grades `natural / bright-interior / warm-food / soft-skin / vivid`, `correction: shared` for before/after (`image-processing.md`) | always through `prepare_footage`; look again by eye |
| **Pacing and cuts** | cut on the voice, on the music, on both; speaker jump cuts; cut on action, match cut; J/L-cut; mid-video re-hook; speed ramps `2x`, `ramp 1>2.5>1`, `0.5x` (needs 60 fps) (`cutting-and-pacing.md`, `sync-and-timing.md`) | per the playbook's `drive` and structure |
| **Virtual camera** | push, pull, pan, roll, hold, `focus`, `keys` (several keyframes with easing), punch-in on keywords, a wide-medium-close shot-size ladder; footage that already moves is kept still (`camera-moves.md`) | one visible move per scene (≥ 12% zoom or 8% pan), aimed at the action |
| **Transitions** | `fade slide wipe zoomThrough blurDissolve whip pushCut iris flip crossZoom cut`, accents `+flash +leak`, at most 3-4 kinds, at most 2 accents (`transitions.md`); HyperFrames adds `+shake +glitch +rgb +pulse` | the playbook's transition family; a straight cut exactly on the beat at the drop |
| **Graphics** | `title callout highlight step checklist price cart sticker progress magnifier thumbs compare ranking lowerThird specs pin label stat chart image punch` (`layout-and-motion-graphics.md`) | per the playbook's `use/avoid` lists; one idea per graphic, anchored to a word with `@"phrase"` |
| **Text** | themes `cool / warm / luxe`; 5 title styles `outline stack gradient glass marker`; captions `karaoke / pop / plain / none`; 3-4 styles per video, never the same twice in a row, one accent word; text on a light/white background uses `outline` or `marker` (`typography.md`, `captions-and-text.md`) | the text colour must suit the footage's tone: the playbook picks the theme, change it with `new_remotion_project.py --theme cool|warm|luxe` when the client asks (repeat `--theme` after every `--update`) |
| **Sound** | voice chain (traced noise reduction, EQ, de-ess, compression, −16 LUFS), music −14 LUFS, music ducks under speech (`volumeDb`, `duckDb`), music at 0 dB when there is no voice, half a second of silence before the reveal/drop, the subject's real sound kept as it is, master −14 LUFS (`audio-and-music.md`, `audio-processing.md`) | always through `process_audio.py` |
| **Sound effects** | `--auto-sfx` from `sfx-map.json` + the playbook's overrides, only CC0 or self-made, never placed across the reveal; soft transitions carry no sound (`sound-design.md`) | only when the playbook and the client want it; by default follow the playbook |
| **Before / after** | the `compare` card, same frame and same correction, time compression noted (`before-after.md`) | only when there is a visible result; not when running ads |
| **CapCut style** | look the technique up in `capcut-techniques.md` before inventing one; use each accent 1-2 times | when the client says "make it CapCut style" |
| **Platform** | TikTok/Reels templates, safe zones, ranking signals, music by platform, the posting checklist (`platforms.md` §6) | always, when reporting |
| **Compliance** | rules by genre: real estate, food, cosmetics, finance, promotions; ads; labelling of AI and commercial content (`claims-and-compliance.md`) | always |

### 5. Acceptance standard (self-check before sending to me)

- **Picture:** the subject is clear in every scene; no scene sunk in darkness, blown out, colour-cast, shaky or obstructed; colour is continuous between
  scenes; text is readable on every background; no graphic crowds a face, a UI zone or the text on a sign.
- **Pacing:** the hook is visible in the first 1-3 seconds; every scene has a visible change; no range repeats a scene already used; no cut
  falls in the middle of a word; strong cuts land on the beat or the drop; the closing scene has the right CTA or contact information.
- **Sound:** the voice is clear, with no hiss or stray noise at the start, the end or the pauses; the music is audible in the opening and does not cover speech; total level
  −14 ± 1 LUFS, peak ≤ −1 dBTP; no transition sounds if I ruled them out.
- **Content:** no forbidden claim; on-screen facts match the documents; people in the picture have a noted consent;
  music and voice have the right licence; commercial/AI labels are mentioned in the posting checklist.

### 6. Delivery and report

- Send the **compressed copy ≤ 30 MB** into the chat, with the path of the master.
- A short report in my language: the playbook and why; duration, number of scenes, hook; the picture corrections applied (from `corrections.json`);
  whether the cuts follow the voice or the music, and the drop point; the measured sound levels; what the sync report still flags; claims corrected or flagged (cite the rule);
  scenes shared under an exception; the posting checklist; and **what was not verified** (not yet listened to, people in the picture have not consented,
  the music rules of a business account, measurement results are heuristics).
- Keep every `edit-plan.md` (it is the footage ledger) and note the status of each video so work can continue next time.
- If you find a defect in the kit (for example a measurement that is wrong for this footage format), say so, propose a fix, and do **not** commit it yourself.

---

## 7. Short version and examples

**Short version (enough when the footage and the request are clear):**

> Use the skill `short-video-editing`. Edit [N] videos of [length] from the footage `[folder]`, voice `[file / none]`, music `[file / find (ask
> me before downloading)]`, post on `[platform]` `[organic/ads]`. Goal: `[CTA]`. Genre: `[playbook name / you propose]`.
> Special requests: `[..]`. No repeated scenes between videos `[except: ..]`. Do the full workflow in `docs/PROMPT-VIDEO.md` (sections 2-6),
> send the compressed copy into the chat and state what was not verified.

**Example A: a restaurant (`food-fnb`, with voice and music)**

> … 1 video of 30 seconds for the restaurant `[restaurant name]` (`[city]`) from `[footage folder]`, voice `[voice file]`, music `[style]` with a licence (ask me
> before downloading). Reference video `[reference file]`: analyse how it is edited. No repeated scenes with the other videos in the batch; only the opening and closing
> shots are shared. Keep `[technique to keep from the reference, for example: the tilting-pan shot in the first scene]`, drop the transition sounds, text in a warm tone.

**Example B: an apartment (`real-estate`, music only, figures needed)**

> … 1 video of 40 seconds, a tour of a 2-bedroom unit in `[project name]`, gimbal footage `[folder]`, music only. Facts: price `[..]`, area `[.. m², clear internal area]`,
> orientation `[..]`, address `[..]`, legal status `[..]`. If there are no other facts, none are shown. Ask me if the project does not yet meet the conditions for sale.

**Example C: a product review sold through the cart (`product-demo`, with before/after)**

> … 3 videos of 35 seconds for `[product]` (price `[..]`, product-card link `[..]`), footage `[folder]`, voice `[file]`. Post on TikTok Shop, **no**
> ads (so the before/after card may be used, with the time compression noted). No range is used twice across the three videos; when the scenes run out, stop and report.
> Claims in the existing voice: flag them, do not keep them silently.

**Example D: a speaker on camera (`talking-head`)**

> … a 45-second video from `[speaker video]`: remove the silences (jump cut), `pop` captions, B-roll from `[folder]` for each idea, the speaker's name and
> title `[..]` (as they really are). Advice touching health or finance: check it against the compliance section before editing.
