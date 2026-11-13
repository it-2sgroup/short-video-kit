# Reading the reference-video report (`analyze_reference.py`)

When the owner hands over a REFERENCE video, run

    python scripts/analyze_reference.py sample.mp4 --out ref/ --dense auto
    python scripts/analyze_reference.py sample.mp4 --out ref/ --dense auto --compare mine.mp4   # also analyses your recreation

and read `ref/report.md` first, `ref/report.json` for exact numbers, then **only** the evidence strips the report lists.
Needs numpy and ffmpeg; the camera needs libvidstab (`doctor.py` checks it). Nothing is downloaded and nothing leaves the machine.

**The rule that organises everything:** the tool measures WHEN and HOW MUCH; Claude reads the NAME from an image. Vision models are
weak at naming editing techniques from video, and a measurement is weak at geometry, so each side does what it is good at. A key
that depends on a guess carries `needs_look: true`. Say "measured" for numbers and "read from the strip" for names, and never
"listened" for sound (the tool cannot hear).

**Verified on synthetic input only.** Every threshold below was checked on clips built with ffmpeg whose answer is known (xfade
over two still pictures, a zoompan push, a pan with a speed change, a freeze, three colour-graded cards): the check is
in `selftest.sh` (group 16, the `analysis-test.sh` block). Nothing here has been tested on real footage, motion blur, heavy
compression, or an `ffmpeg` that has `drawtext`. Marked **[synthetic]** where it matters. Treat the first real reference as a test
of the tool: compare its numbers with what you see.

After the report, `python scripts/technique.py match ref/report.json` lists, for each thing measured (transition family, camera driver and ease,
handheld shake, speed ramp, the nearest kit grade), the cards that explain it, marks the ones whose name you must still read from the strip, and says
**NO CARD** where nothing in the catalogue does: that line is a new technique (`references/adding-techniques.md`). The mapping lives in each card's
`detect` field (`measure` = a path of this report, `signature` = the values that mean the card, `needs_look`).

## Keys of `report.json`

| key | what it is | measured or read |
|---|---|---|
| `shots[]` | `start end length enter edge centre camera speed`. A shot boundary is a hard cut OR the middle of a transition that changes the scene (so a crossfade edit is not one giant shot). `enter` says which. | measured |
| `shot_length` | count, median, shortest, longest, `cuts_per_minute` (hard cuts + scene-changing transitions) | measured |
| `transitions[]` | one row per motion run and per hard cut: `t kind frames seconds family direction confidence needs_look note features` | family measured, geometry read |
| `motion_runs[]` | the old list: 4+ frames above `--motion` (0.025). Kept for compatibility; `transitions[]` is the one to use | measured |
| `flashes[]` | seconds of a one-frame brightening that falls back within 6 frames | measured |
| `shots[i].camera` | zoom / pan curve, ease, shake, keyframes of one shot | measured, `unknown` when unreliable |
| `shots[i].speed` | velocity profile, ramp, identical-frame runs | freeze measured, ramp is a hypothesis |
| `grade` | `global`, `per_shot[]`, `nearest[]` (kit looks) | statistics measured, "nearest" indicative |
| `evidence[]` | one strip per unique observation: `file note occurrences tile_times` | read by Claude |
| `loudness` | LUFS, LRA, true peak (ebur128) | measured |
| `sheets`, `sheet_times` | every image written and the time of each tile | index |
| `ffmpeg` | `{drawtext, vidstab}`: what this build could do | |
| `read_by_claude` | the list of things the tool leaves to you | |

## Transitions (`transitions[]`)

Detection: a **run** is 4+ frames above `--motion` 0.025 (fast) or 6-45 frames above `--gradual` 0.010 (slow: a crossfade between
two different shots changes the picture by only 1-2 % per frame, below the old threshold, so it was invisible before). A run
longer than 1.5 s is never a transition (`content-motion`). A **cut** is a frame-to-frame jump above `--cut` 0.10 that its
neighbours do not share.

For a run, `A` is the frame two before it, `B` two after (inside the same shot), and the in-between frames `M` (the middle 60 %)
are compared with them. Features, all in `features`:

