# Decisions, pitfalls met, and sources

Each entry records **what is true**, **how we know**, and **what is still uncertain**. Only **technical** decisions and pitfalls are kept here;
the work done for each client (client names, campaign figures, file names) is in `docs/CASE-LOG.md`.

## Licences: two places that cost money / may be a violation

| Tool | Terms | Source |
|---|---|---|
| **Remotion** | Free for individuals or for-profit organisations with **at most 3 employees**. Above that a Company License is needed, **$25/month/person "who writes Remotion code themselves or using agentic coding tools"** → Claude writing the code still counts as 1 seat | `LICENSE.md` of the repo remotion-dev/remotion; remotion.dev/docs/license/faq |
| **ElevenLabs** | The Free plan **"cannot be used for any commercial purpose"**; audio generated outside a paid plan "(before or after) cannot be used commercially"; Free requires attribution | elevenlabs.io/docs/help-center/legal/can-i-publish-the-content-i-generate-on-the-platform |
| ffmpeg static build | GPL. Internal use, no redistribution | johnvansickle.com/ffmpeg |
| Whisper / faster-whisper | MIT | — |

Remotion telemetry: the machine-side render CLI only sends data **when a license key is set**; browser-side rendering always sends
(IP, domain name). Recorded for information, **not** a hint to dodge the licence: the company currently qualifies for Free.

## Technical pitfalls met

**1. `eleven_multilingual_v2` does NOT support Vietnamese.** The name "multilingual" is misleading; the model has only 29
languages, with no `vi`. Models with `vi`: `eleven_v4`, `eleven_v4_turbo`, `eleven_v3`, `eleven_turbo_v2_5`,
`eleven_flash_v2_5`. How to know: `GET /v1/models`, look at `languages`. The first version of this document got it wrong: fixed after
asking the API. Current default: `eleven_turbo_v2_5` (tried: it accepts the settings and runs on the Free plan).

**2. The Free plan can only call `premade` voices through the API.** Library/professional voices (including the Vietnamese voice Ethan
in the account) return HTTP 402 `paid_plan_required`.

**3. Whisper mishears Vietnamese.** "túi xách" (handbag) → "tui sách", "kiểu dáng" (style) → "kiểu gián" (cockroach style). Invisible in a transcript,
glaring when burned onto a video. The fix: take the **timing** from Whisper, take the **words** from the original script (we know them
exactly because we sent them to the TTS), and join them by comparing strings with the diacritics removed. Verified: 171/171 words matched.

**4. faster-whisper 1.2.1 breaks with a new PyAV** (`open() got an unexpected keyword argument 'metadata_errors'`).
Do not pin the version; decode with ffmpeg into a numpy array and hand that straight to Whisper.

**5. The `[excited]` emotion tag is only understood by v3-family models.** Other models read the word "excited" aloud. `make_voiceover.py`
drops the tag for models that do not support it; `align_captions.py` always removes tags from the caption text.

**6. A Python venv cannot be carried to another machine** (paths and version are hard-wired). That is why `setup.sh` rebuilds
instead of copying. A Python venv is a symlink to the system Python, so comparing `resolve()` cannot tell the two
apart: this bug was caught by running `selftest.sh` on a simulated "new machine".

**7. The new Hugging Face cache uses a shared `blobs/` folder**, so `du` on the model folder reports 2.6 MB while the real model is
462 MB (symlinks). When packaging, use `cp -L`.

## Edit architecture (11/2026)

**One plan table → `project.json` → one Remotion composition.** No video content lives in the
code: changing the video means changing the plan. Reasons:
- The channel Mike Like Design (TikTok) showed that editing a video by typing a prompt for every change is both slow and token-hungry;
  a fixed set of skills/workflow + data is the fast, cheap way.
