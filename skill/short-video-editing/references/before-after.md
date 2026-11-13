# Before / after — making a result visible, honestly

Any video that sells a change (a mark removed, a room renovated or staged, a look made up, a surface
cleaned, a styling change) lives or dies on one thing: the viewer must *see* the before and *see* the
after. If the result is hard to read, nothing else in the edit matters. This file collects how
before/after is edited in practice and how the kit builds it. The examples are product demos
(product-demo); the method applies to every playbook that shows a change
(real-estate staging or renovation, fashion styling — never a skin, hair or health result:
`claims-and-compliance.md` §3 and §6).
Rules of the platform are in `claims-and-compliance.md` §3. **[D]** documented, **[C]** craft convention,
**[?]** not verified.

---

## 1. What editors do (research, 2026-11-05)

| Technique | What it is | Best for | Source |
|---|---|---|---|
| **Sequential cut or wipe** | BEFORE, then AFTER; a wipe reads as one continuous shot | The hook; the simplest honest version | Captions.ai guide, Filmora/Premiere tutorials |
| **Slider reveal** | A divider sweeps across and uncovers the AFTER (in an editor: keyframe the crop of the BEFORE clip from 0 % to 100 %) | A dramatic change; a "moment" | Premiere Pro tutorial (lensvid) |
| **Split screen** | Both states on screen at once, each filling half the frame (left/right or top/bottom) | A subtle change the viewer must compare in detail, such as a fading mark | Captions.ai, CapCut |
| **Freeze and label** | Stop on the result with a short "Before"/"After" label | Giving the eye time to read the result | Template vendors |
| **Control half** | One half of the item treated, the other left as it was | The strongest proof; it also sidesteps "they swapped the item" | `hook-library.md`, `claims-and-compliance.md` §3 |
| **Show the working time** | Product applied, then the process (rubbing, soaking, waiting), with the dwell time visible | Credibility: the viewer sees the effort and the time the result took | Press interview, craft reading [C] |

What the sources agree on:

- **Locked camera, same angle, lighting and distance** for both states; mark the position on the
  floor or line up a fixed object. A slightly different angle "looks sloppy" and costs credibility
  (Captions.ai, Premiere/Filmora tutorials, a UGC compliance checklist).
- **Label both states** ("Before", "After") so the video reads with the sound off; keep the divider clean.
- **Show a payoff early**, then explain how it was reached; do not save the whole result for the end.
- **Let the result register**: hold the final state long enough to read; one guide says a longer hold
  when the result has detail. No controlled data gives a number [?]; template vendors quote "BEFORE
  1–2 s, AFTER 2–4 s" and whole videos of 6–20 s, which are shorter products than this kit's 30–40 s.
- **Avoid static frames**: motion or a transition into the reveal; text on every key frame.

Gaps: no source covered cleaning demos specifically beyond the above, and none was Vietnamese-specific
(only CapCut and Captions.ai templates and guides). The timing numbers are craft convention, not measurement.

**Policy warning.** TikTok's *advertising* policy lists "product effect comparisons, such as
before-and-after results" among content ads and landing pages must not include (its example is a
wrinkle cream) [D: ads.tiktok.com help article "Misleading and false content"]. The page does not say
whether this covers organic posts, and TikTok's own SMB ad-policy PDF suggests a disclaimer instead
[?]. Cleaning products may use before/after in listings and organic videos (`claims-and-compliance.md` §3),
but **ask whether the video will be boosted or run as an ad (Spark Ads) before building the compare
card around it**.

---

## 2. How the kit shows it

A 35-second demo shows the result three times, each doing a different job:

1. **Hook (0–3 s): BEFORE → AFTER.** Two ~1.5 s beats joined by a wipe, with `TRƯỚC` / `SAU`
   labels (`hook-library.md`). It promises the result immediately.
2. **Process: the working time.** The application, the wait, a `progress` bar labelled
   "Chờ 10 phút · đã rút gọn thời gian". Honest time compression is the credibility layer.