| feature | meaning | separates |
|---|---|---|
| `same_scene` | block-luma correlation of A and B, or "B is A shifted" (`pan_match` >= 0.5) | content-motion (>= 0.80) from a change of shot |
| `lum_min`, `lum_max` | darkest / brightest in-between frame against A and B | dip-to-black, dip-to-white |
| `blend_res` | residual of M against the best mix of A and B, over mean abs(A-B) | crossfade (< 0.06) |
| `bin_res` | how far every pixel is from being exactly A or exactly B | hard-edged masks (<= 0.10) |
| `coherence` | share of neighbouring pixels agreeing on A-or-B | hard-edged (>= 0.97) vs random (< 0.85) |
| `bin_res_shifted`, `shift_a`, `shift_b` | the same after allowing A and B each a displacement along x or y (share of the axis) | slide / cover / reveal (<= 0.15 with a shift >= 0.08) |
| `mask_move` | how the centre of the B-pixels moves | wipe direction |
| `drift` | how much A and B themselves change in the 3 frames beside the run, over mean abs(A-B) | confidence |

Families: `crossfade`, `dip-to-black`, `dip-to-white`, `dissolve` (random or pixel mask: noise dissolve and pixelise look
alike), `mask-wipe` + direction (the way the edge travels), `mask-iris` (a mask growing around a point: circle, radial, bars),
`slide` (both pictures move), `cover` (B slides over a still A), `reveal` (A slides off a still B) + direction of travel,
`content-motion` (same scene before and after: a camera move, animated text or sticker, NOT a transition), `unknown`.
Hard cuts: `hard-cut`, `flash-cut` (a bright frame inside the cut), `dip-cut` (a dark frame inside it).