- `browser-use/video-use` (MIT) does the same: the agent works on a word-level transcript, not on frames.
- `remotion-dev/skills` (Remotion's official rules for AI agents): all motion follows
  `useCurrentFrame()`, transforms on a wrapper layer, `perceptual-scale` when zooming.

Components chosen and reference sources:

| Part | Choice | Source |
|---|---|---|
| Transitions | `@remotion/transitions` (fade, slide, wipe, iris, pushCut, flip, crossZoom) + 3 written by us (zoomThrough, blurDissolve, whip); centred on the cut point so they do not drift from the voice | Remotion docs; HyperFrames (Apache-2.0) for the whip/blur parameters |
| Text | Be Vietnam Pro + Playfair Display Italic (emphasis) + Anton (numbers); 5 title styles; no outlined boxes | Google Fonts metadata (the `vietnamese` subset was checked); sample images from the channel Mike Like Design |
| Layout | Strip at the top / a free face area / a chest strip / a caption strip; avoid the button bar on the right | Third-party measurements (TikTok does not publish them); the Remotion safe-zone overlay |
| Camera | push/pull/pan/hold + a keyword-driven punch-in, perceptual zoom, no reset at cuts | StudioBinder, iart-ai/tiktok-video-skills (MIT), Remotion docs |
| Beat sync | Anchor graphics to a word (`@"word"`), cut on pauses, an automatic sync report | Netflix's Vietnamese subtitle guidelines (17 characters/second), video-use |

`iart-ai` = the MIT skill sets `iart-ai/tiktok-video-skills` and `ecommerce-video-skills` (Remotion). Read, parameters
taken; not copied verbatim because some numbers have no source ("87% decide in 3 seconds").

**Checked for real on the project's Windows machine:** a shader render (`crossZoom`, light leak) with GL `angle`; a full
33.7-second render with 12 scenes, 17 graphic layers, karaoke captions; audio and picture of equal length.

**Not checked:** the final video was not listened to/watched in full on a real phone; the safe zones were not compared against a trial
post; no render from a 2160×3840 proxy yet (a punch-in > 1.15× will be blurry on a 1080p proxy).

## The second renderer: HyperFrames (11/2026)

**Why.** Remotion charges per seat from 4 employees up and an agent writing Remotion code also takes a seat. HyperFrames
(HeyGen, Apache-2.0, "no per-render fee or commercial threshold" according to its README) builds video from HTML + seekable animation,
rendered with headless Chrome + ffmpeg. The choice was to **keep everything before the render step unchanged** (analysis, proxies, voice, captions,
plan, checkers) and only swap the renderer: `project_to_hyperframes.py` reads the same `project.json`.

**Design.** HyperFrames' contract is a paused GSAP timeline; the `kit.js` painter is a **pure function of the frame**
(`render(frame)`) exactly like a Remotion component, so the formulas (easing, spring, camera, centred transitions) were ported as they are
and the motion does not depend on how HyperFrames seeks. GSAP only pushes the playhead through a setter, because `seek()` suppresses callbacks by default.
Scenes with `speed`/`ramp` are baked with ffmpeg (HyperFrames only plays a constant speed); the audio is pre-mixed into one file
(`audio/mix.wav`) so it does not depend on HyperFrames' volume automation.

**Checked for real** (Windows, Node 26, HyperFrames 0.9.26, system Chrome): `check` 0 errors (23 `line_unread` warnings because captions follow
fast speech); a 28.5 s video renders in ~55 s, 855 frames; loudness −16.3 LUFS and duration the same as the Remotion version; 6 frames of
transitions/captions and 7 frames of graphics side by side look identical to the naked eye; speeds 2x, 0.5x and ramp give exactly the scene's frame count.

**Not checked / limits.** The HyperFrames audio was not listened to; the graphics `pin`, `label`, `chart`, `specs`, `stat`,
`progress`, `lowerThird`, `image` were not rendered side by side with Remotion (the HyperFrames image was looked at, the Remotion image of the same frame could not be
rendered in that run); `magnifier`, `thumbs`, `compare`, `ranking` are not drawn; `crossZoom` is a blur-zoom, not a WebGL
shader; on Windows HyperFrames uses screen capture (not the BeginFrame path that exists only on Linux), so a bit-for-bit match with a
Linux render is not guaranteed; GSAP is loaded from jsDelivr, so the first render needs a network.

**Frame comparison with Remotion** (same video, 855 frames): SSIM 0.987, PSNR 36.3 dB; 852/855 frames above 0.95. The first
measurement was only 0.946 because Remotion's `perceptual-scale` interpolates zoom by **area** (`√(a² + t(b² − a²))`), not exponentially
as the first port did: fixed. A frame-counting clip showed that both renderers read exactly the same source frame. Render time (same machine,
one run each): HyperFrames 56 s (an earlier run 122 s), Remotion 100 s.

**CapCut-style effects** (`+shake`, `+glitch`, `+rgb`, `+pulse`, `--look`) exist only in HyperFrames; `plan_to_project.py` stores
`scenes[].fx` and warns that Remotion ignores them. The first version used `drop-shadow` to split colours: wrong (the shadow of an opaque frame only shows at the
edges), so it was changed to an SVG filter that splits the channels for real. A rounding trap: Python's `round()` rounds half to even while
JS `Math.round` rounds up, enough to be one frame off at a 9-frame transition: the script uses a round-half-up helper.

References: `github.com/heygen-com/hyperframes`, `hyperframes.heygen.com` (html-schema, data-attributes, frame-adapters,
gsap-animation, shader-transitions, cli, rendering, faq), `heygen.com/research/html-to-video`. The catalogue of CapCut techniques was compiled
from the app's public descriptions (app stores, feature pages): names and paid tiers change.

## Camera keyframes (11/2026)

**Why.** CapCut builds motion with keyframes (set a value at a mark, change it at another mark, easing for each segment); the toolkit
had only one push/pull/pan per scene. Added `Camera: keys TIME=ZOOM[@X,Y][ roll DEG][ ease] ; …`: 2-4 named frames, one
easing per segment, and the focus is the **point of the shot** placed at the centre of the frame (unlike `focus`, which is the origin point of the scale). Both renderers read
`scenes[].camera.keys` (`ts` = seconds from the cut point; fractions of the scene are converted to seconds in `plan_to_project.py`).

**Design decisions.** Zoom is interpolated by **area** like Remotion's `perceptual-scale`; centre and roll are interpolated linearly; the frame edge
is never exposed (translation is clamped by the spare scale, except what the roll needs); 8 named easings instead of free bezier handles, because that is enough for
short ads and can be checked; `back` (8 % overshoot) is used once per video at most. Sources: CapCut's keyframe page and PC guide (the
recipes: Ken Burns = two scale keyframes a few seconds apart, punch-in = two keyframes close together), the principles of easing/anticipation/
overshoot in motion design (used sparingly).



