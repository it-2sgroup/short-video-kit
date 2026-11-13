# Technique backlog: researched, not built yet

Techniques found while researching (Nov 2026) that the kit does **not** have. Each line says what it looks like, the construction that
was found, the traps, and the licence. None of it is in `assets/techniques.json`, because a card exists only for what is built, documented
and tested (`references/adding-techniques.md`). Pick one from here, build it by that loop, and delete its line.
Tags: **[S]** read on a source page, **[L]** run on the ffmpeg build tested here, **[D]** derived, not rendered, **[U]** unverified.

## Transitions and motion

| Technique | Construction | Traps | Cost |
|---|---|---|---|
| **Match-cut assistant** | from the subject's size and centre at the last frame of A and the first frame of B (matte bounding box), emit camera `keys` so B lands at the same screen point and size: `z2 = z1·s1/s2`, `@x,y` so `c2` maps to `c1`, roll `r1−r2` [D] | a weak match reads as an error; stay under the 1.5x footage limit | M |
| **2.5D parallax from a still** (the two-layer version is built: the `lift` subject mode) | depth map to a displaced mesh, or three matte layers moving 1.0/1.03/1.06 [S: TensorFlow.js 3D photo]; Depth Anything V2 **Small** is Apache-2.0 (Base/Large are CC-BY-NC: not for ads) | model download needs a human yes; stretched edges at depth jumps | L |
| **Dolly zoom, rolling-shutter skew, true shutter motion blur** (echo/trail is built: `+echo`) | CSS 3D layers with `translateZ`; `skewX` tied to velocity; sub-frame sampling of the closed-form camera [S: HyperFrames blocks `camera-dolly-zoom`, `echo-trail`, `motion-blur`] | a flat clip gains nothing from a dolly zoom; N video copies are expensive | S-M each |
| **`@remotion/effects`** (about 90: glow, tear, tvSignalOff, lightLeak, filmBurn, lensBlur, shatter, pageTurn, venetianBlinds...) | per-element effects on `<Solid>`/`<HtmlInCanvas>`; `+leak` already uses `lightLeak()` from it (migrated off the deprecated `@remotion/light-leaks`; renders with `swangle`); the rest are not exposed [S] | HTML-in-canvas; no HyperFrames equivalent | S each |

## Text, light and colour

| Technique | Construction | Traps |
|---|---|---|
| **Halation, glow pulse** (light sweep, lens flare and anamorphic streak are built: `sweep`, `flare`, `streak`) | gradient bands and screen-blended discs with `mix-blend-mode`; wrap in `isolation:isolate`; bake constant glow/halation into the proxy (`split`, `curves`, `gblur`, `blend=screen` [L]) | one flare per video; CSS glow decodes the video twice |
| **Pre-made grain PNGs** | 6-8 grain frames made with ffmpeg `noise` cycled by frame: cheaper than a live `feTurbulence` per frame [D] | |
| **Skin check** | compare `signalstats` HUEMED of a cheek patch before and after a grade, accept a shift of 8 degrees or less [D: the threshold is a heuristic] | |

## Audio (nothing built: the sound bank, ducking and mastering already exist in `process_audio.py` and `sound-design.md`)

- **Sidechain ducking graph**: `[1:a][sc]sidechaincompress=threshold=0.02:ratio=8:attack=8:release=350` then `amix normalize=0`; measured 13.4 dB of ducking
  with a -18 dBFS-peak voice over a -24.9 dB bed at threshold 0.02, ratio 8 [L]. The threshold is linear and must follow the measured voice level.
- **Sound effect sync**: put the transient on the cut frame or at most one frame (33 ms) early; audio early beyond about 45 ms is noticeable
  (ITU BT.1359; EBU R37 allows 40 ms early, 60 ms late) [S: Wikipedia Audio-to-video synchronization]. Any lead belongs in the sound file's
  swell (`lead` in `sfx-map.json`), not in the placement.
- **SFX bus** at -12 to -18 dB against the voice, one hero hit near -6 dB; **silence before the drop** of 80-150 ms with 5-10 ms ramps.
- **Voice chain**: high-pass 80-100 Hz, -2 dB at 250 Hz, +2.5 dB at 3.5 kHz, 3:1 compression, de-ess [L syntax; the numbers are starting points].

## Reference analysis (see `references/reference-analysis.md` for what is built)

- **OCR of on-screen text** (RapidOCR, Apache-2.0, ONNX, `lang_type="vi"`; about 27 MB wheel plus model files) with text-event tracking, caption style
  extraction and font matching by rendering the string in the kit's fonts: needs a download and a human yes [U: not run here].
- **Sound events at known times** (transient z-scores per band; YAMNet labels as hints) and **beat alignment of the reference's cuts**: designs, not measurements.
- Do not add: TransNetV2 (PyTorch), madmom (NC models), VideoSubFinder (GPLv2), EasyOCR (PyTorch), hosted vision APIs (the client's video leaves the machine).
