# The HyperFrames flow (a second renderer)

The kit renders with Remotion (`remotion-output.md`). This file is the same pipeline with **HyperFrames**
as the renderer: HeyGen's open-source framework that turns HTML, CSS and seekable animation into MP4.
Everything before the render (footage analysis, proxies, voice, captions, cuts, the plan, the checkers,
the mastering) is shared; only the last step changes. Nothing here replaces Remotion: pick one per video
(§1).

**[M]** measured in this kit, **[D]** documented by HyperFrames, **[C]** craft convention.

---

## 1. Which renderer

| | Remotion (default) | HyperFrames |
|---|---|---|
| Licence | Free to individuals and companies of up to 3 employees; $25 per seat per month above that, an AI agent writing Remotion code counts as a seat | **Apache-2.0**, no per-render fee and no seat count [D] (`github.com/heygen-com/hyperframes/blob/main/LICENSE`); fonts, footage and music keep their own licences |
| Overlays drawn | all 20 components | 17: **not drawn: `magnifier`, `thumbs`, `compare`, `ranking`** (the generator lists them and skips them) |
| Transitions | all of `TransitionType` (the shader ones are WebGL) | the CSS ones (the first 11 and `blinds`, `diamond`, `doors`, `glitchSlice`, `spinZoom`); the shader and card ones are drawn as a `fade` and listed in the report (`crossZoom` is a zoom-blur dissolve here) |
| Subject effects (`Subject` cell) | fill, outline, glow, dim, colorpop, behind and the newer modes | fill, outline, glow, dim, colorpop (matte PNGs are linked into the project); the modes that need a second copy of the footage (`behind`, `lift`) are Remotion only and listed |
| Camera `shake` | drawn | drawn (the same noise) |
| Library fonts (`font=<id>`) | loaded on demand | the converter imports the families an overlay asks for (`assets/fonts.json`) and drawn on the overlays HyperFrames draws (`title`, `label`, ...) |
| CapCut-style hits (`+shake +glitch +rgb +pulse`), film look (`--look`) | ignored | drawn |
| Speed ramps | frame-by-frame inside `<Freeze>` | baked into one clip per scene with ffmpeg |
| Proven here | many videos | one real video and the example project, frame-compared (§6) |

**Use HyperFrames when** the studio is above the Remotion seat limit, when a video wants the
CapCut-style hits or the film look, or when you want its catalogue (§7). **Use Remotion when** the plan
needs a before/after `compare`, a `thumbs` strip, a `magnifier` or a `ranking`, or the cleanest `crossZoom`.
Say which and why in one line, as with the playbook. A requirement that a video has the same look in both
renderers holds: the tokens, easings and layout come from the same `theme.ts` numbers (§6).

## 2. What HyperFrames is [D]

- A composition is an HTML file. Timed elements carry `data-start` and `data-duration` (seconds);
  `<video>` and `<audio>` also take `data-media-start`, `data-volume`, `data-playback-rate`. The root is
  `data-composition-id`, `data-width`, `data-height`, `data-duration`.
- Motion is a **paused GSAP timeline** registered as `window.__timelines["main"]`. The renderer never plays
  it: headless Chrome seeks to each frame, screenshots it, and FFmpeg encodes. Video is pre-extracted to
  frames, so the render is deterministic as long as the page is a pure function of time: no `Date.now()`,
  no unseeded `Math.random()`, no network at render time.
- Requirements: **Node 22+**, **FFmpeg**, Chrome (the CLI uses the system Chrome when it finds one, so then
  nothing is downloaded beyond the npm package).
- CLI (`npx hyperframes@VERSION …`): `check` (lint, runtime, layout, motion and contrast in one command),
  `snapshot --at 1,3,5` (PNG frames to look at), `preview`, `render` (`--quality draft|standard|high`,
  `--format mp4|mov|webm|gif|png-sequence`, `--fps`, `--workers`, `--docker`, `--output`), `transcribe`,
  `tts`, `remove-background`, `beats`, `normalize-audio`, `add` / `catalog` (a registry of ~450 blocks).
