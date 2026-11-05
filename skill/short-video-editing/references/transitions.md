# Transitions

Every scene boundary gets a deliberate transition, centred on the planned cut so the voiceover never
drifts. Implemented in `assets/remotion-template/src/engine/transitions.tsx` and `timeline.ts`; set
in the plan's **Transition** column. **[D]** documented, **[C]** convention.

---

## Catalogue

| Plan name | Frames (30 fps) | Look | Use |
|---|---|---|---|
| `fade` | 12 | Cross-dissolve | Default; calm beats, same subject |
| `slide [left/right/up/down]` | 14 | New shot pushes in | Change of beat (problem → product), lists |
| `wipe [dir]` | 14 | Soft-edged wipe | BEFORE → AFTER (label the time cut) |
| `zoomThrough` | 12 | Scale through the cut with a blur peak | Problem → product close-up, energy |
| `blurDissolve` | 14 | Dissolve through blur | Texture, lifestyle, gentle reveal |
| `whip [dir]` | 9 | Fast slide with motion blur | Topic switch; ≤ 2 per video, with a whoosh |
| `pushCut` | 11 | Hard cut + punch-in + 2-frame flash [D, v4.0.500] | TikTok-native emphasis beat |
| `iris` | 18 | Circle opening from the centre | Hero/product reveal |
| `flip [dir]` | 16 | 3D card flip | Rarely; comparisons |
| `crossZoom` | 16 | WebGL radial zoom blur | Big reveal; needs the `angle` GL renderer (set in `remotion.config.ts`) |
| `cut` | 0 | Hard cut | Deliberate punch on an emphasis word |

Accents centred on a cut, not changing timing: append `+flash` (white flash, peak 0.55) or `+leak`
(`@remotion/light-leaks`, 0.6 opacity, screen blend). Use at most two per video.

Cadence for the client's 3–4 s scenes [C]: 3–4 transition types per video, one dominant (usually
`fade`); energetic ones (`zoomThrough`, `whip`, `pushCut`) only on section boundaries
(hook → problem → product → proof → CTA). Never spin, glitch or star-wipe packs — they read as
templates and cheapen a product.

---

## The timing maths [D]

`<TransitionSeries>` overlaps scenes: total = Σ sequences − Σ transitions, and a transition may not
be longer than either neighbour. Feeding plan lengths straight in shortens the video and drifts the
audio. The template centres each transition `T` on the planned cut:

```
begin[k]  = cut[k] − T[k]/2          finish[k] = cut[k+1] + T[k+1]/2
duration[k] = finish[k] − begin[k]   startFrom = in·fps − T[k]/2   (pre-roll handle)
```

So each scene needs ~T/2 of spare footage before and after its planned range — the reason
`footage_overlap_checker.py` keeps 0.5 s between used ranges. Transitions longer than half of the
shorter neighbour are clamped. Voice, music and SFX live outside the series so overlaps never move
them.

---

## Shader transitions on Windows

`crossZoom`, `zoomBlur`, `blurSlide`, `dissolve` (a burn effect, not a cross-dissolve), `filmBurn`
and `@remotion/effects` run through HTML-in-canvas/WebGL [D]: Studio preview needs Chrome with
`chrome://flags/#canvas-draw-element`; renders need `--gl=angle` (`swangle` without a GPU). Verified
on this kit's Windows machine (Nov 2026): `crossZoom` and `LightLeak` render correctly with `angle`.
The CSS ones (`fade`, `slide`, `wipe`, `iris`, `flip`, `pushCut`) and the three custom ones work
everywhere.

---

## Sound under transitions

Whooshes sit 14–18 dB under the voice (`volumeDb: -16`), placed so the **peak** lands on the cut
(add an `sfx` row at the cut time minus the file's peak offset, typically 3–8 frames).
Licence-safe sources [D]: Mixkit SFX (free commercial, no attribution), Pixabay (free, no
redistribution of the raw files), Freesound **CC0 only**. Do not use meme sounds of unclear rights
(vine-boom etc.) in commercial TikTok Shop videos.

Sources: remotion.dev/docs/transitions (+ presentations, timings, custom presentations,
audio-transitions, html-in-canvas); remotion-dev/skills `transitions.md`; HyperFrames transition
recipes (whip 0.13–0.3 s, blur swap, dip); Mixkit/Pixabay licence pages.
