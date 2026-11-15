# Policy — videos flagged for reuse, duplicate content or footage lifted from other videos

This document answers one question: **if we make TikTok Shop sales videos from one existing footage source, in
large numbers (hundreds of videos), which approaches get flagged and which are safe?** It also answers whether
footage from other people's videos (for example Douyin) may be spliced in.

**Claude must read this file before** planning a batch of videos, before using any footage that is not the
user's own or licensed, and before proposing "shuffle the scenes / swap the music to get more videos".

Checked on 2026-11-06. This is a working summary of the policies, **not legal advice**.
Confidence labels: **[P]** official policy page that was read; **[S]** secondary source (blog, press, law firm);
**[C]** a convention of this toolkit; **[?]** not verified.

---

## 1. Eight rules for Claude

1. **Do not use third-party footage** (Douyin, TikTok, Kuaishou, YouTube, Facebook, a competitor's shop,
   another creator's video) without a **written commercial licence** from the owner. Ask the user; do not
   download or cut it yourself.
2. **Do not run, modify or rebuild** a "crawl Douyin videos" style pipeline (download Douyin without
   watermark → cut → re-dub → re-post) for sales videos. Section 4.3 explains why.
3. **One source range is not used in two videos of the same batch** (default `r = 1`, section 5). If the user
   wants more videos than the footage allows, **state the numbers and propose shooting more**; do not shuffle
   scenes.
4. **Two different videos must really be different**: script, voice, hook, structure, scenes. TikTok Shop
   names "re-posting the same video with only the order of clips changed" and "using the same generic sales
   script for a range of different products" as repetitive content (section 2.2). Changing the music, voice or
   background does **not** fix it.
5. **The footage must show the product being advertised.** Do not splice in another product's result as the
   "result" (section 2.5). Staged or sped-up footage must be labelled on screen.
6. **Ask the market and the posting limits.** Each market has its own limits (section 2.6); the Vietnam
   market could not be verified. Do not schedule hundreds of videos into one account, and do not post the
   same content to several accounts.
7. **Before/after in paid ads** is barred by the ad policy (`before-after.md`). Ask the user whether they
   plan to run ads / Spark Ads.
8. **Report honestly**: state the risk with numbers, state what is unverified (section 7), and do not say
   "safe" when the source is only a blog.

---

## 2. Violation groups

### 2.1 Unoriginal / reused content

| Rule | Source |
|---|---|
| "Content is also ineligible for the FYF if it includes unoriginal or reused material without anything new." Reused content with nothing new is **not eligible for For You**. | [P] Community Guidelines, *Integrity & Authenticity* |
| "You should only post content you created or have the right to share." Only post what you made or have the right to share. | [P] same page |
| TikTok Shop: content counts as unoriginal if "the user has not added new or creative edits to any imported or uploaded media". A watermark or logo showing on the video "is a sign of unoriginal content". | [P] TikTok Shop Academy, *Content Policy* (US, 2026-10-26) |
| Penalties (TikTok Shop): content removal, feature restrictions, violation points, account restrictions; applies to "all Creators and the content they promote". | [P] same page |

Consequence: a video spliced from other people's footage **without genuinely new creative work** is treated
anywhere from the mildest level (loss of distribution) to the heaviest (video removed, violation points).
Using Douyin footage also falls under section 2.4.

### 2.2 Repetitive (near-duplicate) content — including your own content

TikTok Shop defines repetitive content as content "published continuously and in bulk, where the
structure, visuals, narration, or materials are highly similar". Two examples are named directly in the
policy:

- "Re-posting the same video at high volume with only order of clips changed." (**re-posting the same video in
  bulk, only changing the order of the clips**)
- "Using the same generic sales script for a range of different products." (**one generic script for many
  different products**)

The policy says small changes to the music, narration or background do **not** end the repetition. [P]
*Content Policy*, US.

The Malaysian version of the *Content Posting Limit* article adds: large numbers of videos "hampir sama dengan
variasi kreatif yang minimum" (nearly identical, with minimal creative variation) and "menyiarkan video yang
serupa pada beberapa akaun" (posting similar videos on several accounts). [P] seller-my.tiktok.com (Malay
version, 2026-10-16).

