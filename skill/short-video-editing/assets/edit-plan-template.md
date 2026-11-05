# Edit Plan — [Product] / [Creator]

> Fill this in, then run:
> `python scripts/pacing_checker.py <this-file>`
> `python scripts/plan_to_project.py <this-file> --out project.json --voice audio/x.mp3 --captions captions.srt --words words.json --auto-camera --auto-sfx`
> Keep the column headers: the scripts find columns by name.

**Product:** [name]
**Creator / account:** [handle]
**Platform:** TikTok Shop
**Target runtime:** 30–40s
**Product card:** [TikTok Shop product URL]
**Source footage:** [paths or shot list reference]
**Content type:** [hands-only demo / product close-up / talking head / screen tutorial / listicle]

---

## Scenes

Seconds from the start. Scenes tile the timeline with no gaps or overlaps. Outside the hook a scene
lasts 2.5–4.0s (aim for 3–4s); the hook is two ~1.5s beats and resolves by 3.0s. Cut on pauses in
the voice, never inside a word.

- **Source / In** — clip and the source timecode of the planned cut (the renderer borrows ~0.2s of
  handle on each side for the transition). Drop both when shooting to order.
- **Transition** — how the scene is entered: `fade` (default), `slide [dir]`, `wipe [dir]`, `iris`,
  `pushCut`, `zoomThrough`, `blurDissolve`, `whip [dir]`, `flip [dir]`, `crossZoom`, `cut`; optional
  length (`14f`) and accent (`+flash`, `+leak`). `–` on scene 1. See `references/transitions.md`.
- **Camera** — `push [a>b]`, `pull [a>b]`, `pan left|right|up|down [6%]`, `hold`, optional
  `focus x,y`. Leave blank to let `--auto-camera` vary it. See `references/camera-moves.md`.

| # | Start | End | Source | In | Type | Transition | Camera | Shot | Audio |
|---|-------|-----|--------|----|------|------------|--------|------|-------|
| 1 | 0.0 | 1.5 | [clip] | [s] | HOOK | – | push 1.1>1.0 | BEFORE: [what the camera sees] | [VO line] |
| 2 | 1.5 | 3.0 | [clip] | [s] | HOOK | wipe right 14f | | AFTER: same item, same framing | |
| 3 | 3.0 | 6.2 | | | PROBLEM | fade | | | |
| 4 | 6.2 | 9.0 | | | PROBLEM | slide left | | | |
| 5 | 9.0 | 12.0 | | | CTA-EARLY | fade | | | |
| 6 | 12.0 | 15.3 | | | RE-HOOK | zoomThrough +flash | | Product hero shot | |
| 7 | 15.3 | 18.6 | | | DEMO | fade | | | |
| 8 | 18.6 | 21.8 | | | DEMO | slide up | | | |
| 9 | 21.8 | 24.9 | | | DEMO | fade | | | |
| 10 | 24.9 | 28.0 | | | REVEAL | wipe right +leak | hold | Same framing as the BEFORE | [music out 0.5s before] |
| 11 | 28.0 | 31.0 | | | REVEAL | blurDissolve | | | |
| 12 | 31.0 | 34.2 | | | CTA-CLOSE | slide up | | | |
| 13 | 34.2 | 38.1 | | | CTA-CLOSE | fade | | | |

**Scene types:** `HOOK`, `PROBLEM`, `CTA-EARLY`, `DEMO`, `RE-HOOK`, `REVEAL`, `CTA-CLOSE`, `B-ROLL`

---

## Overlays

Graphics and titles, on their own timeline. See `references/layout-and-motion-graphics.md` and
`references/typography.md`.

- **Start** — seconds, or `@"word or phrase"` (`#2` for the second occurrence) to land 3 frames before
  that word.
- **End** — seconds, `+2.5`, `auto` (reading time), `@"word"`, or `cut` (3 frames before the next cut).
- **Component** — `title`, `callout`, `highlight`, `step`, `checklist`, `price`, `cart`, `sticker`,
  `progress`, `magnifier`, `thumbs`, `compare` (TRƯỚC/SAU), `ranking`, `lowerThird`, plus `punch` (camera punch-in) and
  `sfx` (a hand-placed sound cue, `src=sfx/riser.wav; volumeDb=-12`; `--auto-sfx` adds the rest).
- **Zone** — `top`, `upper`, `center`, `lower` (or `–`). **Tone** — `neutral`, `before`, `after`,
  `cta`, `product`.
- **Content** — `key=value; key=value`. Lists: ` / `. Points: `x,y` as fractions of the frame.

| # | Start | End | Component | Zone | Tone | Content |
|---|-------|-----|-----------|------|------|---------|
| 1 | 0.0 | 1.4 | title | top | before | style=outline; lines=[promise]; sub=TRƯỚC · [honest label] |
| 2 | 1.6 | 2.9 | title | top | after | style=outline; lines=SAU KHI [action]; sub=đã rút gọn thời gian |
| 3 | 9.2 | cut | cart | – | – | text=Giỏ hàng ở góc trái |
| 4 | @"[product name]" | cut | title | top | – | style=stack; lines=[lead] / [main line]; accent=[one word] |
| 5 | @"[product name]" | +2.0 | punch | – | – | scale=1.12 |

---

## Voiceover script

Commerce pace ~4.5–5 words/s: about 150–170 Vietnamese words for 35 s including pauses.

| Scene | Line |
|-------|------|
| 1 | |

---

## Shot list

| Setup | Shots needed | Notes |
|-------|--------------|-------|
| Locked phone, top-down or front-on | | AWB + AE locked; leave space above and below the subject for graphics |

---

## Compliance check

See `references/platform-specs.md`.

- [ ] No antibacterial / antimicrobial claim
- [ ] No "instant" or immediate-result claim
- [ ] No "removes all stains" / ends-all-problems framing
- [ ] No money-back or guaranteed-results claim
- [ ] No absolute superlative (own-sales claims are permitted)
- [ ] No competitor comparison
- [ ] No false scarcity
- [ ] Before/after: same item, same framing, constant lighting; time compression labelled on screen
- [ ] Staged stains labelled (e.g. "vết thử bằng thuốc đỏ")
- [ ] No fake UI elements — the CTA points at the real product card
- [ ] Commercial disclosure toggle to be enabled at upload
- [ ] Music from the Commercial Music Library, or original audio only
- [ ] Graphics inside the safe zones; nothing over a face

---

## Pacing check result

```
```

---

## Deliverables

- [ ] `edit-plan.md` (passing the checker)
- [ ] `captions.srt` + `words.json`
- [ ] `project.json` (sync report reviewed) + rendered MP4, or editor instructions
