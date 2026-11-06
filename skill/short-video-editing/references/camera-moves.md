# Virtual Camera

"Camera direction in the edit": moves made by scaling and translating the footage, so a locked phone
take never looks static. Implemented in `assets/remotion-template/src/engine/camera.ts`; set per
scene in the plan's **Camera** column, or let `plan_to_project.py --auto-camera` / `plan_scenes.py`
choose it from what the shot shows.

**A move that nobody notices is wasted.** On a phone, a 5% push is invisible. The camera has to be
*seen*: at least ~12% change of scale or ~8% of the frame in a pan, aimed at the action (the stain,
the pour, the lifted garment), with the shot size changing from scene to scene.

---

## Moves

| Move | Plan syntax | Magnitude | Use |
|---|---|---|---|
| Push-in | `push 1.22>1.46 focus 0.5,0.4` | +12–30% over the scene | Stains, pours: move toward the detail the voice talks about |
| Pull-out reveal | `pull 1.32>1.0 focus 0.5,0.45` | −20–35% | The lifted garment / result: start tight, open to the whole piece |
| Pan / reframe | `pan left 8% 1.2>1.32 focus …` | 8% of frame width with a small zoom | Fake a second angle on a soaking bowl; follow the action |
| Roll (lean) | `… roll 1.0>-1.0` | ±1–2° | A handheld lean that makes a static shot feel like a new angle; ≤ 1 scene in 4 |
| Hold | `hold` (≈1.03) | none | Reveals that must read, nothing fights it |
| Focus point | `… focus 0.45,0.55` | — | The point that stays put while scaling: aim it at the action, not the middle of the frame |
| Keyword punch-in | Overlays row `punch` at `@"word"`, or `--punch-keywords` | ×1.15 over 6 frames, holds to the scene end | Emphasis on a product name, number, "boom" |

Camera accents on cuts (`+flash`, `+leak` in the Transition column) and speed ramps belong to
`transitions.md`.

### Shot-size ladder

Alternate the size scene to scene, never two equal sizes in a row: **wide** (1.0–1.2, the whole bowl
and garment) → **medium** (1.2–1.35) → **close** (1.4–1.6, the stain or the pour). Each hook beat starts
on a different size than the one before. `plan_scenes.py` picks the move from the shot library's
`kind` (what the shot shows) and `size`:

| Kind | Move |
|---|---|
| STAIN | push 1.22>1.46 on the stain, sometimes with roll |
| POUR_* / PRODUCT | push 1.14>1.4 (wide: 1.0>1.22) |
| SOAK | slow pan 8% with a 1.2>1.32 zoom, left/right alternating |
| LIFT | pull 1.32>1.0 |

---

## Why it no longer feels "khựng" (jerky)

1. **Eased, never linear at the ends** [D]: `Easing.bezier(0.33, 0, 0.67, 1)` for moves; punches use
   a no-overshoot spring (`damping: 200`, 6 frames).
2. **Perceptual scale** [D]: `interpolate(..., {output: 'perceptual-scale'})` so equal time reads as
   equal zoom (a linear 1.0→1.1 visibly decelerates).
3. **One continuous move per scene, across its transition handles**: motion is evaluated over the
   whole sequence including the ±0.2 s the transition borrows, so nothing resets on a cut.
4. **A punch stays** until the scene ends. A punch that springs back reads as a glitch.
5. **Transform a wrapper, not the video** [D, HyperFrames/Remotion]: CSS `scale`/`translate` on a
   wrapper are sub-pixel; animating width/height/top snaps to whole pixels.
6. **Pans never reveal the edge**: scale is raised to at least `1 + 2 × pan`.
7. **Don't stack moves**: no punch-in inside a transition window; no pan + big zoom at once (a roll of
   1–2° is the exception: it costs a little extra scale, which the engine adds).
8. **Resolution budget** [D, arithmetic]: total scale ≤ source px ÷ output px. 1080×1920 proxies
   soften past ~1.15, so render from **1620×2880 proxies** (`new_remotion_project.py --proxies`, the
   default height is 2880): sharp to about ×1.5, and `theme.camera.maxScale` (1.7) caps it.
   Moves bigger than that need a closer shot, not a bigger zoom.

---

## Rules for varying the camera (`--auto-camera`, `plan_scenes.py`)

- Every shot gets a move; never the same move twice in a row.
- Aim `focus` at the action. A shot library records it per span (`focus`: the stain, the pour spout);
  a blank focus defaults to the centre and looks generic.
- Change the shot size at least every scene or two (ladder above); the hook's two beats differ in size.
- REVEAL scenes pull out or hold; CTA-CLOSE gets a calm push with room for the cart arrow.
- At most one punch per 3 s and 6 per video; none within 0.5 s of a cut (the cut already changes
  the frame); punches land 2 frames before the keyword.
- Roll, snap zooms and speed ramps are spice: ≤ 2 per video unless the roll is the only move on a
  static bowl, and only with a reason.

Sources: StudioBinder (push-in grammar); Epidemic Sound / ShortGenius (Ken Burns, push to emphasise,
pull to reveal); CapCut/Submagic and Final Cut docs (ease keyframes; lengthen harsh moves); iart-ai
`short-form-video` (punch 1→1.12, cuts at uneven 2–4 s); Remotion `interpolate`, `spring`,
`motion-blur` docs; ProVideo Coalition (4K reframing headroom).
