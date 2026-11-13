# CapCut techniques, mapped to this kit

What editors do in CapCut for short vertical video, and how to get the same result here: in the plan, in
a script, in the HyperFrames renderer, or not at all. Use it two ways: when the request says "make it like a
CapCut edit" (find the technique, find the cell), and when you want a technique and do not know whether
the kit has it. The renderers: `remotion-output.md`, `hyperframes-flow.md`.

**Status codes.** **K** the kit, both renderers (the plan syntax is given). **H** the HyperFrames renderer
only. **S** a script or an ffmpeg step before the render. **D** a documented how-to that is not wired or
tested here. **—** not done: the reason is given. The feature lists are CapCut's as publicly described (app
stores, the desktop and mobile editors); features, tiers and names change, and some are paid ("Pro")
or need an internet connection: check the current app before promising one [C].

---

## 1. Cutting and rhythm

| CapCut | Status | In the kit |
|---|---|---|
| Cut on the beat; AutoCut / beat sync with music | **K** | `suggest_cuts.py --music track.wav --playbook <id>` finds the beats (spectral flux, tempo, bar starts) and chooses cuts on them; `playbook.py skeleton --cuts` writes the plan. Voice-driven videos cut on pauses instead and may nudge a cut onto a beat within 4 frames |
| Remove silences / jump cut a talking head | **K** | `trim_voice.py talk.mp4 --jumpcut`: pauses removed, scenes carry their source times (`playbooks/talking-head.md`) |
| Split, trim, delete, ripple edit | **K** | the plan's Start / End / Source / In columns; `plan_scenes.py` fills Source and In without reusing a range |
| J-cut and L-cut (sound leads or trails the picture) | **K** | the voice is one continuous track, so every B-roll scene is an L-cut; `audio-and-music.md` |
| Match cut, cut on action | **K** | by hand in the plan; cut between a gesture's start and end, never inside a word |
| Re-hook every 8–10 s | **K** | a punch-in, a title change or a camera switch at the playbook's re-hook beat (`cutting-and-pacing.md`) |
| Multi-clip / multi-track timeline, layers | **K** | one clip per scene, overlays on their own timeline (`Overlays` table) |
| Freeze frame | **D** | no `freeze` keyword. Closest: `Speed: ramp 1>0.15` slows the scene to almost a stop; a true freeze: `ffmpeg -ss T -i clip.mp4 -frames:v 1 still.png`, then a looping clip: `ffmpeg -loop 1 -i still.png -t 2 -r 30 -pix_fmt yuv420p still.mp4` into `public/clips` |
| Reverse a clip | **S** | `ffmpeg -i in.mp4 -vf reverse -an out.mp4` on a proxy (it loads the whole clip in memory: only short clips, never a 4K original) |
| Duplicate / loop a moment | **K** | the same Source range twice breaks the no-reuse rule (`footage_overlap_checker.py`); allowed only deliberately, inside one video, and said in the report |

## 2. Speed and time

| CapCut | Status | In the kit |
|---|---|---|
| Normal speed (0.1×–100×) | **K** | `Speed: 2x`, `0.5x`; under 1× needs a 60 fps proxy (`prepare_footage.py --slowmo`); the sync report flags slow motion that would stutter |
| Speed curve (Montage, Hero, Bullet, Jump cut, Flash in/out, custom) | **K** | `Speed: ramp a>b>c`, speeds spread evenly over the scene and eased (`Easing.inOut(sin)`). Rough equivalents [C]: Montage `ramp 0.6>2.5>0.6`, Hero `ramp 2>0.4>2`, Bullet `ramp 1>0.2`, Flash in `ramp 3>1`. More than five points are not worth it: the ramp is eased between them |
| Smooth slow motion (optical flow, frame interpolation) | **D** | ffmpeg `minterpolate=fps=60:mi_mode=mci` on a short proxy; slow and it smears fast motion. Prefer shooting 60 fps |
| Time compression of a process ("chờ 10 phút") | **K** | `2x` or a ramp **plus** an on-screen note that time was cut (`progress` overlay: "đã rút gọn thời gian"); never silently (`before-after.md`) |
| Audio follows the speed (pitch) | — | scene audio is not used: the voice is separate and sound effects are placed by the plan |

