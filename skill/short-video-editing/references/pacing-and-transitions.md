# Pacing and Transitions

## Why the scene-length rule exists

Distribution on short-form platforms is driven by early retention. A static shot that runs past
about four seconds gives the viewer a natural exit point, and once they leave, the video stops
being shown to anyone else. The 4-second ceiling is not an aesthetic preference — it is a guard
against the most common way a product video quietly dies.

Every source surveyed agrees on the direction (faster cuts → higher completion). None of the
precise percentages circulating in this field survive scrutiny, so treat the cadence as craft, not
as a measured law.

**Client correction (Nov 2026).** The first Remotion renders cut every 1.5–2s with hard cuts and the
client rejected them: *"tốc độ chuyển cảnh nhìn nó chưa liên kết, cứ bị tách rời… tầm 3 đến 4s là
chuyển cảnh… chuyển sao cho mượt hơn"*. A web search for evidence on "3–4s per scene" found nothing
authoritative, so the 3–4s rhythm is recorded here as the **client's requirement**, and the 4s
ceiling above remains the data-backed limit. The two fit together: 3–4s scenes, soft transitions.

---

## The cadence

| Rule | Value | Status |
|---|---|---|
| Hook resolves | ≤ 3.0s | **Hard rule** — checked by `scripts/pacing_checker.py` |
| Maximum scene length | 4.0s | **Hard rule** — checked |
| Minimum scene length (non-hook) | 2.5s | **Hard rule** (client) — checked, `--min-scene` |
| Typical scene length | 3–4s | Target (client requirement) |
| Hook beats | ~1.5s each (min 1.2s) | Target |
| Transition between scenes | ~0.4s soft (fade / slide / wipe), centred on the cut | Target (client requirement) |
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
| **Hook** | 0–3s | Earn the next three seconds. 2 beats of ~1.5s (before → after). |
| **Problem** | 3–9s | Make the stake concrete. Name the garment and the stain. 2 scenes of 3s. |
| **Early CTA** | ~9–12s | Plant the cart reference once, lightly. |
| **Re-hook** | ~12–15s | Product hero shot — a new beat of energy. |
| **Demo** | 15–25s | The transformation. 3 scenes of 3–3.5s. |
| **Reveal** | 25–31s | Pay off the hook. 2 scenes; this is the shot people screenshot. |
| **Close CTA** | 31–38s | Say it again, concretely, pointing at the real cart. |

**On the early CTA.** This is the best-evidenced creative recommendation available: Wistia's
analysis of 14M+ videos found that sub-60s video converts best with the CTA in the first quarter,
not at the end. Caveat — that is hosted business video, not TikTok, and "conversion" means CTA
click. Still, placing the CTA only at the end is a defensible thing to argue *against*.

In the reference dataset, roughly 40% of videos recorded a 0% click-through rate. They were watched
and never tapped. An early, light cart mention is the cheapest insurance against joining them.

---

## Transitions

### Default: a short soft transition on every cut

Hard cuts between unrelated clips read as *"cứ bị tách rời"* (disconnected) to the client. Join scenes
with a ~0.4 s transition centred on the planned cut (`fade` by default, `slide`/`zoomThrough` on a
change of beat, `wipe` for before → after). The catalogue, frame counts, the centred-cut maths and
sound under transitions are in `transitions.md`.

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

Canned preset packs — spin, glitch, star wipe, flashy zoom — read as template content, look amateur on
a small screen, and edge toward the unoriginal-content territory that costs For You feed
eligibility. A plain short cross-dissolve is fine.

### The one place you must not cut

**Never hide a cut between the "before" and the "after" of a demonstration.**

A hidden cut across the reveal is exactly what makes a cleaning demo read as fake, and it is what
TikTok's misleading-demonstration policy treats as creating a false impression. Hold the take when
you can. When the process takes hours, show the same item in the same framing and label the
compression on screen ("tua nhanh ×8", "sau 2 tiếng", "đã rút gọn thời gian"). See
`platform-specs.md` §2.

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
wide 0–4s → punch to the stain 4–8s → tight on the result 8–12s. Three scenes of 4s, one take, no
hidden cut across the reveal.

**There is only one camera setup.** Vary scale rather than angle — wide, medium, macro are three
distinct scenes from the same position. Add on-screen text changes as a fourth axis.

**The voiceover runs long.** Cut the breaths and dead frames first; that routinely removes 15–20%
with no loss. If it is still long, drop a feature rather than extending scenes past 4s — a video
that explains less but holds attention outperforms a complete one nobody finishes.

**You are under 25 seconds.** Do not pad. Add a second stain type or a second garment — real
content, not a longer hold on existing shots. In the reference data, sub-25s videos had the lowest
CTR and sale rate of any length band, so going short is the worse option.
