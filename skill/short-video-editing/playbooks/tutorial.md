# Playbook: tutorial — how-to, recipe, step by step

Result first, then the steps in order, each a beat with its number on screen, long waits compressed and
labelled, the result again at the end. Clarity beats energy: each step stays long enough to be copied.
Goal: saves and shares; for a product used in the steps, the cart.

Labels: **[S]** sourced, **[C]** craft convention.

## When to use it

- Footage: hands doing a task from one fixed angle (top-down or front), a sequence of states
  (ingredients → result), screen recordings or device close-ups.
- Not this playbook: a product sold on its result rather than taught (`product-demo`), a dish shown
  for appetite rather than to be cooked (`food-fnb`).

## Questions to ask when the brief does not say

1. How many steps, and which are essential (a 45 s video holds 4–6 steps)?
2. Real quantities, times and temperatures (on-screen numbers must match what was done).
3. Is a product sold through the steps (cart, price)?

## Structure (35–55 s)

| Phase | Purpose | Graphics |
|---|---|---|
| HOOK 0–3 s | The finished result, then the promise ("3 steps", "5 minutes") | `title` with the count or the time |
| TOOLS 12% | What you need, laid out | `checklist` |
| STEP 62% | One action per step, 3–6 s each; waits sped up and labelled | `step` (numbered), `callout`, `magnifier`, `progress` |
| RESULT 14% | The result in the same framing as the hook | `title` |
| CTA 12% | Save it, or the product used | `title`, `cart` for a TikTok Shop product |

Recipes under 60 s with a text overlay per step are the common short form [S: recipe-video guides];
an ingredients screen the viewer can pause on is valued [S, snippet only].

## Shots the footage needs

The finished result · ingredients or tools laid out overhead · every step as its own 10–15 s take
[S: creator guides] · side angles for texture and steam [S: Filmora] · timer or temperature readouts.
Shot-library kinds this playbook's camera knows: `HANDS`, `SCREEN`, `WIDE`.

## Editing

- Cut on pauses of the voice; a step never straddles a cut it does not need.
- Waiting (mixing, baking, drying) at `2x`–`8x` in the Speed column, always labelled on screen
  ("sped up ×4", "after 20 minutes"); slow motion on pours (`0.5x`, 60 fps source) [C].
- Soft transitions within the steps (`fade`, `slide left`), a blur dissolve with a light leak into the result.
- Screen recordings: `hold`, and a `magnifier` on the active element instead of camera moves.

## Sound

Voice explains (cleaned, −16 LUFS); a light steady bed 85–115 bpm; `switch` sound on each `step`
(sfx-map), ticks on the checklist.

## Picture

Grade `natural`, corrections **shared** (a step's colour must not change between takes of the same
dish or surface). Theme `cool`.

## Graphics

`step` (one visible at a time, landing on the word that names the action: `@"beat the eggs"`),
`checklist` for tools or ingredients, `progress` for a wait, `callout` and `highlight` on a still
moment, `magnifier` for fine detail, `stat` for a quantity or a time, `cart` when a product is sold.

## Compliance

Sped-up waits labelled; safety steps shown (heat, electricity, chemicals, knives); quantities and times
as actually done ("5 minutes" only if it takes 5 minutes); products named honestly, paid placement disclosed.

## Commands

```bash
python scripts/suggest_cuts.py words.json --playbook tutorial --json > cuts.json
python scripts/playbook.py skeleton tutorial --cuts cuts.json --title "How to make X" > edit-plan.md
python scripts/plan_to_project.py edit-plan.md --out render/v1.json --voice audio/v1.wav --captions captions.srt \
    --words words.json --auto-camera --auto-sfx
```