**This hits the "one source → hundreds of videos" plan squarely:** shuffling scenes from one footage source is
exactly "changing the order of the clips".

The numeric threshold ("how many percent similar gets flagged") is **not published** [?]. Blogs say TikTok
uses content recognition (fingerprinting) to catch duplicates; that is the blogs' guess and is not in the
policy [S].

### 2.3 Spam, deceptive behaviour, multiple accounts, automation tools

- "You can have multiple accounts … but not to deceive others or break the rules." Multiple accounts are
  allowed, but not to get around the rules. [P] *Integrity & Authenticity*
- "We strictly prohibit automation tools, scripts, or other tricks designed to bypass our systems." [P] same page
- The list of TikTok Shop creator violations includes "Using multiple accounts to avoid enforcement". [P]
  *Creator Enforcement Policy* (US, 2026-10-09)
- Penalty for deceptive behaviour: account restrictions, "limiting your ability to post new content, appear in
  top search results, or in the FYF". [P] *Integrity & Authenticity*

Consequence: splitting a batch of near-identical videos across several accounts to "dodge" the limits is the
kind of behaviour that gets punished.

### 2.4 Copyright / intellectual property

**TikTok.** [P] *Copyright Policy* (2025-03-27):
- "We do not allow any content that infringes copyright."
- "The use of copyrighted content of others without proper authorization or legally valid reason may lead
  to a violation of TikTok's policies." (US *fair use* and EU *fair dealing* are mentioned as legitimate
  reasons, but are not guaranteed)
- TikTok may "ban the account of a user who repeatedly commits copyright infringement" and "immediately ban
  any account in cases of severe copyright violations".
- There is an in-app appeal; the copyright owner can object to the appeal.
- No specific number of copyright "strikes" was found [?].

**Douyin (source of Chinese videos).** [P] Douyin User Agreement (updated 2026-02-13, effective 2026-02-20):
- The intellectual property in a video belongs to the poster or the original rights holder (article 10.2).
- The user is only granted **"personal, … non-commercial"** use of Douyin and **may not** "改编、复制、传播、爬虫" —
  adapt, copy, distribute, crawl (article 2.4).
- Automated tools that collect content are prohibited (article 5.1).
- Without Douyin's **written licence**, it is prohibited to: edit content and then display it on another
  platform (5.3-2), download by scraping / simulated download (5.3-4), cover or alter the Douyin logo (5.3-5),
  and **"将抖音中的信息或内容用于任何形式的销售和商业使用"
  — use the content for any form of sales or commercial use** (5.3-7).
- The governing law is Chinese law, with the Haidian court (Beijing) having jurisdiction (article 16).
  Article 14.6: Douyin does not guarantee legality outside its official place of release; users are
  responsible under the law where they live.

Article 10.5 lets other users "转发、复制、下载" (forward, copy, download) **through platform features** — that
is viewing, sharing and personal download; it is not a commercial licence.

**Law.**
- China: the Beijing Internet Court (2018, Douyin v. Huopai) recognised short videos, even 15 seconds long, as
  works protected by copyright law. [S] technode, caixin, ipkitten. There is a criminal case in Jiaxing about
  someone who took film clips in bulk, edited them and evaded filters to re-post for profit. [S]
- Vietnam: Intellectual Property Law Article 28 lists acts that infringe copyright, among them copying a work
  without the owner's permission. [S] summaries by law firms; not checked against the original text [?].
  Administrative penalties are currently in Decree 341/2025/NĐ-CP; the fine amounts could not be read [?];
  there is a criminal bracket for serious cases, figures not verified [?].

Conclusion of this section: **downloading Douyin videos and splicing them into sales videos breaks Douyin's
terms, carries copyright risk in both China and Vietnam, and breaks TikTok's copyright policy.** Cutting them
small or changing the speed does not turn them into "new content" (section 2.1).

