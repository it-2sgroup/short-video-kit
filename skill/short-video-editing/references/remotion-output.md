# Remotion Output

The kit renders with a data-driven Remotion project: `assets/remotion-template`. The edit plan is
compiled to `project.json`; one composition (`Short`) renders any video from it. Nobody edits React
code to make a video — changing a video means changing the plan. The same `project.json` also renders with
HyperFrames (Apache-2.0, no seat count): `hyperframes-flow.md`.

---

## Licence — read before building

Remotion is **source-available, not open source**. Its `LICENSE.md` grants the free licence to
*"an individual"* or *"a for-profit organization with up to 3 employees"*. Above that a Company
License is **$25/month per seat**, a seat being *"per person who writes Remotion code themselves or
using agentic coding tools"* — an AI agent writing Remotion code still consumes a seat. Confirm the
headcount before building; if it is over three and nobody has a seat, say so. Sources:
`remotion.dev/license`, `remotion.dev/docs/license/faq`.

---

## Pipeline

```bash
# 1. Scaffold once per batch: the playbook's theme, corrected and graded proxies
#    (ask before --install: it downloads npm packages + Chromium)
python scripts/new_remotion_project.py ~/renders/batch --playbook <id> --install --proxies "/path/to/raw clips"
# proxies are 1620x2880 by default so camera moves up to ~1.5x stay sharp (--proxy-height 1920 = fast drafts;
# --slowmo keeps 60 fps sources at 60 for 0.5x slow motion)

# 2. Sound into public/audio (SKILL.md step 3)
python scripts/process_audio.py voice voice.mp3 --out ~/renders/batch/public/audio/v1.wav
python scripts/process_audio.py music track.mp3 --out ~/renders/batch/public/audio/music.wav
python scripts/align_captions.py ~/renders/batch/public/audio/v1.wav --script script.txt --out captions.srt --words-out words.json

# 3. Compile the plan
python scripts/plan_to_project.py edit-plan.md --out ~/renders/batch/v1.json \
    --voice audio/v1.wav --music audio/music.wav --captions captions.srt --words words.json \
    --auto-camera --analysis analysis.json --auto-sfx [--platform reels-ad]

# 4. Look before rendering, then render
cd ~/renders/batch
npx remotion still src/index.ts Short out/check.png --frame=45 --props=v1.json
npx remotion render src/index.ts Short out/v1.mp4 --props=v1.json --codec=h264 --crf=18

# 5. Master the sound, look at the result (scene middles + every cut), check durations
python <skill>/scripts/process_audio.py master out/v1.mp4 --out out/v1_final.mp4 --phone
python <skill>/scripts/contact_sheet.py out/v1_final.mp4 --project v1.json --out out/sheet.png
```

`plan_to_project.py` lists any clip, voice, music or sound-effect file the project needs that is not yet
under `public/` (clips, `images/` for the `image` component, audio, sound effects) when `--out` sits
inside the render project, so a missing asset shows up before the render. The scaffold puts the sound effects in `public/sfx/` (recorded CC0 files from `assets/sfx/` plus
the ones `make_sfx.py` synthesizes).

`npm run studio` opens Remotion Studio with `project.example.json`, a footage-free gallery of every
component — the quickest way to see what each style looks like.

---

## Template layout

| Path | Role |
|---|---|
| `src/project.ts` | The input contract (`Project`, `Scene` with `speed`/`ramp`, `Overlay`, `CaptionStyle`, `layout`, …). |
| `src/theme.ts` | Design tokens: fonts, three palettes (`cool`, `warm`, `luxe`), layout zones, caption band per layout (feed, reels-ad), cart point, info-graphic sizes, motion curves, camera limits. Change the look here. |
| `src/engine/timeline.ts` | Scene layout with transitions centred on cuts; source re-timing for `speed` and `ramp`; dB helper. |
| `src/engine/camera.ts` | Push / pull / pan / hold + keyword punches, perceptual scale. |
| `src/engine/transitions.tsx` | Transition registry (built-ins + `zoomThrough`, `blurDissolve`, `whip`). |
| `src/engine/audio.tsx` | Voice, ducked music, SFX — outside the transitions so they never shift. |
| `src/engine/Short.tsx` | The composition; a ramped scene re-times its clip frame by frame inside `<Freeze>`, a constant speed uses `playbackRate`. |
| `src/components/text/` | `Title` (5 styles), `Captions` (karaoke / pop / plain), text primitives. |
| `src/components/graphics/` | Callout, CheckList, Step, Price, CartPointer, Highlight, Sticker, Magnifier, Thumbs, Compare, ImageCard (`image`), Ranking, Progress, LowerThird; `Info.tsx`: Specs, Pin, Label, Stat, Chart. |
| `src/components/registry.tsx` | Component names used in `project.json`; unknown names throw. |

