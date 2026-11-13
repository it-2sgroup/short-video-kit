# Playbooks — one per kind of video

The kit edits many kinds of short vertical video. Everything that depends on the **kind** lives in a
playbook; everything that does not (the safe zones, the caption alignment, the renderer, the rights
policy) lives in `references/` and the scripts. A plan names its playbook in its header
(`**Playbook:** real-estate`) and every tool reads the rules from there.

| Playbook | For | Drive | Scenes | Runtime | Look |
|---|---|---|---|---|---|
| `product-demo` (+ `:unboxing`, `:listicle`) | TikTok Shop review, demo, before/after | voice | 2.5–4 s | 25–45 s | cool · natural · karaoke |
| `real-estate` (+ `:voiceover`) | apartment, house, villa, homestay, land tour | music | 1.8–4 s | 25–60 s | luxe · bright-interior · none |
| `food-fnb` (+ `:review`) | restaurant, dish, drink, menu | music | 1.2–3.5 s | 15–45 s | warm · warm-food · karaoke |
| `talking-head` (+ `:testimonial`, `:agency`) | expert tips, story, founder, customer story; `:agency` = a service pitch cut from the presenter's takes | voice (on camera) | 1–5 s (`:agency` ~1.8 s) | 20–90 s | cool · natural · pop (`:agency` crimson) |
| `tutorial` | how-to, recipe, step by step | voice | 2–4.5 s | 25–75 s | cool · natural · karaoke |
| `fashion-beauty` | try-on, lookbook, makeup, skincare | music | 1–3.5 s | 15–45 s | luxe · soft-skin · pop |
| `montage-recap` | travel, event, opening, behind the scenes | music | 0.5–3 s | 12–60 s | cool · vivid · none |
| `promo-sale` | sale, launch, announcement | music | 1.2–3.5 s | 10–35 s | cool · vivid · plain |

`python scripts/playbook.py show <id>` prints the numbers; `playbooks/<id>.md` explains them.

---

## Choosing the playbook (step 1 of SKILL.md)

The footage decides what is **possible**, the user's intent decides what is **chosen**. Analyse both
before planning anything:

1. `inspect_footage.py CLIPS --measure --json analysis.json` (speech on camera? does the camera move?
   light, colour cast, shake, noise, fps) and `contact_sheet.py CLIPS` — **look** at the sheet.
2. `playbook.py suggest --intent "<the user's words>" --analysis analysis.json` ranks the playbooks.
   It is a first guess from keywords and two measurements; confirm it against what you saw.
3. If the request and the footage agree, say which playbook you chose and why, in one line, and go on.
   If they disagree, or two playbooks are within a point, ask (below). Never force footage into a
   genre it cannot carry: say what is missing and what to shoot.

| What the footage shows | What the user wants | Playbook |
|---|---|---|
| Gimbal walks through rooms, exteriors, nobody talking | sell or rent a property, leads | `real-estate` |
| Same, with an agent speaking or a voiceover | same | `real-estate:voiceover` |
| Hands and a product, a problem and a result | TikTok Shop sales | `product-demo` |
| A sealed box, the opening, overhead | first impression | `product-demo:unboxing` |
| Several of the shop's own products shot alike | help choose, top N | `product-demo:listicle` |
| Plates, cooking, steam, a restaurant interior | visits, orders | `food-fnb` (`:review` when someone talks) |
| Overhead step-by-step hands | teach, recipe | `tutorial` |
| A person on a fixed mark in several outfits or looks; face close-ups with cosmetics | sell clothes or cosmetics | `fashion-beauty` |
| One person speaking to the lens most of the time | authority, followers, explain | `talking-head` |
| A customer talking about the product | trust, ads | `talking-head:testimonial` |
| A presenter pitching a service or agency, the voice cut from their takes, a sample to match | win customers | `talking-head:agency` (`references/agency-pitch-recipe.md`) |
| Many clips of places, people, moments; little speech | reach, event, travel, brand | `montage-recap` |
| Packshots, logo, offer artwork, little action | announce an offer | `promo-sale` |
| Talking head + product demo | sell with authority | `talking-head` for the A-roll, demo shots as B-roll |
| Footage cannot support what is asked | — | stop; list what to shoot |

### Questions worth asking (only what the footage and the request do not already answer)

Ask at most three, each with your default, in one message. The usual gaps:

- **Kind and goal** when ambiguous: "Video này để bán (giỏ hàng/đặt lịch xem) hay để kéo follow/nhận diện?"
- **Platform and use**: TikTok, Reels or both; organic or boosted as an ad (ads forbid before/after
  comparisons and need Reels-ad safe zones: `--platform reels-ad`).
- **Facts on screen** the footage cannot give: price, area, address, offer dates, the product name as listed.
- **Voice**: a supplied recording, a voice to synthesize (ElevenLabs plan and licence), or music only.
- **Length** when the request is outside the playbook's band (say the band and why).

Each playbook's `.md` lists the questions specific to its genre.

---

## What a playbook contains (`<id>.json`), and who reads it

| Key | Meaning | Read by |
|---|---|---|
| `id`, `title`, `summary` | name and one-paragraph intent | `playbook.py list/show` |
| `intents`, `expect`, `signals` | words that point to it; expected speech/motion; what the footage looks like | `playbook.py suggest`, Claude |
| `runtime` `{min, max, ideal, why}` | allowed and ideal length | `pacing_checker.py`, `playbook.py skeleton` |
| `hook` `{deadline, beats, beat, minBeat, purpose, graphics}` | the opening | `pacing_checker.py`, `suggest_cuts.py`, skeleton |
| `scenes` `{min, max, target}` | scene lengths outside the hook | `pacing_checker.py`, `suggest_cuts.py`, `trim_voice.py --jumpcut`, skeleton |
| `drive` | `voice` (cut on pauses) or `music` (cut on beats) | `suggest_cuts.py` usage, SKILL.md |
| `structure` `[{type, share or seconds, purpose, graphics, speed}]` | the beats after the hook | `playbook.py skeleton` (Type, Speed and the Shot hint of every scene) |
| `transitions` `{hook, same, change, into, accentsMax}` | transition cells between hook beats, within a beat, on a change, into a named beat | skeleton, `plan_scenes.py` |
| `camera` `{pattern, byType, byKind}` | virtual camera cells | `plan_to_project.py --auto-camera`, `plan_scenes.py` |
| `captions` | `karaoke` · `pop` · `plain` · `none` | `plan_to_project.py` default |
| `theme` | `cool` · `warm` · `luxe` (`src/theme.ts`) | `new_remotion_project.py --playbook` |
| `grade`, `correction` | a look from `assets/grades.json`; `per-clip` or `shared` corrections | `prepare_footage.py` |
| `music` `{bpm, mood}` | tempo range and mood | `suggest_cuts.py --music` (beat search), music choice |
| `components` `{use, avoid}` | graphics that fit; graphics that do not | skeleton, `plan_to_project.py` warnings |
| `sfx` | overrides of `assets/sfx/sfx-map.json` events (null = silence) | `plan_to_project.py --auto-sfx` |
| `compliance` | checklist printed into the plan | skeleton |
| `references` | files to read for this genre | `playbook.py show`, Claude |
| `variants` | named partial overrides, used as `id:variant` | everything above |

`python scripts/playbook.py check` (run by `selftest.sh`) validates every playbook and variant: types
and ranges, components that exist in the template registry, grades that exist, sounds that exist,
references that exist, and that the playbook's own skeleton passes its own pacing rules at both ends of
its ideal runtime. It also fails when a component, grade, theme or caption style is used by **no**
playbook: the kit carries no technique that nothing uses.

## Adding a playbook (or a house style)

1. Prefer a **variant** when the new kind shares most rules with an existing playbook (a brand's
   house style for product demos, a rental flavour of real estate): add it under `variants` with only
   the keys that differ.
2. Otherwise copy the closest `<id>.json` to `<new-id>.json`, set `id` to the file name, and change
   what differs. Keep every key: `check` requires them.
3. Write `<new-id>.md` with the same sections as the others (when to use, questions, structure, shots,
   editing, sound, picture, graphics, compliance, commands). Mark sourced facts and craft convention.
4. A new graphic → a component in `assets/remotion-template/src/components/`, a row in
   `registry.tsx`, a row in `references/layout-and-motion-graphics.md`, and the playbooks that use it.
   A new look → a grade in `assets/grades.json` or a theme in `src/theme.ts`, used by a playbook.
5. Run `python scripts/playbook.py check` and `./selftest.sh`; render one still with the new theme or
   component (`./selftest.sh --render DIR`) and look at it.
6. Update `docs/CAU-TRUC.md` and the tree in `README.md`.
