# Virtual Camera

"Camera direction in the edit": moves made by scaling and translating the footage, so a locked phone
take never looks static. Implemented in `assets/remotion-template/src/engine/camera.ts`; set per
scene in the plan's **Camera** column, or let `plan_to_project.py --auto-camera` / `plan_scenes.py`
choose it from what the shot shows.

**A move that nobody notices is wasted.** On a phone, a 5% push is invisible. On a locked shot the
camera has to be *seen*: at least ~12% change of scale or ~8% of the frame in a pan, aimed at the action
(the stain, the pour, the face, the dish), with the shot size changing from scene to scene.

**Footage that already moves is the exception.** A gimbal walk through a room, a pan across a market,
a handheld follow: a virtual move on top of a real one reads as a wobble. `inspect_footage.py
--measure` marks those clips `motion: high`, and `plan_to_project.py --auto-camera --analysis
analysis.json` gives them a near-static `hold 1.04`. The real-estate and montage playbooks keep their
patterns subtle (pans of 5–6%, pushes to ~1.12) for the same reason.

---

## Moves

| Move | Plan syntax | Magnitude | Use |
|---|---|---|---|
| Push-in | `push 1.22>1.46 focus 0.5,0.4` | +12–30% over the scene | Stains, pours: move toward the detail the voice talks about |
| Pull-out reveal | `pull 1.32>1.0 focus 0.5,0.45` | −20–35% | The lifted garment / result: start tight, open to the whole piece |
| Pan / reframe | `pan left 8% 1.2>1.32 focus …` | 8% of frame width with a small zoom | Fake a second angle on a soaking bowl; follow the action |
| Roll (lean) | `… roll 1.0>-1.0` | ±1–2° | A handheld lean that makes a static shot feel like a new angle; ≤ 1 scene in 4 |
| Hold | `hold` (≈1.04) or `hold 1.22 focus 0.5,0.35` | a fixed framing | Reveals that must read; footage that moves; talking-head jump cuts alternating wide (`hold 1.0`) and tight (`hold 1.22` on the face) |
| Focus point | `… focus 0.45,0.55` | — | The point that stays put while scaling: aim it at the action, not the middle of the frame |
| Keyframes | `keys 0=1.05 ; 0.5=1.38@0.4,0.5 out ; 1=1.38@0.4,0.5` | 2-4 named framings with an easing each | A scene with an action to follow or reveal (the Keyframes section below) |
| Keyword punch-in | Overlays row `punch` at `@"word"`, or `--punch-keywords` | ×1.15 over 6 frames, holds to the scene end | Emphasis on a product name, number, "boom" |

Camera accents on cuts (`+flash`, `+leak` in the Transition column) belong to `transitions.md`;
speed changes (the Speed column) to `cutting-and-pacing.md`.

### Shot-size ladder

Alternate the size scene to scene, never two equal sizes in a row: **wide** (1.0–1.2, the whole subject)
→ **medium** (1.2–1.35) → **close** (1.4–1.6, the detail the voice talks about). Each hook beat starts
on a different size than the one before. `plan_scenes.py` picks the move for a shot-library span from,
in order: the span's own `move`, the playbook's `camera.byKind` (the longest key the span's `kind`
starts with), then its `size` (wide push 1.0>1.2, medium push 1.08>1.28, close pull 1.3>1.06). Kinds
are words for the footage; each playbook knows its own:

