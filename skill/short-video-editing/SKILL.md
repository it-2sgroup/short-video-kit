---
name: short-video-editing
description: Plan, script and assemble short vertical product videos (TikTok Shop, Reels, Shorts) of 25-45 seconds — timestamped edit plans, hooks, SRT captions, voiceover, and renderable compositions. Use this whenever someone asks to make, edit, cut, script, storyboard or improve a short-form video, a product review, an affiliate/KOC/UGC video, a TikTok Shop video, a Reel or a Short — and also when they ask for a shot list, a video hook, burned-in captions, a before/after product demo, or want to know why their videos get no views. Apply it even when the request sounds like a small one ("just add captions", "make this snappier", "write me a TikTok script"), because the pacing and commercial-claim rules it enforces apply to all of those.
---

# Short Video Editing

Build short vertical product videos that get distributed, convert, and survive platform review.

The core insight behind this skill, measured on 16,242 real TikTok Shop videos: **reach is almost
always the bottleneck, not persuasion.** The top 20% of videos by views earned 95% of all revenue,
while the bottom 80% averaged 171 views — and when those low-reach videos did reach someone, they
converted at the same rate. Their problem was never the sales pitch. It was that nobody saw them.

Distribution follows early retention, and early retention follows the hook and the cut rhythm.
That is why the hard rules below are about the first three seconds and scene length, and not about
how thoroughly the product is explained.

---

## Hard rules

These are non-negotiable and are checked mechanically. Do not deliver a plan that breaks them.

**1. The hook resolves within the first 3 seconds.**
The opening must combine three channels doing three *different* jobs: an arresting visual,
on-screen text stating the promise, and audio that starts a thought the viewer needs to finish.
A silent title card throws away a third of the hook. Frame 0 is the feed thumbnail — never empty.

**2. No scene runs longer than 4 seconds.**
A static shot past four seconds is a natural exit point, and an exit kills distribution. Hook
scenes should be faster still — 1–2 seconds each. A "scene change" is any of: a new shot, a
different angle, a punch-in, a B-roll cutaway, a substantial text change, or a visible speed ramp.
This means one locked take can legitimately become four scenes without extra shooting.

**3. Every plan carries explicit timestamps.**
Rule 2 is unverifiable without them. Use the table in `assets/edit-plan-template.md`, which
`scripts/pacing_checker.py` parses directly.

**4. Runtime lands in 25–45 seconds, ideally 30–40.**
In the reference data, click-through rate and sale rate both peaked in the 35–44s band, and
sub-25s videos were worst on every measure. Proven creators made a sub-25s video about 1% of the
time. If asked for a 15-second cut, push back and explain why.

**5. Check commercial claims before delivering.**
For cleaning, laundry, cosmetic and health-adjacent products, most moderation risk is in the words,
not the footage. Read `references/platform-specs.md` and run the checklist. This is not optional
polish — undisclosed or non-compliant content gets demoted, removed, or costs the account.

---

## Workflow

### 1. Establish the brief

Before planning, know: the product and its category, the creator/account, the available footage
(or whether it must be shot), the product card URL, and the target platform.

If the product is in a regulated category — cleaning, cosmetics, supplements, health — read
`references/platform-specs.md` now rather than after writing the script.

**If raw clips already exist, inspect them before planning anything.** A timeline written against
imagined footage usually survives contact with the real files only in outline. Run:

```bash
python scripts/inspect_footage.py /path/to/clips --log
```

It reports duration, resolution, orientation, frame rate and audio presence per clip, and flags
landscape sources, silent clips, mixed formats and thin coverage. Then read
`references/footage-ingest.md` for how to build a shot log, carry source timecodes into the plan,
and emit an ffmpeg cut list. Source in/out points and timeline positions are different numbers;
the plan needs both or the editor has to guess.

### 2. Choose the hook

Read `references/hook-library.md`. Work in this order, because it fails fast:

1. Does the footage contain a visible transformation? Use it — best structural fit, needs no claim.
2. Is there genuine social proof (real comment volume, real sales rank)? Use it — compliant, and
   own-sales claims are the one superlative platforms permit.
3. Can you name the problem specifically — this garment, this stain, this moment? Use a pain point.
4. Otherwise: product reveal, strengthened with an open loop on the second beat.

Avoid authority framing ("as an expert…") and bare commands ("buy now") — both rank worst in the
only hook dataset with a disclosed methodology.

### 3. Draft the timeline

Use `assets/edit-plan-template.md`. The default skeleton for a 30–40s review:

| Phase | Timing | Purpose |
|---|---|---|
| Hook | 0–3s | 2–3 beats of 1–2s |
| Problem | 3–8s | Make the stake concrete |
| Early CTA | ~8–10s | Plant the cart once, lightly |
| Demo | 10–26s | The transformation; keep cutting inside it |
| Re-hook | ~18–20s | Reset attention mid-demo |
| Reveal | 26–32s | Pay off the hook; hold slightly longer |
| Close CTA | 32–38s | Repeat concretely, pointing at the real cart |

The early CTA is deliberate. Roughly 40% of videos in the reference data recorded zero
click-through — watched and never tapped. Wistia's analysis of 14M+ videos found sub-60s video
converts best with the CTA in the first quarter. (Caveat: hosted business video, not TikTok.)

See `references/pacing-and-transitions.md` for transition choices and for what to do when the
footage fights the rules.

### 4. Write and synthesize the voiceover

Commerce pace runs about 4.5–5 words per second, so a 35-second video supports roughly **150–170
words** including pauses. Write to that budget rather than trimming after synthesis.

