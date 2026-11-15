# Playbook: product-demo — review / demo of a product (TikTok Shop), with or without before/after

The kit's first and best-evidenced genre: a product shown working, sold through the cart. The numbers
come from 16,242 measured TikTok Shop videos (`references/niche-winning-patterns.md`); the rhythm and
look are this playbook's house style (3–4 s scenes, soft transitions, no text in boxes on demos), a
default for this genre, not a rule for every genre.

Variants: `product-demo:unboxing` (first impression), `product-demo:listicle` (top N of the shop's
own products; never against competitors).

## When to use it

- Footage: hands and the product in close-up, tabletop or top-down; a visible process with a result
  (a stain, a mess, a surface, a gadget doing its job); little camera movement.
- Intent: sell through TikTok Shop or affiliate (KOC/UGC), review, "dùng thử" (try-out), before/after.
- Not this playbook: someone explaining at length to camera (`talking-head`, with the demo as B-roll),
  a step-by-step how-to where copying matters more than selling (`tutorial`).

## Questions to ask when the brief does not say

1. The product's name exactly as listed, its price and the product-card URL (on-screen prices must match).
2. Will the video be **boosted as an ad**? TikTok ads forbid before/after comparisons: plan a version
   without the `compare` card and the BEFORE/AFTER labels (`references/before-after.md`).
3. How many videos must this footage feed (batch capacity, `references/policy.md` §4.1)?

## Structure (30–40 s; `playbook.py skeleton product-demo --duration 36`)

| Phase | Timing | Purpose |
|---|---|---|
| HOOK | 0–3 s | Two ~1.5 s beats: BEFORE → AFTER of the same item, joined by a wipe |
| PROBLEM | 3–9 s | The stake made concrete: name the item and the problem; `thumbs` when the voice lists three |
| CTA-EARLY | ~9–12 s | Plant the cart once, lightly |
| RE-HOOK | ~12–15 s | Product hero shot, new energy (zoomThrough + flash, punch on the product name) |
| DEMO | 15–25 s | The transformation, 3 scenes of 3–3.5 s, match-on-action |
| REVEAL | 25–31 s | Pay off the hook; the same framing as the BEFORE; then the `compare` card |
| CTA-CLOSE | 31–38 s | Repeat concretely, point at the real cart |

- **Why an early CTA** [S]: Wistia's analysis of 14M+ videos found sub-60 s videos convert best with
  the CTA in the first quarter (hosted business video, not TikTok; directional). About 40% of the
  reference videos had a 0% click-through rate: watched, never tapped.
- **Runtime** [measured]: CTR and sale rate peaked at 35–44 s; sub-25 s was the worst band. Push back
  on 15-second requests with that number; do not pad, add a second item or case instead.
- **Scene length** [house style + data]: the 4 s ceiling is data (a static shot past 4 s is an exit point);
  the 3–4 s rhythm with soft transitions is this playbook's default style (with soft transitions, 1.5–2 s hard
  cuts read as jerky). Fast genres (food, fashion, montage) cut at 1–2 s: say so if the same user asks for another genre.
- **Re-hook and open loops** [C]: 2–3 small unresolved questions and one mid-point reset around
  18–20 s ("The second one is the one that surprised me", "But there is one spot that is a bit different, I'll show you in a moment").

## Shots the footage needs (shot list when it must be shot)

Locked phone, top-down or front-on, AWB and AE locked; leave space above and below the subject for the
titles and captions. BEFORE close-up · the product (hero, in hand) · the process (pour, scrub, soak) ·
the AFTER in the **same framing and light** as the BEFORE · a control (an untreated half) if possible ·
the item lifted to camera. Shot-library kinds this playbook's camera knows: `STAIN`, `POUR`, `SOAK`,
`LIFT`, `PRODUCT`, `WIDE`.

## Editing

- Cut on pauses of the voice (`suggest_cuts.py words.json --playbook product-demo`).
- Transitions: soft (`fade`, `slide`, `blurDissolve`) within a beat, `slide up` / `wipe` / `zoomThrough
  +flash` on a change, `wipe right +leak` into the REVEAL; at most two accents per video.
