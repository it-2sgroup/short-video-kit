# Adding a technique to the kit

The kit is a framework that grows: a reference video, a client's request or a tutorial shows a transition, a text
effect, a grade, a camera move or a sound the kit cannot do yet. This is the one loop for adding it, so that every
technique is findable by name, implemented in one place, documented in one place and proven by one test. Nothing about
the video that revealed the technique (its brand, its footage, its words) is ever written into the kit.

## 0. What a technique is, and where each kind lives

`python scripts/technique.py kinds` lists the kinds. A technique is one **card** in `assets/techniques.json`; the card
points at the code, the doc and the test. `python scripts/technique.py check` compares the cards with the code in both
directions and fails when a technique has no card, doc or test, or a card describes something that is gone.

| Kind | What it is | Implemented in |
|---|---|---|
| `overlay` | A graphic or text drawn over the footage for a time window (`title`, `callout`, `phrase`...) | `src/components/**` + `registry.tsx` |
| `transition` | How scene N+1 replaces scene N | `src/engine/transitions.tsx` + `project.ts` + `timeline.ts` (default length) |
| `hit` | CapCut-style accent on a cut (`+shake`, `+glitch`...) | `plan_to_project.py` + the HyperFrames kit |
| `text-fx` | One animation of a line of text (entrance, loop, exit) | `src/components/text/Fx.tsx` |
| `subject-fx` | An effect shaped by a person matte (flash, outline, glow, spotlight, colour pop, text behind) | `src/engine/Subject.tsx` + `project.ts` |
| `title-style`, `caption-style`, `caption-highlight` | How text is drawn or how the spoken word is marked | `Title.tsx`, `Captions.tsx` |
| `camera-move`, `camera-ease`, `camera-option` | Virtual camera moves, their easing, and options on top (roll, focus, pan, shake) | `src/engine/camera.ts` |
| `speed-curve` | A named speed curve for a scene (`montage`, `hero`, `ramp`...) | `footage_overlap_checker.py` (`SPEED_PRESETS`) |
| `grade` | A colour look baked into the footage proxies by ffmpeg | `assets/grades.json` |
| `look` | A finish over the whole picture (vignette, grain, colour push) | `src/engine/Short.tsx` + `project.ts` |
| `theme` | A palette for the template's graphics | `src/theme.ts` |

Kinds added later (a matte effect, a light effect, an audio treatment) are one line in `technique.py` (`KINDS`) plus the
same loop. A new pipeline **script** is not a technique card: it goes in `SKILL.md`'s workflow, `docs/STRUCTURE.md` and the README tree,
and gets its selftest.

## 1. Analyse the sample (when the technique comes from a reference video)

`SKILL.md` §1b: `analyze_reference.py sample.mp4 --out ref/ --dense A-B`, then **look** at `scenes.png`, every
`dense_*.png` and `spectrum_*.png`. Write down every technique you see, one line each, in neutral words: what moves, how
long it lasts in frames at the sample's fps, what the sound does on it. The numbers are measurements; the technique name is
your reading, so say which you are giving.

`technique.py match ref/report.json` does this for the measured parts at once (transition family, camera, speed, grade): every line that says NO CARD is a candidate.

## 2. Look for it before building it

```bash
python scripts/technique.py search "glitch rgb split"      # by id, name, aliases (CapCut / Premiere / After Effects names), tags
```

Most "new" techniques exist under another name, or are an existing one with other parameters (a longer `whip`, a
different `ease`, another `grade`). If it exists, write the plan with it and stop. If it almost exists, add a
**parameter** (a key in the component's content, an option in the plan cell), not a second component.

Techniques already researched but not built are listed in `references/technique-backlog.md`: start there before researching again, and delete a
line when you build it.

## 3. Research it (a new technique is never faked with a lookalike)

Find how it is built: the maths of the easing, the filter chain, the SVG/CSS construction, the sound's envelope. Prefer
primary sources (docs, the project's own repository, the licence file). Record on the card: `source` (URL or book) and
its **licence** (CC0, MIT, Apache-2.0, OFL for fonts; commercial use must be allowed). Anything copied from a
sample's own footage, music, logo or typeface belongs to its owner: do not put it in the kit.

## 4. Implement it where its kind lives (§0), data-driven

- No video content in code: text, colours, durations and positions come from the plan or `project.json`; defaults are
  neutral. No client names or footage names in comments, examples or help strings: use `CLIP_A`, `BRAND`, `Text A`.
- A graphic is a pure function of the frame (`useCurrentFrame()`), never of the clock; nothing animates by CSS transitions.
- Both renderers: if HyperFrames cannot draw it, say so in `scripts/project_to_hyperframes.py` (it lists what is
  Remotion-only) and on the card (`"renderers": ["remotion"]`).
- A sound goes into `assets/sfx/` only if it is CC0 or self-made (a row in `assets/sfx/SOURCES.md`); a font only if it has
  the `vietnamese` subset and an open licence.
- ffmpeg-side: check the filter exists in the user's build (`doctor.py` lists the filters the scripts call; this machine's
  ffmpeg may lack `drawtext`).

## 5. Write the card

`python scripts/technique.py scaffold <kind> <id>` prints the files to touch and an empty card. Fill: `id`, `kind`, `name`,
`about` (what it looks like, and when it earns its place, one or two sentences), `plan` (how a plan asks for it), `renderers`,
`doc` (a file under `skill/short-video-editing/` that mentions the id), `test` (the label of its selftest), `aliases`
(the names editors use), `tags`, `source`. Optional and validated: `params` (`{key, type, default, min, max, step, unit, options, desc}`: the knobs of
the plan cell, with bounds), `use_when` / `avoid_when` / `pairs_with` (guidance for Claude and playbook authors), `licence` (SPDX or `kit-original`, separate
from `source`), `since`, `status` (`stable` or `experimental`: a card made from one reference stays experimental until a second case or a test supports it),
`deprecated` / `replaced_by` (an id never disappears silently), `timing` (typical frames and easing), `renderer_notes` (one line on parity gaps) and
`detect` (which analyser output means this technique: see `references/reference-analysis.md`).

## 6. Document it once

One row in the reference file its kind uses (`transitions.md`, `typography.md`, `layout-and-motion-graphics.md`,
`camera-moves.md`, `image-processing.md`, `sound-design.md`...). If a playbook should recommend it, add it to that playbook's
JSON (`components.use`, `transitions`, `grade`...); a technique no playbook recommends is allowed (the kit is a library) but
is listed by `playbook.py check` as a note, so playbook authors can see it.

## 7. Prove it

A test in `selftest.sh`, labelled with the card's `test` string: for a component, a typecheck plus a still rendered and
**looked at**; for an ffmpeg chain, a measurement on a synthetic clip (a colour grade changes the mean in the direction
claimed; a transition has the claimed length in frames); for a script, a run on generated input. Then:

```bash
python scripts/technique.py check && python scripts/playbook.py check && ./selftest.sh
./selftest.sh --render <render project>       # when the template changed: typecheck + a still, then look at it
```

## 8. Record it in the repo's maps

`docs/STRUCTURE.md` (what every file is) and the structure tree in `README.md` change in the same commit as the file that
made them stale. The case that revealed the technique (client, dates, measurements, what was not verified) goes into
`docs/CASE-LOG.md`, never into the skill.
