---
name: short-video-editing
description: Plan, script and assemble short vertical product videos (TikTok Shop, Reels, Shorts) of 25-45 seconds — timestamped edit plans, hooks, captions, voiceover, motion graphics, virtual camera moves, transitions and a data-driven Remotion render. Use this whenever someone asks to make, edit, cut, script, storyboard or improve a short-form video, a product review, an affiliate/KOC/UGC video, a TikTok Shop video, a Reel or a Short — and also when they ask for a shot list, a video hook, burned-in captions, kinetic text, motion graphics, transitions, a before/after product demo, several videos from one batch of raw footage, or want to know why their videos get no views. Apply it even when the request sounds small ("just add captions", "make this snappier", "write me a TikTok script"), because the pacing, layout and commercial-claim rules it enforces apply to all of those.
---

# Short Video Editing

Build short vertical product videos that get distributed, convert, and survive platform review.

The core insight, measured on 16,242 real TikTok Shop videos: **reach is almost always the
bottleneck, not persuasion.** The top 20% of videos by views earned 95% of all revenue, while the
bottom 80% averaged 171 views — and when those low-reach videos did reach someone, they converted at
the same rate. Distribution follows early retention, and early retention follows the hook, the cut
rhythm and how the frame keeps moving. That is why the hard rules are about the first three seconds,
scene length and layout, not about how thoroughly the product is explained.

---

## Hard rules

Checked mechanically. Do not deliver a plan that breaks them.

**1. The hook resolves within the first 3 seconds.** Three channels doing three different jobs: an
arresting visual (ideally the before → after itself), on-screen text stating the promise, and audio
that starts a thought. Frame 0 is the feed thumbnail — never empty.

**2. Scenes last 3–4 s: never longer than 4, never shorter than 2.5 outside the hook.** Past 4 s a
static shot is an exit point (reference data). Cuts every 1.5–2 s felt jerky to the client
(*"bị ngắt"*), so the working rhythm is 3–4 s, joined by soft transitions. The hook is the
exception: two ~1.5 s beats. (4 s ceiling: data. 3 s target: client house style.)

**3. Every plan carries explicit timestamps** in the table of `assets/edit-plan-template.md`, which
the scripts parse.

**4. Runtime lands in 25–45 s, ideally 30–40.** CTR and sale rate peaked at 35–44 s; sub-25 s was
worst on every measure. Push back on 15-second requests.

**5. Check commercial claims before delivering.** For cleaning, laundry, cosmetic and health-adjacent
products most moderation risk is in the words. Run the checklist in `references/platform-specs.md`.

**6. One batch of raw footage feeds as many videos as it can; no stretch is used twice.** Plan the
batch, give every video its own source ranges, never repeat a moment inside a video, and spend scarce
shots (product hero, clean "after") where they matter most.
`scripts/footage_overlap_checker.py` enforces it.

**7. Graphics respect the frame.** Nothing over a face; nothing in TikTok's UI zones (y < 220,
y > 1400, x > 900 below y ≈ 700); captions keep their own band; at most two informational elements
at once; no text in boxes on product demos (client rule). See
`references/layout-and-motion-graphics.md`.

---

## Workflow

### 1. Establish the brief
Know the product and category, the creator, the footage (or whether it must be shot), the product
card URL, the platform, and **how many videos this footage must feed**. Regulated category → read
`references/platform-specs.md` now.

**Inspect and look at raw clips before planning anything:**
```bash
python scripts/inspect_footage.py /path/to/clips --log
python scripts/contact_sheet.py /path/to/clips --out clips.png   # one row of frames per clip: open the PNG(s)
```
Run the scripts from this skill's folder (`~/.claude/skills/short-video-editing` once installed);
`align_captions.py` re-launches itself in the kit's venv, the rest need only Python 3 and ffmpeg.
Then build a shot log by kind of moment (BEFORE, AFTER, POUR, HERO, SCRUB, PROBLEM) and budget it
across the batch — `references/footage-ingest.md` §1b.