To add a component: write it under `components/graphics/` taking `{ov, dur, instant}`, read its
content from `ov.props`, take every colour/size/curve from `theme.ts`, register it, and document
its content keys in `layout-and-motion-graphics.md`, and add it to the `components.use` of the
playbooks it serves (`playbook.py check` fails on a component no playbook uses). No video text in code.

A render project is a **copy** of the template. After changing the template, bring existing projects
along with `python scripts/new_remotion_project.py <render dir> --update` (replaces `src/` and the
config files; keeps `public/`, `node_modules/` and your `*.json` projects).

---

## Rules that keep renders correct

These follow Remotion's own agent rules (`remotion-dev/skills`, `remotion-best-practices`) [D]:

- Everything animates from `useCurrentFrame()`. No CSS transitions/animations, no `Date.now()`,
  no unseeded randomness.
- Footage with `<OffthreadVideo>`; transform a **wrapper**, never the video element.
- Scale animations use `interpolate(..., {output: "perceptual-scale"})`.
- Fonts through `@remotion/google-fonts` with explicit weights and subsets (`latin` +
  `vietnamese`), so no frame renders in a fallback face.
- Assets in `public/`, referenced with `staticFile()`; no network fetches at render time.
- Shader transitions and light leaks need `Config.setChromiumOpenGlRenderer("angle")` (set in
  `remotion.config.ts`).
- A card scene (`Layout card|expand`) is rendered inside a transparent scene over the grid; its camera math is done on the full 1080x1920 frame and the
  frame is scaled into the card, so `Camera` cells mean the same thing in both layouts. Footage-only colour (`plan_to_project.py --look 1.12,1.05,1.03`) is a CSS
  filter on the footage, never on graphics.
- Many 2880-tall proxies read by many workers at once can fail with `No frame found at position`: render with `--concurrency=5` (8 failed on a 63 s card-heavy
  video, 5 passed). `cardSlide` and `cardSwirl` render each shot up to three times during the transition, which is why.
- Scene extras: `flash` (white silhouette PNGs on listed frames), `face` (the head, for `faceGlow`). Project extras: `look`, `faceGlow`, `captionHighlight`,
  `captionKeywords`, `captionBands` (with `hide` and a per-band `highlight`). The silhouette matte is drawn inside the camera framing, so it matches the footage even
  while the camera pushes.
- Render a still at every transition before a full render; a full 35 s render takes ~2 minutes on
  the reference Windows machine, a still a few seconds.

---

## Where the boundary with ffmpeg sits

| Job | Tool |
|---|---|
| Tone-mapping, framing, denoise, stabilisation, levelling, white balance, exposure, grade, fps | **ffmpeg** via `prepare_footage.py` (the proxies) |
| Measuring footage (light, cast, noise, shake, motion, speech) | **ffmpeg** via `inspect_footage.py --measure` |
| Trimming a voice, jump-cutting a talking head | **ffmpeg** via `trim_voice.py` (`silencedetect`, `atrim` + `concat`) |
| Voice cleanup, music levelling, the final loudness master | **ffmpeg** via `process_audio.py` |
| Beat detection for music-driven cuts | **ffmpeg** decode + Python in `suggest_cuts.py --music` |
| Looking at footage or at the render | **ffmpeg** via `contact_sheet.py` |
| Scene cuts, speed and ramps, transitions, camera, graphics, captions, the mix | **Remotion** |
| Handing to a human editor | `edit-plan.md` + `captions.srt` → CapCut / Premiere / DaVinci |
