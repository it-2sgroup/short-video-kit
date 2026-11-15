# Evidence behind the product-demo playbook defaults — measured TikTok Shop data

Everything here comes from one real TikTok Shop dataset: **16,242 videos** for one Vietnamese
household-cleaning product (a stain remover), posted 2025-06-02 → 2026-11-03, totalling **45.5M views**,
**2,967,050,809 VND GMV** and **33,067 units sold**. It is the evidence for the numbers in
`playbooks/product-demo.json` (runtime band, hook-first structure, early cart).

Read this before writing an edit plan for a household-cleaning or similar demo-driven product.
It tells you where the leverage actually is, which is not where most editing advice assumes. One
product in one market is one data point: the findings justify the playbook's defaults, they are not
laws for other genres.

Each finding is tagged:
- **[DATA]** — measured directly in the dataset, with the numbers shown.
- **[HYPOTHESIS]** — plausible, consistent with the data, but not measurable in it. Treat as a
  bet to test, not a fact to assert.

---

## Table of contents

1. [The single most important finding](#1-the-single-most-important-finding)
2. [Duration: the sweet spot is 35–44s](#2-duration-the-sweet-spot-is-3544s)
3. [CTR is the money lever](#3-ctr-is-the-money-lever)
4. [Creator concentration beats volume](#4-creator-concentration-beats-volume)
5. [Caption patterns: real but weak](#5-caption-patterns-real-but-weak)
6. [Posting time](#6-posting-time)
7. [The demo format: the transformation is the hook](#7-the-demo-format-the-transformation-is-the-hook)
8. [What the data cannot tell you](#8-what-the-data-cannot-tell-you)
9. [Data quality caveats](#9-data-quality-caveats)

---

## 1. The single most important finding

**[DATA] Reach is the bottleneck, not persuasion.**

Splitting all 15,784 videos with views into quintiles by view count:

| Group | Videos | Avg views | Median views | % that made any sale | Total GMV | Share of all GMV |
|---|---|---|---|---|---|---|
| Top 20% | 3,157 | 13,745 | 1,907 | 69.4% | 2,820,204,775 VND | **95.1%** |
| Bottom 80% | 12,627 | 171 | 102 | 9.0% | 144,761,814 VND | 4.9% |

The top fifth of videos earned 95% of all revenue. The bottom 80% averaged **171 views** — they
were barely distributed at all.

Now the part that changes how you edit. GMV per 1,000 views was *slightly higher* in the bottom
80% (692,383 VND) than the top 20% (605,102 VND). When a low-reach video did reach someone, it
converted them just fine.

**So the product pitch was never the problem. Distribution was.** Distribution on TikTok is driven
by early retention, which is driven by the hook and the cut rhythm. This is why the hard rules in
SKILL.md are about the first 3 seconds and scene length, not about how well you explain features.

When asked to "make the product benefits clearer", recognise that this dataset says
that is rarely the binding constraint. Push the effort to the hook instead.

---

## 2. Duration: the sweet spot is 35–44s

**[DATA]** Video length comes from each video's duration field. Across 15,607 videos with a duration:

| Duration | Videos | Avg views | Avg CTR | % that made any sale |
|---|---|---|---|---|
| <15s | 1,194 | 422 | 2.33% | 11.9% |
| 15–24s | 3,392 | 660 | 2.45% | 14.9% |
| 25–34s | 4,727 | 2,735 | 3.12% | 23.2% |
| **35–44s** | 3,613 | 4,908 | **3.37%** | **26.6%** |
| 45–59s | 2,130 | 5,301 | 2.91% | 24.6% |
| 60–89s | 473 | 1,326 | 2.74% | 17.1% |
| 90s+ | 78 | 2,875 | 2.52% | 17.9% |

Both click-through rate and the share of videos that sell anything peak in the **35–44s** band.
Videos under 25 seconds are markedly worse on every measure.

**The creator-controlled check.** A reasonable objection: maybe good creators just happen to make
longer videos, and it is the creator, not the length, doing the work. Restricting to proven
creators only (≥30 videos and >20M VND GMV each):

| Duration | Videos | Avg CTR | % that made any sale |
|---|---|---|---|
| <25s | 11 | 4.55% | 9.1% |
| 25–34s | 287 | 2.31% | 68.3% |
| **35–44s** | 523 | **3.41%** | 67.5% |
| 45s+ | 315 | 2.01% | 63.5% |

The CTR peak at 35–44s survives the control, so there is a real length effect. But notice the
first row: **proven creators made a sub-25s video only 11 times out of 1,136 attempts — about 1%.**
People who have learned what works on this product have essentially stopped making short videos.

**Practical rule: target 30–40s.** That straddles the two best bands and leaves room for the plan
to run slightly over without falling off a cliff. Do not go under 25s. Treat a request for a
"quick 15-second version" as worth pushing back on, and say why.

---

## 3. CTR is the money lever

**[DATA]** Splitting 9,499 videos (≥100 views) into quintiles by click-through rate:

| CTR quintile | CTR range | Videos | Avg duration | Avg views | Avg GMV | Share of all GMV |
|---|---|---|---|---|---|---|
| Top | ≥1.54% | 1,900 | **35.1s** | 12,569 | 916,304 VND | **59.0%** |
| 2nd | 0.28–1.54% | 1,900 | 32.0s | 5,480 | 344,317 VND | 22.2% |
| 3rd | 0–0.28% | 1,900 | 31.4s | 1,636 | 73,910 VND | 4.8% |
| 4th | 0% | 1,900 | 32.5s | 1,814 | 98,987 VND | 6.4% |
| 5th | 0% | 1,899 | 32.3s | 2,431 | 118,530 VND | 7.6% |

The top CTR quintile produced 59% of all revenue, and it is also the band with the **longest
average videos (35.1s)**. Every lower quintile averages 31–32.5s.

Two quintiles sit at exactly 0% CTR — roughly 40% of videos never got a single product-card click.
Those videos were, commercially, wasted effort regardless of their view count.

**What this means for editing:** the product card click is the hinge of the whole funnel. The edit
plan must make the viewer *want to tap* — which means the product has to be visibly on screen and
verbally pointed at, not just mentioned. See `captions-and-text.md` for cart-pointing patterns.

---

## 4. Creator concentration beats volume

**[DATA]** Out of roughly 2,900 creators who posted about this product, the nine highest by GMV
(creators are anonymised here):

| Creator | Videos | Total views | Avg views | GMV per 1k views (VND) | Cumulative share of GMV |
|---|---|---|---|---|---|
| A | 96 | 6,141,949 | 63,979 | 67,118 | 13.9% |
| B | 144 | 4,961,042 | 34,452 | 59,931 | 23.9% |
| C | 73 | 2,646,494 | 36,253 | 89,075 | 31.9% |
| D | 173 | 4,738,220 | 27,389 | 44,445 | 39.0% |
| E | 33 | 1,449,341 | 43,919 | 114,891 | 44.6% |
| F | 264 | 1,417,951 | 5,371 | 82,989 | 48.6% |
| G | 48 | 1,341,877 | 27,956 | 85,318 | 52.4% |
| H | 32 | 1,748,598 | 54,644 | 59,188 | 55.9% |
| I | 51 | 1,379,213 | 27,043 | 71,659 | 59.3% |

**Nine creators produced 59.3% of all revenue. Fifteen produced 68%.**

Volume on its own does not substitute. The single most prolific creator posted **642 videos**, more
than anyone, and averaged 1,545 views, delivering 1.71% of GMV. Meanwhile creator E posted 33 videos
and delivered 5.62%, a 19× better return per video.

**[DATA] Reach and conversion are different skills.** Compare creators:
- Creator B: 34,452 avg views, 59,931 VND per 1k views — high reach, average conversion.
- A creator with 5,894 avg views and **144,101 VND per 1k views** — low reach, outstanding conversion.
- Creator F: 5,371 avg views, 82,989 VND per 1k views — low reach, strong conversion.

A creator who converts well but cannot get reach is an editing problem you can fix: give them a
stronger hook and tighter pacing, and their existing conversion carries the rest. A creator with
reach but weak conversion needs the opposite — clearer product visibility and a firmer CTA.

**Ask which problem a given creator has before deciding what to change.** The same generic edit
plan applied to both wastes the advantage each already has.

---

## 5. Caption patterns: real but weak

**[DATA]** Comparing captions of the top 20% by views against the rest:

| Caption feature | Top 20% | Bottom 80% | Lift |
|---|---|---|---|
| Avg distinct problem types (stain types) named | 0.95 | 0.64 | 1.5× |
| Captions naming 3+ problem types | 11.2% | 6.1% | 1.8× |
| Avg hashtag count | 3.1 | 2.7 | 1.1× |
| Mentions colored fabric safety | 2.3% | 1.2% | 1.9× |
| Makes a result claim ("như mới" = like new, "trắng bóc" = spotless white, "sạch bong" = squeaky clean) | 3.9% | 2.1% | 1.9× |
| Avg caption length (chars) | 78 | 65 | 1.2× |

Every signal points the same way, at roughly 2×, but all are low-prevalence — even among winners,
only 11% name three or more problem types. **Caption is a real but minor lever.** Do not spend much
of the edit budget here, and do not promise that caption rewriting will fix a video.

What the winning captions actually do, from reading the top 25 by GMV:
- Enumerate the specific problems the product handles (a list of named cases) rather than claiming
  general power.
- Lead with a reaction, not a feature (*"Không tin được..."*, "Unbelievable...").
- Carry 3–4 specific hashtags that name the use, not a hashtag wall.

**Caution on one observed pattern.** A high-earning caption promised "no payment if it is not
clean". This is a guaranteed-results / money-back claim. It performed well here, but see
`claims-and-compliance.md` — guarantee claims are a documented moderation risk. **Do not copy it.**
That it worked for one video is not a reason to put an account at risk.

---

## 6. Posting time

**[HYPOTHESIS — weakest finding here]** Grouping by posting hour (Asia/Ho_Chi_Minh):

| Slot | Videos | Avg views | Median views | % that made any sale |
|---|---|---|---|---|
| 22:00–04:00 | 820 | 9,535 | 562 | 40.2% |
| 10:00–13:00 | 2,480 | 5,671 | 420 | 32.5% |
| 18:00–21:00 | 2,164 | 4,323 | 462 | 34.0% |
| 14:00–17:00 | 2,272 | 4,123 | 466 | 35.2% |
| 05:00–09:00 | 1,763 | 2,755 | 386 | 30.4% |

Late-night posting leads on both mean and median views and on sale rate. But this is the smallest
sample, and which creators post late is uncontrolled — the top creators may simply post at night.
**Mention it as worth testing; do not present it as established.**

---

## 7. The demo format: the transformation is the hook

**[CONVENTION, consistent with the data]** The default format of the product-demo playbook stages a
visible change and holds the shot while it happens: apply the product to a prepared problem (for a
cleaning product, a stain made on camera) and keep the camera on it until the change is visible, with the
before/after result on screen **within the first 3 seconds**. This is consistent with the duration and
CTR findings: the transformation *is* the hook, and it is what earns the early retention that drives
distribution. The dataset cannot rank formats (it has no hook-type column, §8); this is the format
that product's creators were asked to use, not a measured winner.

**[HYPOTHESIS]** Three refinements that follow from the demo format but are not measured:
- Shoot the before and after from a locked, identical camera position. A matched frame reads as
  evidence; a re-framed one reads as a cut-away and invites suspicion.
- Keep lighting constant between before and after. A brighter "after" shot is the single most
  common reason viewers call a cleaning demo fake.
- Show the problem being *created* on camera when possible. Viewers who watch it appear are
  far less likely to assume two different items were swapped.

See `cutting-and-pacing.md` for how to place the reveal on the timeline.

---

## 8. What the data cannot tell you

Be honest about these limits when reporting. The dataset has no column for:

- **Hook type.** There is no label for whether a video opened with a question, a shock claim, or a
  result-first reveal. The hook taxonomy in `hook-library.md` comes from published editing research,
  not from this dataset. Any claim that "question hooks beat pain-point hooks for this product" is
  unfounded.
- **Retention / completion rate.** TikTok Shop's API does not expose watch-time curves here. Views
  are a downstream proxy at best.
- **Cut rhythm, scene count, transition style.** Nothing about the edit itself is recorded. The
  3–4 second scene rule comes from general short-form practice, not from this data.
- **Audio, music choice, voice.** Not recorded.

So: the duration, CTR, creator-concentration and reach findings above are yours to assert. The
pacing and hook guidance is informed practice. Keep the two apart when you explain your plan.

---

## 9. Data quality caveats

- The click-through-rate field contains some impossible values (a maximum of 4.0, i.e. 400%).
  A small number of records are corrupt. The quintile analysis is robust to this because it ranks
  rather than averages raw values, but do not quote a single video's CTR without sanity-checking it.
- There is a companion daily-metrics table whose rows repeat on a 7-day cycle. Summing it
  overstates totals by more than 100×. Every figure above comes from the per-video snapshot table
  instead. If you re-run this analysis, use the snapshot, not the daily table.
- About 40% of videos show exactly 0% CTR. Some of this is genuine (no one clicked); some may be
  unattributed. Treat the bottom two CTR quintiles as "no measurable commercial signal" rather than
  as a precise zero.
