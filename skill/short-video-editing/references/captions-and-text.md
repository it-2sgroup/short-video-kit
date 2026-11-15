# Captions and On-Screen Text

TikTok's creative guidance asks for captions or concise overlay text on every video, at 5–10 words
per second of on-screen text (`platforms.md` §3). Beyond sound-off viewing, burned-in words are read by
the platforms for search, so they affect discovery. Titles and graphic text are in `typography.md` and
`layout-and-motion-graphics.md`; this file is about spoken captions and the words that work beside them.
**[S]** sourced, **[C]** craft convention.

---

## Burned-in, not platform captions

Platform auto-captions can be switched off and are often wrong on Vietnamese. Burn captions in
whenever there is a voice. Captions take the **words from the script** and the **timing from Whisper**
(`align_captions.py`): Whisper mishears Vietnamese ("túi xách", handbag → "tui sách").

## Styles (`project.json` `captionStyle`; default from the playbook)

| Style | What it shows | Playbooks | Why |
|---|---|---|---|
| `karaoke` | the phrase (≤ 2 lines), the spoken word coloured | product-demo, tutorial, food-fnb, real-estate:voiceover | the 2025–26 default in commerce; whole phrase readable |
| `pop` | one phrase of ≤ 5 words (≤ 20 characters) on one line, bigger (66 px), the spoken word coloured and springing | talking-head, fashion-beauty | the bold education style; still a whole phrase at once |
| `plain` | the phrase, no highlight | promo-sale, testimonials, calm or serious content | static sentences read as sober |
| `none` | nothing | real-estate, montage-recap (music only) | no voice, nothing to caption |

### How the spoken word is marked (`captionHighlight`, or `Highlight` in a caption band)

| Value | Look |
|---|---|
| `color` (default) | the word turns the highlight colour and swells |
| `box` | a rounded block hugs the word and hops to the next |
| `underline` | a bar draws under the word |
| `glow` | a halo glows around the word |

Keywords (`captionKeywords`) are marked all the time (bigger, coloured) whatever the value. Pick the one that stays readable on the
footage: `box` on busy backgrounds, `underline` on calm ones.

**Why no word-by-word reveal** [S]: viewers read ahead. Deaf and hard-of-hearing viewers preferred 6- and
12-word lines over single words (ASSETS 2021, they split attention between captions and picture), and
highlighting 5–15% of the important words improved comprehension without distracting (ASSETS 2019).
Revealing one word at a time stops the look-ahead. Vietnamese is monosyllabic, so a "word" is a
syllable: one-word captions would be fragments. Both styles that highlight show the whole phrase from
its first word.

## Grouping and timing

| Parameter | Value | Source |
|---|---|---|
| Line length | ≤ ~26 characters per line at 58 px, ≤ 2 lines (pop: one line of ≤ 5 words, 20 characters) | Netflix: 42 chars/line, 2 lines [S], scaled to a phone frame [C] |
| Reading speed | ≤ ~17–20 characters/s | Netflix adult 20 cps [S] |
| On screen | 0.8–7 s per group; never under 0.45 s (the sync report flags it) | [C] |
| Groups at once | 1 | two groups compete and neither is read |
| Breaks | after punctuation, before conjunctions; keep noun phrases together | Netflix [S] |
| Emphasis | colour on ≤ 15% of the words | ASSETS 2019 [S] |

Fast speech gives fast captions: reading speed is a **script** problem (the word budget), not an edit
problem. What the edit must avoid is a group that flashes: `align_captions.py` merges them.

## Placement

The caption band is the lower third: y ≈ 1340, 58 px, ≤ 2 lines, x 90–890 (clear of TikTok's action
rail), lifted 120 px while a `cart` arrow is on screen. Reels ads move it to y ≈ 1100
(`--platform reels-ad`, Meta keeps the bottom 35% clear). The middle of the frame belongs to the
footage: big captions in the middle pull the eye off the subject.

- Never centre with `left: 50%; translate(-50%)`: long text clips. Use a full-width container.
- Never over the subject at the moment that matters (the detail, the dish, the face): move it or drop it.

## Contrast

Variable backgrounds (fabric, foam, sky, white walls): outlined text with a soft shadow (the kit's
`OutlineText`), never a full-width bar. White on white fabric disappears: check every caption on the
contact sheet; over white garments use the `outline` or `marker` title styles for titles.

## Text that does work the voice is not doing

Picture, text and voice carry three different messages; a caption that only repeats the voice wastes
a channel — that is why **titles** say something else.

| Moment | Voice says | Title says |
|---|---|---|
| Hook (demo) | "I thought I would have to throw this part away" | "This, 10 minutes ago" |
| Room (property) | "The living room gets sun all morning" | `label`: "Living room · 32 m²" |
| Step (tutorial) | "I put this ingredient in first" | `step`: "Step 1 — wait 5 minutes" |
| Point (talking head) | "Most people lose money at this step" | `stat`: "73% · the shop's own survey" |
| CTA | "I put it in the cart at the bottom left" | "Cart ↙" |

Procedural facts (steps, timings, quantities, prices, areas) read faster than they are heard. Three
kinds of text pull extra weight: **search keywords** (the problem, the dish, the neighbourhood);
**time-compression labels** ("sped up ×8", "after 10 minutes"), required in spirit by the instant-effect
rules; **evidence labels** ("Same camera angle", "illustration", "estimate").

## Pointing at the cart (TikTok Shop only)

Point at the **real** product bar (`cart`, aimed at (112, 1677)); never draw a fake cart or button
(`claims-and-compliance.md` §1). Reels have no product bar: no arrow there.

## SRT for a human editor

```
1
00:00:00,706 --> 00:00:01,967
Hey everyone
```

Commas as the decimal separator, `HH:MM:SS,mmm`, a blank line between entries. CapCut, Premiere and
DaVinci import it directly.