### 2. Choose the hook
`references/hook-library.md`. In order: a visible transformation → genuine social proof → a specific
pain point → product reveal with an open loop. Avoid authority framing and bare commands.

### 3. Draft the timeline
`assets/edit-plan-template.md`. Default skeleton for 30–40 s:

| Phase | Timing | Purpose |
|---|---|---|
| Hook | 0–3 s | Two ~1.5 s beats: BEFORE → AFTER joined by a wipe |
| Problem | 3–9 s | Make the stake concrete: 2 scenes of ~3 s |
| Early CTA | ~9–12 s | Plant the cart once (arrow toward the real basket) |
| Re-hook | ~12–15 s | Product hero shot, new energy |
| Demo | 15–25 s | The transformation: 3 scenes of 3–3.5 s |
| Reveal | 25–31 s | Pay off the hook; hold the result |
| Close CTA | 31–38 s | Repeat concretely, pointing at the real cart |

Choose cut points **on pauses in the voice**, never inside a word (`references/sync-and-timing.md`).
Give every scene a transition (`references/transitions.md`) and a camera move, or leave Camera blank
for `--auto-camera` (`references/camera-moves.md`).

### 4. Design the graphics layer
Fill the plan's **Overlays** table: title styles (`references/typography.md`), callouts, steps,
checklists, prices, the cart pointer and so on (`references/layout-and-motion-graphics.md`). Anchor
graphics to words with `@"phrase"` so they land on the voice. Vary title styles (3–4 per video),
never the same style twice in a row, one accent word per title. On-screen text must say something
**different** from the voiceover.

### 5. Write and synthesize the voiceover
Commerce pace is ~4.5–5 words/s: **150–170 words** for 35 s. Check every line against
`references/platform-specs.md` §7 before synthesizing.
```bash
python scripts/make_voiceover.py --quota                              # plan + credits left
python scripts/make_voiceover.py script.txt --voice <id> --dry-run    # price it, spend nothing
python scripts/make_voiceover.py script.txt --voice <id> --out audio/
```
Vietnamese needs a model that lists Vietnamese (default `eleven_turbo_v2_5`; `eleven_multilingual_v2`
does not). Free-plan audio is non-commercial forever — tell the user before spending credits on
something they cannot ship. Details: `references/voiceover-and-captions.md`.

**A supplied voice (no synthesis)** is the usual case when the user hands over a recording:
1. Several voice files? Match by the video's name and ask when it is ambiguous. Length decides the
   rest: 30–40 s is right, 40–45 s is allowed (say it is long), over 45 s must be trimmed, under 25 s
   needs a word with the user (rule 4). `python scripts/trim_voice.py voice.mp3 --silences` lists the
   pauses; keep ranges with `--keep 0-3.8,8.3-16.1 --out short.mp3`. Drop whole sentences only, and
   tell the user which.
2. Run `align_captions.py` **without** `--script` for a draft transcript, correct it by hand until it
   matches what is actually said (supplied voices rarely match the written script), save it as
   `script.txt`, then align again with `--script`.
3. Read the voice for claims the plan cannot repeat (`references/platform-specs.md` §7) and flag them.

### 6. Captions and word timings
```bash
python scripts/align_captions.py voice.mp3 --script script.txt --out captions.srt --words-out words.json
```
Whisper supplies the timing; the script supplies the words (Whisper mishears Vietnamese: "túi xách"
→ "tui sách"). If the audio does not match the written script, transcribe it, correct the spelling
by hand and align against that. `references/captions-and-text.md`.

### 7. Check the plan
```bash
python scripts/pacing_checker.py edit-plan.md
python scripts/footage_overlap_checker.py plans/kb7.md plans/kb4.md plans/kb9.md --clips /path/to/clips   # every plan of the batch, named
```
Errors block delivery; paste the pacing output into the plan.

