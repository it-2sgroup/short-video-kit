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
| `whip [dir]` | 9 | A velocity-matched pan: both shots travel on one curve, smeared along the axis of travel by a directional blur (SVG, not a CSS blur) and a small rolling-shutter skew | Topic switch; ≤ 2 per video, with a whoosh |
| `pushCut` | 11 | Hard cut + punch-in + 2-frame flash [D, v4.0.500] | TikTok-native emphasis beat |
| `iris` | 18 | Circle opening from the centre | Hero/product reveal |
| `flip [dir]` | 16 | 3D card flip | Rarely; comparisons |
| `crossZoom` | 16 | WebGL radial zoom blur | Big reveal; WebGL (see "Shader presentations" below) |
| `cardSlide [right]` | 10 | Card layout: the old card slides off with two fading copies behind it, the next card slides in | Between card scenes over the animated grid; ~0.8-1.5 s per card; also leaves a full-frame shot for the first card |
| `cardSwirl` | 16 | The incoming full-frame shot arrives as a stack of tilted cards that straighten into the frame; the old shot dims and sinks | The hero entrance after a card sequence (a new section: the offer) |
| `cut` | 0 | Hard cut | Deliberate punch on an emphasis word |
| `blinds` | 16 | Eight horizontal blinds widen until they meet | A graphic, clean wipe (tutorials, promos) |
| `diamond` | 16 | A diamond opens from the centre | A shape reveal of a product or a place |
| `doors` | 16 | The old shot splits down the middle and the halves slide apart, uncovering the new shot | A reveal, a "door opens" beat (HyperFrames shows the new shot through a widening slit; the halves do not move) |
| `glitchSlice` | 10 | Seven bands jump sideways with a hue split; old shot first half, new shot second | Tech, gaming, a hard topic switch; one per video (HyperFrames: a single jitter and hue split) |
| `spinZoom` | 14 | The old shot spins and grows into a blur, the new one spins in and settles | Energy, a fast montage; one per video |
| `filmBurn` | 20 | A warm overexposed burn through the cut | Food, fashion, nostalgia; two at most, never on a reveal |
| `zoomBlur` | 14 | A zoom blur between the shots | Energy, a rush toward the product |
| `dreamyZoom` | 18 | A soft glowing zoom with a gentle rotation | Beauty, travel, weddings |
| `linearBlur` | 14 | A directional blur dissolve | Motion, sport, a smear between two angles |
| `crosswarp` | 16 | The shots warp into each other | Liquid or fabric subjects, a morph feel |
| `zoomInOut` | 18 | Zoom out of the old shot, in to the new | A tunnel, "into the next topic" |
| `blurSlide [dir]` | 14 | A slide with built-in motion blur | A softer, more modern slide |
| `clockWipe` | 18 | A clock hand sweeps the new shot in | Time, schedules, countdowns |
| `ripple` | 18 | A water ripple from the centre | Water, drinks, calm |
| `burnDissolve` | 18 | A glowing burning edge eats the old shot | A dramatic reveal; rarely |
| `cube [dir]` | 16 | Two faces of a 3D cube | Rarely; a tech or "next side" beat |
| `bookFlip [dir]` | 20 | A page turn | Stories, albums, before/after of documents |
| `swap` | 18 | The two shots swap places in depth | Comparisons, two options |
| `inkBleed` | 20 | Ink drops grow from a few points, swell and merge into the new shot (an SVG goo mask with a torn edge; both renderers draw it) | Beauty, food, drinks, an organic reveal; once per video |
| `lumaWipe [dir]` | 16 | A noisy luma mask (a gradient from the side the new shot comes from, broken up by noise) thresholded by the progress: smoky, ragged wipe edge (both renderers) | A softer alternative to `wipe`; fabric, smoke, atmosphere |
| `cutCurve [dir]` | 12 | A hard cut hidden in a move: the old shot accelerates along the axis, the picture swaps at peak speed, the new shot carries the move on and settles; no blur, both shots scaled up while off centre (both renderers) | Hook to first scene, a beat on the voice, rhythm montages; the direction must match the camera move (`left` = the new shot comes from the right) |
| `glPixelate` | 14 | Square blocks grow to a peak in the middle and shrink away again; the swap is at the peak (GL shader, Remotion only) | Retro, gaming, a playful change of topic |
| `glDirectionalWarp [dir]` | 16 | A soft wipe whose edge waves, stretching the old shot along it (GL shader, Remotion only) | A fluid change of scene in the direction of the move |
| `glSwirl` | 18 | The picture twists around the centre, strongest mid-move, and untwists into the new shot (GL shader, Remotion only) | Dreamlike, a flashback, liquids; once per video |
| `glMosaic [dir]` | 18 | Squares open from the middle of every grid cell, starting on the side the new shot comes from (GL shader, Remotion only) | Tech, collections, a "grid of products" reveal |
| `glRgbSplit [dir]` | 12 | The red, green and blue channels dissolve at different times and slide apart, then snap together (GL shader, Remotion only) | An RGB glitch without hard edges: music beats, tech, fashion |
| `glRadialShutter` | 16 | A fan of spiral blades opens the new shot, like a camera shutter (GL shader, Remotion only) | A lens or "focus" beat, a product reveal |
| `glRipplePixel` | 18 | A pixelated ring spreads from the centre; the new shot inside, the old outside (GL shader, Remotion only) | A pulse on the beat, tech and sound subjects |
| `gridFlash` | 18 | A 3 x 3 grid: in a random order each cell goes flat cream for a frame, then shows the new shot; thin dark lines stay between cells; two cream frames close it (Remotion only) | Tech, a beat in a showreel, a product grid; see `transition-pack.md` |
| `cropPop` | 8 | The new shot, scaled down, pops open as a window low in the middle and grows to the full frame with an ease-out (Remotion only) | A run of cuts on the beat about a second apart ("frame click") |
| `cropNegative` | 8 | The same from a smaller window at the lower right of centre, an inverted black-and-white picture for the first half (Remotion only) | One punch accent per video |
| `flashWipe [dir]` | 12 | A cream band wider than the frame sweeps across; the picture swaps under it (Remotion only) | A "teleport": two takes from one locked tripod, the subject moved |
| `blackFlicker` | 14 | The picture flickers to black and back about five times while the shot changes; the frames beside a black one are dimmed (Remotion only) | Night, events, a drop in the music; keep it under three flashes a second |
| `zoomFade` | 16 | The old shot dips to black while growing; the new one fades up from black growing 90 % to 100 % (Remotion only) | The last transition of a sequence, a mood change |