## Multi-genre extension (11/2026)

**Why playbooks.** The original toolkit served a single genre (product review): the pacing constants (2.5–4 s, 25–45 s), the structure
HOOK→PROBLEM→…→REVEAL, the shot types STAIN/POUR/SOAK, the camera and the transitions were all hard-coded in scripts. Now everything that depends on the
genre is data in `playbooks/<id>.json`, with 8 genres and 7 variants. A client's house style (scenes 3–4 s, soft
transitions, no text in boxes) is the default of the `product-demo` playbook, not applied to food or montage (where 1–2 s scenes on the
beat are the craft standard): if the same client does another genre, say so to the client.

**The principle "a technique must be used".** `playbook.py check` (run by the selftest) fails if a graphic component, grade,
theme or caption style is not used by any playbook; every key in the JSON has a script that reads it (the table in `playbooks/README.md`);
the plan skeleton generated by the playbook itself must pass the playbook's own pacing rules at both ends of the ideal duration range.

**Pitfalls met while building (measured, fixed):**

| Pitfall | Consequence | How the code handles it |
|---|---|---|
| "Gray world" white balance on every pixel | A green plastic basin in a real clip read as a +0.10 green cast | Measure only near-neutral pixels; when < 5% of the frame is neutral, do not guess |
| Measuring noise by PSNR against a denoised copy | Textured concrete (daytime, clean) read 43.6 dB as "noisy" | Denoise only when < 40 dB, or < 44 dB and the scene is dark |
| `hqdn3d` on the first frame | Barely filters → first-frame PSNR 55 dB against 41 dB for later frames | Skip the first frame when measuring |
| An RGB filter right after `vidstabtransform` | ffmpeg 7.0 segfaults (exit −11) | Insert `scale=iw:ih` |
| A chain of separate colour filters on 4K60 | 113 s for 6 s of footage | Bake white balance + exposure + grade into a 3D LUT (Hald 64³): 45 s, 46 dB PSNR difference |
| ffmpeg's `grayworld` | 23× slower than real time, outputs float | Not used |
| Two 4K ffmpeg jobs in parallel | A 14 GB machine ran out of RAM, a process was killed | Documented: one heavy job at a time on a small machine |
| Noise floor = 10th percentile | A TTS voice with few pauses: it landed on a word's edge (−47 dB) → "denoising" a clean file, floor up to −31 dB | The 5th percentile (real pauses, −90 dB) |
| Compression with a fixed −24 dB threshold | A loud voice was compressed by 10 dB and the level-matching step pulled the noise up with it | Threshold = voice level − 8 dB, plus a light expander |
| `afftdn`, `alimiter`, `loudnorm` | 25 ms delay; adds gain by itself; sample limiting rather than true peak; linear silently turns into dynamic | See `references/audio-processing.md` |
| Captions showing one word at a time | ASSETS 2019/2021 research: viewers read ahead, sentences of 6–12 words are easier than single words | The `pop` style shows a whole phrase of ≤ 5 words and highlights the spoken word |
| Animating `playbackRate` in Remotion | Does not work (Remotion docs) | A ramp re-reads the source frame frame by frame inside `<Freeze>`; checked on a clip with a clock |

