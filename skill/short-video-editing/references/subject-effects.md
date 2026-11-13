# Subject effects: effects shaped by a matte of the person

A **matte** is a picture the size of the frame, white where the subject is and transparent elsewhere. With one, the picture
can treat the subject differently from the background: fill it with a colour that blinks, trace its outline, spotlight it,
leave it in colour while the rest goes grey, put words behind it, blur the background around it (rack focus), pop it forward a few percent. They all share one mechanism (`Scene.subject`, drawn by
`src/engine/Subject.tsx` inside the scene's camera framing, so it follows every push and pan) and one plan cell.

## Make the matte

```bash
python scripts/person_matte.py clip.mp4 --at 5.22 --frames 0,2,4 --out render/public/mattes/CLIP_A          # a blink: three matte frames
python scripts/person_matte.py clip.mp4 --at 5.22 --range 0-60 --step 3 --out render/public/mattes/CLIP_A   # a subject that moves: one every 3 frames
```

`--at` is the clip time of the planned cut (the scene's `In`); offsets are frames after it at `--fps`. It needs the 168 MB person
model (`./setup.sh --person-model`: ask before downloading). The matte is a first cut: soft-edged, slightly grown, hair approximate. It is
fine for a blink that lasts a few frames and for a ring or a halo; for a long spotlight on a moving subject, look at the stills.

## Ask for it in the plan: the Subject column

`[MODE] FRAMES @ MATTE [; color=..; width=..; opacity=..; every=N; text=..; size=..; y=..]`

| Cell | Means |
|---|---|
| `0,2,4 @ mattes/CLIP_A` | `fill` white, visible only on those frames after the cut (the silhouette flash: the speaker's outline blinks, then the video plays) |
| `fill 0,2,4,6 @ mattes/CLIP_A; color=#FFD23F` | the same in a colour (a blink in the brand colour) |
| `outline 0-45 @ mattes/CLIP_A; color=#FFFFFF; width=10` | a ring of 10 px around the subject for frames 0-45 (the matte at offset 0 is held) |
| `glow 0-60 @ mattes/CLIP_A; every=3; color=#FF3D6E; width=22` | a soft halo; a matte exists every 3 frames, the latest one at or before the frame is used |
| `dim 12-90 @ mattes/CLIP_A; opacity=0.65` | everything except the subject darkened: a spotlight |
| `colorpop 12-90 @ mattes/CLIP_A` | everything except the subject turned grey, the subject keeps its colour |
| `behind 0-80 @ mattes/CLIP_A; every=2; text=WORD / WORD; size=320; y=0.38; color=#FFFFFF` | big text between the footage and a cut-out copy of the subject: the person stands in front of the words (a matte for every frame the subject moves) |
| `blur 0-60 @ mattes/CLIP_A; every=3; from=0; width=24` | rack focus: the background (everything outside the matte) goes from `from` px of blur at the start of the window to `width` px at its end, eased; the subject stays sharp. `from=24; width=0` pulls it back sharp. One video decode (a backdrop filter) |
| `lift 0-45 @ mattes/CLIP_A; every=3; width=5; y=0.8; opacity=0.4` | depth pop: a cut-out copy of the subject grows 100 -> 105 % over the window above the unchanged picture, anchored at 80 % of the frame height, with a soft shadow that fades in with it |

The old column name `Flash` is still read as `Subject`. `plan_to_project.py` checks that every `PREFIX_<offset>.png` the cell needs exists
(`missing_assets`).

## Which effect, and where it fails

- **The blink** (`fill`) is a hook device: the first frames of a talking-head opener. Three to five frames, once per video. The sound that
  goes with it is the `flash` event of `sfx-map.json`.
- **`outline`, `glow`** read on any background but cost attention: use them on one beat, not across a whole video. A ring must never cross
  the face of another person; the matte's edge defines it.
- **`dim`, `colorpop`** turn the background into the second subject's absence: good for "look at this one" beats (a product in a hand, a person
  in a crowd). Both need the matte to follow a moving subject, or the subject's edge shows as a ghost.
- **`behind`** needs a **clean matte on every frame** and a subject that stays in front of the text: with a poor matte the cut-out flickers.
  Use it on a short, still beat and look at a still after the camera moves.
- **`blur`** halos: the blur samples the picture behind it, including the subject, so a soft glow of the subject's own colours spreads into the
  background near its edge (seen on the stills below); never blur a price or a claim. Use it on one beat, ending on the subject.
- **`lift`** shows best over a detailed background (the shadow and the shift of the details around the subject carry it); with a flat or
  striped background only the shadow reads. Freeze the footage on a sharp frame (`Speed: freeze-hit`, `cutting-and-pacing.md`) and the
  recipe is CapCut's "depth" look: `freeze-hit` + `lift` + `+flash` + a camera `keys` punch of 1.04-1.08.
- HyperFrames does not draw subject effects: `project_to_hyperframes.py` lists them as Remotion-only.
- A matte of one pose reused over a moving subject leaves the effect behind where the subject was: for any movement use `--range`.

## Adding a mode

`SubjectMode` in `src/project.ts`, a branch in `src/engine/Subject.tsx`, the name in `SUBJECT_MODES` of `scripts/plan_to_project.py`,
a card in `assets/techniques.json` and a row here; then `technique.py check` and a still in `selftest.sh --render` (`references/adding-techniques.md`).

## Measured on a real matte

**Not done.** The folder the footage was meant to come from (`source video/`) was empty, so no real person was matted. What was measured is the
geometry, on a synthetic matte (a head-and-shoulders silhouette with a 3 px feather) over colour bars, 1080x1920 stills with `gl=swangle`:

- `outline`: an even 10 px ring, no gap, none on the inside; `behind`: the words are hidden exactly where the silhouette is and drawn elsewhere.
- `blur` (0 -> 28 px over 60 frames): the subject stays sharp from the first frame, the background goes soft; a glow of the subject's colours spreads
  into the blurred background around the head (the halo above).
- `lift` (6 %): the grown copy covers its own original, the shadow falls round it and fades in with the growth.

What a real matte still has to answer, and nobody has looked at: the edge of hair and loose clothing (a first-cut matte is soft and slightly grown:
`blur` will show a fringe, `lift` a dark rim), ghost edges while the subject moves (one matte per `every=N` frames), and whether a 3-5 s window on a
phone clip stays clean. Look at `person_matte.py` stills with these four modes on a real clip before promising any of them to a client.