### 2.5 Misleading depiction: another product's footage, a result that is not yours

- TikTok Shop, *How to Avoid Misleading Content* (applies globally): consequences are "content removal or
  account suspension". [P] seller-us.tiktok.com (2026-06-25)
- Before/after must use the same light and angle, with no staged difference; the demo must reflect the real
  effect. See `claims-and-compliance.md` §3.
- A "result" demo video taken from another product (such as a Douyin clip) that lets viewers believe it is the
  result of the product being sold is **false advertising**, quite apart from the copyright risk. Vietnam: the
  Advertising Law bans misleading advertising; Decree 38/2021/NĐ-CP has a penalty bracket, with secondary
  sources giving 60–80 million VND for untrue or misleading ads, a cap of 100 million (individuals) and 200
  million (organisations), and one source saying it changed from 2026-05-15 [S][?]. Not checked against the
  text; a human needs to verify.
- Reminder of the toolkit's rule: never label a staged graphic as a "real customer review" (`CLAUDE.md`).

### 2.6 Posting frequency limits

| Market | Rule | Source |
|---|---|---|
| US | From 2026-05-11: at most 30 short shopping videos and 60 photo posts per day; trial affiliates under 5,000 followers: 3 videos per day and 3 LIVEs per week | [P] *Creator Eligibility Policy* (2026-09-25) |
| Malaysia | Posting 5 or more videos that are "tidak interaktif atau mengelirukan" (non-interactive or misleading) in 7 days gets a limit of 7 videos in the next 7 days; videos over the quota can still be posted but **lose their product link**. A pre-recorded voice or machine voice counts as "non-interactive" | [P] *Content Posting Limit* and the *Non-interactive content* article (seller-my, 2026-10-16 and 2026-11-05) |
| Vietnam | **No official page found** | [?] — check Seller Center / Creator Academy VN |

This toolkit's videos use a pre-recorded voice, so if the market applies the "non-interactive" definition as
Malaysia does, **batches of pre-recorded-voice videos may be limited** even when no scenes overlap.

### 2.7 Paid advertising

TikTok's ad policy does not allow "product effect comparisons, such as before-and-after results" in ads and
landing pages [P]; see `before-after.md`. Ask the user whether they run Spark Ads or ads.

---

## 3. Escalation of enforcement

| Step | What the policy says | Source |
|---|---|---|
| Distribution | "Unoriginal" videos lose the right to appear on For You; an account posting a lot of ineligible content may have the whole account made ineligible | [P] + [S] |
| Warning, restriction | "a warning, temporary feature or account restriction, or a full account ban, depending on what happened" | [P] *Accounts & features* |
| TikTok Shop (US) | Content removal, shopping-video limits, commission freeze, monetisation suspension, reduced reach. **The same violation 6 times in 90 days** can lose e-commerce access and freeze commission. A first warning carries no points | [P] *Creator Enforcement Policy* |
| Account ban | "Repeated rule violations" or "A single, severe violation"; serious copyright violations are banned immediately | [P] *Accounts & features*, *Copyright Policy* |
| Appeal | Appeal within 30 days of the action, once per violation; frozen commission can be lost if the appeal is late or rejected | [P] *Creator Enforcement Policy* (US) |

---

## 4. Application: one footage source has to yield many videos

### 4.1 "200–300 videos from one source": how much footage is needed

A 12-scene video needs about **42 seconds of its own source** (12 scenes × 3.5 seconds, which includes the
0.5 second buffer between two ranges of the same clip, see `footage-ingest.md` §1b). For example a 587-second
source ≈ 9.8 minutes is enough for about 14 videos when no scene is reused. Let `r` be the number of videos
allowed to share the same source range:

| Number of videos | `r = 1` (no reuse) | `r = 2` | `r = 3` | `r = 5` |
|---|---|---|---|---|
| 14 | 9.8 min | | | |
| 200 | 140 min | 70 min | 47 min | 28 min |
| 250 | 175 min | 88 min | 58 min | 35 min |
| 300 | 210 min | 105 min | 70 min | 42 min |

(How many minutes of **usable footage** are needed to reach the number of videos at reuse level `r`.)

- With a source of about 10 minutes, 200–300 videos are only possible if **each source range is reused about
  14–21 times**. That is the "re-post, change the order of the clips" model that TikTok Shop names as
  repetitive content (section 2.2).
- Changing the voice, music, background, crop or speed does **not** save it: the policy says small changes to
  music, narration and background do not end the repetition, and "visuals" are in the list of elements compared.
- The safe threshold is not published [?]. The toolkit's convention [C]: **`r = 1`** is the safe default;
  `r = 2` only when the two videos are completely different in script, voice, hook and order, and the user has
  accepted the risk.
- Even with enough footage, posting 200–300 videos from one account hits the frequency limit (section 2.6) and
  is easily treated as spam. The legitimate way to scale is **many real creators, each shooting and posting
  their own content** (section 6).

### 4.2 "Take scenes from another video and splice them in"

| Scene source | Conclusion | Reason |
|---|---|---|
| Douyin, TikTok, Kuaishou, YouTube… from other people | **No** without a written commercial licence | Sections 2.1, 2.4, 2.5 |
| A competitor's or another shop's video | **No** | Same reasons, plus the risk of copyright and trademark complaints |
| A video sent by a customer | Only with **written consent** allowing commercial use and posting on the channel | The rights belong to the person who filmed it |
| A hired creator/KOC video | **Yes** if the contract states commercial-use rights and editing rights; Spark Ads need an authorisation code | The right to share exists (section 2.1) |
| Licensed stock video | Only as **background / atmosphere**, not as "the product's result" | Commercial-use rights exist, but it is not footage of our product (section 2.5) |
| AI-generated footage | **No** for the product's result | Unrealistic effect demos are banned and AI must be labelled (`claims-and-compliance.md` §3) |
| Watching Douyin for **idea reference**, then shooting it again yourself | **Yes** | Ideas and kinds of shots are not works; a new shoot is original content |

### 4.3 The "download Douyin → re-dub → re-post" pipeline (a sample repo was read, only read, not run)

Open-source "crawl Douyin videos" repos (one public Python repo was read as a sample) do exactly one thing:
**download Douyin videos without watermark** (change `/playwm/` to `/play/` in the playback path, relying on
Douyin's internal page structure; or yt-dlp; or outside tools such as `Douyin_TikTok_Download_API` and `f2`
for bulk download by user / hashtag), then **STT → translate → TTS → blur the original caption → insert
subtitles → post to TikTok** through the Content Posting API. The sample repo has no part that recognises the
product content or cuts by scene.

Why it should **not** be used for sales videos:
- Downloading by scraping internal pages and avoiding the watermark = exactly the things Douyin bans (5.1,
  5.3-4, 5.3-5, 2.4).
- Commercial use is banned without a written licence (5.3-7).
- The "download → re-dub → re-post" pipeline is the **reused content** model, the same kind that section 2.1
  says is not eligible for For You and can be removed.
- The sample repo's README says: "Only download / re-dub / re-post public videos for personal / research
  purposes … Do not use for bulk download / commercial re-upload … without the owner's permission." (translated
  from the Vietnamese-language note.)
- The sample repo's posting part uses an app that has not passed TikTok's audit, so it can only post in
  private mode.

If Douyin footage is needed later: **ask the video's owner for a commercial licence** (contact directly, buy
the rights), keep the document, and only then put it into the footage library with a source line. Only then
use the scene-cutting tools. Claude must not download it in advance "to try".

---

## 5. The toolkit's convention for controlling scene overlap [C]

Applies to every batch of videos:

1. **Source ledger.** All `edit-plan.md` files of the batch sit side by side; run `footage_overlap_checker.py`
   with **all** the plan files (each file named). The result must be PASS (no overlap, ranges at least
   0.5 seconds apart).
