# Log of jobs done for clients (CASE LOG)

This file is **history**, not a guide. The skill and the toolkit **must not read it to learn how to work**: every reusable lesson
has been turned into a technique in `skill/short-video-editing/` (general documents, no client names, no footage file
names) and into `docs/DECISIONS.md` (technical decisions and pitfalls). Only here may a client name, campaign figures or real file names be written.

Rule for entries: one entry per job, with the **date, what the job was, what was measured, what was not checked**; a lesson that can be reused is written into
`DECISIONS.md` and a one-line pointer is left here. **The repo must stay private** (GMV figures, client names).

## Niche data (16,242 SAIZA mould-remover videos, 2025-06-02 → 2026-11-03)

Reproduced with `docs/niche-data-queries.sql`. Measured:
- The top 20% of videos by views account for **95.1% of GMV**; the remaining 80% average **171 views**, yet their GMV per 1,000 views
  is even *slightly higher* → the bottleneck is **reach**, not the sales pitch.
- CTR and the order rate peak at **35–44 seconds**; under 25 s is the worst. This holds when only proven KOCs are considered.
  Good KOCs make a video under 25 s only about 1% of the time.
- **9 KOCs produce 59.3% of GMV** out of ~2,900 people.

**Data that is NOT there:** retention / completion rate, hook type, cutting rhythm, sound. Every judgement about hooks and cutting
rhythm in the skill is **craft practice**, not a measurement: the skill labels them `[DATA]` / `[HYPOTHESIS]` to tell them apart.

The rules "scene ≤ 4 seconds" and "hook ≤ 3 seconds" come from common short-form practice, **not** from this data.
The rhythm "3–4 seconds per scene, soft transitions" is a **client requirement** (11/2026): a web search found no measured source for it.

## Service-intro video rebuilt from a sample video (11/2026)

The job: an agency ad video (SISMO) from 28 takes of one presenter + a 62.6 s voice file, following the client's sample video (63.7 s, 60 fps, 31 scenes). The full
recipe and the commands: `references/agency-pitch-recipe.md`. Why it was done this way, and what was tried and dropped:

- **The voice file is the takes' own camera audio, spliced** (correlation 0.98–1.0). So for each presenter scene the take's own picture is used with `In = start + lag`
  (`match_voice_takes.py`) and the lips match sample for sample; `check_lipsync.py` re-checks the final cut (21 scenes off by ≤ 5 ms). For the part that no take contains
  (the portfolio part), cutaway pictures come from the silent pre-roll/walk-off of other takes (`find_cutaways.py`), never another take of the same line.
- **The opening silhouette flash**: measured on the sample, the presenter is filled white on frames 0, 2, 4 (30 fps) and then the video plays. Made with the person-segmentation model `u2net_human_seg`
  (Apache-2.0, 168 MB, kept outside the repo, ask before downloading) → alpha PNG; the same model gives the head position (`--faces`) to brighten the skin. This model was chosen because it runs on CPU with
  onnxruntime (already there with faster-whisper), needs no GPU and no account.
- **Text**: 14 effects in one engine (`Fx.tsx`) instead of one component per effect; each effect is used once or twice in the video. The ellipse around the "stamp" text
  cut across the presenter's face → replaced by a two-bar frame hugging the text; a flickering neon made the text disappear → a gentler flicker pattern.
- **Sound**: a single whoosh and a single pop made the video monotonous, so the bank has 58 CC0 recordings (Kenney, OpenGameArt) + 17 self-synthesized sounds, rotated per
  event (no immediate repeats), each text effect has its own sound, the variant's `sfx.rules` allows 5 sounds per 3 s. Nobody listened: chosen by name, pack description and measurements.
  **Tried and dropped**: automatically detecting the effect sounds in the mix (energy jumps above 1 kHz). Tested on a mix with 68 sounds at known positions: it found 5 sounds, and
  the measure separating moments with a sound from random moments gave only AUC 0.53–0.58 (almost a coin toss) because the voice masks them. `analyze_reference.py` instead gives a
  spectrogram image (`spectrum_*.png`) for people to look at; the number of sounds and the share of cuts with a sound are NOT reported.
- **Music**: a TikTok business account may only use the Commercial Music Library (which a render cannot reach) → `make_music.py` writes a self-made bed that follows the cuts, and delivers an
  extra version without music. Music level `--music-levels=-6,-6` (the `=` is required): the first render came out without music because argparse rejected `-8,-8` and nobody read the "wrote" line.
