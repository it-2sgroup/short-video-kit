# Cutting and Pacing — rhythm, cut types, beat cutting, speed ramps

How the timeline moves, for every genre. The numbers (scene lengths, runtime, hook) belong to the
playbooks and are checked by `pacing_checker.py`; the beat structure of each genre is in its
`playbooks/<id>.md`; the transition catalogue and its maths are in `transitions.md`.
**[S]** sourced, **[M]** measured, **[C]** craft convention.

---

## Why rhythm matters

Distribution on short-form platforms follows early retention: interactions and watching to the end are
what both TikTok and Instagram say they rank on (`platforms.md` §3). A static shot that runs too long
is an exit point. Every source agrees on the direction (more visual change holds attention), and none
of the precise percentages that circulate survive scrutiny, so the cadence is craft, encoded per genre:

| Playbook | Scenes (min–target–max) | Why that rhythm |
|---|---|---|
| product-demo | 2.5–3.3–4 s | data: past 4 s a static demo shot loses viewers; house style: with soft transitions, 1.5–2 s hard cuts read as jerky |
| tutorial | 2–3.3–4.5 s | each step must be followable |
| real-estate | 1.8–2.8–4 s | the walk is the motion; cut on bars of the music |
| talking-head | 1–3.2–5 s | jump cuts on pauses; a new framing every cut |
| food-fnb | 1.2–2.2–3.5 s | sensory shots are brief, the hero dish holds |
| fashion-beauty | 1–1.9–3.5 s | looks change on the beat |
| promo-sale | 1.2–2.2–3.5 s | the offer repeats, quickly |
| montage-recap | 0.5–1.2–3 s | the music's beats are the cuts |

The hook resolves by 3 s in every playbook; frame 0 is the thumbnail and is never empty.

**What counts as a visual change** (any of these resets the clock, so one camera setup can still make
several scenes): a new shot or angle · a punch-in or pull-out on the same take (the cheapest and most
underused) · a cutaway to B-roll · a substantial change of on-screen text or graphics · a speed ramp
that visibly alters the motion.

---

## Cut types and when they fit

Definitions [S: No Film School, Vimeo, Descript]; fit [C].

| Cut | What it is | Fits | Avoid |
|---|---|---|---|
| **Cut on action** | Cut mid-movement, the motion continues in the next shot | pours, prep, demos, walks | static shots |
| **Match cut** | Shape or motion carries across the cut | door → door (property), pose → pose (fashion), plate → plate (food) | a weak match looks like an error |
| **Jump cut** | Same shot, time skipped | pause removal (talking head), compression (unboxing, tutorial) | overuse without a new framing disorients |
| **Punch-in jump cut** | Same take re-framed ≥ 12% tighter on one side of the cut | talking heads, a single locked demo take | changes under ~8% read as a glitch |
| **J-cut / L-cut** | Sound leads / trails the picture | sizzle before the dish, voice over B-roll | music-only montages |
| **Smash cut** | Abrupt tone change | hook → reveal | calm, premium genres |
| **Mask / occlusion** | A hand or the product crosses the lens and wipes the frame | vertical demos, fashion changes | — |
| **Whip** | Fast pan whose blur hides the cut; both sides at matched speed and direction | rooms, places, outfits | mismatched directions read broken |

Cut **during** a movement, not after it finishes: a match cut placed after the action completes reads
as two separate shots. Canned preset packs (spin, glitch, star wipe) read as template content.

---

## Cutting on the voice or on the music

A playbook's `drive` says which clock the cuts follow:

- **voice** (product-demo, tutorial, talking-head, the voiced variants): cut on pauses, never inside a
  word. `suggest_cuts.py words.json --playbook <id>`; a talking-head A-roll is cut by
  `trim_voice.py --jumpcut` (every pause over 0.35 s removed, the kept stretches become scenes).
- **music** (real-estate, food-fnb, fashion-beauty, montage-recap, promo-sale): cut on beats, bar
  starts first. `suggest_cuts.py --music track.wav --end N --playbook <id>`. A scene of one bar at
  120 bpm is 2.0 s; montages cut every beat or two at their peak; voice-paced genres every one or two bars.
- **both**: voice cuts, nudged onto a beat within 4 frames (`suggest_cuts.py words.json --music track.wav`).

Cut density follows the music's sections: fewer cuts in a verse, more as it builds, a hard cut onto
the drop's first downbeat [C, vendor guidance]. Cut 2–3 frames early if a cut "feels late".

---

## Speed: fast-forward, slow motion, ramps

The Scenes table has a **Speed** column: blank (1x), a constant (`2x`, `0.5x`), or a ramp
(`ramp 1>2.5>1`: speeds at evenly spaced points across the scene, eased between). The renderer reads
the source at that speed; the source frame at the planned cut is still `In`; `footage_overlap_checker.py`
counts the footage a fast scene uses (a 3 s scene at 2x reads 6 s).

