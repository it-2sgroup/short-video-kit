# Sound design — sound effects on transitions and graphics

Sound effects (SFX) are short sounds that make a cut or a graphic feel intentional: a whoosh on a
slide, a click when the cart arrow appears. The voiceover stays the master; SFX sit under it and never
fight a word. Music and mixing live in `audio-and-music.md`. **[D]** documented, **[C]** craft
convention, **[?]** not verified here.

---

## 1. Where sounds may come from (licences)

A TikTok Shop video is commercial. Every sound needs a licence that allows commercial use. Checked on
2026-11-05:

| Source | Licence | Verdict |
|---|---|---|
| **The kit's recorded files** (`assets/sfx/`: whoosh, whip, switch, mouse-click, shutter-modern) | CC0: no attribution, commercial use allowed. Originals by 1bob, JW_Audio, Pixeliota, ristooooo1 (Freesound) and Kenney; rows in `assets/sfx/SOURCES.md` [D] | **Use** |
| **The kit's synthesized sounds** (`scripts/make_sfx.py`: pop, tick, ding, thud, swoosh, riser) | Made by ffmpeg oscillators and noise; no third-party rights | **Use** |
| **Kenney.nl packs** (Interface Sounds 100 files, Impact Sounds 130, UI Audio, Digital Audio…) | "public domain licensed (CC0)… free to use them, even in commercial projects"; attribution not required [D: kenney.nl/support] | **Use** for new sounds |
| **Freesound** | Per sound: CC0 is free of conditions; CC BY needs a credit that a video cannot show; CC BY-NC forbids commercial use [D, via third-party guides; no official page was readable]. A download needs a free account | **CC0 only**; filter the search by licence |
| **Pixabay** | Content License: commercial use and no attribution are allowed; you may not sell or distribute a file standalone, and content with recognisable trademarks, logos or brands cannot be used commercially [D: pixabay.com/service/license-summary]. Samples inside a sound may carry extra rights | Possible, one sound at a time; read its page |
| **Mixkit** | Third-party reviews say its SFX licence allows commercial use without attribution; the licence text itself could not be read here | **[?]** read mixkit.co/license before relying on it |
| **Sonniss GameAudioGDC bundles** | Royalty-free, commercial, no attribution; no standalone redistribution, **no AI training**; the text names games, films, TV and "videos" but not advertising [D: sonniss.com/gdc-bundle-license v2.0] | Confirm with Sonniss for ads; large downloads (GB) |
| **BBC Sound Effects archive** | A review of the archive reports personal, educational and research use only; the page could not be opened here | **[?] Do not use** commercially until read |
| **Other sounds in `@remotion/sfx`** | `bruh`, `windows-xp-error`, `vine-boom` and `ding` have no author or licence in Remotion's `generate.ts`, although a comment calls the group CC0 | **Do not use**; meme and Microsoft sounds are not safe for a brand |
| **TikTok Commercial Music Library** | Pre-cleared *music* for business accounts; the licence is for content on TikTok [D: ads.tiktok.com blog]. Sound effects are not covered by what was found | Music only |
| **Editor libraries (CapCut and others)** | Commercial terms not established | **[?]** read the terms first |

Rules for the kit: only CC0 or self-made sounds go into `assets/sfx/`; every file gets a row in
`SOURCES.md` (title, author, URL, licence); a file without a row does not ship. Downloading a sound
is a download: name the file, source and size, and ask first.

---

## 2. The sound bank