3. **Reveal: lift, then compare.** The treated item is revealed in one uncut take (never a cut across the
   reveal), and about half a second later the **`compare` card** puts the BEFORE frame from earlier
   in the same video next to the AFTER. This is where the viewer is *shown* the difference rather
   than asked to remember it.

Optional fourth: a `thumbs` recap near the CTA.

The sound rule stands: nothing across the reveal itself; the compare card carries one short whoosh
as the second panel arrives (`sound-design.md`).

---

## 3. The `compare` component

```
| 14 | 28.85 | 31.95 | compare | top | – | before=CLIP_A@1.6; after=CLIP_A@27.6; beforeFocus=0.68,0.55; afterFocus=0.55,0.33; zoom=1.4; note=Cùng một món · sau 10 phút (đã rút gọn thời gian) |
```

| Key | Meaning |
|---|---|
| `before`, `after` | `CLIP@seconds`: one frame of a proxy clip (required) |
| `mode` | `side` (default): two portrait panels, the AFTER slides in; `slider`: one card with a divider that sweeps from BEFORE to half-and-half; `stack`: the same, top/bottom |
| `beforeFocus`, `afterFocus`, `focus` | Point of the source frame (0..1) shown at the centre of that side's area. The changed spot is rarely in the same place before and after, so set the two separately; `focus` sets both |
| `zoom` | 1 = the whole frame fits; 1.4–1.6 magnifies the detail (1080p proxies soften past ~1.6) |
| `beforeLabel`, `afterLabel` | Default `TRƯỚC` / `SAU`, in the tone colours (coral / green) with an outline, no box |
| `note` | The honest line under the card: what elapsed and that time was compressed |

Behaviour: the card enters over 10 frames on a **dark scrim** (so a white subject does not blend into
the live white footage behind it), holds the BEFORE for 8 frames, then the AFTER arrives over 20
frames, labels fade in, and the card holds to the end of the row. It sits in zone `top`, inside the
safe width (x 60–900), and its note reaches the `lower` zone, so no other `top` or `lower` graphic may
overlap it (the sync report checks both). Tokens are in `theme.ts` (`compare`).

**Timing.** Give it at least 2.5 s: about 1 s for the entrance and sweep, then 1.5 s or more of the
finished comparison (a result that cannot be read is wasted). Start it after the lift has landed, on
the line that talks about the result, and end it at least 3 frames before the next cut.

---

## 4. Choosing the pair

- **The same item, the same side, the same camera position and light.** Check on the contact sheet.
- **BEFORE:** the problem at its worst and unobstructed, hand out of the way, and the product visible if
  possible. **AFTER:** the end of the process, the item held up and the problem's place in view.
- **Take both frames from ranges the video already shows.** `footage_overlap_checker.py` does not see
  frames used by `compare`, `thumbs` or `magnifier`, so reusing a range already on screen costs no
  new footage and breaks no budget.
- **Label what is staged** ("vết thử có chủ đích") and the time ("sau 10 phút · đã rút gọn
  thời gian"). The result must be typical or its limits disclosed (`claims-and-compliance.md` §3).
- **Over a white subject** the scrim and the white border keep the card readable; keep the labels in the
  outlined text style, never a coloured box.

---

## 5. Pitfalls found while building it

- A frozen frame must be read with `startFrom` and `Freeze frame={0}`. `Freeze frame={N}` with a large
  N inside a short overlay shows the wrong moment of the clip (a clip frame near the end of the
  overlay's own length). The same applies to `thumbs`.
- Mixed poses: before and after rarely match, so a slider laid over both misaligns the subject.
  `side` mode gives each its own centred window and avoids it.
- A card the same colour as the footage behind it vanishes: keep the scrim.

Sources: Captions.ai "before and after transformation videos"; Coinis "before/after TikTok ad
template"; lensvid "before and after wipe in Premiere Pro"; Filmora and CapCut split-screen guides;
TikTok Ads help centre "Misleading and false content"; retention-editing blogs for reveal pacing
(craft rules of thumb [C]).
