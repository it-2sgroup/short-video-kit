# Footage Ingest — planning an edit around clips that already exist

Most of this skill describes planning a video that will be shot to order. This file covers the
other case: someone hands over a folder of raw clips and wants a finished short out of them.

The order matters. Writing the timeline first and then discovering the footage cannot support it
wastes the plan — and the usual failure is not dramatic, it is a plan that calls for a locked
macro shot when every clip is handheld, or a 3-second hold on a moment that only lasts 1.2
seconds in the source.

---

## 1. Inspect before planning

```bash
python scripts/inspect_footage.py /path/to/clips --log
```

This reports duration, resolution, orientation, frame rate and whether each clip carries audio,
then flags the problems that are expensive to find late:

| Flag | Why it matters |
|---|---|
| **LANDSCAPE clips** | A 1920x1080 clip in a 1080x1920 frame either gets cropped to ~56% of its width, or needs a blurred-fill backdrop. Decide which before building the timeline, because cropping changes what is actually visible in the shot. |
| **No audio track** | No diegetic sound — no pouring, no fabric, no room tone. The demo leans entirely on voiceover, and `audio-and-music.md`'s advice about keeping real demo audio audible does not apply. |
| **Mixed frame rates / resolutions** | Conform before cutting, or the render inherits judder and scaling artefacts. |
| **Total source under ~45s** | There is almost no room to choose moments. Expect to reuse shots via punch-ins (which is legitimate — see rule 2) or to ask for pickups. |

`--log` prints a blank shot-log table to fill in.

A clip shot on a phone may carry rotation metadata rather than rotated pixels. The script accounts
for this and marks it; do not conclude such a clip needs reframing just because the raw width
exceeds the height.

---

## 2. Build a shot log

Watch the clips and record where the usable moments actually sit. One row per usable moment, not
one row per file — a 40-second clip often contains three separate beats worth cutting to.

| Clip | In | Out | What happens | Usable for |
|------|----|-----|--------------|------------|
| clip_03.mp4 | 12.4 | 16.0 | Pink bottle poured directly on the collar stain | demo |
| clip_03.mp4 | 28.1 | 31.5 | Hand presses the liquid into the fabric | demo |
| clip_05.mp4 | 2.0 | 5.2 | Shirt lifted from basin, stain visibly faded | reveal |

**In/Out are source timecodes. Start/End in the edit plan are timeline positions.** They are
different numbers and conflating them is the most common error when working from a shot log —
a scene at timeline 10.0–12.2s might be sourced from clip_03 at 12.4–14.6s.

While logging, note specifically:
- **Where the transformation is visible.** That decides the hook (see `hook-library.md`).
- **Whether any before/after pair shares framing and lighting.** If the "after" is brighter or
  reframed, that pair cannot be cut together — see `platform-specs.md` §2. Reshoot the after at
  the original time of day rather than colour-matching in post.
- **Any unusable stretch**: blown highlights, the creator talking off-script, a competitor's
  product in frame, a visible brand that is not the client's.

---

## 3. Carry the source into the plan

Extend the scene table in `assets/edit-plan-template.md` with two columns so the plan is cuttable
rather than merely descriptive:

| # | Start | End | Source | In | Type | Shot | On-screen text | Audio |
|---|-------|-----|--------|----|------|------|----------------|-------|
| 1 | 0.0 | 1.4 | clip_05.mp4 | 2.0 | HOOK | Shirt lifted, stain faded | Cùng 1 cái áo | VO mid-sentence |

`pacing_checker.py` ignores the extra columns, so the hard rules still validate.

An editor who receives a plan without source references has to re-watch everything and guess.
With them, the plan is a cut list.

---

## 4. Emit an ffmpeg cut list

When the video will be assembled by script rather than by hand, generate the segment extractions
from the shot log:

```bash
# one segment per scene — -ss before -i seeks fast; re-encode so cuts land on exact frames
ffmpeg -ss 12.4 -i clip_03.mp4 -t 2.2 -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" \
       -r 30 -c:v libx264 -crf 18 -an seg_06.mp4
```

Then concatenate:

```bash
printf "file 'seg_01.mp4'\nfile 'seg_02.mp4'\n" > list.txt
ffmpeg -f concat -safe 0 -i list.txt -c copy silent_cut.mp4
```

Three things that bite here:
- **`-c copy` on the extraction step cuts only on keyframes**, so segments drift by up to a second
  from the in-point you asked for. Re-encode the segments; copy only at the concat step, where
  every input already shares a codec and timebase.
- **`-an` on the segments** drops source audio deliberately when the voiceover is a separate
  track. Leave it off when you want the diegetic sound.
- **The crop filter above fills the frame** from a landscape source, discarding the sides. For a
  blurred-fill treatment instead, build it in Remotion — see `remotion-output.md`.

---

## 5. When the footage cannot support the plan

Say so plainly rather than delivering a plan that cannot be cut. The useful response names the
specific gap and the cheapest fix:

> The brief calls for showing colour-safety on coloured fabric, but all five clips are white
> shirts. Either cut that beat, or shoot a 10-second pickup — one coloured item dropped into the
> same basin, same tripod, same light. The pickup is about two minutes of shooting.

A missing shot is a shooting problem with a known cost. A plan that pretends the shot exists is an
editing problem discovered at the timeline, which is more expensive.