- **Colour range**: Remotion exports full-range `yuvj420p`; phones show it washed out or burnt → `finish_video.py` converts it back to limited BT.709, master −14 LUFS / ≤ −1 dBTP.
- **Render**: 8 workers report "No frame found at position" with 2880-tall proxies → `--concurrency=5`.
- **Logo** was keyed out of a sample frame (alpha = (R−G+55)/260, ffmpeg `geq`, 4× Lanczos upscale): the last resort, ask the client for the vector file.
- **Not checked**: nobody listened to the sound/music or watched the whole video; sentence 8 of the script was guessed from a poor Whisper transcript; the figures in the voice (more than 300 brands, 10–50 videos/month,
  5–10 days, an offer valid only this month) are the client's claims and need evidence; the client names on the cards need consent.
- **Tools added for this job** (all in `docs/STRUCTURE.md`): `analyze_reference.py`, `montage.py`, `stills.mjs` (template), `mix_report.py`, `match_voice_takes.py`,
  `find_cutaways.py`, `person_matte.py`, `agency_plan.py`, `make_music.py`, `finish_video.py`, `check_lipsync.py`; `align_captions.py --prompt`; `doctor.py` checks
  onnxruntime, the person-segmentation model and the new ffmpeg filters; `./setup.sh --person-model`; `project_to_hyperframes.py` reports every feature only Remotion has.

## The "object drop" technique learned from a public TikTok video (2026-11-15)

The job: the user sent https://vt.tiktok.com/ZSpqrEJLQ/ (a 14.6 s video, 576x1024, "Trên đường về nhà" (On the way home), channel vantien96666, tag #editcapcut) and asked for research into the "object placement" technique. Viewed only in the browser; **nothing of theirs was downloaded or taken** into the kit.

Measured (frames at 1/30 s around second 6.1): the object (a gate) enters from the top edge at 6.10, falls for 3-4 frames, **hard cut** to a new scene at 6.20 with a yellow-orange explosion flash at the foot of the gate (4 frames), then grey smoke for 2 frames, gone by 6.33. The same pattern at 0.6 (a crane), 2.5 (a half-built house), 12.2 (a tower), 12.6 (a church dropping in front of the tower); plus vertical slide transitions (2.9 / 4.0 / 11.4 s) and tilted rotation (9.0-9.6 s). Sound: continuous music with a beat of ~0.4-0.6 s, the beat 6-8 dB louder right after the touchdown at 6.2 and after the cut at 8.1 (level measured, not listened to).

