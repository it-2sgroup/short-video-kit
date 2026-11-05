# Hook Library

The hook is the first 0–3 seconds. It decides whether the video is distributed at all.

In the reference dataset (`niche-winning-patterns.md`), the top 20% of videos by views earned 95%
of all revenue, while the bottom 80% averaged 171 views — and GMV per 1,000 views was actually
*marginally higher* in the bottom group. Those videos were not failing to persuade. They were
failing to be seen. That is what makes the hook the highest-leverage part of the edit.

---

## How a hook is built

A hook is three channels doing **three different jobs** at the same time. The common mistake is
making all three say the same thing, which wastes two of them.

| Channel | Job | Example |
|---|---|---|
| **Visual** | Show the most arresting state — usually the end result or the worst-case problem | Locked shot of a badly stained white collar |
| **On-screen text** | State the promise or the stake in words | "Cái áo này suýt bị vứt" |
| **Audio** | Start a sentence the viewer needs to finish | VO mid-thought: "...và đây là lúc mình định bỏ nó đi" |

TikTok's own creative guidance is explicit that a video should open with sound rather than a silent
title card; the platform reports that 88% of users consider sound integral to the experience
(`ads.tiktok.com/business/library/Creative_Best_Practices_UKI_SMB.pdf`). A silent opening throws
away a third of the hook.

**Structural requirements** (enforced by `scripts/pacing_checker.py`):
- The hook resolves by **3.0 seconds**.
- Frame 0 is never empty — it is the thumbnail in the feed.
- Prefer **two ~1.5s beats** (before → after, joined by a wipe) over one static 3s shot. Motion in the first second is
  itself a reason to keep watching.

---

## Hook archetypes, ranked

The ranking below comes from the only hook dataset I found with a disclosed methodology: 121,820
hooks analysed by median views (`quso.ai/tools/video-hook-generator`).

**Read the ranking with care.** The spread between the best and worst archetype is only about 31%,
and the sample came from a narrow niche. It is strong enough to tell you what to *avoid*, not
strong enough to promise that one archetype will beat another on your product.

| Rank | Archetype | What it does | Fit for a cleaning demo |
|---|---|---|---|
| 1 | **Social proof** | Frames the video as a response to demand | Excellent — and it is the one superlative TikTok permits |
| 2 | **Product reveal** | Product enters frame immediately, unexplained | Good |
| 3 | Transformation | Before state → after state | **Best structural fit for this product** |
| 4 | Shocking stat / claim | Opens on a number or assertion | Constrained by the exaggeration rules — see `platform-specs.md` |
| 5 | Pain point | Names the viewer's problem in their own words | Good when specific, weak when generic |
| 6 | Open loop | Withholds the resolution | Good as a second beat, weak as a first |
| 7 | Curiosity question | "Why does nobody know about this?" | Mid-pack — weaker than its reputation |
| 8 | Contrarian / counter-claim | "Stop scrubbing. You're ruining the fabric." | Underperforms its reputation |
| 9 | Direct command | "Do this before you throw that shirt out" | Avoid |
| 10 | Authority | "As a textile chemist…" | Avoid — worst of the ten tested |

**The practical read:** lead with social proof, a product reveal, or the transformation itself.
Stay away from authority framing and bare commands.

---

## Written hooks for a laundry stain remover

All of these are checked against the claim rules in `platform-specs.md`. Vietnamese, in the
conversational register the campaign's top creators actually use.

### Result-first / transformation (strongest fit)

The transformation *is* the product. Show it immediately, then earn the right to explain it.

> **Visual:** Locked shot. Clean white collar fills frame. Hand pulls it aside to reveal the
> stained "before" underneath.
> **Text:** "Cái áo này 10 phút trước"
> **VO:** "Chỗ ố này mình tưởng phải bỏ áo luôn rồi…"

> **Visual:** Split frame — one half of the stained cloth treated, the other half untouched.
> **Text:** "Nửa trái ngâm rồi, nửa phải chưa"
> **VO:** "Cùng một cái áo, cùng một chỗ nha."

The split-half version is worth reaching for. It removes the "they swapped the shirt" suspicion
entirely, and because it is self-evidencing it also sidesteps the misleading-demonstration rules.

### Social proof (compliant superlative)

> **Text:** "Cái mọi người hỏi trong cmt nãy giờ"
> **VO:** "Rồi rồi, nay mình test thật cho coi."

> **Text:** "Bán chạy nhất shop mình tháng này"
> **VO:** "Mà mình vẫn phải tự thử mới dám nói."

Claims about your own sales are explicitly permitted — this is the compliant way to use a
superlative.

### Pain point — specific, not generic

Specificity is what separates a pain-point hook that works from one that scrolls past. "Bạn có mệt
mỏi vì quần áo bị ố không?" is generic and dead. Name the garment, the stain, the moment.

> **Text:** "Áo đồng phục của con, mới mua tháng trước"
> **VO:** "Dính sa tế một cái là coi như xong."

> **Text:** "Vết này 2 năm rồi"
> **VO:** "Giặt bao nhiêu lần cũng vậy."

### Pattern interrupt

> **Visual:** Hand drops the stained shirt into a bin. Beat. Hand reaches back in and retrieves it.
> **Text:** "Khoan đã"

### Stain-creation open (anti-fake)

Showing the stain being made on camera is the strongest credibility signal available, because the
viewer watches the "before" come into existence.

> **Visual:** Clean white shirt. Red antiseptic poured directly onto the collar in close-up.
> **Text:** "Cố tình làm bẩn để test"
> **VO:** "Làm bẩn thật luôn, chứ không lấy áo cũ ra đâu."

---

## Hooks to avoid

| Avoid | Why |
|---|---|
| "Sản phẩm tốt nhất thị trường" | Prohibited absolute superlative |
| "Tẩy sạch ngay lập tức" | Prohibited instant-effect claim |
| "Không sạch hoàn tiền" | Guaranteed-results claim — appears in existing scripts for this campaign and should be removed |
| "Diệt khuẩn 99.9%" | Prohibited antibacterial claim for a cleaning product |
| "Là chuyên gia giặt là, tôi khuyên…" | Authority archetype, worst-ranked |
| "Hãy mua ngay" as the opening line | Direct command, second-worst ranked, and asks before earning |
| A silent 3-second title card | Throws away the audio channel |

---

## Choosing a hook in practice

Work in this order, because it fails fast:

1. **Does the footage contain a visible transformation?** If so, use it. It is the best structural
   fit and needs no claim to carry it.
2. **Is there genuine social proof available** — real comment volume, real sales rank? Use it.
   It is compliant and well-ranked.
3. **Can you name the problem specifically** — this garment, this stain, this moment? Use a pain
   point.
4. Otherwise fall back to a product reveal, and strengthen the second beat with an open loop.

Then write the on-screen text and the voiceover to say **different** things, and check the opening
line against the rewrite table in `platform-specs.md` §7 before locking it.
