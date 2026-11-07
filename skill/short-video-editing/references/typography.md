# Typography

How on-screen words should look and move. Implemented in `assets/remotion-template`
(`theme.ts` for fonts/colours, `components/text/` for styles). Tags: **[D]** documented,
**[C]** craft convention or client preference.

---

## Fonts (Vietnamese)

Vietnamese needs the `latin` **and** `vietnamese` subsets: Google's `vietnamese` subset holds only
the extra marks (U+0102–0103, U+01A0–01B0, U+1EA0–1EF9 …); plain letters live in `latin` [D:
fonts.googleapis.com CSS, Remotion `loadFont` docs]. The template loads
`["latin", "latin-ext", "vietnamese"]`.

| Role | Template font | Why |
|---|---|---|
| Titles, labels, captions | **Be Vietnam Pro** 500/700/800/900 | Designed for Vietnamese; compact stacked marks |
| One accent word | **Playfair Display Italic** 700 | Serif-italic contrast against heavy sans |
| Prices, counters | **Anton** | Condensed, tall numerals |

Verified to ship a `vietnamese` subset (Google Fonts metadata, Nov 2026) and safe alternatives:
Inter / Inter Tight, Montserrat, Lexend, Plus Jakarta Sans, Archivo, Manrope, Bricolage Grotesque,
TikTok Sans, Nunito, Lora, Fraunces, Newsreader, Dancing Script.

**No Vietnamese subset — do not use for Vietnamese text:** Instrument Serif, DM Serif Display,
Bebas Neue, Archivo Black, Sora, Outfit, Urbanist, DM Sans, Figtree, Rubik, Fredoka, Caveat,
Kalam, Lobster Two. A subset existing does not prove the marks look good: render
`ẩ ặ ễ ộ ự Ữ Ằ` in any new font before adopting it.

