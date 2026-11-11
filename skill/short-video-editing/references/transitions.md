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
| `cardSlide [right]` | 10 | Card layout: the old card slides off with two fading copies behind it, the next card slides in | Between card scenes over the animated grid; ~0.8-1.5 s per card; also leaves a full-frame shot for the first card |
| `cardSwirl` | 16 | The incoming full-frame shot arrives as a stack of tilted cards that straighten into the frame; the old shot dims and sinks | The hero entrance after a card sequence (a new section: the offer) |
| `cut` | 0 | Hard cut | Deliberate punch on an emphasis word |

Accents centred on a cut, not changing timing: append `+flash` (white flash, peak 0.55) or `+leak`
(`@remotion/light-leaks`, 0.6 opacity, screen blend). Use at most two per video.

**The playbook chooses** (`transitions` in `playbooks/<id>.json`): a `same` list within a beat, a
`change` list when the beat changes, `into` for named beats (into a REVEAL, into the SPECS), and a cap on
accents. `playbook.py skeleton` and `plan_scenes.py` write those cells; change them by hand where the
footage asks for something else. The families per genre [C]:

| Playbooks | Dominant | On a change | Never |
|---|---|---|---|
| product-demo, tutorial | `fade`, `slide`, `blurDissolve` (soft, ~0.4 s) | `slide up`, `wipe`, `zoomThrough +flash` | hard cuts between unrelated clips (client: *"bị tách rời"*) |
| real-estate | `cut` on the beat, `fade 10f` | `whip` in the walking direction, `slide` past a door frame | shader gimmicks |
| talking-head | `cut` (jump cuts with a new framing) | `pushCut` | anything decorative |
| talking-head:agency | `cut` (jump cuts), `cardSlide` between cards | `zoomThrough +leak`, `crossZoom`, `whip`, `cardSwirl` | more than ~2 shader or leak accents |
| food-fnb, fashion-beauty, montage-recap, promo-sale | `cut` on the beat | `whip`, `zoomThrough`, `pushCut`, rarely `crossZoom` | dissolves between outfits; spin, glitch, star-wipe packs |

Use 3–4 transition types per video at most, energetic ones only on section boundaries. Never spin,
glitch or star-wipe packs: they read as templates and cheapen the subject.

### When the client says "chuyển cảnh chưa mượt" (product demos)

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
on this kit's Windows machine (Nov 2026): `crossZoom` and `LightLeak` render correctly with `angle`.
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