## 3. Camera and keyframes

| CapCut | Status | In the kit |
|---|---|---|
| Keyframe zoom in / out (Ken Burns) | **K** | `Camera: push 1>1.16`, `pull 1.24>1`: one continuous move per scene, eased, scaled perceptually (equal time = equal apparent zoom); moves must be visible (≥ 12 % scale) |
| Keyframe pan | **K** | `Camera: pan left 6%` |
| Keyframe rotate / handheld lean | **K** | `Camera: push … roll -1>1` (degrees); spare image is added so the corners never show |
| Focus on a point (zoom toward the product) | **K** | `focus 0.5,0.4` after the move (fractions of the frame) |
| Zoom punch on a word | **K** | `plan_to_project.py --punch-keywords "product name,70"`: a ×1.12–1.15 spring on the keyword that stays until the cut |
| Beat zoom pulse | **H** | `+pulse` on the cut: ×1.08 over 10 frames and back |
| Camera shake | **H** | `+shake` on the cut: decaying shake over 14 frames (an impact or a drop) |
| Ken Burns on a still photo | **D** | turn the still into a clip (`ffmpeg -loop 1 -i p.jpg -t 4 -r 30 -vf scale=1620:2880:force_original_aspect_ratio=increase,crop=1620:2880 -pix_fmt yuv420p p.mp4`) and give it a `push` |
| Auto reframe to 9:16 | **S** | `prepare_footage.py` scales to fill and centre-crops to 9:16 (no face tracking): check the contact sheet; put the subject in the middle third when shooting |
| Stabilize | **S** | `prepare_footage.py` (vid.stab, two passes, only when `inspect_footage.py --measure` finds shake) |
| Multi-point keyframes: scale, position, rotation, an ease per segment | **K** | `Camera: keys 0=1.05 ; 0.4=1.38@0.34,0.5 out ; 1=1.38@0.32,0.54 soft`: framings with an easing each (`camera-moves.md`, Keyframes). Overlay position/opacity keyframes: not built; each component moves by its own curve |
| Custom bezier keyframe graph | — | eight named easings (`inOut soft out in snap back linear hold`), no free bezier handles; the curves are in `engine/camera.ts` |

## 4. Transitions