### 8. Assemble
- **Remotion (default)** — `references/remotion-output.md`. Scaffold once with
  `scripts/new_remotion_project.py`, compile with `scripts/plan_to_project.py` (prints a sync
  report: cuts inside words, text on cuts, UI-zone collisions, zone overlaps, flashing captions),
  render stills at every transition, then render. Licence: free only up to 3 employees.
  Add `--auto-sfx` for sound effects on transitions and graphics (`references/sound-design.md`):
  licence-safe sounds only, nothing across the reveal, and say whether you listened to the result.
- **Human editor** (CapCut, Premiere, DaVinci) — the edit plan plus `captions.srt`.

### 9. Verify before delivering
Look at a contact sheet of the render (`python scripts/contact_sheet.py out/video.mp4 --project
project.json --out sheet.png`: the middle of every scene plus every cut). Confirm the
compliance checklist; for a before/after demo: same item, same framing, **time compression labelled
on screen**, staged stains labelled. Check `ffprobe` durations of video and audio match the plan.

---

## Reference files

Read as the task requires, not all at once.

| File | Read it when |
|---|---|
| `references/niche-winning-patterns.md` | **First, for a cleaning/household product.** What the campaign data shows about duration, CTR, creators. |
| `references/platform-specs.md` | Writing any script or claim; regulated categories; before/after rules; the rewrite table. |
| `references/hook-library.md` | Choosing or writing the opening. |
| `references/pacing-and-transitions.md` | Cadence, structure, re-hooks, footage that fights the rules. |
| `references/transitions.md` | Choosing transitions; the centred-cut maths; shader transitions on Windows; SFX. |
| `references/camera-moves.md` | Push/pull/pan/hold, keyword punch-ins, avoiding jerky zooms. |
| `references/typography.md` | Fonts with Vietnamese support, the five title styles, captions vs titles. |
| `references/layout-and-motion-graphics.md` | Safe zones, layout per content type, the component catalogue, density. |
| `references/sync-and-timing.md` | Cutting on pauses, anchoring graphics to words, music ducking, beat sync, verification. |
| `references/captions-and-text.md` | Caption grouping, placement, SRT. |
| `references/footage-ingest.md` | Inspecting clips, shot log, budgeting footage across several videos. |
| `references/voiceover-and-captions.md` | ElevenLabs voiceover and Whisper alignment. |
| `references/audio-and-music.md` | Mixing, music licensing, diegetic sound. |
| `references/sound-design.md` | Sound effects: licence-safe sources, the sound bank, which sound on which event, levels and timing. |
| `references/remotion-output.md` | The render pipeline and template layout. Read the licence section first. |

---

## Output format

Deliver, in this order:

1. **`edit-plan.md`** — Scenes and Overlays tables, passing `pacing_checker.py` (output pasted in).
2. **`captions.srt`** (+ `words.json` when rendering).
3. **Shot list** — only if footage must be captured (include "leave space above the head and below
   the chin for graphics").
4. **Assembly artefact** — `project.json` + rendered MP4, or editor instructions.

Then state plainly, in the user's language: runtime, scene count, the hook and why, what the sync
report still flags, anything changed for compliance (name the removed claim and the rule), and what
was not verified (e.g. "not listened to end-to-end").

---

## Honesty about evidence

**Measured** on the reference dataset: the duration/CTR relationship, reach-not-persuasion, creator
concentration, weak caption signals. Yours to assert.

**Documented**: platform policy (binding), Remotion APIs, font subsets, licence terms.

**Craft convention or client preference**: the 3–4 s rhythm, transition and camera choices, title
styles, layout bands, mix levels. Present these as informed practice, not measurement — two of the
most-cited statistics in short-form advice turned out to be fabricated or misattributed. If asked
whether a hook or style will perform better, the honest answer is usually that the data does not
say; recommend on structural fit and test it.
