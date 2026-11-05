# Sync and Timing

How the parts lock together: raw-clip cuts, the voiceover, transitions, graphics, captions, camera
punches, music and SFX. **[D]** documented, **[C]** convention.

---

## One master clock: the voice

The voiceover decides time. Everything else is anchored to it:

1. `align_captions.py voice.mp3 --script script.txt --out captions.srt --words-out words.json`
   gives word timings (timing from Whisper, spelling from the script).
2. The plan's scene cuts are chosen on pauses; overlays can be anchored to words with
   `@"phrase"` instead of hard-coded seconds.
3. `plan_to_project.py` resolves the anchors, then prints a **sync report**.

Because anchors follow the words, re-recording the voice and re-running steps 1 and 3 re-times the
whole edit without touching the plan.

---

## Cutting on speech [C, with D for the detection tools]

- Hard cuts: in the middle of a pause ≥ 120 ms. Soft transitions: centred on pauses ≥ 250 ms
  (sentence ends).
- Never cut inside a word (the sync report flags any cut between `start+2f` and `end−2f`).
- No pause nearby: cut 0–2 frames before a stressed word.
- Find pauses with the word gaps in `words.json`, or
  `ffmpeg -i vo.wav -af silencedetect=noise=-35dB:d=0.12 -f null -` (the ffmpeg defaults, −60 dB/2 s,
  are far too coarse).
- J-cut/L-cut (sound leads or trails the picture by 4–8 frames) apply to clips with their own
  audio; a continuous voiceover makes them unnecessary.

---

## Graphics on words

| Event | Timing |
|---|---|
| Graphic enters | word start − 3 frames (`@"word"` does this) |
| Holds at least | max(0.83 s, 0.3 s + characters ÷ 15) — `End = auto` (Netflix VN guide: 17 cps, 5/6 s min [D]) |
| Leaves | ≥ 3 frames before the next cut (`End = cut`) |
| Punch-in | 2 frames before the keyword, 6-frame ease, holds to the scene end |
| Caption group | Fades in over 4 frames; groups shorter than 0.45 s are merged by `align_captions.py` |

Text that appears or vanishes on the exact frame of a cut looks like a mistake; the sync report
flags anything within 3 frames of a cut.

---

## Music and beats

- Voice-led edits: the voice decides cuts. Snap a cut to a musical downbeat only if one falls within
  ±4 frames of a legal speech cut. Beat-led montages only for wordless B-roll [C].
- Beat detection: `librosa.beat.beat_track(y=y, sr=sr, units="time")` (ISC licence) →
  `frame = round(t * 30)`; frames per beat = 1800 ÷ BPM (120 BPM → 15 frames; 2 bars = 4 s, which
  matches the 3–4 s cadence). Avoid GPL/AGPL trackers (aubio, essentia) in shipped tooling.
- Ducking (built into the template's `Soundtrack`): music at −18 dB, dipping a further −12 dB under
  speech, 2-frame attack, 12-frame release; speech gaps < 0.4 s stay ducked so the bed doesn't pump
  [C; Remotion recommends a frame-computed `volume` [D]].
- Master to about −14 LUFS integrated, true peak ≤ −1 dBTP (`ffmpeg -af ebur128`) [C].
- Music must come from TikTok's Commercial Music Library or carry a licence covering commercial
  social use — see `audio-and-music.md`.

---

## Verifying sync

1. **Static:** `plan_to_project.py` sync report (cuts inside words, text on cuts, right-rail
   collisions, zone overlaps, flashing captions) and `pacing_checker.py`.
2. **Stills** at cut−1 / cut / cut+1, every transition centre and every overlay entrance+3:
   `npx remotion still src/index.ts Short out/f.png --frame=N --props=project.json`, tiled with
   `ffmpeg -vf tile` into a contact sheet and looked at.
3. **Rendered file:** `ffmpeg -vf "select='gt(scene,0.3)',showinfo"` lists detected cuts, which
   should match the plan within ±1 frame; `ffprobe` duration equals the plan runtime; audio and video
   durations agree.

Sources: Remotion `audio`, `media-utils`, `captions`, `transitions` docs; browser-use/video-use
(cut padding, silences ≥ 400 ms as cut points, loudness targets); HyperFrames beat maths; librosa
docs; Netflix Vietnamese timed-text guide.