| CapCut family | Status | In the kit (`Transition` cell) |
|---|---|---|
| Dissolve, fade | **K** | `fade` (default 12 frames) |
| Slide, push | **K** | `slide left|right|up|down` |
| Wipe | **K** | `wipe [dir]`: soft-edged, good before → after |
| Iris, circle open | **K** | `iris`: a hero reveal |
| Zoom, zoom blur | **K** | `zoomThrough`, `blurDissolve`, `crossZoom` (a real WebGL blur in Remotion; a zoom-blur dissolve in HyperFrames) |
| Whip pan, swipe | **K** | `whip [dir]`: fast slide with motion blur |
| Flip, card turn | **K** | `flip [dir]`, use sparingly |
| Hard cut with a punch | **K** | `pushCut`: cut at the middle, scale and a 2-frame flash |
| Flash, white flash | **K** | accent `+flash` |
| Light leak, film burn | **K** | accent `+leak` |
| Glitch, RGB split | **H** | `+rgb`, `+glitch` on the cut |
| Shake / earthquake | **H** | `+shake` |
| Shader family (ripple, swirl, liquid, burn, domain warp, lens, thermal) | **D** | `@hyperframes/shader-transitions` has 14 (`hyperframes-flow.md` §7); it needs its own scene structure |
| White silhouette flash (the speaker's outline filled white for a frame, three times) | **K** | scene `Subject` cell `0,2,4 @ mattes/CLIP_A` (other modes: `references/subject-effects.md`); `person_matte.py` cuts the person out of those frames with a segmentation model |
| Slide with trail, stacked-card slide | **K** | `cardSlide`: card scenes slide off with two fading copies behind (the card layout, `layout-and-motion-graphics.md`) |
| Spin-in cards, stack zoom | **K** | `cardSwirl`: the incoming shot arrives as three tilted cards that straighten into the frame |
| Wave warp, bulge, flag wave | **K** | scene layout `expand`: a card grows to the full frame with a fabric-like wave (SVG displacement) |
| Spin, mirror, pixelate, luma wipe, clone, page curl | — | not built; a hard cut or `whip` carries the same beat |

Playbooks set which transitions a genre uses and how many accents it may spend (`playbooks/<id>.md`,
`transitions.md`); a playbook's house style (`product-demo`: 3–4 s scenes, soft transitions) beats a fashion
taste for glitches.

## 5. Effects and looks

| CapCut | Status | In the kit |
|---|---|---|
| Vignette | **H** | `project_to_hyperframes.py --look vignette=0.3` |
| Film grain | **H** | `--look grain=0.06` (re-seeded every 6 frames) |
| Blur background / blur fill (a wide clip in a 9:16 frame) | **D** | `prepare_footage.py` crops to fill; for a blur-fill make the proxy with `ffmpeg -filter_complex "[0:v]scale=1620:2880:force_original_aspect_ratio=increase,crop=1620:2880,boxblur=40[bg];[0:v]scale=1620:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2"` |
| Black and white, sepia, duotone | **S** | a `grades.json` look (one 3D LUT with the white balance and exposure steps) |
| VHS, CRT, scanlines, lens flare, bokeh, snow, particles | **D** | CSS or an SVG layer in `kit.js` (`#look`); on Remotion a component. Not built: they read as a template look and compete with the product |
| Mirror, kaleidoscope, fisheye | — | not built |
| Split screen, grid, collage | **D** | two proxies side by side by a custom ffmpeg `hstack`/`vstack` clip; before/after has its own card (`compare`, Remotion only) |
| Picture in picture, magnifier | **K** | `magnifier` overlay (Remotion only): a lens on a 2.2× crop of a clip |
| Freeze + zoom "spotlight" | **D** | a `highlight` circle plus a `+pulse` on the cut |
| Letterbox bars | — | against the viewer-first layout (the footage owns the middle of the frame) |

## 6. Masks, cut-outs and compositing

| CapCut | Status | In the kit |
|---|---|---|
| Mask reveal (linear, circle, heart, star…) | **K** | the transition does it: `wipe` (linear, soft edge), `iris` (circle). A mask that stays on a clip is not built |
| Chroma key (green screen) | **D** | `ffmpeg -i fg.mp4 -vf "chromakey=0x00ff00:0.15:0.1" -c:v prores_ks -pix_fmt yuva444p10le fg.mov`, then composite in a render. Not wired: a green-screen shoot is not in any playbook |
| Remove background / smart cutout | **D** | `npx hyperframes remove-background` (u2net_human_seg, Apache-2.0) writes a transparent clip of the person; a model download: **ask first** |
| Text behind the subject (the trending "depth" title) | **D** | needs the cut-out above: title layer between the footage and the person layer. Layer order is CSS `z-index` in `kit.js`; add the cut-out as a second `<video>` above `#overlays`' title. Not built or tested; check the cut-out edge at 2× on a still |
| Overlay / blend modes (screen, multiply) | **K** | the light leak uses `screen`; others are one CSS line in `kit.js` |
| Track the subject (motion tracking of a sticker) | — | not built; a `callout` is placed by hand and only on a still moment (the sync report asks for a still check) |

## 7. Colour

| CapCut | Status | In the kit |
|---|---|---|
| Filters / LUTs | **S** | `assets/grades.json` (natural, bright-interior, warm-food, soft-skin, vivid): one baked 3D LUT per clip with the white balance and exposure steps; the playbook chooses |
| Adjust: exposure, brightness, contrast, saturation, temperature, tint | **S** | `inspect_footage.py --measure` finds a cast, dark or flat clip, `prepare_footage.py` corrects it from near-neutral pixels (a green bowl fooled grey-world: measured) |
| Colour match across clips | **S** | `correction: shared`: a BEFORE and an AFTER get the same correction |
| HSL, curves, selective colour | **D** | an ffmpeg `curves`/`selectivecolor` step in a `grades.json` look |
| HDR to SDR | **S** | `prepare_footage.py` tone-maps (iPhone HDR → BT.709) |
| Denoise, sharpen | **S** | only when dark or very noisy (texture fools the meter); a light unsharp at the end |
| Relight, skin retouch, body reshape, AI enhance | — | not built, and a product's own result must not be retouched: a demonstration is never faked (`SKILL.md` rule 8) |

## 8. Text and captions

| CapCut | Status | In the kit |
|---|---|---|
| Auto captions | **K** | `align_captions.py`: Whisper's **timing**, the script's **words**; corrected by hand first |
| Caption templates, word highlight (karaoke) | **K** | `captionStyle karaoke`: the whole phrase, the spoken word coloured; `pop`: a short phrase popping, for talking heads; `plain` |
| One word at a time | — | rejected on purpose: viewers read ahead (`captions-and-text.md`) |
| Text styles (outline, gradient, glass card, highlighter marker) | **K** | `title` styles `outline`, `stack`, `gradient`, `glass`, `marker`; one accent word; never the same style twice in a row |
| Text animations (in, out, loop: rise, blur-in, scale, typewriter) | **K** | every title rises through a mask with a blurred accent word; `phrase` letters scatter in and fly apart again; `pill` types in (short labels only: a typewriter on a long line delays the reading) |
| Curved text, text on a path, echo trail | **K** | `arc`: letters on an arc with echoes fanning out behind (the opening shout) |
| Handwritten, brush font | **K** | `script` (Pacifico) for one phrase; `phrase` for loud red/white blocks (Barlow Condensed) |
| Text pile / echo burst ("hidden letters jump up") | **K** | `burst` |
| Text presets: slam, stamp, glitch, neon, shine, drop, elastic, wave, flip, split, mask wipe, typewriter | **K** | `phrase` `fx=` (14 effects, `layout-and-motion-graphics.md`) |
| Beauty: skin brighten and soften | **K** | `faceGlow` (a feathered backdrop-filter patch on the head, `Face` column) and `look` warm; `image-processing.md` |
| Karaoke with a bigger coloured word | **K** | `captionStyle karaoke` (scaled, coloured word) and `captionBands` to move the captions above a card |
| Text templates, speech bubbles, boxes | — | no text in boxes on product demos (that playbook's house style); the `glass` card is the one panel, for busy footage |
| Text-to-speech | **K** | ElevenLabs (`make_voiceover.py`; Vietnamese needs `eleven_turbo_v2_5`; a free plan is not commercial) |
| Auto-translate captions, bilingual | — | not built; a Vietnamese line and an English line would double the text |
| Lyrics / karaoke for music | — | out of scope |

## 9. Graphics and stickers

| CapCut | Status | In the kit |
|---|---|---|
| Animated background (moving grid, gradient, cloth) | **K** | the card layout's grid: a net of lines blown by a wind (`components/graphics/Grid.tsx`) |
| Logo reveal, brand intro | **K** | `logo`: blurs in from a motion smear and snaps sharp; `tint=white` on a red backdrop |
| Stickers and emoji (megaphone, bullseye, !!!, magnifier) | **K** | `icon` (`target megaphone bang search check`), `circled`, `tag` |
| Counter, number roll | **K** | `counter`: "5 -> 10" with a drawn arrow |
| RAW vs FINAL, split compare | **K** | `rawfinal`: the same take unedited and edited, side by side |

| CapCut | Status | In the kit |
|---|---|---|
| Stickers, badges | **K** | `sticker` (rotated badge, one per video, no claims) |
| Arrows, circles, underline | **K** | `highlight shape=circle|underline|arrow`; `cart` for the TikTok Shop bar |
| Callout with a leader line | **K** | `callout label, target=x,y` (only on a still moment) |
| Lower third, name tag | **K** | `lowerThird`, `label` |
| Countdown, progress bar | **K** | `progress`; `stat` counts a number up |
| Price tag, sale badge | **K** | `price` (count-up, struck-through old price), `sticker` |
| Charts, bars | **K** | `chart` (2–5 bars growing in turn), `ranking` (Remotion only) |
| Animated emoji, GIF stickers | — | not built; a licensed sticker is a `image` overlay (a file the user owns) |
| Subscribe / follow animations | — | a platform widget, not a graphic of ours |

## 10. Audio

| CapCut | Status | In the kit |
|---|---|---|
| Noise reduction, voice enhance | **S** | `process_audio.py voice`: noise print, presence, de-esser, compression, −16 LUFS |
| Loudness normalise | **S** | `process_audio.py master`: −14 LUFS, true peak ≤ −1 dBTP, AAC |
| Auto ducking (music under voice) | **K** | the music bed (`music.volumeDb`, −10 dB by default) ducks a further −8 dB under speech with a 2-frame attack and 12-frame release, from the word timings (`audio-and-music.md`, levels) |
| Beat detection, beat markers | **K** | `suggest_cuts.py --music --beats-out beats.json` |
| Sound effects (whoosh, pop, riser, ding) | **K** | `--auto-sfx`: CC0 or self-made sounds only (`sound-design.md`), none across a reveal |
| Fade in / out | **D** | no automatic fade: `ffmpeg -af afade=t=out:st=T:d=1` on the master's last second |
| Voice changer, voice cloning | — | a voice must be licensed and the account's plan must allow it (`CLAUDE.md`: ElevenLabs) |
| CapCut's music and sound library | — | **not for a commercial video** unless its licence says so for your account and platform: use TikTok's Commercial Music Library, CC0 or licensed tracks (`audio-and-music.md`) |
| Stem separation, vocal remover | — | not built |

## 11. Templates and AI

| CapCut | Status | In the kit |
|---|---|---|
| Templates (one tap) | **K** | a **playbook** is the template: structure, rhythm, look, graphics, sound; `playbook.py skeleton` writes the plan |
| AutoCut, auto video from clips | **K** | `suggest_cuts.py` + `plan_scenes.py` (cuts on beats or pauses, non-overlapping footage) |
| Script to video, AI avatar, AI footage | — | the footage is the user's (an AI-generated clip is fine if the user made it); the kit does not generate any |
| Lip sync, AI dubbing | — | not built |
| Upscale, AI colour, AI relight | — | `ffmpeg scale=…:flags=lanczos` only; the proxies are 2880 px tall so a 1.5× zoom stays sharp |
| Export presets (1080p, 30 fps, 9:16) | **K** | 1080×1920, 30 fps, H.264, AAC; `process_audio.py master … --phone` for a chat copy |

## 12. Recipes: a CapCut-style review in the plan [C]

None of these is measured to perform better: they are structure and taste. Spend each once or twice.

- **Hook with impact.** Scene 1 `hold` or a fast `push 1>1.2`; a `title` in `stack` at 0.15 s; the first
  cut with `pushCut +flash`. Voice and picture each do a different job (`hook-library.md`).
- **The turn.** The cut into the reveal or the first use: `whip left` or `slide up`, plus `+shake` only if the
  music has a hit there; sound effect `swoosh` before the cut, none across the reveal.
- **The proof.** A `punch` on the number or the product name, a `stat` or `price` counting up, a `highlight`
  circle on the thing, a `callout` only on a still moment.
- **Close.** A `cart` arrow early (about 9–12 s) and at the end, a `glass` or `marker` title with the offer,
  the last scene a `pull` so the frame settles.
- **Finish.** Optional `--look vignette=0.25,grain=0.04` on the whole video (HyperFrames), then
  `process_audio.py master`. If the picture reads dirty or flat on the contact sheet, remove it.
- **What not to copy.** Over-fast cuts under the playbook's minimum, a glitch on every cut, chart-topping
  music with no licence, a before/after with a hidden cut, a claim in a caption that the voice must not make
  (`claims-and-compliance.md`).

## 13. Adding a technique

1. Decide where it lives: a footage or audio step (a script and `scripts/` + `CAU-TRUC.md`), a cell of the
   plan (`plan_to_project.py` parses it, the plan template and `playbooks/README.md` name it), or a
   component or effect in the renderer (`remotion-template/src` and `hyperframes-template/kit.js` together).
2. Put it in the tables above with its status, and make the sync report warn when a renderer ignores it.
3. Render a still of it in each renderer that has it and look at both.
