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
| Hard no-go | y < 220, y > 1400, and x > 900 when y > 700 | TikTok tabs, caption/username, action rail (the product bar starts at y ≈ 1640; the cart arrow is the one graphic allowed below 1400) |
| Top strip | y ≈ 236–420 (`zone: top`) | Hook titles, steps, cards: hugging the top edge of the safe area |
| Upper | y ≈ 470 (`zone: upper`) | Rare secondary title when the top strip is taken |
| Center | y ≈ 860 (`zone: center`) | Only a callout or highlight on the product itself, short |
| Lower | y ≈ 1230 (`zone: lower`) | Progress label, a price: close to the captions, never in the middle |
| Caption band | y ≈ 1340 (58 px, ≤ 2 lines, x 90–890) | Spoken captions only; lifted 120 px while a `cart` overlay is on |

**Viewer-first rule (why the zones moved).** The picture is the reason people stay; text is the
reason they understand. With the old zones (titles at y 270–560, captions at y 1190) text blocks sat
close to the middle and covered the action, so viewers read subtitles instead of watching (client
feedback, Nov 2026). Now the middle ~900 px (y ≈ 420–1330) belongs to the footage: titles are one strip
at the top edge, captions one short block just above the bottom no-go, and nothing else stands between
them except a callout, label or circle *on* the subject. Check every video on a contact sheet: the
subject (the stain, the room, the dish, the face) is fully visible in every scene.

**Reels ads** keep the top 14%, bottom 35% and 6% each side clear (y 269–1248, x 65–1015):
`plan_to_project.py --platform reels-ad` raises the captions to y ≈ 1100 and flags overlays outside
that box and anything in `lower` (`platforms.md` §2).
| Cart anchor | (112, 1677) | Centre of the yellow bag tile of TikTok Shop's product bar (below). Point at it; never draw a fake cart |

**Where the product bar really is** (measured, not estimated). On a 1284×2778 iPhone screenshot of the
feed (a video with a "05 kg miến sợi…" product link) the yellow bag tile spans x 48–107, y 2180–2239 and
the tab bar starts at y 2530. The video fills the 1284×2530 area above the tab bar, so a 1080×1920 frame
is scaled ×1.3177 and cropped 69.5 px on each side; in frame pixels the tile centre is **(112, 1677)**,
the bar spans x 80–607, y 1644–1709, the account name starts near y 1750 and the description near
y 1820. The action rail sits at x ≳ 920 from y ≈ 960 down to 1760. Other phones differ by about 40 px, so
the arrow aims above the tile, not at its edge. Two things follow: the bottom no-go starts at y ≈ 1640,
not 1400, and a graphic in the strip y 1400–1640 at the left is free of TikTok UI (the cart arrow lives
there; nothing else should, because phones differ). Check any change with a mockup: scale a still to
1423×2530, crop 1284 wide, and draw the tile box at (48, 2180, 60×60).

QA the real UI with Remotion's TikTok safe-zone overlay element and a private test post [D].

**Film for graphics** (the main lesson from the creator Mike Like Design): frame the subject in the
middle third and leave empty space above the head and below the chin, so graphics have somewhere to
go. Put it on the shot list.

---

## Layout by content type

| Content (playbook) | Subject | Graphics |
|---|---|---|
| Talking head | Face y ≈ 600–1190, never covered | Titles/stat/chart in the head-room band; checklists, lower-third in the chest band; `pop` captions |
| Product close-up (product-demo) | Product centred y 500–1300 | Callouts in the side gutters (left preferred — the right rail covers the other side), ≤ 2 per side |
| Hands-only top-down demo (product-demo, tutorial) | Bowl or bench fills x 90–990, y 450–1350 | Titles and steps in the top band; circles/underlines on the subject; lists in `upper` |
| Room or exterior (real-estate) | The whole frame; verticals straight | `label` bottom-left per room, `pin` top-left on arrival, `specs` + `price` over one calm wide shot, never over the view |
| Dish (food-fnb) | Plate centred, steam visible | `label` with the dish name, `price` low, `pin` at the end; nothing over the money shot |
| Full-body look (fashion-beauty) | Person x 200–880, head below y 300 | `label` (item · price) beside the garment, left or `align=right`; title only on the hook |
| Montage | The whole frame | Two to four words; `pin` with place and date; logo at the end |
| Offer (promo-sale) | Product or storefront visible behind the type | Big `price`/`stat` in `upper`, terms as a `checklist`, one `sticker` |
| Screen tutorial | Device frame width ≤ 820 | Magnifier on the active element; step label on top |
| Listicle / ranking | — | Rank chip top-left, `ranking` podium at the reveal, a `thumbs` strip when the voice lists three things |