Accents centred on a cut, not changing timing: append `+flash` (white flash, peak 0.55) or `+leak`
(`lightLeak` of `@remotion/effects`, 0.6 opacity, screen blend). Use at most two per video.

### Shader presentations (WebGL / HTML-in-canvas): `filmBurn zoomBlur dreamyZoom linearBlur crosswarp zoomInOut blurSlide ripple burnDissolve bookFlip swap crossZoom`

They ship with Remotion's `@remotion/transitions` (the same shaders as the GL Transitions project, MIT heritage) and need WebGL in headless Chrome.
`remotion.config.ts` and `stills.mjs` default to the software renderer (`swangle`), which works with or without a GPU; set `SVK_GL=angle` on a
machine with a GPU for the faster path. Without WebGL the render **throws** ("Failed to create WebGL2 context") instead of falling back: that is
the first thing to check when a render dies on a shader transition. The Studio preview shows a hard cut for these unless Chrome has
`chrome://flags/#canvas-draw-element` enabled; renders are not affected. HyperFrames draws all of them as a `fade` and says so in its report
(`project_to_hyperframes.py` lists them under "Remotion only"); `blinds`, `diamond`, `doors`, `glitchSlice`, `spinZoom`, `inkBleed`, `lumaWipe` and `cutCurve` are CSS/SVG and exist in both.
The six showreel transitions (`gridFlash`, `cropPop`, `cropNegative`, `flashWipe`, `blackFlicker`, `zoomFade`) are CSS and SVG, measured on two technique-breakdown videos and described frame by frame in `references/transition-pack.md`; HyperFrames draws a fade for them.
Each was rendered here as a still at mid-transition on a synthetic pair of clips (all 19 shipped names and the 10 kit-written ones below; `inkBleed`, `lumaWipe` and `cutCurve`
also through the HyperFrames page); nobody has judged them on real footage.

### Adding a GL transition (one `.glsl` file and one registry line)

