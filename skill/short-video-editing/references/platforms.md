# Platforms — TikTok, TikTok Shop, Instagram Reels (and YouTube Shorts)

What each platform documents about format, safe zones, ranking and originality, and what that changes
in the edit. **[O]** official statement or help page, **[C]** craft convention, **[U]** unverified.
Research of 2026-11-07; platforms change their pages often, so re-check a number before quoting it.

---

## 1. Delivery format

| | TikTok (organic / In-Feed ad) | Instagram Reels (organic / ad) | YouTube Shorts |
|---|---|---|---|
| Aspect | 9:16 recommended [O] | 9:16 [O] | vertical or square [O] |
| Resolution | ≥ 540×960, "shoot at least 720p" [O] | ads: 1440×2560 recommended [O] | — |
| Length | ads up to 10 min; the spec page recommends no length [O] | up to 3 min (Mosseri, 20 Jan 2025) [O]; ads 0 s–15 min | up to 3 min (uploads after 15 Oct 2024) [O] |
| File / codec | ads ≤ 500 MB, ≥ 516 kb/s [O] | ads ≤ 4 GB, H.264, constant frame rate, AAC ≥ 128 kb/s [O] | — |

The kit's master: **1080×1920, 30 fps (constant), H.264 CRF 18, AAC 192 kb/s 48 kHz, +faststart**,
audio at −14 LUFS / −1 dBTP (`process_audio.py master`). One clean master serves every platform.
Length is a **playbook** decision (`playbooks/`), not a platform one: the platforms allow minutes;
what holds attention depends on the genre.

## 2. Safe zones

TikTok publishes downloadable safe-zone templates but no pixel values [O]. The kit measured the real
feed on an iPhone screenshot (product bar's bag tile at frame (112, 1677), bar y 1644–1709, action rail
x ≳ 920 from y ≈ 960; `layout-and-motion-graphics.md`), and uses a conservative layout: hard no-go
y < 220, y > 1400 (except the cart arrow), x > 900 below y ≈ 700; titles at y 236–420, captions at
y ≈ 1340.

Meta documents a safe zone for **Reels ads**: keep the top 14%, the bottom 35% and 6% on each side
clear [O] — on 1080×1920, top 269 px, bottom 672 px (y > 1248), sides 65 px. Organic Reels have a
bottom overlay (username, caption, audio) of roughly the bottom fifth [U].

| Use | Layout | How |
|---|---|---|
| TikTok, TikTok Shop, organic Reels | feed layout (captions y ≈ 1340) | default |
| Reels or Facebook **ads** | captions raised to y ≈ 1100, nothing in `lower`, overlays inside x 65–1015, y 269–1248 | `plan_to_project.py --platform reels-ad` |
| Reels (any) | no `cart` arrow: there is no TikTok Shop product bar | the sync report warns |

Check a real phone before a campaign: a private test post, or Remotion's safe-zone overlay.

## 3. What the ranking rewards (only what the platforms said)

- **TikTok For You** (TikTok newsroom, June 2020) [O]: user interactions (likes, shares, comments,
  watch completion), video information (captions, sounds, hashtags), then device and account settings
  with lower weight.
- **TikTok ads creative guidance** (June 2025) [O]: the proposition in the first 3 s, the hook within
  6 s, use sound, captions or text for context, on-screen text at 5–10 words/s, a DIY rather than
  over-polished look, a clear CTA. TikTok Shop Academy (May 2026, via a summary): hook in the first
  3–6 s, then hook → key message → call to action.
- **Instagram** ("Instagram Ranking Explained", 31 May 2023) [O]: for Reels the key predictions are
  reshare, watching to the end, like, and visiting the audio page. Reels that are **watermarked**,
  low-resolution, muted, bordered, mostly text, or already posted are shown less.
- **Mosseri** (Jan 2025) [O]: the top three signals are watch time, likes per reach and sends per reach.
- **Originality** (Instagram, 30 Apr 2024; Meta, July 2025) [O]: reposts are replaced by the original
  in recommendations; recommended content must carry no visible watermark; accounts that repeatedly
  repost without meaningful changes lose reach. TikTok: reused content without creative edit, or with
  another platform's watermark, is ineligible for the For You feed (`Chính sách.md`).
- **Trial Reels** (Dec 2024) [O]: a Reel can be shown to non-followers first; useful to test two hooks
  of the same edit without hurting the main account.

What the edit does with this: hook in 3 s (every playbook), sound on from frame 0, burned-in captions
for viewers with sound off, no watermark from another app, no text-only slides (`promo-sale` keeps the
footage visible under the type), one master exported clean (never a TikTok download re-posted to Reels).

Numbers that circulate without a source, do not repeat them: "90% of ad recall in 6 s", "21–34 s ads
= +280% conversions", "85%/92% watch on mute" (contradicts "80% of Reels watched with sound"), "animated
captions = +34% watch time", "safe-zone violations = −39% CTR", "trending audio = +58% add-to-cart".

## 4. Music by platform

| | What a business account may use |
|---|---|
| TikTok | The **Commercial Music Library** (about 1 million tracks, free for businesses, organic or paid, region-dependent) [O]; off-TikTok use not covered, assume TikTok only [U]. In a study of 1,842 TikTok Shop affiliate videos, 74% used original audio or none, 22% the CML. |
| Instagram / Facebook | Meta Sound Collection (about 14,000 royalty-free tracks) [U, second-hand]; business accounts cannot use most popular licensed music. |
| YouTube Shorts | A Short over 1 minute with any copyright claim is blocked globally [O]. |

Bake into the master only CC0, self-made or all-platform licensed music; add CML music inside the
TikTok app at upload when wanted. Details and levels: `audio-and-music.md`.

## 5. TikTok Shop specifics

- Shoppable video minimum 8 s; shoppable videos ≥ 60 s are disqualified from Creator Rewards
  (commission still paid) [P-adjacent].
- An original script per video (TikTok Shop creator policy): adapting one brief for many creators means
  a different opening, specifics and framing for each.
- The product bar and its cart tile are real UI: point at them, never draw a cart.
- A removed shoppable video still counts toward posting-frequency limits; penalties escalate from a
  warning to removal, points, suspension and deactivation; TikTok Shop Vietnam removes the product and
  related content on detection (`claims-and-compliance.md`, `Chính sách.md` §2.6).

## 6. Publishing checklist (every video)

- [ ] Master passes `process_audio.py measure` (−14 ± 1 LUFS, TP ≤ −1 dBTP) and plays on a phone.
- [ ] Commercial-content disclosure switched on (TikTok "Disclose commercial content"; Instagram
      "Paid partnership" label) when anything of value changed hands; ads labelled (Luật Quảng cáo 75/2025).
- [ ] AI-generated or substantially AI-edited content labelled.
- [ ] Music licensed for this platform and account type.
- [ ] Reels ad? Rendered with `--platform reels-ad`, no cart arrow, no before/after comparison.
- [ ] Posting limits of the market respected (`Chính sách.md` §2.6).