All files are WAV with their peak at −3 dB. `lead` is how long the file starts before its event so
its loudest moment lands on it (measured from each file's peak).

| Sound | Length | Lead | Kind | Use |
|---|---|---|---|---|
| `swoosh` | 0.55 s | 0.30 s | synthesized noise sweep | `slide` and `wipe` transitions |
| `whoosh` | 0.15 s | 0.08 s | recorded | `zoomThrough`, `flip` |
| `whip` | 0.17 s | 0.03 s | recorded | `whip` transition |
| `thud` | 0.40 s | 0 | synthesized impact | `pushCut`, `+flash` accent |
| `riser` | 1.00 s | 0.95 s | synthesized rise that stops | `crossZoom`; manual run-up to a moment |
| `shutter-modern` | 0.49 s | 0.21 s | recorded | hook BEFORE → AFTER, `thumbs` |
| `switch` | 0.33 s | 0.12 s | recorded | `step` numbers |
| `mouse-click` | 0.40 s | 0.12 s | recorded | the cart pointer arriving (CTA) |
| `pop` | 0.12 s | 0 | synthesized | `title` styles `stack` and `glass`, `highlight`, `sticker` |
| `tick` | 0.06 s | 0 | synthesized | `checklist` |
| `ding` | 1.00 s | 0 | synthesized bell | `price`, `ranking` |

`new_remotion_project.py` copies the recorded files into a render project's `public/sfx/` and
synthesizes the rest there, so a render project never needs a network fetch.

---

## 3. Which sound on which event

The table lives in `assets/sfx/sfx-map.json`; change it to change the sound design, not the script.
`plan_to_project.py --auto-sfx` reads it. Reasoning behind the defaults:

- **Soft transitions get nothing.** `fade` and `blurDissolve` are meant to be felt, not heard.
- **Moving transitions get one sound**, matched to their energy: `swoosh` for slide/wipe, `whip` for
  a whip, `whoosh` for a zoom. Never stack two on one cut [C].
- **A flash accent (`+flash`) gets a `thud`** in place of the transition sound.
- **The hook's before → after cut gets the camera shutter**: it says "this is the same item, a moment
  later" and fits the honest-comparison rule.
- **Nothing across the reveal.** The existing rule stands: the pouring and fabric sounds carry the
  payoff (`audio-and-music.md`). `"*>REVEAL": null` silences the transition into it.
- **Graphics: only where the sound adds meaning.** A click when the cart arrow lands, a switch for a
  numbered step, a pop for the product-name title. Plain outline titles, callouts and captions are
  silent; sound on every piece of text turns the video into a template [C].
- **Cuts already sit on pauses in the voice** (`sync-and-timing.md`), so a transition sound lands in a
  gap and does not touch a word. Graphic sounds may overlap speech; they are quiet and short.

Hand-placed cues: an Overlays row with component `sfx` and `src=sfx/riser.wav; volumeDb=-12` at the
time of the event (subtract the sound's lead yourself). Hand-placed cues always stay; automatic ones
step aside.

---

## 4. Timing and level

- **Peak on the event, not the start.** Whooshes lead the cut so the loudest part meets the first
  frame of the new shot; sources agree on "start just before the cut" [C]. The map's `lead` values
  come from each file's measured peak.
- **Short sound for a short transition.** Match the sound's length to the transition's length [C];
  a 0.55 s swoosh suits a 14-frame (0.47 s) slide centred on the cut.
- **Level.** Guides put whooshes at −18 to −25 dB and impacts at −12 to −18 dB on a mix meter, and
  advise ducking music 3–6 dB under an effect [C]. In this kit the voice peaks near −4.5 dBFS and
  integrates near −13 LUFS, so `gainDb` is set so each effect's peak sits about 8–12 dB under the
  voice (swoosh −10, pop −12, tick −15). Raise or lower everything with `--sfx-gain`.
- **Density.** The map enforces at least 0.2 s between sounds and at most 2 in any 3-second window;
  a 35-second video ends up with roughly 11–15 cues. Fewer is better; if the video feels busy, remove
  rows from the map, not words from the voice.
- **Never mask the claim.** Keep loud sounds (`thud`) off the first word after a cut and off the
  price or the product name.

---

## 5. Verify

1. `plan_to_project.py … --auto-sfx` prints the cue count; open `project.json` and read `sfx`.
2. The render must not clip: `ffmpeg -i out.mp4 -af volumedetect -f null -` should show a
   `max_volume` of −1 dB or lower, and a mean close to the voice-only file's. To see each effect
   against the voice, subtract the voice-only track from the render and compare peaks in the 0.6 s
   after every cue. Beware: ffmpeg's stereo → mono downmix adds 3 dB to a file with identical
   channels, so measure stereo sounds per channel or expect +3 dB. In the first KB4/KB7 renders the
   effects came out 3–14 dB under the voice's peak in the same window, and the click and thud were
   the closest (3–6 dB), so their `gainDb` was lowered.
3. **Listen.** A tool cannot judge whether a swoosh sounds right on a particular cut. Play the video
   with phone speakers and say in the report that it was (or was not) listened to.

Sources: Remotion `@remotion/sfx` docs and `remotion.media` `generate.ts` (file list, authors,
licences); Pixabay and Sonniss licence pages; Kenney support page; transition-sound guides from
Pixflow, Sonilo and SFXEngine (timing and level rules of thumb [C]).
