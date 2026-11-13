# Hook Library

The hook is the first 0–3 seconds, in every playbook. It decides whether the video is distributed at all.

In the product-demo reference dataset (`niche-winning-patterns.md`), the top 20% of videos by views
earned 95% of all revenue, while the bottom 80% averaged 171 views — and GMV per 1,000 views was
*marginally higher* in the bottom group. Those videos were not failing to persuade; they were failing
to be seen. TikTok's own guidance puts the proposition in the first 3 s and the hook within 6 s
(`platforms.md` §3). That is what makes the hook the highest-leverage part of any edit.

---

## How a hook is built

A hook is three channels doing **three different jobs** at the same time. The common mistake is
making all three say the same thing, which wastes two of them.

| Channel | Job | Example |
|---|---|---|
| **Visual** | Show the most arresting state — usually the end result, the best view or the worst-case problem | The finished room from the balcony; a cheese pull; the worst-case problem in close-up |
| **On-screen text** | State the promise or the stake in words | "Căn 2PN view sông dưới 4 tỷ" · "Món này suýt bị vứt" |
| **Audio** | Start a sentence the viewer needs to finish, or hit the music's first downbeat | VO mid-thought: "...và đây là lúc mình định bỏ nó đi" |

TikTok's own creative guidance is explicit that a video should open with sound rather than a silent
title card; the platform reports that 88% of users consider sound integral to the experience
(`ads.tiktok.com/business/library/Creative_Best_Practices_UKI_SMB.pdf`). A silent opening throws
away a third of the hook.

**Structural requirements** (enforced by `scripts/pacing_checker.py` from the playbook):
- The hook resolves by **3.0 seconds**.
- Frame 0 is never empty — it is the thumbnail in the feed.
- The playbook sets the beats: two ~1.5 s beats for demos and tours (before → after, view → facts),
  one sentence for a talking head, two beats on the first downbeats for montages and lookbooks. Motion
  in the first second is itself a reason to keep watching.

---

## Hook archetypes, ranked

The ranking below comes from the only hook dataset found with a disclosed methodology: 121,820
hooks analysed by median views (`quso.ai/tools/video-hook-generator`).

**Read the ranking with care.** The spread between the best and worst archetype is only about 31%,
and the sample came from a narrow niche. It is strong enough to tell you what to *avoid*, not
strong enough to promise that one archetype will beat another on your product.

| Rank | Archetype | What it does | Notes |
|---|---|---|---|
| 1 | **Social proof** | Frames the video as a response to demand | Strong, and own-sales claims are the one superlative TikTok permits |
| 2 | **Product / place reveal** | The subject enters frame immediately, unexplained | Good for products, dishes, properties |
| 3 | Transformation | Before state → after state | Best fit wherever a visible result exists (demo, renovation, makeup) |
| 4 | Shocking stat / claim | Opens on a number or assertion | Constrained by the claim rules — `claims-and-compliance.md`; a real price works |
| 5 | Pain point | Names the viewer's problem in their own words | Good when specific, weak when generic |
| 6 | Open loop | Withholds the resolution | Good as a second beat, weak as a first |
| 7 | Curiosity question | "Why does nobody know about this?" | Mid-pack — weaker than its reputation |
| 8 | Contrarian / counter-claim | "Stop doing X. You're ruining Y." | Underperforms its reputation |
| 9 | Direct command | "Do this before you throw that out" | Avoid |
| 10 | Authority | "As a trained specialist…" | Avoid as the opening line — worst of the ten tested (credentials belong in a lower third) |

**The practical read:** lead with social proof, a product reveal, or the transformation itself.
Stay away from authority framing and bare commands.

---

## Hooks by playbook

Each playbook's `.md` has its own examples (product-demo: written and compliance-checked hooks). The patterns that fit each genre [C]:

| Playbook | Visual (0–1.5 s) | Text | Sound |
|---|---|---|---|
| product-demo | the result, then the problem; a split half (treated / untreated) | the stake, specific ("Món này mới mua tháng trước") | VO mid-thought |
| real-estate | the best view or room, a door opening onto it | price + place, or one specific feature ("3,2 tỷ có gì ở Thảo Điền?") | first downbeat |
| food-fnb | the money shot: pull, pour, sizzle, steam | the dish + one hook word (price, place) | the sizzle itself (J-cut) |
| talking-head | the speaker mid-sentence on the boldest line, or B-roll of the payoff | the payoff, not the topic | the sentence itself |
| tutorial | the finished result | the number of steps or the time ("3 bước, 5 phút") | VO promise |
| fashion-beauty | the final look, or the most striking change on a beat | how many looks / the theme / the budget | the drop |
| montage-recap | the most spectacular moment, hard cut on beat 1 | two to four words, or nothing | the track's opening hit |
| promo-sale | the offer on the product | the number ("−50%", "11.11") | a hit under the number |

Write the on-screen text and the voice to say **different** things, and check both against the
playbook's compliance list before locking them.

---

## Hooks to avoid

| Avoid | Why |
|---|---|
| "Sản phẩm tốt nhất thị trường" | Prohibited absolute superlative |
| "Tẩy sạch ngay lập tức" | Prohibited instant-effect claim |
| "Không sạch hoàn tiền" / "cam kết lợi nhuận" | Guaranteed results (products) or returns (property) |
| "Diệt khuẩn 99.9%", "trị mụn", "giảm cân" | Prohibited category claims (`claims-and-compliance.md`) |
| "Là chuyên gia …, tôi khuyên…" | Authority archetype, worst-ranked as an opener |
| "Hãy mua ngay" as the opening line | Direct command, second-worst ranked, and asks before earning |
| A silent 3-second title card | Throws away the audio channel |

---

## Choosing a hook in practice

Work in this order, because it fails fast:

1. **Does the footage contain a visible transformation or a spectacular moment?** Use it. It is the
   best structural fit and needs no claim to carry it.
2. **Is there genuine social proof** — real comment volume, real sales rank, a real customer? Use it.
3. **Can you name the problem or the promise specifically** — this item, this price, this
   neighbourhood, this step count? Use it.
4. Otherwise fall back to a reveal, and strengthen the second beat with an open loop.

Two hooks can be tested on the same edit with Trial Reels (shown to non-followers first); never by
posting near-identical copies, which is repetitive content (`policy.md`). The data rarely
says in advance which archetype wins for a given product.