`confidence` = `1 - 3*drift`, scaled by how far the deciding feature is from its threshold. `needs_look` is true for `unknown`,
`content-motion`, `dissolve`, `mask-wipe`, `mask-iris` (the geometry is not measured), any confidence under 0.6, and any
cut that is not plain. For those, open the `evidence/` strip or `dense_*.png` and say what you see ("circle opening from the
subject", "zoom blur", "whip pan").

**[synthetic]** correct family on all of: fade, fadeblack, fadewhite, dissolve, wipeleft (direction left), wipeup (direction up), slideleft,
slideright, coverleft, revealleft, for 0.6 s (18-frame) transitions between two still pictures. **Known failures:**
- circle/iris, diagonal, smooth, pixelize and zoom styles are not separated by these features; expect `unknown` or `mask-iris`.
- two shots that both move a lot during the transition: residuals are large, `unknown` with low confidence.
- a crossfade between two similar shots (change below 1 % per frame) is not detected at all.
- text or a sticker animating in over a still background is `content-motion`: the overlay is not measured (no OCR here).
- 18-frame transitions only were tested; 4-8 frame ones (the usual short edit) have fewer middle frames and are less certain.

## Camera (`shots[i].camera`)

From libvidstab's local-motion vectors on a 480 px copy (one pass for the whole video), fitted per frame as translation +
uniform scale + rotation with three passes of outlier trimming; frames inside scene-changing transitions are ignored and filled
by interpolation. Content zoom = 1 / fitted scale (vid.stab reports the camera, not the picture). `pan_x`, `pan_y` are the
CAMERA's travel as a share of the frame WIDTH (positive = camera moves right/down, so the picture moves left/up).

Keys: `quality` (`ok` / `unknown` with `reason`), `driver` (`zoom-in`, `zoom-out`, `pan-left|right|up|down`, `static`; a move
counts from 3 % zoom or 3 % of the width), `zoom_end` (1.00 at the start of the shot), `zoom_rate_per_s`, `pan_x`, `pan_y`,
`curve` (5 samples), `ease` (`linear`, `ease-in`, `ease-out`, `ease-in-out`, `irregular`; the lowest RMS against each shape, over 0.15 =
irregular), `shake.rms_pct` and `level` (`locked` < 0.08, `slight` < 0.3, `handheld`; levels are guesses, not calibrated),
`keyframes` (Ramer-Douglas-Peucker, <= 8 points), `vectors_per_frame`, `inliers`.

Gate: a frame needs 12+ vectors with 50 % agreeing, and half the frames of the shot must pass, otherwise the camera is `unknown`
(flat, blurred, dark or text-covered picture). **Never** quote a camera number whose quality is `unknown`.

**[synthetic]** a zoompan push z = 1 + 0.1 t over 3 s read `zoom-in`, `zoom_end` 1.32 (true 1.29, +2 %), `linear`; a pan read
`pan-right`. **Known failures:** a picture with a running counter or heavy overlay pollutes the field (nonsense zoom); a very
low-contrast picture gives no vectors; a zoom is physical OR digital, the tool cannot tell; shake levels untested on handheld.

## Speed and freezes (`shots[i].speed`)

- `frozen_runs[]`: 4+ identical frames (mean change under 0.0015). A title card or a still photo is "frozen" too, so look
  before calling it a freeze frame effect. **[synthetic]** a 0.8 s freeze read 0.84 s.
- `frame_repeat`: share of repeated frames when 25-80 % of them repeat (slow motion made by repeating frames, or a low-fps source).
- `ramp` (`speed-up`, `slow-down`, `none`), `ramp_factor`, `profile` (8 velocities, frame widths per second): the content's
  apparent velocity (camera translation + half the zoom rate) in the first third against the last, a factor of 2 or more.
  It is a **hypothesis**: the same curve is an eased camera move (compare `camera.ease`), and handheld or accelerating
  subjects look like a ramp. `needs_look` is always true for a ramp. **[synthetic]** a 1x then 3x pan read `speed-up` x3.5: vid.stab
  gives whole pixels at 480 px, so slow motion is quantised by up to 30 % and the factor is an estimate, not a measurement.

## Grade (`grade`)

Per shot (three frames outside transitions) and pooled: `lab_mean`, `lab_std` (CIE Lab), `luma` p1 / p50 / p99 (black lift,
white clip), `chroma`, `warmth_b` (mean b*, positive = yellow/warm), `tint_a`, `vignette` (corner luma / centre luma; under ~0.8
is consistent with a vignette, but a centred subject on a dark background does the same), `palette` (5 colours, k-means, fixed
seed). These describe the picture **as graded**: the ungraded original is unknown, so a scene that is warm by nature reads
as a warm grade.

`nearest[]`: each look in `assets/grades.json` is applied to a neutral card (SMPTE bars), its change in p1, p99, chroma and warmth
is measured, and the reference's black point, white point and warmth are matched against a typical-footage prior plus that
change. **Indicative, low confidence, `needs_look`**: use it to start from the nearest look and then compare stills side by
side; never say "the grade is X". **[synthetic]** warm / untouched / cold cards ordered correctly by `warmth_b` (19 / 3 / -12);
nothing else about `grade` is verified (vignette, nearest looks and palette are unchecked on real footage).

## Evidence packets (`evidence/ev*.png`, `evidence[]`)

One strip per UNIQUE observation (a transition family and length, a flash, a camera move kind and ease, a speed ramp, a
freeze), at most 16; `occurrences` lists every time it appears. Read them instead of the whole video. `dense_*.png` are the
same idea for time ranges (`--dense auto` picks half a second around every transition and flash).

**No `drawtext` in this ffmpeg?** (this machine: no libfreetype) `montage.py`, `contact_sheet.py` and the analyzer write clean tiles
and print an index: tiles read left to right, top to bottom, and `sheet_times` / `evidence[].tile_times` / the report's "Sheets to
look at" list give the time of each. With `drawtext` the time is burnt into each tile.

## `--compare mine.mp4` (`diff.md`)

Runs the same analysis on the recreation (`<out>/mine/`) and writes `diff.md`: cut count and rate, median and shortest shot,
transition families and mean run length, flashes, camera moves and the largest `zoom_end`, LUFS and true peak, grade
(warmth, chroma, p1, p99), transitions paired by time within 0.5 s, shots paired by order, and the five largest relative
differences. Fix those first, then put the two videos side by side at the same seconds with `montage.py`. A table cannot say
the recreation looks right: it says where it differs.

## What the report does NOT measure (say so)

Text, fonts and caption style (no OCR); what a graphic or sticker is; sound events (blind detection under a voice found 5 of 68
known cues: read the spectrograms); the geometry of iris and diagonal transitions; the ungraded original of a grade; motion
that stays below 1 % per frame. For these, name the technique from the evidence strips, add it to the kit only after its
construction is known from a primary source, and record the case in `docs/`.