**Research (2026-11-07):** three parallel strands: editing techniques for 12 genres (with Vietnamese rules: Advertising Law 75/2025
in force from 2026-01-01, the 2023 Real Estate Business Law, Decree 339/2026 replacing Decree 16/2022, the ban on "trị" (treat/cure) in cosmetics, the dietary-supplement (TPBVSK) warning), audio processing
+ platform parameters (TikTok/Instagram publish no LUFS standard; Meta's Reels ad safe zone is 14% top / 35% bottom /
6% on both sides; Mosseri's ranking signals, 2025-01), image processing (self-measured on ffmpeg 7.0, synthetic clips and one real 4K60
iPhone clip). Five often-quoted figures had no traceable source: they are listed in `references/platforms.md` §3 so they are not repeated.

**Further checks after the user handed over "decide yourself, do your best" (2026-11-07):**

| Item | How it was checked | Result |
|---|---|---|
| HDR | An HLG/BT.2020 10-bit version converted from a real iPhone clip | The common `hable` formula darkened it by 30% (luma 90 against 128) → changed to `mobius`: 125 / saturation 11.6 against 11.6 for the original |
| Night scene | A real clip darkened + sensor noise | Measured as "exposure, denoise"; the proxy lifts shadows, grain clearly reduced |
| On-camera voice detection | The same picture, one version with ambient sound, one with a voice | no / yes, correct |
| Shake/movement | A real clip shot on a tripod | 0.0 / 0.0: correctly a still camera |
| Beats on real music | 3 CC0 OpenGameArt tracks, checked against onset spacing | The pure-Python detector was wrong on 2/3 tracks, the "contrast" version wrong on 2/3; the numpy version (spectral flux + tempogram + DP) was right at 97 and 104 bpm, 88–95% of beats on onsets; the syncopated track came out at 73 bpm (110 is also plausible) |
| Output audio | A 9 s render with voice + real music + SFX, mastered, measured | −14.0 LUFS, peak −1.4 dBTP; speech ~−11.7 LUFS, music in the pauses ~−20.1 LUFS (about 8 LU lower) |
| Eval `routes-real-estate-tour` | A fresh agent with only the installed skill, scored by 5 graders | Passed 5/5: playbook `real-estate`, the visitor route, cut on music, a balcony hook at 1.5 s, facts verbatim, no invented legal claims, checker PASS, compliance mentioned. It exposed a bug: `suggest` leaned to `:voiceover` because of the word "môi giới" (broker) → variants now add the keywords of the base playbook and drop negated keywords ("không có giọng đọc", no voiceover) |
| Eval `asks-when-ambiguous` | As above, 2 graders | Passed 2/2: recognised the two directions (talking-head / food-fnb:review), asked exactly 3 questions with defaults. It exposed a bug: "giày" (shoes) wrongly matched "50 giây" (50 seconds) once diacritics were removed → matching now keeps diacritics and respects word boundaries; added the keyword "đứng nói" (standing and talking) for talking-head; reports a "Close call" between two genres |
| Installation on this machine | `setup.sh` (using the Whisper model already in the Hugging Face cache, no re-download) | `selftest.sh` passes in full, `--render` passes |

**Still not checked:** real handheld footage, night shots, 0.5× wide angle, real HDR footage; music with changing tempo; human ears
have not heard any output (the file `mix_final_phone.mp4` was sent for a listening test).

