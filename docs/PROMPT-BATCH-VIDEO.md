# Prompt structure for a **batch of videos to publish for real** (several videos, several sources, with a voice, with a handover)

This file is for jobs like: "merge new and old footage, make N videos that do not repeat each other, speed up the voice, push the result into the
Drive sync folder, post to the real TikTok channel". The general rules, the step-by-step workflow and the technique catalogue are in
[`PROMPT-VIDEO.md`](PROMPT-VIDEO.md); this file only adds a **frame for writing the requirements of a production batch** and points out where prompts tend
to be ambiguous. No genre is hard-coded: length, pacing, colour, text and music come from the kit's playbook.

**Language:** you may write the prompt in any language; Claude answers in the language you write in (the user normally writes Vietnamese).

---

## 0. Six principles for writing the prompt for this job

1. **State the goal and the constraints, not the method.** "Each video 40-45 s, the voice clearly audible" is better than "speed up 1.7x". The speed-up
   factor is a method; length and clarity are the target. Write the factor as a **ceiling**, so that Claude lowers it when the voice distorts.
2. **Every number has a unit, a scope and a way of measuring.** "40% new footage" must say: counted in seconds on screen in each video or
   across the whole batch, with what tolerance. "1.07 to 1.18" must say whether it is 1 minute 07 seconds or 1.07 seconds.
3. **Full paths, dates double-checked.** A source "11-10-2026" and a destination "11-09-2026" are two different days: picking the wrong one writes to the
   wrong folder. Claude will ask again instead of guessing.
4. **Replace "absolutely no errors" with measurable criteria** (section E). Where a tool can check, write the tool's name; where only a person listening can
   know, write "Claude must say it has not listened".
5. **Split into stop gates instead of "ask everything first" or "do everything without asking".** Safe work is done on its own; stop only at the listed
   conditions (section F). Make **one sample video** that meets the standard, then multiply it across the batch.
