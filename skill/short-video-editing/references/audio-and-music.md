# Audio and Music

Audio is the channel most often treated as decoration and most often responsible for a video
feeling amateur. It is also where a licensing violation can cost a commercial account.

---

## Licensing first

**Business accounts must use TikTok's Commercial Music Library**, not the general consumer music
catalogue. Using chart music on a commercial video is a licensing violation regardless of how well
it performs.

In a study of 1,842 TikTok Shop affiliate videos across 67 brands, about 74% used original audio
or no music at all; the rest used the Commercial Music Library
(`oktorun.ai/research/tiktok-shop-affiliate-music-study`).

**A correction worth carrying.** The claim that *"trending audio generated 58% more add-to-cart
actions"* is misattributed — the study it is credited to measured licensing compliance and
explicitly did not measure conversion. Do not repeat it, and do not let it justify a licensing
risk.

**Default:** original voiceover as the primary audio, with a cleared library track low in the bed.

---

## Levels

| Element | Level | Note |
|---|---|---|
| Voice peak | −6 to −12 dB | Standard dialogue target |
| Music **under** voice | 15–25 dB below the voice | The single most useful number here |
| Music in gaps (no VO) | −12 to −18 dB | Let it rise between beats |
| Ducking | 6–10 dB reduction, 300–600 ms release | Avoids audible pumping |
| Final loudness | −13 to −10 LUFS | Short-form runs hotter than YouTube's −14 LUFS norm |

The most common mix error in affiliate video is music that sits only 6–8 dB under the voice. It
does not sound loud in headphones while editing; on a phone speaker it buries the words.

A quick check with ffmpeg:

```bash
ffmpeg -i mix.mp3 -af volumedetect -f null - 2>&1 | grep -E "mean_volume|max_volume"
```

Mean around −20 dB with peaks near −4 dB is a reasonable target for a voice-led short.

---

## Diegetic sound is the credibility layer

For a cleaning demo, the real sounds — liquid pouring, fabric scrubbing, the bottle cap — are the
strongest authenticity signal available, and they are free. **Do not bury them under music.**

When the reveal arrives, consider dropping the music entirely and letting the room tone carry it.
A demo that sounds like a room is more believable than one that sounds like an advert.

---

## J-cuts and L-cuts

A **J-cut** starts the next shot's audio before its picture arrives. An **L-cut** holds the
previous shot's audio over the new picture.

Why they matter at this cadence: when you cut every 2–3 seconds, audio and picture cutting together
every time produces a staccato, machine-gun feel. Alternating J and L cuts so the two never cut on
the same frame makes fast editing feel smooth instead of choppy.

Two specific uses:

- **J-cut into the demo.** Let the pouring sound start a beat before the shot appears. It pulls the
  viewer forward.
- **L-cut across the reveal.** Let the voiceover continue over the cut so the transition is not
  felt — useful precisely because you must not cut *picture* across a before/after.

---

## Silence as a tool

Cut music and voice for about half a second immediately before the reveal. On a platform where
every video is loud, a sudden gap is a genuine pattern interrupt, and it forces attention onto the
payoff shot.

Use it once. Twice reads as a technical fault.

---

## Sound effects

One whoosh per transition, not stacked. SFX sell punch-ins and whip pans; layered over every cut
they turn the video into a template.

Useful set for a product demo:
- Short noise sweep on moving transitions and punch-ins
- A soft click or pop when the product card or the cart arrow appears
- Nothing at all across the reveal — let the diegetic sound carry it

Licensed sources, the sound bank, the event map, levels and timing are in `sound-design.md`;
`plan_to_project.py --auto-sfx` applies them.

---

## Voiceover pacing

From building Vietnamese commerce voiceovers with `edge-tts`:

| Parameter | Value |
|---|---|
| Voice | `vi-VN-HoaiMyNeural` (female), `vi-VN-NamMinhNeural` (male) |
| Rate | `+10%` to `+15%` for commerce energy; default reads slow against fast cuts |
| Gap between lines | 0.2–0.3s |
| Lead-in silence | 0.5–0.6s |
| Tail after last line | ~2s for the CTA card to land |

Roughly 200 Vietnamese words at default rate runs about 66 seconds — far over target. At `+12%`
the same script lands near 48s. Plan for about **4.5–5 words per second** at commerce pace, so a
35-second video supports roughly **150–170 words** of voiceover including pauses.

Write to that budget before recording. Trimming a script after synthesis wastes a pass.

**Rate limiting.** The free `edge-tts` endpoint rejects bursts with "No audio was received".
Synthesise one line at a time, 2–3 seconds apart, with exponential backoff and at least 5 retries.
Expect roughly one retry per three lines; this is normal and not a parameter error.