Not checked: which tool the author used to cut out the object (searches in Vietnamese and English found neither the technique's name nor a tutorial); the sound was not listened to; nobody asked permission to use that video as a reference (the kit takes only the technique).

Built into the kit: the overlays `objectDrop` and `impact` (`Drop.tsx`), `scripts/object_cutout.py` (`--poly` needs no model; `--model` only runs with a model the user supplies, so far tried with `u2net_human_seg` on a scene with a person, **not tried with `isnet-*`**), the method in `references/layout-and-motion-graphics.md` ("The object drop"). Licences of the background-removal weights, checked on 2026-11-15 through the GitHub pages: SAM 2 Apache-2.0 (code and checkpoint); rembg MIT but each model has its own licence; `isnet-general-use` the DIS page does not state; RMBG-2.0 needs a paid agreement; BiRefNet code MIT, weights not stated. No full video has been rendered with this technique yet; only stills of each falling and exploding frame on a test scene were looked at.

The first SISMO demo (4 drops, each scene 2.4 s, the presenter standing still, a big round explosion flash) was scored 4/10: against the original video, 4 events in 12.4 s instead of ~22 in 14.6 s, median motion 1.7 instead of 9.7, the explosion flash was a round glow covering the whole torso. The original was measured frame by frame (the meter: the brightness difference between two consecutive frames at 72x128, counting yellow pixels): each drop is a fall of 3-4 frames, a hard cut, a whole-frame horizontal blur for 2 frames, a thin flat yellow-white burst of rays on the ground (about 29% of the frame wide, 10% high), brown dust thinning out. `impact` was rewritten the way a post-production artist layers it (an exposure pop, a small core, sparks with trails, embers falling with gravity, noisy dust with ragged edges, a contact shadow, a very faint shock ring), and a `+jolt` hit was added (a horizontal blur and a decaying shake at the cut). Version 2: 12 scenes of 0.8-1.6 s, 11 drops, re-measured as 11 events in 11.6 s, median motion 3.8. Still not equal to the original in motion (a static camera, a fake push-in) and two presenters are still visible for 4 frames at the moment of the drop because the old scene also contained her. The sound was not listened to.

## Two technique-breakdown videos taken apart and built into the kit (2026-11-16)

The user supplied two public short videos (576 x 1024, 30 fps, 32.7 s and 23.4 s) that show one editing technique after another: the clip in a window, the name of the technique under it, the editor's timeline below with a playhead sweeping across it (`references/transition-pack.md`, section 1). Nothing was downloaded or reused; the files were analysed with `analyze_reference.py`, half-second and per-frame sheets of the window, and the timeline panel measured (the playhead moves linearly: 15.4 px/s on the first video, 22.2 px/s on the second).
Measured: 17 technique segments (9 + 8); the names read from the pictures are Flicker, Dolly zoom, Grid transition, Frame click, Teleport, Shape transition, Reverse, Crop + negative, Motion blur / Match cut, Grid mask, iPhone green screen, Grid mask, Mask transition, Black flash + mix, Pull in II, Zoom fade in. The label times were found by the shape of the label text (a pulse between bold and pale hides a plain frame difference).
Built into the kit: six transitions `gridFlash`, `cropPop`, `cropNegative`, `flashWipe`, `blackFlicker`, `zoomFade` (engine/transitions.tsx, cards, selftest), `scripts/find_occluders.py` (it found the passing sleeve at 9.90 s on the second video's window), `scripts/reverse_clip.py`, and the frame-by-frame description of every technique with its sound.
Not built (in `technique-backlog.md`): the dolly zoom, a full-frame object matte, the mosaic of nine clips, the strip split cut, a locked phone-screen composite. The six transitions were rendered as stills on two test clips and tested in `selftest.sh`; nobody has judged them on real footage, and nobody has listened to any sound. That the Reverse segment is reversed is read from the label and the timeline, not proven by a still.

## The current campaign scripts contain violating claims

Lark doc *"TQA 6 - REVIEW - GIỌNG ADAM"* ("TQA 6 - REVIEW - ADAM VOICE") (21 scripts). The sentences to rewrite, checked against the TikTok Shop policy
in `references/claims-and-compliance.md` §2:

| Sentence | Problem |
|---|---|
| "Không hiệu quả anh gửi tiền lại liền" (if it does not work I send the money back right away) · "Hổng sạch hổng lấy tiền" (no clean, no payment) | A money-back promise / guaranteed result |
| "diệt khuẩn" (kills bacteria), "diệt nấm mốc" (kills mould) | A cleaning product may not claim to kill/inhibit bacteria, **fungi**, viruses |
| "tẩy sạch mọi vết bẩn" (removes every stain) · "sạch tinh như mới" (spotless as new) | "Solves every problem" / an instant restoration |
| "ngay lập tức" (immediately) | An instant effect |
| "tốt nhất thị trường" (best on the market) | An absolute superlative with no evidence |

The money-back sentence is in **one of the highest-revenue videos** of the campaign. Running ≠ compliant.
Also, TikTok Shop asks for an **original script for each video**: playing one script as is across many KOCs is a risk.

## Batch of 8 videos posted for real: the client's original prompt and where it is ambiguous (11/2026)

An analysis of the real prompt of one batch (source: `docs/PROMPT-LO-VIDEO.md` before it was split; now `docs/PROMPT-BATCH-VIDEO.md`). The reusable frame stays in `PROMPT-BATCH-VIDEO.md`.

### The prompt rewritten into the frame

```
Use the skill `short-video-editing`. Work in Vietnamese. Today is 2026-11-11. General rules and workflow as in
docs/PROMPT-VIDEO.md (sections 2–6).

## A. Goal and risk level
- Make 8 vertical 9:16 videos for the TikTok channel [channel name], [organic / run as ads]. This is the version that gets POSTED FOR REAL.
- Success: 8 files that meet the criteria in section E, in the right destination folder, no video sharing a scene with another.

## B. Input
- NEW footage (made today, both new video and AI voice): the Drive folder "video ngày [11-10-2026 — confirm the date]" (that day's videos) at
  `[path downloaded to the machine]`; the new footage is [AI-generated with which tool / really shot].
- OLD footage: the folder "Video AI cà phê" (AI coffee videos) at `[path]`; [AI-generated / really shot].
- AI voice: in the folder "[...]", [number] files, each 1 minute 07 seconds – 1 minute 18 seconds; made with [ElevenLabs plan ... / another
  tool]. Pairing: [one voice per video / a voice reused across several videos].
- Music: [not used / please find some, ask before downloading]. Text script: [yes/no]. On-screen facts: [price, product name, ...].

## C. Quantity and constraints
- 8 videos, each 40–45 seconds.
- Footage ratio: about 40% new / 60% old, by seconds on screen in EACH video, tolerance ±5 percentage points.
- No source range is used twice across all 8 videos (no exceptions).
- Genre: let Claude propose (the product is [name]); give the reason.
- Special requirements: [keep the client's conventions if any: scenes of 3–4 s, soft transitions, no text in boxes].

## D. Voice handling
- The voice reads slowly: speed it up so each video is 40–45 s, at most 1.7×, keeping the pitch; every word clearly audible, no distortion.
  If more than 1.7× is needed → stop and report. Transcription and captions are done after the speed-up.

## E. Acceptance: as in the frame, section E.

## F. Method: as in the frame, section F (make video 1 first, then multiply to the other 7 videos, no need to wait for my approval of the sample).

## G. Delivery
- Destination: `G:\[...]\Video Final\[11-09-2026 or 11-11-2026 — confirm]`. File names `[Channel]_[date]_V01 … V08.mp4`. Copy, do not move,
  check that all 8 files are there, do not overwrite. Drive syncing is the Drive app's job.
```

---

### Where the original prompt could make Claude guess wrong (and the fix)

| Original sentence | Problem | Fix |
|---|---|---|
| "dài từ 1.07s cho tới 1.18s" (from 1.07s to 1.18s long) | Is it 1:07–1:18 (67–78 s) or 1.07 s? If 67–78 s, dividing by 1.7 gives **39.4–45.9 s**: just enough, with almost nothing spare to drop a sentence. | Write "1 minute 07 seconds". Check the arithmetic first: the voice length ÷ the factor must land in 40–45 s. |
| "tăng lên khoảng 1.7x" (speed up by about 1.7x) | 1.7× is a method, not a goal. The kit notes that a commercial voice faster than ~1.15× already sounds rushed (`voiceover-and-captions.md`); 1.7× on a Vietnamese voice easily loses tones and swallows sounds. The kit **has no speed-up script yet** (only `make_voiceover.py --speed` when synthesizing), so Claude would use `ffmpeg atempo` in the work folder. | Make the goal = length and clarity, with 1.7× as a ceiling; give a plan for when the ceiling is exceeded. |
| "40% video thô hôm nay và 60% cũ" (40% of today's raw video and 60% old) | By seconds on screen, by number of clips, or by file size? Per video or the whole batch? No tolerance. And `CLAUDE.md` records that the "new" share is capped by arithmetic when reuse is not allowed: 8 × ~42 s = ~336 s of usable footage, 40% is ~134 s new and ~202 s old. | State how it is measured and the tolerance; Claude computes the budget and reports it before editing. |
| "ko trùng nhau" (do not overlap) | Overlapping scenes, overlapping source ranges, or only a different order? TikTok Shop calls reshuffling the order repetitive content (`policy.md`). | "No source range is used twice across the whole batch", checked with `footage_overlap_checker.py`. When the scenes run out, stop and report. |
| "11-10-2026" source, "11-09-2026" destination | Two different dates, while today is 11-11. One of them may be a slip. | Write the full path or let Claude list the folder and you confirm. |
| "đẩy vào ổ G … tự đồng bộ" (push into drive G … syncs by itself) | Drive G may not be mounted; Drive files are sometimes only placeholders that are not downloaded; an existing file may be overwritten by mistake. | Section G and F.1: check existence, copy, do not overwrite, check after copying. |
| "ai voice audio" (AI voice audio) | An AI voice: which plan? ElevenLabs' free plan is not for commercial use; posting to a real channel is commercial use. AI footage also needs an "AI-generated content" label. | Write down where each thing comes from in section B; Claude puts it in the publishing checklist. |
| "Áp dụng mọi kỹ thuật … tuyệt đối không được lỗi" (Apply every technique … there must absolutely be no errors) | Not checkable, and "every technique" can be overused (the kit says to use what the playbook says, not everything). | Replace with measurable criteria (section E) and the sample-then-multiply workflow. |
| "Bắt đầu làm đi!!!" (Start now!!!) together with "nghiên cứu kĩ trước" (research carefully first) | Two requests pulling in opposite directions: both take inventory and start right away. | Section F: the inventory and the budget are steps 1–2 (no waiting), stopping only at the listed conditions. |
