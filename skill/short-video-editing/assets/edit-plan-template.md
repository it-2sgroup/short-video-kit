# Edit Plan — [Product] / [Creator]

> Copy this file, fill it in, then run:
> `python scripts/pacing_checker.py <this-file>`
> The checker reads the scene table below, so keep its column headers intact.

**Product:** [name]
**Creator / account:** [handle]
**Platform:** TikTok Shop
**Target runtime:** 30–40s
**Product card:** [TikTok Shop product URL]
**Source footage:** [paths or shot list reference]

---

## Scenes

Timestamps are in seconds from the start. Scenes must tile the timeline with no gaps and no
overlaps. No scene may exceed 4.0s; the hook must resolve by 3.0s.

| # | Start | End | Source | In | Type | Shot | On-screen text | Audio |
|---|-------|-----|--------|----|------|------|----------------|-------|
<!-- Source/In = which clip and its source timecode. Drop both columns when shooting to order.
     Start/End are timeline positions and are what pacing_checker.py reads. -->
| 1 | 0.0 | 1.4 | HOOK | [what the camera sees] | [text — must differ from VO] | [VO line / SFX] |
| 2 | 1.4 | 3.0 | HOOK | | | |
| 3 | 3.0 | 6.0 | PROBLEM | | | |
| 4 | 6.0 | 9.0 | PROBLEM | | | |
| 5 | 9.0 | 11.5 | CTA-EARLY | | Giỏ hàng ↙ | |
| 6 | 11.5 | 15.0 | DEMO | | | |
| 7 | 15.0 | 18.0 | DEMO | | | |
| 8 | 18.0 | 20.5 | RE-HOOK | | | |
| 9 | 20.5 | 24.0 | DEMO | | | |
| 10 | 24.0 | 27.0 | DEMO | | | |
| 11 | 27.0 | 30.5 | REVEAL | | Cùng một góc máy | [music out 0.5s before] |
| 12 | 30.5 | 34.0 | REVEAL | | | |
| 13 | 34.0 | 37.0 | CTA-CLOSE | | Giỏ hàng ↙ | |

**Scene types:** `HOOK`, `PROBLEM`, `CTA-EARLY`, `DEMO`, `RE-HOOK`, `REVEAL`, `CTA-CLOSE`, `B-ROLL`

---

## Voiceover script

Written to roughly 4.5–5 words per second at commerce pace — about 150–170 Vietnamese words for a
35-second video including pauses.

| Scene | Line |
|-------|------|
| 1 | |
| 2 | |

**Word count:** [n] → estimated [n ÷ 4.75] seconds of speech

---

## Shot list

Shots to capture, grouped by setup so the shoot can be ordered efficiently.

| Setup | Shots needed | Notes |
|-------|--------------|-------|
| Locked tripod, front-on | | AWB + AE locked before rolling |
| | | |

---

## Compliance check

Confirm each before delivery. See `references/platform-specs.md`.

- [ ] No antibacterial / antimicrobial claim
- [ ] No "instant" or immediate-result claim
- [ ] No "removes all stains" / ends-all-problems framing
- [ ] No money-back or guaranteed-results claim
- [ ] No absolute superlative (except own-sales claims, which are permitted)
- [ ] No competitor comparison
- [ ] No false scarcity
- [ ] Before/after: locked camera, constant lighting, **no cut across the reveal**
- [ ] Any sped-up footage is labelled on screen
- [ ] No fake UI elements — CTA points at the real product card
- [ ] Commercial disclosure toggle to be enabled at upload
- [ ] Music is from the Commercial Music Library, or original audio only
- [ ] Captions sit inside the safe zone (y 250–1410, x 60–940)

---

## Pacing check result

Paste the output of `python scripts/pacing_checker.py <this-file>`:

```
```

---

## Deliverables

- [ ] `edit-plan.md` (this file, passing the checker)
- [ ] `captions.srt`
- [ ] Shot list
- [ ] Remotion composition — or ffmpeg commands, or CapCut instructions