`assets/remotion-template/src/engine/glTransitions.tsx` loads any transition written in the gl-transitions.com convention (GLSL ES: `vec4 transition(vec2 uv)`
reading `getFromColor(uv)`, `getToColor(uv)`, `progress` (0 = old shot, 1 = new) and `ratio` (width / height); uv origin bottom-left) and wraps it in
`makeHtmlInCanvasPresentation`. To add one: (1) write `shaders/<name>.glsl` with an `Author:` and `License:` header line (the kit's own start `short-video-kit` / MIT; a file taken
from gl-transitions.com keeps its own header, and say where it came from in a comment); parameters are `uniform float strength; // = 0.5` lines (float, int, bool, vec2..vec4,
default after `= `), and a `uniform vec2 direction;` receives the plan's direction as the side the new shot comes from (y up); (2) add one line `glName: name,` to `src/engine/glShaders.mjs`
(a plain `.mjs` on purpose: webpack reads the `with { type: "text" }` import itself, Remotion's esbuild step would strip it from a `.ts` file); (3) add `glName` to `TransitionType`
(`project.ts`) and its length to `DEFAULT_FRAMES` (`timeline.ts`); (4) add `glName` to `REMOTION_ONLY_TRANSITIONS` in `scripts/project_to_hyperframes.py`; (5) a card in `assets/techniques.json`
and a row above, then render a still at the middle of the transition on two different clips and look. Names start with `gl` and a capital letter (`glitchSlice` is a CSS transition).
Traps: the shaders run per pixel on 1080x1920 (software `swangle` is slow with many texture reads); the incoming and outgoing shots are rasterised, so cross-origin media is dropped
(the template serves proxies from `public/`, same origin); shaders written for `texture2D` or with extra sampler uniforms (a luma texture) need a loader change first.

**The playbook chooses** (`transitions` in `playbooks/<id>.json`): a `same` list within a beat, a
`change` list when the beat changes, `into` for named beats (into a REVEAL, into the SPECS), and a cap on
accents. `playbook.py skeleton` and `plan_scenes.py` write those cells; change them by hand where the
footage asks for something else. The families per genre [C]:

| Playbooks | Dominant | On a change | Never |
|---|---|---|---|
| product-demo, tutorial | `fade`, `slide`, `blurDissolve` (soft, ~0.4 s) | `slide up`, `wipe`, `zoomThrough +flash` | hard cuts between unrelated clips (they read as disconnected in a soft-style demo) |
| real-estate | `cut` on the beat, `fade 10f` | `whip` in the walking direction, `slide` past a door frame | shader gimmicks (`filmBurn` only if the light is warm) |
| talking-head | `cut` (jump cuts with a new framing) | `pushCut` | anything decorative |
| talking-head:agency | `cut` (jump cuts), `cardSlide` between cards | `zoomThrough +leak`, `crossZoom`, `whip`, `cardSwirl` | more than ~2 shader or leak accents |
| food-fnb, fashion-beauty, montage-recap, promo-sale | `cut` on the beat | `whip`, `zoomThrough`, `pushCut`, rarely `crossZoom` | dissolves between outfits; spin, glitch, star-wipe packs |

Use 3–4 transition types per video at most, energetic ones only on section boundaries. The spin, glitch and
shape-wipe transitions are in the library for the genres that want them; a pack of them in one video reads as a template
and cheapens the subject, so one of each at most.

### When a product-demo's transitions feel abrupt (Vietnamese feedback: "chuyển cảnh chưa mượt", the transitions are not smooth)

1. Check scene lengths first: 3–4 s outside the hook for product-demo. Cuts every 1.5–2 s are what read as jerky; no
   transition fixes that (`pacing_checker.py` warns under 3 s).
2. Make `fade` or `blurDissolve` the dominant type and lengthen it (`fade 18f`). Drop `whip`,
   `pushCut`, `crossZoom` and `+flash`; keep at most one `zoomThrough` at the hook → problem boundary.
3. Cut on a pause in the voice (`sync-and-timing.md`), so picture and speech change together.
4. Let the camera move continue through the cut instead of resetting it (`camera-moves.md`).
5. Re-render and look at the contact sheet, then play it: smoothness shows only in motion.

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
on Windows: `crossZoom` and `LightLeak` render correctly with `angle`.
The CSS ones (`fade`, `slide`, `wipe`, `iris`, `flip`, `pushCut`) and the three custom ones work
everywhere.

---

## Hits on a cut (HyperFrames renderer only)

`+shake`, `+glitch`, `+rgb`, `+pulse` after the transition in the plan's Transition cell: a decaying camera
shake, a torn glitch, an RGB channel split, a zoom pulse, over the first 8–14 frames after the cut. They are
CapCut-style accents, drawn only by the HyperFrames renderer (Remotion ignores them and the sync report says
so), spent like `+flash`: at most two per video, never on the reveal. Details and the other CapCut
techniques: `hyperframes-flow.md` §4 and `capcut-techniques.md` §4.

## Sound under transitions

`plan_to_project.py --auto-sfx` puts one sound on each moving transition (`slide`/`wipe` → swoosh,
`whip` → whip, `zoomThrough`/`flip` → whoosh, `pushCut` and `+flash` → thud), none on `fade` and
`blurDissolve`, and none across the reveal. The file starts before the cut so its peak lands on it.
Which sounds are licence-safe, the level and the timing rules: `sound-design.md`. Do not use meme
sounds (vine-boom and the like) in commercial TikTok Shop videos.

Sources: remotion.dev/docs/transitions (+ presentations, timings, custom presentations,
audio-transitions, html-in-canvas); remotion-dev/skills `transitions.md`; HyperFrames transition
recipes (whip 0.13–0.3 s, blur swap, dip).