| Shape | Curve | Use | Source |
|---|---|---|---|
| **Fast-forward** | `2x`–`8x` | waiting, prep, repetitive work; always labelled ("tua nhanh ×4") when it compresses a result | any fps |
| **Montage ramp** (slow → fast → slow) | `ramp 1>2.5>1` | corridors, stairs, doorways, travel; the fast middle carries the viewer to the next place and can hide a cut | any fps, a constant-speed take |
| **Hero ramp** (fast → slow → fast) | `ramp 1>0.4>1` | a pour, a drop, a spin, the reveal of a dish | high fps |
| **Slow motion** | `0.5x` | a money shot, a hair flip | 60 fps for 0.5x, 120 fps for 0.25x |
| **Named curves** | `montage` · `hero` · `bullet` · `flash-in` · `flash-out` · `freeze-hit` | the same ramps by name (CapCut's "velocity" vocabulary): `montage` = `ramp 1>2.5>1`, `hero` = `ramp 2>0.4>2`, `bullet` = `ramp 1>0.15>0.15>1.6` (a near-freeze then release), `flash-in` = `ramp 3>1`, `flash-out` = `ramp 1>3`, `freeze-hit` = `ramp 1>0>0>1` (runs, one held frame for the middle third of the scene, runs) | `hero` and `bullet` need a 60 fps proxy; CapCut publishes no numbers for its presets, these are the kit's own approximations |

- Clean slow motion is the timeline fps ÷ the source fps: 60 fps → 50%, 120 → 25%, 240 → 12.5% on the
  30 fps timeline [S]. Slower than that repeats frames (stutter); interpolation smears texture [S].
  `prepare_footage.py` keeps 60 fps sources at 60 in their proxies, and `plan_to_project.py` warns
  when a slow scene would stutter (with `--analysis`).
- One or two ramps per 30 s, tied to a beat or an impact sound; slow down as the action enters the
  frame; don't overuse [S: Fstoppers, Kapwing].
- Implementation: a ramp re-times the source frame by frame inside `<Freeze>` in `engine/Short.tsx`
  (Remotion cannot animate `playbackRate`; its docs re-time per frame too). Mute source audio is the
  kit's default, so no pitch artefacts.
- **Freeze hit** (`Speed: freeze-hit`): a scene of 0.8-1.6 s holds ONE frame for its middle third (6-15 frames), easing into and out of it. The engine
  handles a speed of 0 (`advance()` stays constant; two stills 13 frames apart inside the hold were bit-identical) and `plan_to_project.py` does not call
  it stutter. Dress it on the same beat: `Transition: cut +flash`, a camera `keys` punch of 1.04-1.08, and, over a person, a Subject `outline` or
  `lift` window of the hold's frames (a 36-frame scene holds from about frame 12 to 24: `outline 12-24 @ mattes/CLIP_A`). Freeze on a sharp frame, and
  never across a before/after reveal. The scene reads a third of its length in footage (`footage_overlap_checker.py` counts that).
- **Echo / trail** (`Transition: cut +echo`, or `echo` on a scene of project.json: `{copies: 1-3, delay: frames, decay: 0.5, frames: N}`): the same clip drawn again
  `k * delay` frames behind the live frame, each copy `decay ** k` as opaque, inside the camera framing. `+echo` = 2 copies, 3 frames apart, for the first 15
  frames after the cut (the last 6 fade out). It decodes the clip N+1 times: keep it to one scene per video, on fast movement (a spin, a whip, a pour);
  on a still shot it only doubles the picture. Remotion only.

---

## Re-hooks and open loops

A 30–40 s video carries **2–3 small unresolved questions** and **one mid-point reset** where attention
sags (around 45–55% of the runtime): a new angle, the second item, a music drop, a speed ramp, a bold
title. Place it where attention naturally falls, not at a tidy structural boundary. Each playbook names
its own (product-demo's RE-HOOK; real-estate's FEATURE; montage's PEAK).

---

## The one place you must not cut

**Never hide a cut between the BEFORE and the AFTER of a demonstration** (stain, skin, renovation,
cleaning, styling). A hidden cut across the reveal is exactly what makes a demo read as fake, and what
TikTok's misleading-demonstration rules treat as a false impression (`claims-and-compliance.md` §3).
Hold the take; when the process takes hours, same item, same framing, same grade, and the compression
labelled on screen. The credible choice and the compliant choice are the same choice.

---

## When the footage fights the rules

- **One long take that cannot be cut**: punch-ins make scenes from it (wide 0–4 s → tight on the detail
  4–8 s → the result 8–12 s), with no hidden cut across a reveal.
- **One camera setup**: vary scale rather than angle (wide, medium, macro), and text as a fourth axis.
- **A voice that runs long**: cut breaths and dead air first (15–20% routinely); then drop a point
  rather than stretching scenes past the playbook's maximum.
- **Under the playbook's minimum runtime**: do not pad; add real content (a second item, another room).
- **Not enough fresh footage for the batch**: stop and report the numbers (`policy.md` §4.1).
