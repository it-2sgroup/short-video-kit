# Pacing and Transitions

## Why the scene-length rule exists

Distribution on short-form platforms is driven by early retention. A static shot that runs past
about four seconds gives the viewer a natural exit point, and once they leave, the video stops
being shown to anyone else. The 4-second ceiling is not an aesthetic preference — it is a guard
against the most common way a product video quietly dies.

Every source surveyed agrees on the direction (faster cuts → higher completion). None of the
precise percentages circulating in this field survive scrutiny, so treat the cadence as craft, not
as a measured law.

---

## The cadence

| Rule | Value | Status |
|---|---|---|
| Hook resolves | ≤ 3.0s | **Hard rule** — checked by `scripts/pacing_checker.py` |
| Maximum scene length | 4.0s | **Hard rule** — checked |
| Typical scene length | 2–3s | Target |
| Hook beats | 1–2s each | Target |
| Something changes visually | every 5–7s minimum | Floor |
| Re-hook | once, around the midpoint | Target |

**What counts as a scene change.** Any of these resets the clock, so you are not obliged to keep
finding new camera setups:

- A new shot or a different camera angle
- A punch-in or pull-out on the same footage (the cheapest option, and the most underused)
- A cutaway to B-roll
- A substantial change in on-screen text or graphics
- A speed ramp that visibly alters the motion

That last group matters for the budget: a single locked demo take can legitimately be cut into
four scenes using punch-ins and text changes, with no extra shooting.

---

## Structure for a 30–40s product review

The reference data puts the ideal runtime at 30–40s, with CTR peaking in the 35–44s band. This
skeleton fits that window.

| Phase | Timing | Purpose |
|---|---|---|
| **Hook** | 0–3s | Earn the next three seconds. 2–3 beats of 1–2s. |
| **Problem** | 3–8s | Make the stake concrete. Name the garment and the stain. |
| **Early CTA** | ~8–10s | Plant the cart reference once, lightly. |
| **Demo** | 10–26s | The transformation. The longest phase; keep cutting inside it. |
| **Re-hook** | ~18–20s | Reset attention mid-demo — a new angle, a second stain type, a surprising detail. |
| **Reveal** | 26–32s | Pay off the hook. Hold slightly longer here; this is the shot people screenshot. |
| **Close CTA** | 32–38s | Say it again, concretely, pointing at the real cart. |

**On the early CTA.** This is the best-evidenced creative recommendation available: Wistia's
analysis of 14M+ videos found that sub-60s video converts best with the CTA in the first quarter,
not at the end. Caveat — that is hosted business video, not TikTok, and "conversion" means CTA
click. Still, placing the CTA only at the end is a defensible thing to argue *against*.

In the reference dataset, roughly 40% of videos recorded a 0% click-through rate. They were watched
and never tapped. An early, light cart mention is the cheapest insurance against joining them.

---

## Transitions

### The default is a hard cut

A straight cut is the right choice in the large majority of cases. Transitions that occupy many
frames — dissolves, long wipes — waste a disproportionate share of a 35-second runtime and are
harder to read at phone size.

If you cannot articulate *why* a particular transition is there, cut instead.

### Transitions that earn their place

| Transition | What it is | When |
|---|---|---|
| **Match on action** | Movement started in shot A continues in shot B | Pouring, scrubbing, wiping — the natural fit for a cleaning demo |
| **Graphic match** | Composition of A echoes B | Stained cloth → clean cloth in identical framing |
| **Whip pan** | Fast camera move; motion blur hides the cut | Location jumps. Both sides must whip at matched speed and direction or it reads broken |
| **Mask / occlusion** | A hand, cloth or the product crosses the lens and wipes frame | Clean, native-looking on vertical, and cheap to shoot |
| **Punch-in jump cut** | Same shot re-framed tighter, cut on a word | The workhorse. Use it on emphasis words |

Cut **during** the movement, not after it finishes. A match cut placed after the action completes
reads as two separate shots.

### Transitions to avoid

Canned preset packs — spin, glitch, star wipe, cross-dissolve — read as template content. Beyond
looking amateur on a small screen, heavy reliance on them edges toward the unoriginal-content
territory that costs For You feed eligibility.

### The one place you must not cut

**Do not cut between the "before" and the "after" of a demonstration.**

A hidden cut across the reveal is exactly what makes a cleaning demo read as fake, and it is what
TikTok's misleading-demonstration policy treats as creating a false impression. Hold the take.
If the real process takes hours, speed-ramp it and label the compression on screen ("tua nhanh ×8",
"sau 2 tiếng"). See `platform-specs.md` §2.

This is the rare case where the credible choice and the compliant choice are the same choice.

---

## Re-hooking and open loops

A 30–40s video should carry **2–3 small unresolved questions** and **one explicit mid-point reset**.

Open loops for a cleaning demo:
- "Cái vết thứ hai mới là cái mình bất ngờ" (plants a second reveal)
- "Mà có một chỗ nó không ra hẳn, lát mình chỉ" (promises honesty — also useful compliance cover,
  since an imperfect result avoids "ends all problems" framing)
- "Chai hồng là bước một thôi, bước hai mới quan trọng"

The mid-point re-hook is a deliberate interruption around 18–20s: switch angle, introduce the
second stain type, or drop the music out for a beat. Place it where attention naturally sags, not
at a tidy structural boundary.

---

## Keeping within the rules when the footage fights you

**The demo take is 12 seconds and cannot be cut.** Use punch-ins. One locked take becomes:
wide 0–3s → punch to the stain 3–6s → back to wide 6–9s → tight on the result 9–12s. Four scenes,
one take, no hidden cut across the reveal.

**There is only one camera setup.** Vary scale rather than angle — wide, medium, macro are three
distinct scenes from the same position. Add on-screen text changes as a fourth axis.

**The voiceover runs long.** Cut the breaths and dead frames first; that routinely removes 15–20%
with no loss. If it is still long, drop a feature rather than extending scenes past 4s — a video
that explains less but holds attention outperforms a complete one nobody finishes.

**You are under 25 seconds.** Do not pad. Add a second stain type or a second garment — real
content, not a longer hold on existing shots. In the reference data, sub-25s videos had the lowest
CTR and sale rate of any length band, so going short is the worse option.