## Tools for on-camera presenter videos and rebuilding from a sample video

General decisions (the history of the first run is in `CASE-LOG.md`; the full recipe: `references/agency-pitch-recipe.md`):

- **A voice spliced from the takes themselves**: when the voice file is the original camera audio of the spliced takes (correlation 0.98–1.0), each presenter scene uses the picture of
  the take itself with `In = start + lag` (`match_voice_takes.py`), so the lips match sample for sample; `check_lipsync.py` re-checks the final cut. A part
  that no take contains gets cutaway pictures from the silent pre-roll/walk-off of other takes (`find_cutaways.py`), never another take of the same line.
- **The opening silhouette flash**: the presenter is filled white on the first few frames (e.g. frames 0, 2, 4 at 30 fps) and then the video plays. Made with the person-segmentation model
  `u2net_human_seg` (Apache-2.0, 168 MB, kept outside the repo, ask before downloading) → alpha PNG; the same model gives the head position (`--faces`). Chosen because it runs on CPU with
  onnxruntime (already there with faster-whisper), needing no GPU or account.
- **Text**: the effects live in one engine (`Fx.tsx`) instead of one component per effect, and each effect is used few times in a video. An ellipse around the
  text cut across the face → use a two-bar frame hugging the text; a flickering neon made the text disappear → a gentler flicker.
- **Sound**: a bank of many CC0 recordings + self-synthesized sounds, rotated per event (no immediate repeats), each text effect has its own sound, the variant's `sfx.rules`
  limits the number of sounds per 3 s. Nobody listened: chosen by name, pack description and measurements. **Tried and dropped**: automatically detecting the effect sounds in the mix
  (energy jumps above 1 kHz): on a mix with 68 sounds at known positions, AUC was only 0.53–0.58 because the voice masks them. `analyze_reference.py` instead gives a spectrogram image
  (`spectrum_*.png`) for people to look at; the number of sounds and the share of cuts with a sound are NOT reported.
- **Music**: a TikTok business account may only use the Commercial Music Library (which a render cannot reach) → `make_music.py` writes a self-made bed that follows the
  cuts, and delivers an extra version without music. `--music-levels=-6,-6` needs the `=` (argparse rejects `-8,-8`; without reading the "wrote" line the video comes out without music).
- **Colour range**: Remotion exports full-range `yuvj420p`; phones show it washed out or burnt → `finish_video.py` converts it back to limited BT.709, master −14 LUFS / ≤ −1 dBTP.
- **Render**: 8 workers report "No frame found at position" with 2880-tall proxies → `--concurrency=5`.
- **A client's logo** is keyed out of a sample frame only when there is no other way (alpha = (R−G+55)/260, ffmpeg `geq`, 4× Lanczos upscale): ask the client for the vector file.
- **Not checked on first use**: nobody listened to the sound/music; figures spoken in the voice are the client's words and need evidence; client names on cards need consent.

## Tools surveyed

| Tool | Conclusion |
|---|---|
| **Kinocut** (github.com/KyaniteLabs/kinocut): an MCP server wrapping ffmpeg, 205 tools, Apache-2.0 | Real (243 stars). **Not installed, not tried.** A candidate if we want a checking layer between Claude and ffmpeg |
| auto-editor | Cuts silent passages automatically. Fits the step of cleaning raw footage. Not used |
| browser-use/video-use (MIT) | Transcript-based editing, cuts on pauses ≥ 400 ms. Its rules were taken; its transcription step needs ElevenLabs Scribe (paid) |
| heygen-com/hyperframes (Apache-2.0) | HTML + GSAP, not React. Motion/caption rules taken, not the code. The old HyperFrames project was deleted from the repo |
| remotion-dev/skills | Official rules for agents; no licence was found so it is only referenced, not copied |
| MoviePy, editly, OpenTimelineIO | MoviePy is slow; editly abandoned since 05/2025; OTIO only when exporting to Premiere/DaVinci is needed |

⚠️ A search result advertised a repo `kyanitelabs/mcp-video` with "87 tools": that repo **does not exist** (the GitHub API
returns 404; the real name is KyaniteLabs/kinocut). Third-party MCP directories give contradictory star counts. **Always check a repo
through the GitHub API before trusting it.**
