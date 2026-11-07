# Audio and Music

Audio is the channel most often treated as decoration and most often responsible for a video feeling
amateur; it is also where a licensing violation costs a commercial account. Cleaning and levelling
(noise, EQ, loudness) are in `audio-processing.md`; sound effects in `sound-design.md`.

**[O]** official, **[M]** measured with the kit's tools, **[C]** craft convention.

---

## Licensing first

**Business accounts use the platform's commercial catalogue**, not the consumer music catalogue:
TikTok's Commercial Music Library, Meta's Sound Collection (`platforms.md` §4). Chart music on a
commercial video is a violation however well it performs. About 74% of 1,842 TikTok Shop affiliate
videos used original audio or none (`oktorun.ai/research/tiktok-shop-affiliate-music-study`).

The claim that *"trending audio generated 58% more add-to-cart actions"* is misattributed (the study
measured licensing, not conversion). Do not repeat it.

### Finding a track the render can use

The commercial libraries live inside the apps, so a render cannot fetch from them. Bake into the master
only music that is CC0, self-made, or licensed for every platform it goes to; the human may add a CML
track in the TikTok app at upload. A licence-safe source tested 2026-11-06: **OpenGameArt** tracks whose
page says `License(s): CC0` (search `art-search-advanced?keys=lofi&field_art_type_tid[]=12&field_art_licenses_tid[]=4`,
open each page, confirm CC0 and the author, download the file linked there). Pixabay answers 403 to
scripted requests; the Internet Archive search errored. Keep a `SOURCES.md` beside the tracks (title,
author, URL, licence) and **ask before downloading**.

---

## Choosing the music for the genre

The playbook gives the tempo range and the mood (`playbook.py show <id>`), and `suggest_cuts.py
--music` searches beats only inside that range:

| Playbook | bpm | Mood | Role |
|---|---|---|---|
| product-demo, tutorial | 85–120 | light, steady | a bed far under the voice |
| talking-head | 80–110 | unobtrusive, no vocals | optional, very low |
| real-estate | 95–125 | warm, modern, steady 4/4 | carries the tour; cut on bars |
| food-fnb | 100–128 | warm, playful | carries it; ducks under sizzle and bites |
| fashion-beauty | 100–130 | trend-friendly, clear downbeats | outfit changes on the beat |
| montage-recap | 100–140 | energetic, a clear drop | the script: sections and drop |
| promo-sale | 110–140 | bright, punchy | hits under the price reveals |

Beat arithmetic: one beat = 60/bpm s; at 30 fps, 1800/bpm frames (120 bpm = 15 frames). A bar of four
beats lasts 2.0 s at 120 bpm, 2.7 s at 90 bpm, so a voice-paced 3–4 s scene is about one or two bars [C].

---

## Cutting to music

- `suggest_cuts.py --music track.wav --end 40 --playbook <id>` finds the beats (spectral flux, tempo by
  autocorrelation weighted toward 120 bpm with half-beat evidence, dynamic-programming beat tracking,
  bar starts from the low end) and chooses cuts on them, bar starts first, every scene within the
  playbook's lengths. `--beats-out beats.json` keeps the grid and a confidence. It needs numpy and
  re-launches itself in the kit's venv.
- Voice-driven videos with music: cut on the voice's pauses and add `--music` to nudge a cut onto a beat
  within 4 frames when that keeps it out of a word [C].
- Use the beats to support a sequence, not to force every cut [C]; cut more often as the track builds and
  hard-cut onto the drop's first downbeat; land speed ramps on a beat.
- **How good it is** [M, three CC0 tracks from OpenGameArt, 2026-11-07]: 97 bpm and 104 bpm found where the
  inter-onset intervals say ~97–98 and ~105; 88–95% of the detected beats sit within 30 ms of a strong
  onset (a grid shifted half a beat: 15–86%). The third track has a compound feel (a 0.273 s
  subdivision): it was read as 73 bpm where 110 is equally defensible; both grids land on onsets, so the
  cuts still sit on the music, but the cut rhythm differs. Two simpler detectors tried first (pure Python
  energy envelope; on/off-beat contrast) got two of the three tracks wrong. Look at the cut list against
  the waveform or listen, and prefer tracks whose bpm the library states.

---

## Levels (the numbers the tools implement)

| Element | Level | Where it is set |
|---|---|---|
| Voice | −16 LUFS integrated, true peak ≤ −1.5 dBTP, compressed 3:1 | `process_audio.py voice` |
| Music file | −14 LUFS, true peak ≤ −1.5 dBTP | `process_audio.py music` |
| Music in pauses | −10 dB on the levelled file ≈ 8 LU under the voice | `plan_to_project.py` (`volumeDb -10`) |
| Music under speech | a further −8 dB (≈ 16 LU under the voice), 2-frame attack, 12-frame release | `duckDb -8`, ducking from the word timings |
| Music with no voice | 0 dB: the track is the soundtrack | automatic when `--voice` is absent |
| Sound effects | peaks ~8–14 dB under the voice | `assets/sfx/sfx-map.json` |
| Final mix | −14 LUFS integrated, true peak ≤ −1 dBTP | `process_audio.py master` |

Music 15–20 LU under the voice during speech and 8–12 LU under it in gaps is the common practice [C];
the research mix measured 17 LU under with a 9.6 dB duck at −14.4 LUFS overall [M]. The most common
error in affiliate video is music only 6–8 dB under the voice: fine in headphones, it buries the words
on a phone speaker. Neither TikTok nor Instagram publishes a loudness target [O]; −14 LUFS is common
practice, not a platform rule.

---

## Diegetic sound is the credibility layer

The real sounds of the subject (a pour, a scrub, a sizzle, a door, the crowd) are the strongest
authenticity signal there is, and free. Do not bury them: drop the music under them, or let the room
tone carry the reveal. A demo that sounds like a room is more believable than one that sounds like an
advert. Real estate: record 10 s of room tone per room to cover cuts.

---

## J-cuts and L-cuts

A **J-cut** starts the next shot's audio before its picture; an **L-cut** holds the previous audio
over the new picture. When picture and sound always cut together at short scene lengths, the edit feels
staccato; offsetting them makes fast cutting feel smooth.

- **J-cut into a demo or a dish**: the pour or the sizzle starts a few frames before its shot.
- **L-cut into B-roll** (talking head, testimonial, agent voiceover): the voice continues over the new
  picture. In the kit the voice is one continuous track, so every B-roll scene is an L-cut.
- **L-cut across a reveal**: the voice carries over the moment you must not cut picture across.

---

## Silence as a tool

Cut music and voice for about half a second just before the reveal or the drop. On a feed where every
video is loud, a sudden gap is a real pattern interrupt. Once per video; twice reads as a fault.

---

## Voice budget

Commerce pace is about 4.5–5 words/s: a 35 s voice-driven video holds 150–170 Vietnamese words with
its pauses. Write to that budget before recording or synthesizing; trimming after synthesis wastes a
pass. ElevenLabs settings and the supplied-voice path are in `voiceover-and-captions.md`.
