# Playbook: montage-recap — travel, event, opening, behind the scenes, brand film

Music is the script: cuts on the beats, energy in sections that follow the track, speed ramps into the
hits, one or two words on screen at most, the place and the date as quiet labels. Goal: reach, shares,
event awareness.

Labels: **[S]** sourced, **[C]** craft convention.

## When to use it

- Footage: many short clips of varied places, people and moments; moving camera; no voiceover, only
  ambient sound (`inspect_footage.py --measure` reports `speech: none`, `motion: high`).
- Not this playbook: a narrated story (`talking-head` with B-roll), a property (`real-estate`).

## Questions to ask when the brief does not say

1. The track (licensed for commercial use? its bpm if known) and how long the edit should run.
2. Place, date and brand to show; numbers of the event (only real ones).
3. People recognisable on screen: did they agree (staff, guests, children with a guardian)?

## Structure (15–30 s, set by the music section)

| Phase | Purpose | Graphics |
|---|---|---|
| HOOK 0–2 s | The most spectacular moment, cut hard on the first beat | a 2–4 word `title`, or nothing |
| OPEN 25% | Establish the place and the mood; wider shots, two beats per cut | `pin` (place, date) |
| BUILD 40% | People and action, one beat per cut, `ramp 1>2.5>0.8` into the hits | — |
| PEAK 20% | The best moments on the music's drop | `stat` (real event numbers) |
| OUTRO 15% | A calm last shot and the brand | `title`, `lowerThird` or `image` (logo) |

"Use the beats to support a sequence, not to force every cut" [S: Filmora]. Cut more often as the
track builds (every other downbeat in a verse, every beat in the chorus), and hard-cut to the hero shot
on the drop's first downbeat [S: vendor guides]. End on the peak of a music section, not mid-phrase.

## Shots the footage needs

Many short B-roll clips per place · establishing wides · details · people · movement at 60 fps (slow
motion and ramps need it) · aerials where legal [S: Filmora, Splice]. Kinds the camera knows: `WIDE`,
`CROWD`, `AERIAL`.

## Editing

- `suggest_cuts.py --music track.wav --end 25 --playbook montage-recap --beats-out beats.json`: cuts
  on beats, bar starts preferred; at 120 bpm a beat is 15 frames.
- Transitions: cuts on the beat; whips and a zoomThrough with a flash on section changes; a crossZoom
  sparingly; a long fade out on the outro. Keep to one family per video [C].
- Speed ramps land on a beat; motion blur is welcome above 3x [C].

## Sound

The track carries everything (`volumeDb 0` with no voice); keep a little ambient sound where it adds
life (cheers, waves). Whip sounds on whips; cuts silent. Licensed music only; never a chart track on a
business account.

## Picture

Grade `vivid` (rich but not neon), corrections per clip so footage from different phones and hours
matches; one consistent look across all cameras [C]. Theme `cool`.

## Graphics

`title` (two to four words), `pin` (place and date), `stat` for real event numbers, `lowerThird` or
`image` (logo) at the end. No checklists, steps or cart.

## Compliance

Consent of recognisable people in a commercial video; children only with a guardian's consent; real
numbers; licensed music; other brands' logos and artworks not featured without permission.

## Commands

```bash
python scripts/new_remotion_project.py ~/renders/event --playbook montage-recap --proxies CLIPS
python scripts/process_audio.py music track.mp3 --out ~/renders/event/public/audio/music.wav
python scripts/suggest_cuts.py --music ~/renders/event/public/audio/music.wav --end 25 --playbook montage-recap --json > cuts.json
python scripts/playbook.py skeleton montage-recap --cuts cuts.json --title "Grand opening of X" > edit-plan.md
python scripts/plan_to_project.py edit-plan.md --out ~/renders/event/v1.json --music audio/music.wav --auto-camera --analysis analysis.json --auto-sfx
```
