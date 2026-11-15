# Playbook: fashion-beauty — try-on, outfit, lookbook, makeup, skincare

Transformation on the beat: looks change on the music with match cuts (same mark, same pose, same
framing) and short speed ramps, each item labelled with its name and price, skin kept natural. Goal:
sales (cart, link), saves. Beauty claims are tightly regulated: show the routine, never promise a cure.

Labels: **[S]** sourced, **[C]** craft convention, **[L]** law (research, not legal advice).

## When to use it

- Footage: a person in full or half body on a fixed mark, mirror shots, the same framing with
  different outfits; face close-ups with cosmetics; fabric and texture macros.
- Not this playbook: a talk about style (`talking-head`), a single product demo (`product-demo`).

## Questions to ask when the brief does not say

1. Item names, prices and sizes as listed; the model's height/weight if sizes are shown.
2. Music only (lookbook) or a voice (try-on review, makeup tutorial)?
3. Is any result claimed (skin, hair)? Then read the compliance section before writing a word.

## Structure (20–35 s)

| Phase | Purpose | Graphics |
|---|---|---|
| HOOK 0–2.4 s | The final look first, or the most striking change on a beat | `title` (how many looks, theme or budget) |
| LOOK 70% | One look or step per beat; match-cut the pose, whip between looks; `ramp 1>1.6>1` through a spin | `label` (item · price), `price` |
| DETAIL 15% | Fabric, texture, product close-ups | `callout` |
| CTA 15% | The favourite look again and where to buy | `cart` (TikTok Shop), `price` |

Outfit changes land on a beat drop or a strong accent [S: Finchley]; full-body shots from the same taped
floor mark and light every time, so the changes read as transitions [S: vendor guides]. A makeup or
skincare tutorial is the same structure with LOOK as the steps (product → application → result, 4–6 s
each, voice-driven: cut it with `suggest_cuts.py words.json --playbook fashion-beauty`).

## Shots the footage needs

Tripod full-body shots from one mark, the same light · each look from front, back and in movement ·
fabric and tag macros · for beauty: bare skin at the start, every step as product, application and
result, the final look under the same light [S: Zhiyun]. Kinds the camera knows: `MIRROR`, `FACE`, `TEXTURE`.

## Editing

- Music-driven: `suggest_cuts.py --music track.wav --end 30 --playbook fashion-beauty` (1–2 beats per
  look at 100–130 bpm).
- Cuts and whips between looks (jump, snap, spin, hand-cover transitions are shot, not added); a
  zoomThrough with a flash into the CTA. No dissolves between outfits [C].
- Speed ramps through spins and walks, landing at 1x on the pose.

## Sound

Trend-friendly music with clear downbeats; a whoosh on the opening change (the playbook overrides the
shutter). With a voice: cleaned, music low.

## Picture

Grade `soft-skin` (gentle contrast, warm skin, protected highlights), corrections per clip; colour
accuracy of the fabric comes first, because wrong colours mean returns [C]. Theme `luxe`. Over white
garments use the `outline` or `marker` title styles. No smoothing or reshaping filters on a result.

## Graphics

`label` (item · price; `align=right` for the second item), `price`, `callout` on a detail, `cart`,
`stat` (e.g. size worn), `compare` only for a styling change, never for a skin or hair result.

## Compliance [L]

- Cosmetics may not claim to treat: "trị", "điều trị", "chữa" (to treat, to cure, e.g. acne or melasma
  treatment: "trị mụn", "trị nám"), nor "trắng da cấp tốc" (instant whitening) or "mọc tóc" (hair regrowth) [S: CV 1609/QLD-MP; ASEAN Cosmetic Claim Guidelines].
- TikTok bars before/after for acne, whitening and hair-loss products; ads bar before/after entirely.
- The same grade on every shot; no filter on a result.
- Prices and sizes match the listing; gifted or paid items disclosed; licensed music.

## Commands

```bash
python scripts/new_remotion_project.py ~/renders/lookbook --playbook fashion-beauty --proxies CLIPS
python scripts/suggest_cuts.py --music music.wav --end 30 --playbook fashion-beauty --json > cuts.json
python scripts/playbook.py skeleton fashion-beauty --cuts cuts.json --title "5 office outfits" > edit-plan.md
```
