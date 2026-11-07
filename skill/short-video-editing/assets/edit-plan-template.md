# Edit Plan — [video name]

> Start from the playbook: `python scripts/playbook.py skeleton <id> --cuts cuts.json --title "…" > edit-plan.md`
> fills the header, the Scenes rows (Type, Transition, Speed, a hint per beat) and the compliance list.
> Then: `pacing_checker.py edit-plan.md` · `plan_scenes.py --plan edit-plan.md …` ·
> `plan_to_project.py edit-plan.md --out RENDER/v1.json --voice … --captions … --words … --auto-camera --auto-sfx`
> Keep the column headers: the scripts find columns by name. Keep this file: it is the footage ledger.

**Playbook:** [id or id:variant — product-demo, real-estate, food-fnb, talking-head, tutorial, fashion-beauty, montage-recap, promo-sale]  
**Platform:** [tiktok, reels; organic or boosted as an ad]  
**Target runtime:** [from the playbook]  
**Drive:** [voice: cuts on pauses · music: cuts on beats]  
**Look:** [theme, grade, captions — from the playbook]  
**Goal / CTA:** [what the viewer should do]  
**Subject:** [product / property / place / speaker, with the facts that will be on screen and where they come from]  
**Source footage:** [folder; analysis.json]

---

## Scenes

Seconds from the start. Scenes tile the timeline with no gaps or overlaps, inside the playbook's scene
lengths; the hook resolves by 3.0 s. Cut on pauses in the voice or on beats of the music, never inside a word.

- **Source / In** — clip and the source timecode at the planned cut (the renderer borrows ~0.2 s of
  handle each side for the transition).
- **Type** — the playbook's beat (HOOK, DEMO, LIVING, STEP, POINT, LOOK, OFFER…).
- **Transition** — how the scene is entered: `fade`, `slide [dir]`, `wipe [dir]`, `iris`, `pushCut`,
  `zoomThrough`, `blurDissolve`, `whip [dir]`, `flip [dir]`, `crossZoom`, `cut`; optional length (`14f`)
  and accent (`+flash`, `+leak`). `–` on scene 1. See `references/transitions.md`.
- **Camera** — `push [a>b]`, `pull [a>b]`, `pan left|right|up|down [6%]`, `hold [scale]`, optional
  `focus x,y` and `roll a>b`. Blank = `--auto-camera` (the playbook's pattern). `references/camera-moves.md`.
- **Speed** — blank (1x), `2x`, `0.5x` (60 fps source), `ramp 1>2.5>1`. `references/cutting-and-pacing.md`.

| # | Start | End | Source | In | Type | Transition | Camera | Speed | Shot | Audio |
|---|-------|-----|--------|----|------|------------|--------|-------|------|-------|
| 1 | 0.0 | 1.5 | [clip] | [s] | HOOK | – | | | [what the camera sees] | [VO line / beat] |
| 2 | 1.5 | 3.0 | [clip] | [s] | HOOK | [transition] | | | | |

---

## Overlays

Graphics and titles on their own timeline (`references/layout-and-motion-graphics.md`, `typography.md`).

- **Start** — seconds, or `@"word or phrase"` (`#2` for the second occurrence): 3 frames before that word.
- **End** — seconds, `+2.5`, `auto` (reading time), `@"word"`, or `cut` (3 frames before the next cut).
- **Component** — `title`, `callout`, `highlight`, `step`, `checklist`, `price`, `cart`, `sticker`,
  `progress`, `magnifier`, `thumbs`, `compare`, `ranking`, `lowerThird`, `specs`, `pin`, `label`,
  `stat`, `chart`, `image`, plus `punch` (camera punch-in) and `sfx` (`src=sfx/riser.wav; volumeDb=-12`).
- **Zone** — `top`, `upper`, `center`, `lower` (or `–`). **Tone** — `neutral`, `before`, `after`, `cta`, `product`.
- **Content** — `key=value; key=value`. Lists: ` / `. Points: `x,y` as fractions of the frame.
  Decimals with a point (`value=5.2; decimals=1`).

| # | Start | End | Component | Zone | Tone | Content |
|---|-------|-----|-----------|------|------|---------|
| 1 | 0.0 | 1.4 | title | top | – | style=outline; lines=[promise]; sub=[honest label] |

---

## Voiceover script

Commerce pace ~4.5–5 words/s: about 150–170 Vietnamese words for 35 s including pauses. Music-only
playbooks: leave this out.

| Scene | Line |
|-------|------|
| 1 | |

---

## Shot list (only when footage must be shot)

From the playbook's "Shots the footage needs". Leave space above and below the subject for graphics.

| Setup | Shots needed | Notes |
|-------|--------------|-------|
| | | |

---

## Compliance check

The playbook's checklist (`playbook.py skeleton` prints it); details in `references/claims-and-compliance.md`.

- [ ] …
- [ ] Commercial-content disclosure at upload; music licensed for this platform and account
- [ ] Graphics inside the safe zones; nothing over a face

---

## Pacing check result

```
```

---

## Deliverables

- [ ] `edit-plan.md` (passing the checker)
- [ ] `captions.srt` + `words.json` (when there is a voice)
- [ ] `project.json` (sync report reviewed) + mastered MP4 + contact sheet, or editor instructions
