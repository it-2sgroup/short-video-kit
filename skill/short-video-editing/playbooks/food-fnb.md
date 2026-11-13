# Playbook: food-fnb — restaurant, dish, drink, menu

Appetite first. The hero moment (a bite, a cheese pull, a pour, a sizzle) is on screen inside the
first second, then the place, the making, the dish, the reaction, the price and where to find it.
Goal: visits and orders; saves ("lưu lại đi ăn").

Variant: `food-fnb:review` when a reviewer talks (voice-driven, longer scenes, verdict at the end).

Labels: **[S]** sourced, **[C]** craft convention, **[L]** law (research, not legal advice).

## When to use it

- Footage: close-ups of food, steam, pouring, cutting; a kitchen or a table; warm restaurant light
  (amber, wood); a person eating or reacting.
- Not this playbook: a recipe someone should be able to follow (`tutorial`), a talking food critic
  without much food on screen (`talking-head`).

## Questions to ask when the brief does not say

1. Name of the place and the dish **as on the menu**, price on the day of filming, address/district, hours.
2. Is there a promotion (dates, conditions)? Is the visit paid or gifted (disclosure)?
3. Voice (reviewer, voiceover) or music only?

## Structure (22–35 s)

| Phase | Purpose | Graphics |
|---|---|---|
| HOOK 0–2.6 s | Money shot (pull, pour, sizzle, steam), then the dish in full | `title`: what it is + one hook word |
| PLACE 15% | The place or the stall, the vibe | `pin` (name, district) |
| PREP 30% | The making, match cuts on the action, `1.5x` through repetitive work | `checklist` (ingredients) or `label` |
| DISH 25% | The finished dish in macro, slow push, steam | `label` (name), `price` |
| REACTION 15% | The bite and the face; real sound up | one-word `title` or `sticker` |
| CTA 15% | Price, address, hours, how to order | `price`, `pin`, `stat` (hours) |

A slow exterior opener is the classic weak start [S: restaurant-marketing guides]. Shots of 1.5–3 s for
sensory moments, 3–4 s for the hero dish [C]. That is faster than the product-demo playbook's 3–4 s house
style: say so if the same user asks for food after a product demo.

## Shots the footage needs

The money shot at 60–120 fps (slow motion needs it) · the prep sequence (cutting, frying, seasoning,
plating) · the plated hero overhead and at 45° · eating and reaction · the room and the people · the
menu with prices · clean sound of sizzle and crunch [S: World Food Photography Awards; Lemonlight].
Shot-library kinds this playbook's camera knows: `MACRO`, `POUR`, `TABLE`, `FACE`.

## Editing

- Decide early whether it is voice-led or music-led; it sets the pacing [S: WFPA]. Music-led: cut on
  beats (`suggest_cuts.py --music … --playbook food-fnb`); voice-led: the `:review` variant.
- Cut on action (pour → plate) and match cuts; too many tricks break the flow [S: No Film School, WFPA].
- Speed: slow motion on the money shot (`0.5x` needs a 60 fps source; `0.25x` needs 120 fps);
  `1.5x`–`2x` through repetitive prep [C].
- **J-cut the sizzle**: let the sound of the next shot start a few frames before its picture [C].

## Sound

Music 100–128 bpm, warm and playful (fine dining slower, 70–95) [C]; duck it under sizzle and bite
sounds, which are the stars [C]. Keep the camera's own sound for the reaction scene (put it in the
voice track, or leave `--music` lower). Commercial-use licence on a business account.

## Picture

Grade `warm-food` (warm, a little more saturation and contrast, highlights kept), corrections per clip;
neither washed out nor too dark, natural light where possible [S: WFPA]. Theme `warm` (ivory, gold,
vermilion). Do not push saturation on skin.

## Graphics

`price` exactly as on the menu · `pin` for the place · `label` for dish names · `checklist` for a menu
or ingredients · `stat` for hours or a count · one `sticker` at most. No before/after (`compare`).

## Compliance [L]

- Ordinary food must not be presented as medicine: no "chữa", "giảm cân", "tốt cho gan".
- Health-supplement food (TPBVSK) ads need registered ad content and the warning "Thực phẩm này không
  phải là thuốc, không có tác dụng thay thế thuốc chữa bệnh", shown or read clearly; no doctors or
  medical staff in food ads.
- Alcohol: no appeal to minors, no drinking and driving; follow the platform's alcohol rules (ask).
- Paid or gifted visits disclosed; staff and diners consent or stay out of frame.
- Luật Quảng cáo 75/2025 (from 01/01/2026): a KOC promotes only what they have tried; ads labelled.

## Commands

```bash
python scripts/new_remotion_project.py ~/renders/quan --playbook food-fnb --proxies CLIPS
python scripts/suggest_cuts.py --music music.wav --end 30 --playbook food-fnb --json > cuts.json
python scripts/playbook.py skeleton food-fnb --cuts cuts.json --title "Quán X" > edit-plan.md
```