Rules [C]: line-height ≥ 1.05 (≥ 1.2 for all caps) so marks above Ấ/Ộ don't collide; tracking no
tighter than −0.04em; any `overflow: hidden` reveal needs ~0.28em top padding or marks get clipped
(the template's `MaskRise` does this); split text for per-letter animation with
`Intl.Segmenter('vi', {granularity: 'grapheme'})` after `normalize('NFC')`, never by code point.

---

## The no-box rule (client)

The client rejected titles in dark pills with coloured borders: *"đừng bỏ trong cái khung viền…
mất tự nhiên"*. Contrast comes from, in order of preference:

1. A thick dark **outline drawn under the fill** (`OutlineText`: stroke ≈ font size ÷ 7 on a layer
   beneath, so it never eats the letters) plus a soft drop shadow.
2. A **gradient fill** with `filter: drop-shadow(...)` on the wrapper (a `text-shadow` would show
   through transparent gradient glyphs).
3. A **light frosted card** (`glass` style) — only over busy footage where 1–2 cannot be read. It is
   light, soft-shadowed and borderless-looking; never the dark bordered pill.

Components that draw a surface behind text: `title style=glass` and the `callout` label (light frosted
cards), `sticker` (filled pill), `marker` (a highlighter block behind one accent word), `ranking`
(tiles) and `thumbs` (framed stills). Everything else is bare text with an outline or shadow. On
product demos prefer `outline` and `marker` titles, `highlight`, `step`, `cart`; use the carded ones
only where the plain styles cannot be read, and tell the client which ones appear. Over **white
fabric** the readable styles are `outline` and `marker`; to keep variety, alternate those two and
reserve `glass` for the closing card.

---

## Title styles (`component: title`, `style=`)

| Style | Look | Use | Motion |
|---|---|---|---|
| `outline` | Tone-coloured heavy text, dark outline, optional white sub-line | Default for product demos and honest labels ("TRƯỚC", "SAU KHI NGÂM · đã rút gọn thời gian") | Fade + 24px rise, 10f |
| `stack` | Small lead line (64px/500) over a huge heavy line (≈2.5×, 900, white→sky gradient); one **accent** word in serif italic gradient | Hooks, product name, the key point — over dark or mid-tone footage; over white fabric it washes out like `gradient` | Lead fades up; main line rises through a mask (spring, 14f, +4f); accent blurs in (12f, +10f) |
| `gradient` | Heavy white→sky gradient, soft shadow, no outline | Verdicts, reveals over calm, **dark or mid-tone** footage — never over white fabric, where the white fill vanishes (use `outline` there) | Lines rise through masks, 3f stagger, settle from 1.04 scale |
| `glass` | Light frosted card, navy→royal gradient main line, small lead word | Section titles over busy footage, closing card | Card springs 0.92→1 and rises 40px; text rises inside |
| `marker` | Heavy outlined words; the **accent** gets a highlighter block that sweeps in and turns the word to ink | Naming the problem ("Vết ố"), a key spec | Text rises; block sweeps left→right over 12f from +10f |

Content: `lines=lead / main` (one or two lines), `accent=word in the main line`, `sub=small honest
label`. Exit for every style: fade + 12px lift over the last 8 frames (exits ~40% shorter than
entrances [C, HyperFrames motion rules]).

**Variety rule [C]:** 3–4 title styles per video, one dominant; never the same style on two
consecutive beats; one accent word per title.

---

## Sizes and placement (1080×1920)

- Titles 88–160px (auto-fitted to width by `fitSize`), labels ≥ 40px, nothing under 36px [C].
- At most ~14 characters on the big line; 2–6 words per title.
- Titles live in the **top strip** (y ≈ 236–420, `theme.zones`), at most two lines and ~190 px tall, so
  the centre of the frame stays free for the footage; keep x ≤ 900 below y ≈ 700 (TikTok's right rail).
- Never over a face. See `layout-and-motion-graphics.md` for the bands.

---

## Colour themes

`theme.ts` holds three palettes, switched by one `THEME` line that `new_remotion_project.py DEST
--playbook ID` writes from the playbook (or `--theme`; repeat after every `--update`):

| Theme | Look | Playbooks | Why |
|---|---|---|---|
| `cool` | white text, sky-blue gradients, navy/royal glass card | product-demo, talking-head, tutorial, montage-recap, promo-sale | neutral, reads on most footage |
| `warm` | ivory text, gold accents and highlighter, cream card, brown-to-vermilion line | food-fnb | amber, wooden or candle-lit footage, where blue accents clash (requested for the Kiiro Sushi videos, Nov 2026) |
| `luxe` | warm white, champagne gold, charcoal | real-estate, fashion-beauty | calm and premium; gold reads on white interiors and fabric |

Captions, prices, stats, specs and labels follow the theme (their accent is `toneColor.cta`). Callout,
compare and ranking cards keep their own light cards. A brand's colours = a new theme in `theme.ts`
(all keys of an existing one) and a playbook (or variant) that names it; `playbook.py check` then
accepts it.

---

## Captions vs titles

| | Captions (spoken words) | Titles (designed) |
|---|---|---|
| Source | `align_captions.py` (timing from Whisper, words from the script) | The plan's Overlays table |
| Font | Be Vietnam Pro 800, 58px, outline (≤ 2 lines, x 90–890) | Mixed weights, accent serif |
| Place | Lower third, y ≈ 1340 (`theme.captionTop`); 120 px higher while the cart arrow shows | Top strip |
| Motion | 4-frame fade per group; **karaoke**: the spoken word takes the accent colour and scales 1.08; **pop**: one phrase of ≤ 5 words on one line at 66 px, the spoken word springs to 1.12 | Choreographed entrance/exit |

Keep the caption highlight colour different from title accents. Don't animate a title entrance and a
caption change on the same frame — start titles on a pause. If a title repeats the spoken words,
consider `captionStyle: "none"` for that video or keep the title ≤ 5 words.

Sources: Remotion `loadFont`, `fitText`, `createTikTokStyleCaptions` docs; template-tiktok;
HyperFrames `captions.md`/`motion.md`; iart-ai `caption-animation`; Netflix Vietnamese timed-text
guide (17 cps, 5/6 s minimum); Google Fonts metadata.
