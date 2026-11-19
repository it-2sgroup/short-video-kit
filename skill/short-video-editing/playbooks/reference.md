# Reference — make it like this sample video

**When:** the user hands over a sample ("make it like this") and the footage can be of any kind. The sample sets the style; this playbook sets nothing of its own.
A presenter's service pitch cut from their own takes is a special case with its own recipe: `talking-head:agency` (`references/agency-pitch-recipe.md`).

**What differs from every genre playbook:** no scene lengths, transition lists, camera pattern or caption position of a genre are applied. The numbers come from the sample:

| Taken from the sample (`analyze_reference.py` → `report.json`) | Written into the plan by `reference_to_plan.py` |
|---|---|
| every shot's start and end | the Scenes table, scaled to the new runtime and snapped onto the voice's pauses |
| the transition into each shot (family, direction, frames) | the Transition cell (`fade 12f`, `wipe left 9f`, `cut +flash`) |
| the camera of each shot (driver, zoom, pan, ease, shake) | the Camera cell (`push 1.00>1.18`, `keys 0=1.00 ; 1=1.20 out`, `pan left 6% …`, `hold`) |
| text on screen (time, box, ink colour, entry motion), if OCR was on | Overlays rows at the sample's times and heights; a caption track becomes a Caption bands row |
| nearest grade, loudness, beat alignment | header lines to compare against, not applied automatically |

**What stays yours:** the footage (`[CLIP]`/`[s]` per scene: `plan_scenes.py` or by hand; never reshuffle one source across videos, `references/policy.md`), every word on screen (`--texts`, or the spoken words
when `--words` is given), the music licence, the claims. A genre's compliance checklist is copied in with `--genre ID`.

**Checking:** `pacing_checker.py edit-plan.md --reference ref/report.json` judges the plan against the sample (shortest and longest shot, median shot, the sample's opening, its runtime
± a margin). A scene outside the sample's range is a warning, not an error: you may deviate on purpose; a gap, an overlap or an empty first frame is still an error.

**What it cannot do (say so in the report):** read the sample's wording (OCR strings are hints, never copied), name a transition's exact shape or direction (read it from the dense sheets), tell a speed ramp from an
eased camera move, match a typeface, or free-place text off the vertical axis (`phrase` and `pill` take a vertical position or a point; a free text box is not built yet). Each of these is marked "look" in the plan.

Questions to ask (at most three, with defaults): which footage goes where if the sample's shot count exceeds the clips; whether the sample's text structure (a hook line, a price, a CTA) has real content to put in each slot;
whether the video will be boosted as an ad.