- **Never hide a cut between the BEFORE and the AFTER.** Hold the take; when the process takes hours,
  same item, same framing, and the compression labelled on screen ("sped up ×8", "after 2 hours").
  A sped-up wait is a `Speed` cell (`4x`) plus that label.
- A single locked demo take becomes three scenes by scale: wide 0–4 s → punch to the detail 4–8 s →
  tight on the result 8–12 s (`references/camera-moves.md`).

## Sound

Voice first (supplied or ElevenLabs), cleaned and levelled with `process_audio.py voice`; a light bed
(90–120 bpm) far under it; sounds from `sfx-map.json` (shutter on the HOOK BEFORE→AFTER, silence across
the REVEAL). Music from TikTok's Commercial Music Library, or none (74% of compliant affiliate videos
use original audio only).

## Picture

Grade `natural`, corrections **shared** across clips (`prepare_footage.py` computes one correction for
the whole set): a BEFORE and an AFTER must never be corrected differently, or the grade itself becomes
a misleading demonstration. Over white fabric use the `outline` or `marker` title style.

## Graphics

`title` (3–4 styles, never the same twice in a row) · `thumbs` for a spoken list of three · `step` ·
`callout`/`highlight` on a still moment · `progress` for time passing · `compare` at the reveal ·
`price` (exactly the listing) · `cart` twice (early and close, pointing at (112, 1677)) · `magnifier`
for fine detail · one `sticker`. No text in boxes on demos.

## Hooks (`references/hook-library.md` for the ranking)

Order of preference: a visible transformation → genuine social proof → a specific pain point →
a product reveal with an open loop. Examples written for a cleaning-type demo, checked against the claim
rules (swap in your own item):

- **Result first.** Locked shot, the finished result; a hand moves in to show the BEFORE.
  Text "This was 10 minutes ago" · VO "I thought I'd have to throw this spot away…"
- **Split half.** Half of the item treated, half not. Text "Left half done, right half not yet" · VO
  "Same item, same spot, okay?" Self-evidencing: removes the "they swapped the item" doubt.
- **Social proof (the one permitted superlative: own sales).** "Best seller in my shop this month" ·
  "But I still had to try it myself before I dared to say so."
- **Specific pain.** "Bought this last month" · "Once one breaks, that's it."
- **Problem made on camera (anti-fake).** A mark made on purpose on a clean item. "Ruined on purpose for the test".

## Compliance

The checklist is printed into the plan by the skeleton. Detail and the rewrite table
("Diệt khuẩn 99.9%" ("kills 99.9% of bacteria") → "Làm sạch bụi bẩn bám trên vải" ("cleans dirt clinging to fabric"), "Không sạch hoàn tiền" ("not clean, money back") → remove) are in
`references/claims-and-compliance.md` §2. Claim forms that circulate in this category and must not
be reused: money-back lines ("Không hiệu quả anh gửi tiền lại liền", "if it doesn't work I'll send your money back right away"), guarantee lines ("Hổng sạch hổng lấy tiền", "no clean, no payment"),
instant or total-result lines ("sạch tinh như mới", "spotless like new"; "tẩy sạch mọi vết bẩn cứng đầu", "removes every stubborn stain"). Claims inside a **supplied** voice cannot be edited out silently:
flag them to the user and keep the on-screen text clear of them.

## Variant notes

- **unboxing**: the opening in one take (packaging cannot be resealed convincingly); music low or off
  during the reveal so the packaging sound carries it; a "What's in the box" `checklist`; the creator
  must have actually used the product (Advertising Law 75/2025, Art. 15a).
- **listicle**: one item per beat, each shot the same way so the comparison is fair; `ranking` for
  the order; "Top 1", "the best" need documents; never name a competitor.

## Commands

```bash
python scripts/playbook.py skeleton product-demo --cuts cuts.json --title "Product name / KOC" > edit-plan.md
python scripts/plan_scenes.py --library library.json --plan edit-plan.md --kinds "STAIN,LIFT@CLIP_A,..." --used other-plans...
python scripts/plan_to_project.py edit-plan.md --out render/v1.json --voice audio/v1.wav --captions captions.srt \
    --words words.json --auto-camera --auto-sfx --punch-keywords "product name"
```