6. **Say what each source is** (really shot, AI-generated, the client's, licence bought). It decides the AI label, the voice licence and the
   rule about repeats.

---

## 1. The prompt frame (copy, fill in `[...]`, delete the lines you do not need)

```
Use the skill `short-video-editing`. Answer in the language I write in. Today is [date]. The general rules and the workflow follow
docs/PROMPT-VIDEO.md (sections 2-6); what follows are the requirements specific to this batch.

## A. Goal and level of risk
- Edit [N] vertical 9:16 videos to post on [channel/platform], [organic / paid ads]. This is a [real version to post / demo].
- Success means: [N] files that meet section E, sitting in the right destination folder, no video repeating a scene of another video.

## B. Inputs (full paths, say clearly where each thing comes from)
- NEW footage: `[path]` - [really shot / AI-generated with tool ... / whose, which licence].
- OLD footage: `[path]` - [as above].
- Voice: `[path]` - [number of files; how long each one is; a real person's voice or AI (ElevenLabs, which plan)]; how it pairs with the videos:
  [one file per video / one file used for several videos / let Claude propose].
- Music: [none / a file with a licence / ask Claude to find one, ask me before downloading].
- Text script if any: `[path]`. Facts that must appear on screen: `[price, product name, offer deadline... or "none"]`.
- Style reference video: `[path / none]`.

## C. Quantity and content constraints
- [N] videos, each [min]-[max] seconds (outside the playbook's range, tell me, do not widen it yourself).
- Footage ratio: about [40]% new / [60]% old, counted in **[seconds on screen in each video / the whole batch]**, tolerance ±[5] percentage points.
  Every scene records in the plan whether its source is new or old.
- No source range may be used twice across the whole batch (`footage_overlap_checker.py` over all plans). Shared exceptions:
  [none / opening scene ..., closing scene ...].
- Genre: [playbook name / let Claude propose and give the reason].
- Special style requests: [long and short scenes, transitions, text colour, transition sounds or not, logo at the end...].

## D. Voice processing
- Target length after processing: [40-45] s per video. Speed-up factor: **at most [1.7]x**, pitch preserved (ffmpeg `atempo`), choose the
  smallest factor that reaches the length target.
- After the speed-up it must still: have every Vietnamese word clearly audible, no distortion, no hiss at the start/end/pauses. If more than [1.7]x is needed to reach the
  length, **stop and report** (options: drop which whole sentences, or accept a longer video) - do not squeeze the voice any further on your own.
- Order: cut (if needed) -> speed up -> `process_audio.py voice` -> transcribe, correct by hand -> `align_captions.py`, so that the captions match the
  sped-up version exactly.

## E. Acceptance criteria (each video, write PASS/FAIL in the report table)
- Technical: 1080x1920, h264 + AAC, +faststart; duration within the range of C; `pacing_checker.py` PASS; the new/old ratio deviation within the tolerance.
- Picture: no scene sunk in darkness, blown out, colour-cast, shaky; continuous colour; text readable on every background (look at each video's contact sheet).
- Sound: −14 ± 1 LUFS, peak ≤ −1 dBTP; no hiss or stray noise in the voice at the start, end, pauses; the music does not cover the voice.
- Content: no forbidden claim (cite the rule if corrected); the text facts match the documents I gave; the AI/commercial-content label is in the posting checklist.
- Deliver only when no video has an error; a video with an error is fixed until it passes, or you say clearly why it does not, never delivered silently.

## F. How to work and where to stop
1. Check the machine (`doctor.py`) and **take stock of the inputs**: the folder opens, the files are really downloaded to the machine (not Drive placeholders),
   there is enough disk space; measure the footage, look at the contact sheet; measure each voice file.
2. **Footage budget** (worked out before editing): usable new/old seconds against [N] x [length] x ratio; give the numbers.
3. Make **video 1 complete** (plan -> render -> master -> check against E), give me the compressed copy to watch **if** [I want to approve a sample / do not
   wait for me, carry on]. Then edit the remaining videos with the same workflow; render one after another, one heavy ffmpeg job at a time.
4. Check repeats across **all** plans, check each video against E, and only then deliver (section G).
- STOP and ask me when: the footage is not enough for [N] videos at the ratio and the no-repeat rule (give the numbers, do not reshuffle to make up the count); the source/
  destination folder is not found or the date does not match; an AI voice with an unclear ElevenLabs plan (the free plan is not for commercial use); a
  package/model/music download is needed; the voice is too long/too short after the speed-up; third-party footage; the genre disagrees with the footage.
- No commit, no push, no deleting or editing original files. Work files live outside the repo: `[work folder]`.

## G. Delivery
- Destination: `[destination folder path, for example G:\...\Video Final\<date>]`. File names: `[Brand]_[date]_V01 ... V[N].mp4`.
- **Copy** (do not move) the master into the destination; then check each file: all [N] files are there, the size equals the original, `ffprobe` reads
  it, the duration matches. Do not overwrite a file of the same name already in the destination: if you meet one, stop and ask.
- Syncing to Drive belongs to the Drive app; Claude only confirms that the files are in the right place (it may also check through the Drive
  connector if it is enabled); do not write "uploaded to Drive" if it was not checked.
- Report in my language: a table [video x new/old source x length x speed-up factor x LUFS x PASS/FAIL], which scene uses which clip, claim
  flags, the posting checklist, and **what was not verified** (not fully listened to, not seen on a real phone, Drive not checked...).
```

---

## 2. Small tips for use

- Two consecutive batches for the same client: put sections B, C (special requests) and E into a `brief.md` file in the work folder and then just
  write "make the new batch per brief.md, differences: …". Claude can read the file, no need to paste the whole prompt again.
- If you want to see a sample first, change F.3 to "stop after video 1 and send the compressed copy".
- The lessons about allocating footage across a batch are already in `CLAUDE.md`, so there is no need to repeat them in the prompt: allocate round-robin between videos, reserve one
  closing clip per video, file names without a dot, and an existing voice must be checked for hiss in the first 2 seconds.