---

## Components (`component` → content keys)

| Component | What it does | Content keys | Rules |
|---|---|---|---|
| `title` | Five styles, see `typography.md` | `style, lines, accent, sub` | One per beat |
| `callout` | Dot pops on a part, leader line draws, frosted label slides in from the margin | `label, target=x,y, side, labelY` | **Only on a static moment** — if the product moves (pouring, lifting) the dot points at nothing. ≤ 2 at once. Leader < 250px |
| `highlight` | Hand-drawn circle / underline / arrow draws on | `shape, target, size` | Around the subject, not over it; 10-frame draw |
| `step` | Numbered chip + instruction | `n, text` | One step visible at a time, synced to the voice |
| `checklist` | Ticks draw on, rows stagger 9f | `items=a / b / c, title` | 3–4 rows; lifts itself clear of the caption band |
| `price` | Count-up (vi-VN format), pulse, struck-through old price | `value, unit, label, old, prefix, decimals` | Must match the listing exactly; decimals with a point in the plan (`value=5.2; decimals=1` shows "5,2") |
| `cart` | Hand-drawn arrow that curves down onto the product bar's bag tile (theme `cartPoint`), draws on, then bobs; label above its start | `text` | Early CTA (~9–12 s) and close. The label sits right above the arrow; give a `zone` only to move it. Never add a second graphic in the bottom-left |
| `sticker` | Rotated badge that pops and wobbles | `text, at, rotate` | One per video; no claims |
| `progress` | Bar fills across its life | `label` | Time passing ("Ngâm 1–2 tiếng · đã rút gọn thời gian") |
| `magnifier` | Lens showing a 2.2× crop of a clip | `clip, in, target, at, zoom, diameter` | Fine detail (texture, fine print); keep the camera still meanwhile |
| `thumbs` | Strip of up to 3 framed stills with a caption under each (the three-photo header) | `cards=CLIP@sec:caption+@"word"~x,y,zoom / …` | Top zone; see "The three-photo header" below |
| `compare` | BEFORE and AFTER frames of the same item, TRƯỚC/SAU labels (`beforeLabel`, `afterLabel` to change them), the AFTER arriving over a dark scrim | `before=CLIP@sec; after=CLIP@sec; mode=side/slider/stack; beforeFocus, afterFocus, zoom; note` | The reveal (zone `top`, ≥ 2.5 s, note stays clear of `lower`); frames from ranges already shown; see `before-after.md` |
| `ranking` | Glossy tiles on podiums | `items=Label#rank / …` | Listicles only; no third-party logos without rights |
| `lowerThird` | Name bar | `name, role` | Creator/brand/agent ID, 2–3 s; credentials must be real |
| `specs` | Up to six facts with line icons, popping in turn (two per row past three) | `items=area:85 m² / bed:3 PN / bath:2 WC / compass:Đông Nam; title` | Icons: `area bed bath compass car floor tree pool clock tag pin star`. Over a calm shot; facts from the documents |
| `pin` | A map pin drops with a ring, the place name and a second line slide in | `title, sub, at=x,y` | Arrival or the end; "~15 phút (ước tính)" for travel times |
| `label` | A quiet tag (name + detail) with a line drawing under it | `text, sub, at=x,y, align=left/right` | Rooms, dishes, items; one at a time; default bottom-left above the captions |
| `stat` | One figure counting up (vi-VN format), unit and label | `value, unit, label, prefix, decimals` | A real number with a source; holds ≥ 1.5 s after it lands |
| `chart` | 2–5 horizontal bars growing in turn, values counting up, the largest highlighted | `items=Label#45 / Label#120; unit; title; highlight` | Real measurements only; one idea per chart |
| `image` | A still from `public/` scaling in, framed (`card`) or bare (`none`) | `src=images/x.png, at=x,y, width, frame, caption` | Floor plans, logos, packshots; files the user owns |
| `burst` | The opening shout as a pile of copies: a gray ghost under, then more and more tilted copies pop up around it, each larger and nearer the frame edge ("hidden letters jumping up") | `text, at, copies, speed, fill, stroke, hold` | The first second, once (the alternative to `arc`); `speed=1.7` builds it in ~0.4 s |
| `phrase` | A white lead line over a loud emphasis line (red, or `emphColor=yellow`), letters scatter in and fly apart on exit; the lead can come first and the emphasis `emphAt` seconds later | `lead, emph, emphAt, y, emphColor, enter=scatter/rise, exit=scatter/fade` | The agency look: every spoken thought is a block; one block at a time (while a `logo` or `counter` holds the top strip, a phrase sits at `y=0.285`); `y` is the top as a fraction of the height |
| `pill` | A rounded label (white with red text, or red with white text) whose text types in | `text, variant=white/red, at=x,y, size, type` | Lists of two or three offers one under another; <= 30 characters |
| `arc` | Letters along an arc with echoes fanning out behind them | `text, echoes, at, fill, stroke` | The opening shout (a city name), once; it is there on frame 0. The alternative to `burst`: use one of the two |
| `script` | One handwritten phrase in the highlight colour (Pacifico), letters scatter in | `text, at, rotate, size` | One per video, on a word that deserves warmth |
| `tag` | A small loud label (red letters, white outline) popping over a card | `text, at` | "SẢN PHẨM", "F&B": kinds of clients or work; <= 14 characters |
| `logo` | The brand mark (`public/images/logo.png`, a transparent PNG) arrives out of a motion blur and snaps sharp; `tint=white` for a red backdrop, `hold=1` for an end card | `at, width, src, tint, hold` | On the beats that name the brand and at the end; keyed from the brand's own file (a vector or PNG the user supplies; never redraw it) |
| `counter` | A number pops, an arrow draws, the second number pops, a unit slides up | `from, to, label, at` | One range the voice says ("5 -> 10 ngày"); the figures are the brand's own and need evidence |
| `icon` | A pictogram popping in at a point: `target megaphone bang search check` | `name, at, size, rotate` | A word that names the picture (mục tiêu, đừng bỏ qua); not on faces |
| `circled` | A label that a hand-drawn ellipse draws around, a pictogram popping in below it | `text, at, icon` | One support or promise ("HỖ TRỢ"); the word is said while it is on |
| `rawfinal` | Two cards side by side playing the same take: the unedited clip (`public/raw/…`) and the finished look | `raw, final, at, saturate, contrast, brightness` | The honest "what editing does": same take, only the edit differs; put it on a card scene with no clip |

