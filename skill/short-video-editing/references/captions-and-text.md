# Captions and On-Screen Text

TikTok's own creative guidance tells creators to include closed captions or concise overlay text
on every video (`ads.tiktok.com/business/library/Creative_Best_Practices_UKI_SMB.pdf`). Beyond
accessibility and sound-off viewing, on-screen text is OCR'd by TikTok for search indexing, so the
words you burn in affect discovery.

---

## Burned-in, not platform captions

Platform auto-captions can be switched off by the viewer and are frequently wrong on Vietnamese.
Burn captions into the frame. For commerce content this is the default.

---

## Grouping and timing

| Parameter | Value | Reason |
|---|---|---|
| Words per group | 2–4 | Legible at phone size; matches speech rhythm |
| Groups visible at once | 1 | Two groups on screen compete and neither is read |
| Minimum time on screen | ~0.5s + 0.3s per word | Below this, the line cannot be read before it changes |
| Style | Word-by-word highlight (karaoke) over static blocks | Widely reported to hold attention better; the magnitude claims circulating are vendor-sourced and not citable |

The minimum-display formula matters more than it looks. A four-word group needs about 1.7 seconds.
When captions are generated from word-level timings, fast speech produces groups that flash past
unreadably — merge them rather than shipping something nobody can read.

---

## Placement

Design to the conservative safe zone from `platform-specs.md` §6:

| Edge | Keep clear |
|---|---|
| Top | 250 px |
| Bottom | 510 px |
| Right | 140 px |
| Left | 60 px |

Usable band on a 1080×1920 frame: **y = 250 → 1410**, **x = 60 → 940** (and x ≤ 900 below y ≈ 700, where
TikTok's action rail sits — the template's caption band is x ≈ 130–950, y ≈ 1190–1380).

**Captions sit low-centre but above the bottom 510 px** — roughly y = 1150–1400. That clears
TikTok's own caption, username, audio tag and product card.

Two placement rules worth stating explicitly:

- **Never use `left: 50%; transform: translateX(-50%)`** to centre a caption. It clips at frame
  edges when the text is long. Use a full-width absolute container with `text-align: center`.
- **Never place a caption over the product or over the stain** during the demo. The whole point of
  those seconds is that the viewer sees the transformation. Move the caption up, or drop it.

---

## Titles and labels

Titles, labels and their styles (no boxes on product demos, the five title styles, fonts with
Vietnamese support) are in `typography.md`. This file is about spoken captions.

---

## Contrast over fabric

Fabric and foam are variable backgrounds — a caption that reads over a white shirt disappears over
a shadow. Use one of:

- A text shadow or stroke (simplest; `text-shadow: 0 2px 8px rgba(0,0,0,0.9)`)
- A scrim sized to the text, at 30–40% opacity

**Not a full-width bar.** A bar across the frame costs more of the picture than the text needs and
looks like a news ticker.

Guidance on blend mode by background brightness (0–255): under 60 use `screen`; 60–180 use
`overlay`; over 180 use normal with an opaque colour.

---

## Text that does work the voiceover is not doing

The hook has three channels — visual, text, audio — and they should carry three different
messages. A caption that merely transcribes the voiceover wastes the channel.

| Moment | Voiceover says | On-screen text says |
|---|---|---|
| Hook | "Chỗ ố này mình tưởng phải bỏ áo luôn" | "Cái áo này 10 phút trước" |
| Demo | "Mình đổ chai hồng lên trước" | "Bước 1 — ngâm 5 phút" |
| Reveal | "Mấy vợ nhìn nè" | "Cùng một cái áo, cùng một góc máy" |
| CTA | "Mình để ở giỏ hàng góc trái rồi" | "Giỏ hàng ↙" |

Procedural detail is better on screen than in speech — steps, timings and dilutions read faster
than they are heard, and putting them in text frees the voiceover for reaction and persuasion.

Three kinds of text pull extra weight:

- **Keyword text for search.** Burn the problem in words — "vết thâm kim", "ố vàng", "dầu mỡ".
  TikTok OCRs it.
- **Time-compression labels.** "tua nhanh ×8", "sau 2 tiếng ngâm". Required in spirit by the
  instant-effect rules in `platform-specs.md`.
- **Evidence labels.** "Cùng một góc máy", "Nửa trái ngâm rồi". These pre-empt the
  "staged/fake" reaction and cost one line.

---

## Pointing at the cart

The CTA text should point at the **real** TikTok Shop element.

Permitted: an arrow or hand gesture toward the actual product card, with text like "Giỏ hàng ↙".

Prohibited: drawing a fake cart, a fake "Buy" button, or a fake swipe-up. TikTok's policy names
fake interactive elements as clickbait. See `platform-specs.md` §4.

Since the product card sits in the bottom-left area that the safe zone already excludes, place the
CTA text just above it and let the arrow do the work.

---

## Generating captions from a voiceover

When the voiceover is synthesised, word-level timings usually come free. `edge-tts` (free,
supports Vietnamese) emits them when `boundary="WordBoundary"` is set:

```python
communicate = edge_tts.Communicate(text, "vi-VN-HoaiMyNeural", boundary="WordBoundary")
async for chunk in communicate.stream():
    if chunk["type"] == "WordBoundary":
        # chunk["offset"] and chunk["duration"] are in 100-nanosecond units
        start = chunk["offset"] / 10_000_000
```

Two practical notes from using this on Vietnamese commerce scripts:

- The free endpoint rate-limits. Synthesise one line at a time with a 2–3 second gap and retry
  with backoff; bursts fail with "No audio was received".
- Offsets are relative to each line's own audio. Add the cumulative offset of preceding lines and
  any inter-line silence to get absolute timeline positions.

For recorded human voiceover, `python scripts/align_captions.py <file> --lang vi`
produces the same word-level JSON.

---

## SRT output

When the deliverable is for a human editor rather than a Remotion render, emit standard SRT:

```
1
00:00:00,706 --> 00:00:01,967
Ủa mọi người ơi

2
00:00:02,743 --> 00:00:03,558
Có ai giống mình
```

Commas as the decimal separator, `HH:MM:SS,mmm`, blank line between entries. CapCut, Premiere and
DaVinci all import this directly.