| Playbook | Kinds and moves |
|---|---|
| product-demo | STAIN push 1.22>1.46 · POUR/PRODUCT push 1.14>1.4 · SOAK pan 8% 1.2>1.32 · LIFT pull 1.32>1.0 · WIDE push 1.0>1.2 |
| real-estate | EXTERIOR pan up 6% · ROOM pan right 6% · WALK hold 1.04 · DETAIL push 1.1>1.3 · VIEW pull 1.2>1.0 |
| food-fnb | MACRO push 1.15>1.4 · POUR push 1.1>1.3 · TABLE pan 8% · FACE hold 1.08 |
| talking-head | FACE hold 1.12 on the face · BROLL push 1.0>1.16 |
| tutorial | HANDS push 1.1>1.3 · SCREEN hold · WIDE push 1.0>1.16 |
| fashion-beauty | MIRROR hold · FACE push to 1.28 · TEXTURE push 1.15>1.4 |
| montage-recap | WIDE push 1.0>1.12 · CROWD hold · AERIAL hold |
| promo-sale | PACKSHOT push 1.05>1.25 · STORE pan 8% |

---

## Keyframes (the CapCut way: a framing at chosen moments)

CapCut's keyframe animation: put the playhead where a move starts, record a value (position, scale,
rotation, opacity), move on, change the value, and the editor interpolates; an easing shapes how the value
travels between two keys. Its own recipes: a slow zoom is two Scale keys seconds apart (Ken Burns), a
punch-in is two Scale keys close together, a fade is two Opacity keys [D: capcut.com keyframe-animation and
its PC keyframe guide]. A single push or pull per scene (above) is the two-key case. When a scene has
**something to follow or reveal**, name the framings yourself with `keys`:

```
| 4 | 6.80 | 9.66 | … | Camera: keys 0=1.1@0.45,0.45 ; 0.4=1.38@0.34,0.5 out ; 1=1.38@0.32,0.54 soft |
```

| Part | Meaning |
|---|---|
| `TIME=` | when the key is reached: a **fraction of the scene** (`0`, `0.4`, `1`) or **seconds from its start** (`1.2s`). Keys are sorted; before the first key the first framing holds, after the last the last holds |
| `ZOOM` | scale, 1.0 = the whole frame; never below 1.0 (the edge is never shown); capped at `theme.camera.maxScale` |
| `@X,Y` | the point of the **footage** the camera centres on, as fractions of the frame (`@0.32,0.54` = the glass). Default `@0.5,0.5`. Unlike `focus` (a transform origin) it moves the picture, and it is clamped so the frame edge stays covered: a point near the border simply stops at the border |
| `roll DEG` | optional lean in degrees at that key |
| ease word | the easing of the segment that **arrives at** this key (none = `inOut`) |

| Ease | Curve | Use |
|---|---|---|
| `inOut` (default) | `bezier(.33,0,.67,1)` | the standard slow-in slow-out move |
| `soft` | `bezier(.45,.05,.55,.95)` | a very gentle drift: a long settle on a calm shot |
| `out` | `bezier(0,0,.58,1)` | arriving at the target: fast start, long settle (a push to a product) |
| `in` | `bezier(.42,0,1,1)` | leaving: slow start, fast end (a pull-away) |
| `snap` | `bezier(.16,1,.3,1)` | a punch-in: nearly instant, then settles |
| `back` | `bezier(.34,1.4,.64,1)` | overshoots about 8 % and settles: **once per video, at most** |
| `linear` | straight | a mechanical move; rarely right on a phone |
| `hold` | a step | keeps the previous framing until the key's time, then jumps (a deliberate cut-in) |

Zoom between keys is eased in **area** (scale squared, the same `perceptual-scale` as a plain push, so equal
time reads as equal zoom); the centre and the roll move linearly. A **hold** is two keys with the same
framing (`0.4=1.05 ; 0.6=1.05`); `punches` (keyword punch-ins) still multiply on top.

**How to choose the keys** [C, with the animation principles of easing, anticipation and restraint]:

- **Follow the voice.** The framing at a key is what the voice names at that moment: the pour, the
  glass, the bag. Read the fractions off a still of the scene (`contact_sheet.py`, or a HyperFrames
  `snapshot`), and **look at the end of the move**: the subject must be inside the frame, not just near it.
