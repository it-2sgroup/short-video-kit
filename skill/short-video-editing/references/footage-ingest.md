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
python scripts/inspect_footage.py /path/to/clips --log --measure --json analysis.json
```

This reports duration, resolution, orientation, frame rate, audio and HDR, and with `--measure` the
light, colour cast, noise, shake, camera travel and probable speech of each clip, with the corrections
`prepare_footage.py` will apply (`image-processing.md`) and a summary `playbook.py suggest` uses to
guess the genre. It flags the problems that are expensive to find late:

| Flag | Why it matters |
|---|---|
| **LANDSCAPE clips** | A 1920x1080 clip in a 1080x1920 frame either gets cropped to ~56% of its width, or needs a blurred-fill backdrop. Decide which before building the timeline, because cropping changes what is actually visible in the shot. |
| **No audio track** | No diegetic sound — no pouring, no fabric, no room tone. The demo leans entirely on voiceover, and `audio-and-music.md`'s advice about keeping real demo audio audible does not apply. |
| **Mixed frame rates / resolutions** | Conform before cutting, or the render inherits judder and scaling artefacts. |
| **HDR clips** | iPhone HLG looks washed out if rendered directly: only render from the tone-mapped proxies. |
| **Total source under ~45s** | There is almost no room to choose moments. Expect to make several scenes from one take with punch-ins (legitimate) or to ask for pickups. |

`--log` prints a blank shot-log table to fill in. The numbers do not show what is *in* the clips, so
also run `python scripts/contact_sheet.py /path/to/clips --out clips.png` and open the PNG(s): one row
per clip, frames evenly spaced, with the timestamps printed. Build the shot log from that.

A clip shot on a phone may carry rotation metadata rather than rotated pixels. The script accounts
for this and marks it; do not conclude such a clip needs reframing just because the raw width
exceeds the height.

---

## 1b. Budget the footage across ALL the videos it has to feed

Raw footage is often shot once and used for many scripts (the same products cut into KB1, KB2, KB3…;
the same apartment for a sale video and a rental video). Treat it as a budget:

1. **Count the demand first, then the supply.** How many videos are waiting? Ask if unknown. A video
   uses about `runtime × average speed + scenes × 0.5 s` of fresh footage: a 36 s product demo of 12
   scenes needs ~42 s, a 40 s property tour with two `ramp 1>2>1` scenes a little more, a jump-cut
   talking head only its own take. Total usable seconds ÷ that is the most videos the footage carries
   without reuse (587 s of product footage → about 14). If the demand is larger, **stop and report the
   shortfall** (`policy.md` §4.1 has the table for 200–300 videos); reshuffling clips into "new"
   videos is the repetitive-content pattern TikTok Shop and Instagram penalise.
2. **Catalogue by kind of moment, not by file.** Kinds are words for what the shot shows, and each
   playbook's camera knows its own (`camera-moves.md`): product-demo `STAIN`, `POUR`, `SOAK`, `LIFT`,
   `PRODUCT`; real-estate `EXTERIOR`, `ROOM`, `WALK`, `DETAIL`, `VIEW`; food `MACRO`, `POUR`, `TABLE`,
   `FACE`… Note which are scarce: in the SAIZA product footage the hero shot existed in one 13 s clip
   while clear BEFORE/AFTER moments existed in a dozen.
3. **Allocate before cutting.** Give every video its own source ranges. Rotate which clips a video
   leans on so the videos do not look alike (video 1 opens on socks, video 2 on a tee, video 3 on a
   shirt) while the scarce shots go where they carry the most weight.
4. **Never reuse inside a video.** Two scenes from overlapping ranges of one clip read as a repeat even
   with different crops. Keep at least 0.5s between used ranges of the same clip (transitions borrow
   ~0.2s of handle on each side).
5. **Keep a ledger.** Each plan's scene table already carries Source and In, so the plans are the
   ledger. Run:

   ```bash
   python scripts/footage_overlap_checker.py plans/kb7.md plans/kb4.md --clips /path/to/clips
   ```

   It fails on any overlap within or between plans and prints the free ranges left per clip. Plan
   the next video from that list. Run it every time a plan changes. It reads only the Scenes
   tables, so keep every plan file (a `project.json` cannot rebuild one) and name them all; it does
   not see clips pulled in by `thumbs` or `magnifier` overlays, so draw those from ranges the same
   video already shows.
   **Let the tools do the allocation.** Write a *shot library* (`assets/shot-library.example.json`): one
   span per stretch of a clip where one kind of shot holds (`kind`; `focus`: where the action is, 0–1;
   `size`: wide / medium / close; optional `move`: a camera cell). Then per video:

   ```bash
   python scripts/suggest_cuts.py words.json --playbook product-demo --json --prefer 8.4,15.2 > cuts.json   # or --music
   python scripts/playbook.py skeleton product-demo --cuts cuts.json > kb7/edit-plan.md
   python scripts/plan_scenes.py --library library.json --plan kb7/edit-plan.md \
       --kinds "STAIN@IMG_0329,LIFT@IMG_0329,SOAK|POUR,..." \
       --used kb4/edit-plan.md --reserve IMG_0330:STAIN,IMG_0330:LIFT --seed 3
   ```

   `plan_scenes.py` fills Source/In so no range is used twice (0.5 s kept between; a scene at 2x needs
   twice its length), keeps the skeleton's Type, Speed and Transition, chooses a content-aware Camera
   from the span and the playbook, and exits 1 when a scene cannot be filled: that is the signal the
   footage has run out (`ANY` at the end of a `--kinds` list accepts any leftover kind). `--reserve`
   keeps the before/after pair of a later video free; `KIND@CLIP` pins a scene to one clip so a
   before/after pair shows the same item. Run the overlap checker afterwards anyway.
6. **Say so when the budget runs out.** If the remaining footage cannot support another video without
   repeats, tell the user and name what to shoot (pickups), rather than quietly repeating shots.

---

## 2. Build a shot log

Watch the clips and record where the usable moments actually sit. One row per usable moment, not
one row per file — a 40-second clip often contains three separate beats worth cutting to.

| Clip | In | Out | What happens | Usable for |
|------|----|-----|--------------|------------|
| clip_03.mp4 | 12.4 | 16.0 | Pink bottle poured directly on the collar stain | DEMO (POUR) |
| clip_05.mp4 | 2.0 | 5.2 | Shirt lifted from basin, stain visibly faded | REVEAL (LIFT) |
| villa_02.mov | 0.0 | 9.5 | Gimbal walk from the door into the living room, constant speed | ARRIVAL (WALK, ramp) |
| villa_02.mov | 11.0 | 14.0 | Pool from the balcony, sunset | HOOK / FEATURE (VIEW) |

**In/Out are source timecodes. Start/End in the edit plan are timeline positions.** They are
different numbers and conflating them is the most common error when working from a shot log —
a scene at timeline 10.0–12.2s might be sourced from clip_03 at 12.4–14.6s.

While logging, note specifically:
- **Where the transformation is visible.** That decides the hook (see `hook-library.md`).
- **Whether any before/after pair shares framing and lighting.** If the "after" is brighter or
  reframed, that pair cannot be cut together — see `claims-and-compliance.md` §3. Reshoot the after at
  the original time of day rather than colour-matching in post.
- **Any unusable stretch**: blown highlights, the creator talking off-script, a competitor's
  product in frame, a visible brand that is not the client's.

---

## 3. Carry the source into the plan

The Scenes table (`assets/edit-plan-template.md`) has Source and In for every scene, so the plan is a
cut list, not a description: an editor (or `plan_to_project.py`) needs nothing else to find the
footage. `pacing_checker.py` ignores the extra columns. A human editor gets the plan and `captions.srt`.

---

## 4. When the footage cannot support the plan

Say so plainly rather than delivering a plan that cannot be cut. The useful response names the
specific gap and the cheapest fix:

> The brief calls for showing colour-safety on coloured fabric, but all five clips are white
> shirts. Either cut that beat, or shoot a 10-second pickup — one coloured item dropped into the
> same basin, same tripod, same light. The pickup is about two minutes of shooting.

A missing shot is a shooting problem with a known cost. A plan that pretends the shot exists is an
editing problem discovered at the timeline, which is more expensive.
