# Creative direction: an idea first, three directions, a memory of what was made

A genre playbook says what is SAFE for a kind of video; used alone it makes every video of that kind the same. The creative layer sits between the footage and the plan and answers
a different question: what is THIS video about, and which few techniques say it. Four tools, one loop. Nothing here replaces taste: it forces the choices to be deliberate, different from each other
and different from the last video. Taste comes from the references the user gives and from their feedback after each round.

```
concept.json  ->  directions.py (3 plans)  ->  choose  ->  concept.py lock  ->  edit, check  ->  style_ledger.py add
 the idea         explore                       a human     the vocabulary       concept.py check   remember
```

## 1. The concept (`concept.py`)

`python scripts/concept.py example` prints the document. Fill it before planning; ask the user only what the footage and the request do not answer (at most three questions, with defaults).

| key | what it holds | why |
|---|---|---|
| `feeling` | 1-4 words: what the viewer should feel (warm, urgent, premium, raw...) | steers which options score well (`style-axes.json` `feel_words`, Vietnamese and English) |
| `tension` | the problem at the start and how the video releases it | a video without tension is a list |
| `motif` | `kind` (colour, movement, text, shape, sound), what returns, `min_count` | a repeated element is what the eye reads as style |
| `signature` | ONE move that breaks the pattern on purpose (`flash-cut`, `hold-then-burst`, `speed-hit`, `zoom-through`, `text-takeover`), where (`hook`, `middle`, `end`, seconds) and why | the one rule broken deliberately, so the other rules can hold |
| `restraint` | `use`: the whole vocabulary of the video (3-16 catalogue ids); `avoid`: ids that are out | a small vocabulary used with intent is a style; a long list is a catalogue |
| `energy` | points `[position 0-1, level 0-1]`, at least three, not flat | the shape the cutting should follow |

Two moments for the restraint: while exploring leave `use` empty (fill `avoid` if you know what is wrong for this video) so the directions can propose different vocabularies; after the choice,
`concept.py lock concept.json --direction dirs/A/direction.json` copies that direction's transitions, fonts, text effects and grade into `use`.

## 2. Three directions (`directions.py`)

`directions.py edit-plan.md --concept concept.json --out-dir dirs [--seed N] [--ledger L] [--keep AXES] [--retime] [--stills RENDER]` rewrites the creative cells of an existing plan three times. The timing, the footage and the words are the base
plan's. Five axes (`assets/style-axes.json`, every id checked against the catalogue by selftest): **transitions** (quiet, soft-flow, kinetic, graphic, glitch-tech, showreel, organic), **camera** (locked, drift, push-in, handheld, kinetic, reveal),
**type** (bold-ad, editorial, tech, hand, clean-sans, retro-pop: fonts and text effects), **colour** (grade, text colours, accent, look flags) and **rhythm** (steady, build, pulse, drop: how the transitions' length and hardness move through the video).
An option is placed on four dimensions (energy, warmth, formality, grit); the concept's feeling words pull toward some of them; the three directions are picked so that no two share more than a few axes and so that none repeats the style
ledger. The same `--seed` gives the same plans. `compare.md` shows the choices side by side, how different the plans really are (style similarity) and the rhythm of each; `--stills` renders one sheet of stills per direction.

What every direction gets from the concept: the signature move on one scene (tag `[signature]` in the Shot column; it overrides a `--keep` cell there, being the deliberate break), the motif on `min_count` scenes (`[motif]`; a colour motif paints those
scenes' text in the accent), header lines `**Direction:**`, `**Grade:**`, `**Signature:**`, and a Build hints block with the grade and look flags to pass to `prepare_footage.py` and `plan_to_project.py`.

`--keep transitions,camera` for a plan made from a sample (`reference_to_plan.py`): the sample's measured cells stay and only the type, colour and rhythm are explored. `--retime` also moves the cuts, for plans whose cuts are not tied to a voice or a beat.

## 3. Checking a plan against its idea (`concept.py check concept.json --plan edit-plan.md`)

Exactly one `[signature]`; at least `motif.min_count` `[motif]`; every transition, text effect and font in `restraint.use` (once locked; `cut` and `fade` are always allowed); the cutting follows the energy curve (a negative correlation between
cut speed and the curve is a warning); scenes are not all the same length (six or more nearly equal scenes are a warning). Errors exit 1; the rest is advice.

## 4. A memory of the style (`style_ledger.py`)

`style_ledger.py add edit-plan.md --ledger work/style-ledger.json --name v3` after a video is done; `check` before the next one. A plan's fingerprint is the set of transitions, camera moves, speed treatments, text effects, fonts, colours, rhythm, grade and
signature it uses; similarity is the mean Jaccard overlap (1 = the same style). Above 0.55 against one of the last eight videos the plan is a repeat. Keep the ledger with the work folder, outside this repo. For a batch, add each finished video before planning the next.

## What this does not do (say so)
It cannot judge whether a direction is GOOD: the similarity, fit and rhythm numbers say how different and how coherent, not how well it works. Look at the stills, and let the user choose. The feeling words it knows are listed in `style-axes.json`; a word it
does not know pulls nowhere (the compare table says so). Nobody has rendered full videos from all of the 6 x 7 x 6 x 8 x 4 combinations: the stills tool shows a direction before the render, the full render is still the test. A new technique joins the axes by adding it to
`style-axes.json` (selftest checks the id against the catalogue).