- **Hold, then move, then hold.** A move of 0.4-1.2 s between two holds reads as intention; a move that
  never stops reads as drift. A reveal: `keys 0=1.05 ; 0.4=1.05 ; 0.6=1.38@x,y snap ; 1=1.38@x,y`.
- **Arrive with `out`, leave with `in`, drift with `soft`.** Ease-in and ease-out are what stops a move
  looking mechanical; do not use `linear`.
- **Two to four keys per scene.** More is a wobble. Key only the scenes that have an action; the rest keep
  the automatic move (`--auto-camera`).
- **Anticipation and settle are spice.** A small step back before a push, or one `back` on the closing
  push; sources on animation agree that overshoot used everywhere "goes against the purpose".
- **Never past the footage's own pixels.** The limit is the clip's resolution, not the proxy's: AI clips of
  720x1280 are already upscaled 1.5x to 1080x1920 and stay clean to about x1.3; 4K footage in 2880 px proxies
  holds x1.5. The sync report warns past 1.5.

Recipes:

| Want | Keys |
|---|---|
| Reveal the product on a word | `keys 0=1.05 ; 0.4=1.05 ; 0.6=1.38@0.42,0.56 snap ; 1=1.38@0.42,0.56` |
| Follow a pour | `keys 0=1.1@0.45,0.45 ; 0.4=1.38@0.34,0.5 out ; 1=1.38@0.32,0.54 soft` |
| Step-back reveal | `keys 0=1.38@0.5,0.2 ; 0.6=1.0 out ; 1=1.0` |
| Slow push to a face | `keys 0=1.0 ; 1=1.35@0.55,0.45 soft` |
| Look from product to face | `keys 0=1.3@0.3,0.55 ; 0.45=1.3@0.3,0.55 ; 0.8=1.3@0.6,0.35 inOut ; 1=1.3@0.6,0.35` |
| A closing push with a settle | `keys 0=1.0 ; 0.5=1.0 ; 0.75=1.2@0.5,0.52 back ; 1=1.2@0.5,0.52` |

Not keyed: the motion of overlays (each component moves by its own curve), colour, and volume (ducking is
computed from the voice). Both renderers read `keys` (`engine/camera.ts`, `hyperframes-template/kit.js`).

---

## Why it no longer feels "khựng" (jerky)

1. **Eased, never linear at the ends** [D]: `Easing.bezier(0.33, 0, 0.67, 1)` for moves; punches use
   a no-overshoot spring (`damping: 200`, 6 frames).
2. **Perceptual scale** [D, read from Remotion's source]: `interpolate(..., {output: 'perceptual-scale'})` eases the
   zoom in **area** (`√(a² + t(b² − a²))`, not geometrically) so equal time reads as equal zoom (a linear
   1.0→1.1 visibly decelerates).
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
- Named beats follow the playbook's `camera.byType` (product-demo: REVEAL pulls out, CTA-CLOSE a calm
  push with room for the cart arrow; real-estate: SPECS holds; talking-head: PAYOFF pushes in).
- At most one punch per 3 s and 6 per video; none within 0.5 s of a cut (the cut already changes
  the frame); punches land 2 frames before the keyword.
- Roll, snap zooms and speed ramps are spice: ≤ 2 per video unless the roll is the only move on a
  static shot, and only with a reason. Speed ramps are in `cutting-and-pacing.md`.

Sources: CapCut keyframe animation (capcut.com/tools/keyframe-animation) and its PC guide; Disney's principles as applied to
interface motion (easing first, anticipation and overshoot with restraint); StudioBinder (push-in grammar); Epidemic Sound / ShortGenius (Ken Burns, push to emphasise,
pull to reveal); CapCut/Submagic and Final Cut docs (ease keyframes; lengthen harsh moves); iart-ai
`short-form-video` (punch 1→1.12, cuts at uneven 2–4 s); Remotion `interpolate`, `spring`,
`motion-blur` docs; ProVideo Coalition (4K reframing headroom).