Check every line against the rewrite table in `references/platform-specs.md` §7 **before**
synthesizing — fixing a prohibited claim afterwards means paying for the synthesis twice.

```bash
python scripts/make_voiceover.py --quota                              # plan + credits left
python scripts/make_voiceover.py script.txt --voice <id> --dry-run    # price it, spend nothing
python scripts/make_voiceover.py script.txt --voice <id> --out audio/
```

Uses ElevenLabs, one audio file per script line so a single line can be redone cheaply. The key
comes from the environment or `~/.config/short-video-kit/env` — never the command line.

Two checks before any real synthesis, both learned the hard way:
- **The model must list Vietnamese.** The default is `eleven_turbo_v2_5`. `eleven_multilingual_v2`
  does *not* support Vietnamese despite its name.
- **The free plan is non-commercial.** ElevenLabs states free-plan audio "cannot be used for any
  commercial purpose", and that stays true even if you upgrade later. A product or client video
  needs audio generated during a paid subscription. Run `--quota`; if the plan is `free`, tell the
  user before spending credits on something they cannot ship.

See `references/voiceover-and-captions.md` for models, `[emotion]` tags (only `eleven_v3`
interprets them) and credit costs.

### 5. Build the captions

```bash
python scripts/align_captions.py audio/voice_full.mp3 --script script.txt --out captions.srt
```

**Whisper supplies the timing; the script supplies the words.** Whisper mishears Vietnamese — on
this project's own voiceover it produced "mua tui sách" for "mua túi xách" and "kiểu gián" for
"kiểu dáng". Invisible in a transcript, glaring burned onto a video. Because we wrote the script
ourselves, the spelling is already known and should never come from recognition. Passing
`--script` is what makes that happen.

Read `references/captions-and-text.md` for style. Key points: burn them in, 2–4 words per group,
one group on screen at a time, minimum display of 0.5s + 0.3s per word, and keep them inside the
safe zone (y 250–1410, x 60–940 on a 1080×1920 frame).

On-screen text should say something **different** from the voiceover — procedural detail, evidence
labels, keywords for search. The aligned SRT is the spoken track; title cards and labels are
written separately in the plan.

### 6. Run the pacing checker

```bash
python scripts/pacing_checker.py path/to/edit-plan.md
```

It validates the hook deadline, the 4-second ceiling, timeline continuity and runtime, and exits
non-zero on failure. Fix errors before moving on; warnings are advisory. Paste the output into the
plan.

### 7. Assemble

Pick the output that matches how the video will actually be finished:

- **Remotion** (automated render) — graphics over ffmpeg-cut footage; see
  `references/remotion-output.md`. Check the licence section first: free only for individuals and
  companies of up to 3 employees.
- **Human editor** (CapCut, Premiere, DaVinci) — deliver the edit plan plus `captions.srt`
- **ffmpeg** (scripted assembly) — cut list, concat, overlay and burn-in commands are in
  `references/footage-ingest.md` §4

### 8. Verify before delivering

Walk the compliance checklist in the template. For a before/after demo specifically, confirm:
locked camera, constant lighting, **no cut across the reveal**, and any time compression labelled
on screen.

---

## Reference files

Read these as the task requires rather than all at once.

| File | Read it when |
|---|---|
| `references/niche-winning-patterns.md` | **Read first for a cleaning/household product.** What the real campaign data shows about duration, CTR, creator effects and where leverage actually is. |
| `references/platform-specs.md` | Writing any script or claim; working in a regulated category; checking safe zones. Contains a banned-phrasing → compliant-phrasing rewrite table. |
| `references/hook-library.md` | Choosing or writing the opening. Archetype ranking plus written Vietnamese examples. |
| `references/pacing-and-transitions.md` | Building the timeline; choosing transitions; when footage won't fit the rules. |
| `references/captions-and-text.md` | Writing captions, placing text, generating SRT or word-level timings. |
| `references/audio-and-music.md` | Mixing, music licensing, voiceover pacing and TTS practicalities. |
| `references/remotion-output.md` | Rendering programmatically with Remotion. Read the licence section before building. |
| `references/voiceover-and-captions.md` | ElevenLabs voiceover and Whisper-aligned captions. |
| `references/footage-ingest.md` | Planning around clips that already exist: inspect, shot-log, cut list. |

---

## Output format

Deliver these, in this order:

1. **`edit-plan.md`** — the filled template, with a passing checker result pasted in.
2. **`captions.srt`** — standard SRT, importable by CapCut, Premiere and DaVinci.
3. **Shot list** — only if footage needs to be captured.
4. **Assembly artefact** — a Remotion composition, ffmpeg commands, or editor instructions.

Then state plainly, in the user's language: the runtime, the scene count, the hook chosen and why,
and anything in the brief you had to change for compliance. If you removed a claim the client
asked for, say which one and cite the rule — do not quietly drop it.

---

## Honesty about evidence

This skill mixes two kinds of knowledge, and they should not be presented as equivalent.

**Measured** on the reference dataset: the duration/CTR relationship, the reach-not-persuasion
finding, creator concentration, and the weak caption signals. These are yours to assert.

**Craft convention**: the 2–4 second cut rhythm, hook archetypes, transition choices, mix levels.
Widely agreed, but the precise percentages circulating in this field are largely unsourced — two
of the most-cited statistics in short-form video advice turned out on inspection to be fabricated
or misattributed. Present these as informed practice, not as measurement.

**Platform policy** is documented and authoritative. Treat it as binding.

If someone asks whether a particular hook type will perform better for their product, the honest
answer is usually that the data does not say — hook type is not recorded in any dataset here. Say
so, then recommend based on structural fit and test it.