Coordinates are fractions of the frame (`0.62,0.55`), measured on the **rendered** frame (the camera
may have zoomed). Check with a still.

### The three-photo header (`thumbs`)

A strip of three small framed stills across the top, each with a two-or-three-word caption, while the
main footage plays below: the layout of Mike Like Design's explainers ("video ra rất lỏ / prompt từng
bước / vừa lâu, vừa tốn token"). It turns a spoken list of three into something the eye can scan, and
it fits where the voice names three things.

- **When it fits:** a spoken list of exactly three: three problems ("áo trắng ố / đồ màu dính mốc /
  dính dầu mỡ"), three steps, three results. Not for one or two items, and not at the same time as a
  `title` or `step` in the top zone (the sync report flags the overlap).
- **Frames:** one still per item, from ranges the video already shows, with the item itself in view.
  Small cards hide detail, so frame the subject (here the stain): `~x,y,zoom` after the caption (`~0.22,0.34,2` centres
  that point of the source frame and magnifies 2×). Check the stain is visible on a still.
- **Sync:** each card lands on its own word: `+@"áo trắng bị ố"` after the caption gives the card its
  delay from that phrase (or `+1.2` for seconds). Without it the cards follow each other 4 frames apart.
- **Timing:** start at the first item's word, hold through the last item's phrase and a beat after,
  and end at least 3 frames before the next cut. The strip may run across a cut.
- **Look:** white rounded border, soft shadow, caption in the outlined text style. No coloured boxes.

```
| 3 | 4.05 | 8.55 | thumbs | top | – | cards=IMG_0319@33.5:Áo trắng bị ố+@"áo trắng bị ố"~0.22,0.34,2 / IMG_0318@1.5:Đồ màu dính mốc+@"đồ màu dính mốc"~0.62,0.32,2 / IMG_0331@0.8:Dính dầu mỡ+@"dính dầu mỡ"~0.6,0.3,1.8 |
```

---

## Text effects (`fx=` of `phrase`, `leadFx=`, `tag`)

One engine (`components/text/Fx.tsx`), fourteen effects; pick by what the words *do*, and never the same effect on two neighbouring blocks:

| `fx` | Look | Use it on |
|---|---|---|
| `scatter` | letters fly in from random places and settle; fly apart on exit | the default loud line |
| `slam` | the whole line slams in from 3x size and shakes | a shout, a claim ("ĐỪNG BỎ QUA!!!", "CHỈ CÓ TRONG THÁNG NÀY!") |
| `stamp` | tilted, lands with an overshoot, a double rule pressed round it | a verdict or a promise ("GIẢI QUYẾT VẤN ĐỀ") |
| `glitch` | RGB-split jitter that settles | the problem, the pain ("THIẾU VIDEO…") |
| `drop` | letters fall from above and bounce | a lead line that sets something down |
| `elastic` | rubbery overshoot, letter by letter | the answer after a problem |
| `wave` | letters rise in a ripple and keep rippling | friendly, flowing lines |
| `flip` | letters flip up in 3D | an instruction ("Bạn chỉ cần chọn mục tiêu") |
| `maskwipe` | a coloured bar wipes the text into view | a list item, a plan |
| `split` | two halves slide in from opposite sides and join | a before/after word pair |
| `shine` | a light sweep crosses the finished text | the line that names the offer |
| `neon` | flickers on, then glows | the call to action ("INBOX NGAY") |
| `typewriter` | letters appear one by one with a cursor | a short label, a quote |
| `rise` | a quiet rise | calm lead lines |

Rotation rule used on the SISMO pitch: lead lines `rise`, `maskwipe`, `drop`, `wave`, `flip`; emphasis lines `slam`, `glitch`, `elastic`, `stamp`, `shine`, `neon`; at most
two loud effects within any 3 s.

## Card layout and the animated grid (`Layout` column: `card`, `expand`)

A scene with `Layout = card` plays its clip (camera moves included) inside a rounded 9:16 card (690 x 1227, top at y 360) floating over an animated
backdrop: a net of fine lines on a deep gradient, blown by a slow wind like a banner (`components/graphics/Grid.tsx`; colours from the theme, `grid` and
`card` in `theme.ts`). It is the portfolio or process section of an agency pitch: 0.8-1.6 s per card (a closing `expand` card longer), `cardSlide` between them, captions in a strip above the
card (`Caption bands`: `| 14.7 | 19.6 | 250 | 44 |`), one tag per card at most. A card scene whose Source is `-` shows the grid alone, for overlays that draw their
own cards (`rawfinal`) or an end card. `Layout = expand` starts as a card and grows to the full frame in 14 frames with a fabric-like wave (an SVG
displacement filter): follow a card with it and a `cut`. The grid shows only where a card scene is transparent, so full-frame scenes cover it.

## Motion conventions [C]

- Count-ups take 0.6–1.2 s with an ease-out and hold ≥ 1.5 s; bars grow ~0.5 s each, staggered; the
  motion never changes the data [S: data-visualisation motion guides].
- Easing carries tone: sharp and fast reads as urgency (promo), slow and eased as calm and premium
  (property, fashion) [S: SVGator]. The components share `theme.motion`; a playbook's tone comes from
  its transitions and music more than from the graphics.
- One idea per graphic: if the viewer has to read it twice, it failed.

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
