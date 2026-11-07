# Playbook: talking-head — one person speaking to camera

Expert tips, explanations, a founder's story, a customer's testimonial. The speaker's own take (the
A-roll) is cut into **jump cuts** on its pauses, framings alternate wide and tight so every cut reads
as intentional, B-roll and graphics illustrate each point, and bold one-line captions carry it with
the sound off. Goal: authority, followers, saves, trust; for a testimonial, conversion.

Variant: `talking-head:testimonial` (a real customer: the result first, the problem, the experience,
the outcome; honesty is the format).

Labels: **[S]** sourced, **[C]** craft convention.

## When to use it

- Footage: one face in a fixed frame most of the time; speech in the camera's own audio; long takes;
  maybe B-roll without speech (`inspect_footage.py --measure` reports `speech: on-camera`).
- Not this playbook: a voiceover over product footage (`product-demo`), a recipe with hands on screen
  (`tutorial`).

## Questions to ask when the brief does not say

1. The point of the talk in one sentence, and the CTA (follow, comment, save, book, buy).
2. The speaker's name and role as they want it shown (credentials must be real).
3. B-roll available for each point? If not, which graphics may stand in (stat, chart, image)?

## Structure (30–60 s)

| Phase | Purpose | Graphics |
|---|---|---|
| HOOK 0–2.8 s | The boldest sentence of the talk, in the first breath; a pattern-break frame or B-roll under it | `title` stating the payoff |
| CONTEXT 15% | Why it matters to the viewer, one sentence | `title` |
| POINT 60% | The points, one per beat; B-roll or a graphic on every point | `step`/`checklist`, `stat`, `chart`, `image`, `highlight`, `thumbs` |
| PAYOFF 15% | The takeaway in one line | `title` |
| CTA 10% | Follow, comment, save, or the offer | `lowerThird` |

Restructure before cutting: the hook is usually a sentence from the middle of the take moved to the
front (`--keep` ranges in `trim_voice.py`). A visual change every ~3–8 s [S: Jupitrr] — a jump cut with
a new framing counts.

## Editing

1. Extract and jump-cut the A-roll: `trim_voice.py talk.mp4 --jumpcut --out voice.wav --scenes-out
   cuts.json` removes every pause over 0.35 s (padded 80 ms), joins stretches shorter than 1 s, splits
   stretches longer than 5 s at their quietest moment, and writes the scenes with their source times.
   Fillers ("ờ", "à") and repeats are not detected: read the transcript (`align_captions.py voice.wav`)
   and drop them with `--keep`.
2. `process_audio.py voice voice.wav --out public/audio/v.wav`, then align the captions on that file.
3. `playbook.py skeleton talking-head --cuts cuts.json` gives a Scenes table with Source and In filled.
4. Framings alternate through the playbook's camera pattern (`hold 1.0` wide, `hold 1.22 focus
   0.5,0.35` tight on the face, a slow push on the payoff): a punch-in of at least ~12% on one side of
   each cut hides the jump [S: No Film School; kit minimum]. Point `focus` at the face (y ≈ 0.33–0.4).
5. B-roll goes over the voice as its own scenes (L-cut: the voice continues over the new picture) [S].
6. Transitions are cuts and `pushCut`; nothing decorative.

## Sound

The speaker's voice is the soundtrack: cleaned with `process_audio.py voice` (noise print from the
quietest pause, presence, de-esser, 3:1 compression, −16 LUFS). Music low or none, never with vocals
under speech; `pushCut` gets a soft pop, cuts are silent.

## Picture

Grade `natural`, corrections per clip (a face under mixed light needs its white balance fixed first).
Keep skin natural: no smoothing filters.

## Graphics and captions

Captions `pop`: one phrase of up to five words (20 characters) on one line, the spoken word coloured and springing.
Viewers read ahead, so the whole phrase appears at once; one word at a time hurts comprehension
(`references/captions-and-text.md`). Graphics in the head-room band above the face, never over it;
`stat` and `chart` carry a source line in the voice or the `label` (numbers the speaker can name).
`lowerThird` with the name and real credentials at the first appearance or the CTA.

## Compliance

Numbers on screen have a source; medical, financial and legal advice is hedged, no guaranteed outcomes;
a testimonial comes from a real customer who agreed to it, and staged scenes are never labelled as a
real review; paid partnerships disclosed. Finance content advertised on TikTok in Vietnam needs the
advertiser's registration with SBV, SSC or MOF [S: TikTok ads policy].

## Commands

```bash
python scripts/trim_voice.py talk.mp4 --jumpcut --out voice_cut.wav --scenes-out cuts.json
python scripts/process_audio.py voice voice_cut.wav --out ~/renders/x/public/audio/v1.wav
python scripts/align_captions.py ~/renders/x/public/audio/v1.wav --out draft.srt     # correct by hand -> script.txt
python scripts/align_captions.py ~/renders/x/public/audio/v1.wav --script script.txt --out captions.srt --words-out words.json
python scripts/playbook.py skeleton talking-head --cuts cuts.json --title "Chủ đề" > edit-plan.md
python scripts/plan_to_project.py edit-plan.md --out ~/renders/x/v1.json --voice audio/v1.wav \
    --captions captions.srt --words words.json --auto-camera --auto-sfx
```