2. **`r = 1` by default.** When the unused source ranges run out, **stop and report**, with the minutes that
   need to be shot (table in section 4.1).
3. **Real variants, not shuffles.** Any two videos must differ in **script** and **voice**; add at least two of
   three factors: hook, scene structure, graphics set. Only changing the order of the clips, the music,
   background, crop or speed is **not enough** (section 2.2).
4. **One script per product.** Do not use a generic script frame for many products.
5. **Do not split a batch of near-identical videos across several accounts.**
6. **Footage of the right product**; staged and sped-up footage is labelled.
7. **Before posting:** ask the market, check the posting limits, remind to turn on "Disclose commercial
   content", ask whether ads will be run.

---

## 6. The legitimate way to get large numbers

- **Shoot by a variant matrix** instead of shooting once and shuffling: each combination of *subject
  (material type, colour, style…) × situation (the problem to solve) × product model (type, size, combo) ×
  camera angle (from above, level, close-up)* gets its own set of clips: before, handling, result. Budget
  **~42 seconds of usable footage per video**.
- **A creator / KOC network**: each person shoots and posts their own content, and you use the reuse rights
  through a contract or a Spark Ads code. This is how TikTok Shop is designed to scale [C].
- **Customer videos** with written consent.
- **Stock footage** only for background; not for results.
- **Ideas from Douyin**: watch as reference, then shoot again with your own product.
- Editing with this toolkit stays cheap; what is scarce is **legitimate footage**, not the editing step.

---

## 7. Unverified, needs a human check

- **TikTok Shop Vietnam policy** (repetitive content, posting limits, violation points): no official page
  found; the pages read are the US and Malaysia versions. Check Seller Center / Creator Academy VN.
- **The "similarity" threshold** that TikTok uses to flag repetition: not published; every number on blogs is
  a guess.
- **The TikTok support article about watermarks of other apps** (videos carrying a Douyin logo are excluded
  from For You): the help page could not be read; only the line "visible watermark … sign of unoriginal
  content" in the Shop Content Policy.
- **Vietnamese law**: Article 28 of the IP Law has not been checked against the original text; the penalty
  amounts in Decree 341/2025/NĐ-CP have not been read; the figures of Decree 38/2021 conflict between sources.
- **Chinese law** only through press (the 2018 case and the Jiaxing criminal case).
- Secondary sources say TikTok Shop began tightening unoriginal content from 2025-09-15 and repetitive content
  from 2025-09-25: no official announcement accompanies this [S][?].

## 8. Sources

Official: TikTok Community Guidelines (`tiktok.com/community-guidelines/en/integrity-authenticity`,
`fyf-standards`, `accounts-features`, `enforcement`, `regulated-commercial-activities`); TikTok Copyright
Policy (`tiktok.com/legal/page/global/copyright-policy/en`); TikTok Shop Academy: *Content Policy* (US,
`knowledge_id=6837891779151617`), *Creator Enforcement Policy* (`6837869503317761`), *Creator Eligibility Policy*
(`6939143037667118`), *How to Avoid Misleading Content* (`4581457528194817`), *Content Posting Limit* (seller-my,
`6519771097237249`), *Non-interactive content* (seller-my, `752633581209360`); TikTok Ads policy *Misleading and
false content*; Douyin User Agreement (`douyin.com/draft/douyin_agreement/douyin_agreement_user.html`).

Secondary: BigSeller (articles 3778, 3766, 4377, 4203), PPC Land (two June 2026 articles), Calywire, TokPortal;
technode, caixin, ipkitten on the Douyin v. Huopai case; law summaries from luatvietnam.vn, lsvn.vn,
thuvienphapluat.vn on Article 28 of the IP Law, Decree 341/2025 and Decree 38/2021.

Sample repo read: a public open-source "crawl Douyin videos" style repo (README and the download/post code
read through the GitHub API; not downloaded, not run).