- On Windows and macOS the renderer falls back to screenshot capture; the deterministic BeginFrame path is
  Linux-only, so a Windows render is not guaranteed bit-identical to a Linux one [D]. The kit is a pure
  function of the frame, so the picture is the same to the eye (§6).
- Agent skills (`npx hyperframes skills update`) are the person's step, not the agent's, and the kit does
  not need them.

## 3. The flow

Steps 0–6 of `SKILL.md` are unchanged. The render project is made as usual, **without** `--install`
(Remotion's npm install is not needed), so it holds the proxies, the sound effects and `project.json`:

```bash
python scripts/new_remotion_project.py RENDER --playbook <id> --proxies CLIPS        # proxies + public/sfx; no --install
python scripts/plan_to_project.py edit-plan.md --out RENDER/v1.json --voice audio/v1.wav --music audio/music.wav \
    --captions captions.srt --words words.json --auto-camera --analysis analysis.json --auto-sfx
python scripts/project_to_hyperframes.py RENDER/v1.json --out HF/v1 --playbook <id> [--look vignette=0.3,grain=0.05]
```

The last command, in order: lays out the scenes with the same centred transitions as `timeline.ts`; bakes
every scene with `speed` or `ramp` into its own clip; mixes voice, ducked music and sound effects into one
`audio/mix.wav` (same levels, 2-frame attack and 12-frame release as `engine/audio.tsx`); links the clips
the scenes use (a hard link on the same volume, so the 1620×2880 proxies are not copied); writes
`index.html`, `kit.js`, `kit.css`, `package.json`. It prints what it could not draw and any scene whose
source runs out before the scene does.

Then, in `HF/v1` (**ask before the first `npx`**: it downloads the `hyperframes` package; tested: 0.9.26):

```bash
npx hyperframes@0.9.26 check                       # 0 errors expected; see §5 for the warnings that are normal
npx hyperframes@0.9.26 snapshot --at 0.5,4.4,9,28  # LOOK at the contact sheet it writes: titles, captions, transitions
npx hyperframes@0.9.26 render --quality high --output final.mp4
python scripts/process_audio.py master HF/v1/final.mp4 --out HF/v1/v1_final.mp4 --phone
python scripts/contact_sheet.py HF/v1/v1_final.mp4 --project RENDER/v1.json --out sheet.png
```

`project_to_hyperframes.py --check` and `--render FILE` run the same commands. The render is 855 frames of a
1080×1920 video in about 55 s on a 16-core desktop [M]; `--quality high` gave about 12 Mb/s, a 41 MB file before
mastering. A phone copy is still needed for the chat (the 30 MiB limit in `CLAUDE.md`): `process_audio.py master … --phone`.

## 4. The plan syntax added for it

`Transition` cell, after the transition and the accent: **`+shake`**, **`+glitch`**, **`+rgb`**, **`+pulse`**
(e.g. `slide up +shake`, `whip left +glitch +rgb`). They hit the first 8–14 frames after the cut:

| Token | Effect | Use |
|---|---|---|
| `+shake` | camera shake decaying over 14 frames (sums of sines, no random numbers), with spare scale so the edge never shows | an impact, a drop on the beat, a reveal |
| `+pulse` | a 10-frame zoom pulse (×1.08 and back) | a hit on the beat, a keyword |
| `+rgb` | red and green-blue channels split 14 px and back over 9 frames (a real SVG channel split) | a tech or hype moment; one per video |
| `+glitch` | `+rgb` plus a horizontal jitter, hue flicker and contrast kick over 8 frames | a hard cut that should feel torn; once or twice |

`plan_to_project.py` stores them as `scenes[].fx` and warns that Remotion ignores them. Spend them like the
other accents: **at most two per video**, never on the reveal itself, never together with `+flash` on one cut
(`accentsMax` in the playbook caps `+flash` and `+leak` in the skeleton; the fx tokens are not counted, so keep them to two yourself). `--look vignette=0.3,grain=0.05` adds a vignette and film
grain over the footage (grain re-seeds every 6 frames); keep both under 0.4 or the picture reads dirty.
Neither is a claim about what performs better: they are CapCut-style finishes [C].

The camera `keys` of `camera-moves.md` (keyframes) are read by both renderers; `kit.js` ports `engine/camera.ts` line
for line, and the same plan was previewed with HyperFrames snapshots to find each subject's coordinates before the
Remotion render: a snapshot of 10 scenes takes about 15 s, a Remotion still about 10 s each.

## 5. What `check` says and what to do

`check` ran on the real video: **0 errors, 23 warnings, 1 note** [M]. The warnings are all `line_unread`:
HyperFrames wants a line of text on screen for 0.5 s + 0.3 s per word, and spoken captions that follow a
fast voice are shorter. That is the voice, not an error (`voiceover-and-captions.md`); do not slow the
captions to please it. Two checks were false alarms and are silenced in the kit:

- the outline layer under every outlined text repeats the text, which `check` read as an overlap and as a
  low-contrast text: `kit.js` marks it `data-layout-ignore`;
- the camera layer is deliberately larger than the frame during a push-in: `data-layout-allow-overflow`.

If `check` reports a **new** error, read it: it can be a real fault (a missing file, an unregistered
timeline). `check --no-contrast` skips the contrast pass; text over moving footage cannot be judged by a
sampled pixel anyway: look at the snapshots.

## 6. Parity with the Remotion render [M]

Checked on the cafe video 3 (28.5 s, 10 scenes, fade/slide/blurDissolve/zoomThrough, captions, two cart
arrows, a glass title):

- **duration** 28.500 s and 855 frames in both; **loudness −16.3 LUFS** in both, true peak −3.6 and −3.7 dBFS
  (the mix is the same maths); 
- six frames taken at transitions and captions, side by side: the same picture. The light leak differs in
  colour (a CSS gradient, not Remotion's shader);
- the example project's titles (stack, outline, gradient, glass, marker), callout, circle, step, checklist,
  sticker, price, cart arrow: indistinguishable in a side-by-side of seven frames (HyperFrames above, Remotion below).

Then both renderers rendered the **same** video 3 (cool theme) and were compared frame by frame [M]:
**SSIM 0.987** (Y 0.984), **PSNR 36.3 dB** average over 855 frames; 852 frames are above SSIM 0.95 and the
three below it sit at 3.40 s and 21.23 s (a transition frame and an overlay edge). The first comparison gave
SSIM 0.946 and dips to 0.79 on every scene with a camera move, and it was a real bug: Remotion's
`perceptual-scale` eases the zoom in **area** (scale squared: `√(a² + t(b² − a²))`), not geometrically; the
kit now does the same. A frame-counting clip shows both renderers read exactly the same source frame
(output 10, 30 and 60 → source 40, 60 and 90). Timing, same machine, one run each: HyperFrames 56 s (122 s on
one earlier run, so the spread is real), Remotion 100 s. Sizes (31.0 MiB Remotion at `--crf=18`, 40.9 MiB
HyperFrames at `--quality high`) reflect the encoder settings, not picture quality.

Not compared: the information graphics after 25 s (`pin`, `label`, `chart`, `specs`, `stat`) were rendered
by HyperFrames and look right but the Remotion stills for those frames failed to render in this run;
`progress`, `lowerThird` and `image` were ported from the source and not rendered.

## 7. What HyperFrames adds that the kit does not use yet

None of this is wired or tested here; it is where to look. [D]

- **Shader transitions**: `@hyperframes/shader-transitions` has 14 WebGL shaders (`domain-warp`, `ridged-burn`,
  `whip-pan`, `sdf-iris`, `ripple-waves`, `gravitational-lens`, `cinematic-zoom`, `chromatic-split`, `glitch`,
  `swirl-vortex`, `thermal-distortion`, `flash-through-white`, `cross-warp-morph`, `light-leak`). It wants a
  scene structure of its own, and a CSS transition must not be mixed with a shader one in the same
  composition, so it would replace `kit.js`'s transitions, not add to them.
- **Caption components** (`caption-kinetic-slam`, `caption-pill-karaoke`, `caption-neon-glow`, …) for composed
  videos; they sit in front of the speaker on talking heads.
- **`remove-background`** (u2net_human_seg, Apache-2.0) cuts a person out: the way to "text behind the
  subject": text between the footage and the cut-out. A model download, so ask first; `capcut-techniques.md` §6.
- **`beats`**, **`normalize-audio`**, **`transcribe`** (Parakeet or whisper.cpp), **`tts`** (local Kokoro): the
  kit already has equivalents (`suggest_cuts.py`, `process_audio.py`, `align_captions.py`, ElevenLabs).
- **Docker** (`--docker`) for a bit-identical render on any machine, and cloud rendering: not needed for
  one video at a time.

## 8. Pitfalls (each cost time or is documented as a trap) [D][M]

- A `<video>` needs `muted` (or `data-has-audio="true"`); the kit's scene videos are `muted` and the sound
  is the separate `audio/mix.wav`.
- Never animate `width`, `height`, `top` or `left` of a `<video>`, never call `play()` or set `currentTime`:
  the kit moves a wrapper (`.tr` for transitions, `.cam` for the camera).
- `data-track-index` does nothing in a render: stacking is CSS `z-index` (`kit.js` sets it per scene).
- `window.__timelines["main"]` must be registered under the root's `data-composition-id`, or every frame is
  the first. `kit.js` drives the playhead through a property setter, not a callback, because GSAP's
  `seek()` suppresses callbacks by default.
- Python's `round()` sends halves to the even number and JavaScript's `Math.round` to the larger: the
  generator uses a half-up helper so a 0.5-frame transition length cannot drift a frame from Remotion.
- A source clip shorter than a sped-up scene is padded with its last frame and reported
  ("ends 0.67 s before the scene does"): use a longer range or a slower speed.
- Slow motion (< 1×) needs a 60 fps proxy (`prepare_footage.py --slowmo`), as in Remotion.
- GSAP loads from jsDelivr (`gsap@3.14.2`, pinned) and the Google Fonts CSS is inlined by HyperFrames at render
  time: the first render needs a network. To render offline, copy `gsap.min.js` into the project and change
  the `<script src>` in `index.html`.
- The project pins `hyperframes@0.9.26` in `package.json` so a re-render is identical; move the pin
  deliberately (`HF_VERSION` in `project_to_hyperframes.py`) and re-run `check` and a snapshot.
- A project is generated: edit the plan or `project.json` and regenerate, not `index.html`. `--out` on an
  existing folder refreshes it (the generated files are overwritten; `renders/` and `.hyperframes/` stay).

## 9. Extending the kit

- A **new overlay** is one function in `FACTORY` (`assets/hyperframes-template/kit.js`): it builds its DOM once
  and returns `update(f, dur, instant)`, a pure function of the frame, exactly like the Remotion component it
  mirrors. Add its name to the Remotion `registry.tsx` and the layout table too, or `playbook.py check` fails.
- A **new effect** on a cut is a branch in `fxFor` plus a token in `plan_to_project.parse_transition`.
- A **new look** is a theme in `THEMES` (and `theme.ts`): change both or the two renderers drift.

Sources: `github.com/heygen-com/hyperframes` (README, LICENSE), `hyperframes.heygen.com` (`html-schema`,
`data-attributes`, `frame-adapters`, `gsap-animation`, `shader-transitions`, `cli`, `rendering`, `faq`),
`heygen.com/research/html-to-video` (June 2026).
