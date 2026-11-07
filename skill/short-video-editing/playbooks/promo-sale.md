# Playbook: promo-sale — sale, launch, announcement (graphics carry the message)

A short announcement where the type is the message: the offer in the first second, the product or the
place shown, the terms clear, the deadline real, one call to action. The footage stays visible behind
big type; every number matches the listing. Goal: clicks on the offer, store visits.

Labels: **[S]** sourced, **[C]** craft convention, **[L]** law (research, not legal advice).

## When to use it

- Footage: packshots, a storefront, product photos; logos and offer artwork supplied; little usable
  action. Intent: a sale, a voucher, a launch, an opening, a campaign date (11.11, 12.12).
- Not this playbook: a demo that proves the product (`product-demo`).

## Questions to ask when the brief does not say

1. The exact offer: price, discount, voucher code, dates, conditions (minimum order, while stock lasts).
2. Where to act: TikTok Shop cart, a store address, a link in bio.
3. Logo and artwork files (`public/images/`), and whether the promotion is registered (khuyến mại).

## Structure (15–25 s)

| Phase | Purpose | Graphics |
|---|---|---|
| HOOK 0–2.6 s | The offer itself (the number) on the product | `price` or `stat`, big |
| PRODUCT 40% | What is on offer, hero shots | `title`, `image` (packshot or logo) |
| OFFER 30% | The terms: price, discount, dates, conditions | `price` (old price struck), `checklist` (terms), `sticker` |
| CTA 30% | Where and until when | `cart` (TikTok Shop) or `pin` (store), `stat` (days left, only if real) |

Proposition in the first 3 seconds and a clear CTA are TikTok's own documented guidance [S: TikTok
creative best practices]. Sharp, fast motion reads as urgency [S: SVGator]; one transition family per video [C].

## Editing

Cuts on the beat (`suggest_cuts.py --music … --playbook promo-sale`), `pushCut` into the offer, a
zoomThrough with a flash into the CTA. Packshots get pushes; stills (`image`) scale in. Repetition
(the offer at the start and the end) beats length.

## Sound

Bright, punchy music 110–140 bpm; a ding on the price, a pop on stickers (sfx-map). A short voiceover
can read the offer; captions `plain` then.

## Picture

Grade `vivid`, corrections **shared** (product colours consistent across shots). Theme `cool`, or the
brand's colours in a new theme (`references/typography.md` → Colour themes).

## Graphics

`price` with `old` (struck through) and `decimals` when needed · `stat` (a percentage, days left) ·
`checklist` for the terms · `sticker` (one) · `image` for the logo or packshot · `cart` or `pin`.
Never a fake button or a fake cart: the arrow points at the real product bar.

## Compliance [L]

Every price, discount and date matches the listing or the store's terms; the old price was real; no
false scarcity or invented countdown; conditions stated; logos and artwork owned or licensed;
superlatives ("rẻ nhất", "số 1") need documents (Luật Quảng cáo 2012 Đ8; TT 10/2013); ads labelled
(Luật Quảng cáo 75/2025); commercial-content disclosure on.

## Commands

```bash
python scripts/new_remotion_project.py ~/renders/sale --playbook promo-sale --proxies CLIPS
python scripts/suggest_cuts.py --music music.wav --end 20 --playbook promo-sale --json > cuts.json
python scripts/playbook.py skeleton promo-sale --cuts cuts.json --title "Sale 11.11" > edit-plan.md
```
