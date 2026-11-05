# Layout and Motion Graphics

Where graphics go and which ones to use. Components are in `assets/remotion-template/src/components`
and are placed from the plan's **Overlays** table. **[D]** documented, **[C]** convention.

---

## The frame (1080×1920)

TikTok publishes no pixel margins for organic posts; its ads page only offers template downloads
[D]. Third-party measurements disagree (top 108–240px, bottom 320–660px, right rail 120–300px). The
template uses the conservative union [C]:

| Region | Pixels | Use |
|---|---|---|
| Hard no-go | y < 220, y > 1400, and x > 900 when y > 700 | TikTok tabs, caption/username, action rail |
| Top band | y ≈ 270–560 (`zone: top`) | Hook titles, steps, cards, podiums |
| Upper | y ≈ 560–820 (`zone: upper`) | Secondary titles, CTA text, lists when the chest band is busy |
| Center | y ≈ 860 (`zone: center`) | Only over hands/products — never over a face |
| Chest band | y ≈ 1010–1180 (`zone: lower`) | Prices, checklists, lower thirds |
| Caption band | y ≈ 1190–1380 | Spoken captions only |
| Cart anchor | ≈ (300, 1440) | TikTok Shop's yellow basket. Point at it; never draw a fake cart |

QA the real UI with Remotion's TikTok safe-zone overlay element and a private test post [D].

**Film for graphics** (the main lesson from the creator Mike Like Design): frame the subject in the
middle third and leave empty space above the head and below the chin, so graphics have somewhere to
go. Put it on the shot list.

---

## Layout by content type

| Content | Subject | Graphics |
|---|---|---|
| Talking head | Face y ≈ 600–1190, never covered | Titles/cards in the head-room band; prices, checklists, lower-third in the chest band |
| Product close-up | Product centred y 500–1300 | Callouts in the side gutters (left preferred — the right rail covers the other side), ≤ 2 per side |
| Hands-only top-down demo (laundry, cleaning) | Bowl fills x 90–990, y 450–1350 | Titles and steps in the top band; circles/underlines on the stain; lists in `upper` |
| Screen tutorial | Device frame width ≤ 820 | Magnifier on the active element; step label on top |
| Listicle / ranking | — | Rank chip top-left, `ranking` podium at the reveal, `thumbs` recap at the end |

---

## Components (`component` → content keys)

| Component | What it does | Content keys | Rules |
|---|---|---|---|
| `title` | Five styles, see `typography.md` | `style, lines, accent, sub` | One per beat |
| `callout` | Dot pops on a part, leader line draws, frosted label slides in from the margin | `label, target=x,y, side, labelY` | **Only on a static moment** — if the product moves (pouring, lifting) the dot points at nothing. ≤ 2 at once. Leader < 250px |
| `highlight` | Hand-drawn circle / underline / arrow draws on | `shape, target, size` | Around the subject, not over it; 10-frame draw |
| `step` | Numbered chip + instruction | `n, text` | One step visible at a time, synced to the voice |
| `checklist` | Ticks draw on, rows stagger 9f | `items=a / b / c, title` | 3–4 rows; lifts itself clear of the caption band |
| `price` | Count-up (vi-VN format), pulse, struck-through old price | `value, unit, label, old, prefix` | Must match the product listing exactly |
| `cart` | Bobbing arrow toward the real basket + optional text | `text` | Early CTA (~9–12 s) and close; text in `upper` so it never meets a price |
| `sticker` | Rotated badge that pops and wobbles | `text, at, rotate` | One per video; no claims |
| `progress` | Bar fills across its life | `label` | Time passing ("Ngâm 1–2 tiếng · đã rút gọn thời gian") |
| `magnifier` | Lens showing a 2.2× crop of a clip | `clip, in, target, at, zoom, diameter` | Fine detail (texture, fine print); keep the camera still meanwhile |
| `thumbs` | Row of up to 3 frozen frames with captions | `cards=CLIP@sec:caption / …` | Recap at the end |
| `ranking` | Glossy tiles on podiums | `items=Label#rank / …` | Listicles only; no third-party logos without rights |
| `lowerThird` | Name bar | `name, role` | Creator/brand ID, 2–3 s |

Coordinates are fractions of the frame (`0.62,0.55`), measured on the **rendered** frame (the camera
may have zoomed). Check with a still.

---

## Density and rhythm [C]

- A new graphic event every 2–4 s (≈ 10–14 in 35 s), but **at most two informational elements at
  once** plus captions, and never two in the same zone (the sync report flags overlaps).
- Hold ≥ 0.3 s × words + 0.5 s, minimum 1.2 s; exit before the next element enters the same zone.
- Leave one or two clean beats (≥ 2 s) where the footage breathes.
- Graphics land 3 frames **before** their word (anchor with `@"word"` in the plan) and leave ≥ 3
  frames before a cut.
- Graphics and camera never peak on the same frame: while a callout enters, the camera holds.

Sources: Material motion durations (enter 225 ms, exit 195 ms, > 400 ms feels slow); TikTok creative
best practices (key message in 3 s, text overlays, stickers); Remotion safe-zone overlay; HyperFrames
`vertical.md`; iart-ai `tiktok-video-skills`; Mike Like Design TikTok (embed caption, Nov 2026) and
four reference screenshots.
