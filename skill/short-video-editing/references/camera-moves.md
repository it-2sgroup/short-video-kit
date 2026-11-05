# Virtual Camera

"Camera direction in the edit": moves made by scaling and translating the footage, so a locked phone
take never looks static. Implemented in `assets/remotion-template/src/engine/camera.ts`; set per
scene in the plan's **Camera** column, or let `plan_to_project.py --auto-camera` vary it.

---

## Moves

| Move | Plan syntax | Magnitude | Use |
|---|---|---|---|
| Slow push | `push` or `push 1.0>1.08` | +5–10% over the scene | Default life on any shot; builds attention [D: push-in grammar] |
| Pull-out reveal | `pull 1.16>1.0` | −10–25% | Show the whole result/product after a detail |
| Pan / reframe | `pan left 6%` | ≤ 8% of frame width | Fake a second angle inside a 4K source; follow the action |
| Hold | `hold` (≈1.03) | none | Reveals: let the result read, nothing fights it |
| Focus point | `… focus 0.45,0.55` | — | The point that stays put while scaling (product, face) |
| Keyword punch-in | Overlays row `punch` at `@"word"`, or `--punch-keywords` | ×1.12 over 6 frames, holds to the scene end | Emphasis on a product name, number, "boom" |

Camera accents on cuts (`+flash`, `+leak` in the Transition column) and speed ramps belong to
`transitions.md`.

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
7. **Don't stack moves**: no punch-in inside a transition window; no pan + big zoom at once.
8. **Resolution budget** [D, arithmetic]: total scale ≤ source px ÷ output px. 1080×1920 proxies
   soften past ~1.15; render from 2160×3840 proxies when a video needs punches above that.
   `theme.camera.maxScale` caps it.

---

## Rules for varying the camera (`--auto-camera`)

- Every shot gets a move; never the same move twice in a row (the pattern cycles push → tighter
  push → pull → pan left → push → pan right → pull).
- Change scale tier at least every 2–3 scenes: wide 1.0–1.07, medium 1.06–1.16.
- REVEAL scenes **hold**; CTA-CLOSE gets a calm push with room for the cart arrow.
- At most one punch per 3 s and 6 per video; none within 0.5 s of a cut (the cut already changes
  the frame); punches land 2 frames before the keyword.
- Snap zooms, dutch tilt and speed ramps are spice: ≤ 2 per video, and only with a reason.

Sources: StudioBinder (push-in grammar); Epidemic Sound / ShortGenius (Ken Burns, push to emphasise,
pull to reveal); CapCut/Submagic and Final Cut docs (ease keyframes; lengthen harsh moves); iart-ai
`short-form-video` (punch 1→1.12, cuts at uneven 2–4 s); Remotion `interpolate`, `spring`,
`motion-blur` docs; ProVideo Coalition (4K reframing headroom).
