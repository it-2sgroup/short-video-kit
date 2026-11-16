# Transition pack: the techniques of a "technique breakdown" showreel, measured frame by frame

Two public short videos of the same kind (a creator shows ONE edit technique after another: the finished clip in a window, the technique's name under it,
the editor's timeline below) were taken apart frame by frame with `analyze_reference.py`, the half-second and per-frame sheets of the preview window,
and the timeline panel. Together they show 17 techniques in 56 s. This file records what each one IS, in frames, how to build it in the kit, what
footage it needs and what it sounds like. Nothing of the videos (footage, music, text) is reused; the kit builds the techniques itself.

Status per technique: **built** (a card in `assets/techniques.json`, drawn by `engine/transitions.tsx`), **tool** (a script finds or prepares what it needs),
**recipe** (done with parts the kit has; the steps are here) or **backlog** (`technique-backlog.md`). All timings are at 30 fps.
The reference was graded and compressed (576 x 1024); every number here is a measurement of that video, a starting point, not a law.

## 1. The format

Two layouts were seen; both are the same idea.

| | Layout A | Layout B |
|---|---|---|
| Frame | 576 x 1024, 32.7 s, 9 techniques | 576 x 1024, 23.4 s, 8 techniques |
| Background | animated deep-blue light swirls, a two-word title at the top (y 13-21 %) | pale grey graph paper |
| Preview window | x 8-92 %, y 24-50 %, rounded corners (484 x 272 px) | x 7-93 %, y 12-39 % (495 x 278 px) |
| Name of the technique | y 52-57 %, a small "Effect:" word then the name in a heavy condensed face | y 40-44 %, a rounded display face that pulses between a bold and a pale state (seen on alternate half-second samples) |
| Timeline panel | y 59-80 % (484 x 210 px), the WHOLE edit as one screenshot | y 45-92 % (495 x 480 px), a zoomed screenshot of the project |
| Playhead | a white vertical line sweeping the panel at a constant 15.4 px/s (x = 22 + 15.4 t) | the same at 22.2 px/s (x = 60 + 22.2 t) |

- The playhead moves linearly: the panel is a still picture and the line is drawn over it, so the viewer sees where in the edit the demonstrated moment lives.
- The window shows the finished result of ONE technique at a time, 1.2 to 9 s each (layout A: 2.2, 1.5, 1.2, 4.2, 1.3, 1.7, 9.0, 1.4, 6.2 s; layout B: 2.6, 2.6, 2.8, 1.2, 2.8, 2.4, 1.7, 3.2 s). The name changes on the first frame of the technique's first shot.
- Both end on a 4 s platform end card (not content). The music has a clear beat (150 bpm was measured, with cut hits near the beat); the timeline shows beat markers and a sound track of short effects under each transition.
- The timelines show how the demos were built: stacked adjustment layers for the look (a cinematic glow and a night grade over the whole edit), purple effect bars
  (a radial blur) on the first frames after cuts, a staircase of 10 short clips for the match cut, compound clips, a freeze clip, and under them the effect sounds
  (camera flash charging, camera flash, a digital blur, a cinematic hit, "flash screen").
- To make such a video in the kit: the clip window is the `card` layout (`references/layout-and-motion-graphics.md`), the name is a `title` (style `outline` or `stack`),
  the timeline panel is an `image` card, the technique clips are scenes with the transitions below, and the beat comes from `make_music.py` or a licensed track.
  The `tutorial` playbook's rules for "one step per beat" apply; each technique's clip is a real example of it, never a mock-up.

## 2. The techniques

### Grid transition / grid mask: `gridFlash` (built)
**Seen** in layout A at 3.63-4.87 s and twice in layout B (2.57-5.17 s, 7.97-9.17 s). A 3 x 3 grid lies over the old shot. In a random order each cell goes flat cream for about
one frame and is then the new shot. The reveal takes 10-17 frames; thin dark lines (about 3 px at 576 wide) stay between the cells during it; layout A ends with two cream full frames
(a vignette darkens the corners) and then the clean shot. Layout B's first grid uses 9 DIFFERENT shots, one per cell, held for 1.5 s as a mosaic (not built: a mosaic of nine clips needs nine
streams in one scene); its second one reveals one shot and the lines stay for about a second.
**Kit:** `Transition: gridFlash` (18 frames by default; 3 x 3; the order is fixed by a seed so a still equals the render). The cell colour is a warm cream `#FFFBEF`: the measured flashes are never pure white.
**Footage:** none. Works best between two shots with different content at the same screen weight.
**Sound:** a click or shutter per cell; the reference has soft ticks (not listened to).

### Frame click and crop with negative: `cropPop`, `cropNegative` (built)
**Seen** as "frame click" (layout A, 4.87-9.07 s, four cuts about 1 s apart) and "crop + negative" (21.03-22.40 s). The new shot is a small window (frame click: about 46 % of the frame wide, low in the
middle; crop + negative: about 22 % wide, lower right of centre) that opens over the old shot and grows to the full frame in 6-8 frames with an ease-out. In the negative version the window is an
inverted black-and-white picture for its first 4-5 frames and turns to colour at the end. A slow push (1.0 to 1.1) follows on the new shot. One more variant: at 4.92-4.98 s the new shot arrives as one, then
two, vertical strips before filling the frame (a 3-frame "split"); not built.
**Kit:** `Transition: cropPop` and `Transition: cropNegative` (8 frames each). Cut on the beat: the reference's four frame-click cuts are 0.8-1.1 s apart.
**Footage:** none. Look at the new shot's first frame: the window shows the WHOLE frame scaled down, so the subject should be readable at 30 % size.

### Teleport: `flashWipe` (built) + a locked-off pair of takes
**Seen** at 9.07-10.40 s. A person stands at the bottom of a staircase; a cream band sweeps from the right to the left over 5 frames (9.10 to 9.27 s, soft edges, wider than the frame); behind it
the same place has the person at the top of the stairs. The cut is hidden under the band.
**Kit:** `Transition: flashWipe left` (12 frames; `left` = the band travels right to left). The progress of a transition is eased (fast in the middle), so besides the band (140 % of the frame, soft edges) a cream wash peaks at the swap and the cut is always covered. The reference's band took 5 frames; the eased 12 frames give about 4 fast ones.
**Footage:** two takes from the SAME locked tripod position, the subject in a different place in each (near, then far). Shoot a clean plate first; a handheld take cannot teleport.
**Sound:** a short whoosh under the band plus a click on the swap.

### Black flash and mix: `blackFlicker` (built)
**Seen** at 11.93-14.37 s. Over 16 frames (11.93 to 12.47 s) the picture alternates between black and the shot about five times (black on 5 of the first 9 frames, a dimmed "mix" frame between), and the
new shot arrives on frame 17. The analyzer lists these as five flashes at 11.97, 12.07, 12.17, 12.27 and 12.40 s. After the arrival small cream blobs glint on the highlights (12.57, 12.70, 13.10, 13.63-13.77, 14.03-14.30 s): flash overlays on the beat, with a camera-flash sound.
**Kit:** `Transition: blackFlicker` (14 frames; the pattern is a fixed function of the frame, black on frames 2, 3, 6, 9 and 10 with the neighbours dimmed, so it renders the same twice; the easing of the transition is undone to find the frame, so keep `frames` at 14). Add the glints with `flare` or `+flash` accents on the beat (`references/layout-and-motion-graphics.md`).
**Sound:** the camera-flash charge rising before it, a flash at the arrival.

### Zoom fade in: `zoomFade` (built)
**Seen** at 16.10-19.33 s. The old shot darkens and grows a little (16.5-16.7 s); the new shot fades up from black at 16.8 s, starting at about 90 % size with a dark border, grows to fill the frame in
about 0.5 s and keeps pushing slowly to 19.0 s, then fades out. **Kit:** `Transition: zoomFade` (16 frames) followed by a `push 1.0>1.12` camera.

### Pull in: `zoomThrough` (the kit already has it)
**Seen** at 14.37-16.10 s ("pull in II"). The old shot punches in with a radial blur on its last frames (14.57 s) and the new shot starts zoomed in and settles over 10 frames. `zoomThrough` (scale through the
cut with a blur peak) or `zoomBlur`; match the push of the old shot to the settle of the new one.

### Motion blur on every cut: `+jolt`, `linearBlur`, `blurSlide` (the kit already has them)
**Seen** at 22.40-28.63 s: six hard cuts, each new shot arriving with 3-4 frames of directional blur that decays to sharp; handheld footage with a push. Layer A's shots also start with a radial blur resolving in 3 frames.
The kit's `+jolt` hit (`Transition: cut +jolt`) is exactly this on a hard cut: a sideways blur and a shake decaying with the square of the time left.
The same sequence ends with a cream flash (1 frame, 27.73 s) and a pixel-block tear that dissolves to black over 12 frames (27.87-28.5 s): `glitchSlice` or `glPixelate` into black.

### Flicker: the subject silhouette (the `fill` subject effect; the object matte is backlog)
**Seen** at 0-2.17 s. The shot opens on a radial blur that settles in 3 frames; then the silhouette of the subject (a sign; later two walkers) goes flat cream on single frames (frame 10) and on every
fourth frame (24, 28, 32) before the cut at 1.13 s, and once more at frame 48 in the next shot. A strobe of a few cream silhouettes on the beat.
**Kit:** the `fill` subject effect with `frames: [10, 24, 28, 32]` and a colour of `#FFFBEF` (`references/subject-effects.md`), with a matte from `person_matte.py` when the subject is a person. For an object there is no
full-frame matte tool yet (`object_cutout.py` writes a cropped cut-out for `objectDrop`, not a full-frame matte): backlog.

### Match cut montage: `match_cut.py` + very short scenes (a recipe)
**Seen** at 0-2.57 s of layout B. About 26 shots of one kind of object (a street-name sign, always the same shape) in 2.6 s: each shot lasts 2-3 frames (66-100 ms, about 10 cuts a second), the sign
is kept at the same size and place on the screen (about 40 % of the frame wide, centred, a small zoom and tilt per shot to line it up), only the background changes. The last one holds for 6 frames and zooms
into the next technique. The timeline is a staircase of 10 clips; the sound is a shutter tick at every cut (about 10 vertical lines a second in the spectrum).
**Kit:** `match_cut.py --a CLIP_A@T --b CLIP_B@T` gives the Camera cell that puts B's subject where A's ended; write each shot as a scene of 2-3 frames (`--cuts` of `suggest_cuts.py` at a 0.1 s grid, or by hand), `Transition: cut`. The shortest scene the pacing checker accepts
depends on the playbook (`montage-recap` allows 0.5 s): a montage this fast needs `**Playbook:**` rules set for it, otherwise the checker will stop it.
**Footage:** many shots of the same object from the same distance, shot in one session; a sign is the easy case.

### Mask transition and shape transition: `find_occluders.py` (tool) + a hard cut
**Seen** at 9.17-11.93 s (layout B) and 10.40-12.07 s (layout A). Something passes the lens: a person's sleeve and shoulder from the right (9.30 to 10.0 s; the frame is covered at about 9.9 s) in B,
a curved silver handrail from the lower right (10.40 to 10.58 s) in A. The old shot ends under the object and the new shot is already there when it leaves; the camera move carries over the cut (the tilt keeps going).
**Kit:** `find_occluders.py CLIPS` lists the moments where a flat, defocused mass covers the frame after a textured one (it found the sleeve at 9.90 s in the reference preview). Cut the old shot at the peak; start the new shot where ITS own foreground is leaving, or on a fast
move in the same direction (`cutCurve` carries the move). `Transition: cut +jolt` for the arrival. **Footage:** shoot it on purpose: walk a hand, a sleeve, a bag or a pillar across the lens at the end of a take, and begin the next take with the same object leaving.

### Reverse: `reverse_clip.py` (tool)
**Seen** at 12.07-21.03 s: six shots from a train driver's cab, played backwards (the label says reverse; a still cannot prove the direction, the motion of the track does). Hard cuts about 1.5 s apart.
**Kit:** `reverse_clip.py CLIP --from 3.2 --to 7.0 --out public/clips/CLIP_REV.mp4`, then use the file as the scene's Source with In = 0. Reversed footage works where the motion has a direction (a train, a pour, a door, a walker).

### Phone green screen (a recipe)
**Seen** at 5.17-7.97 s of layout B. The previous clip (the 9-shot mosaic) is the screen of a phone held in a hand in front of the next place: black bezel edges enter around the mosaic, the phone is
in the hand at the right of the frame for about 1 s, then it moves down and shrinks away. The host shot is a hand holding a phone with a flat green screen; the green is keyed out and the previous clip shows through.
**Recipe:** shoot the hand and a phone showing pure green (`#00FF00`, no reflections, the room evenly lit), then composite the key over the previous clip with ffmpeg:
`ffmpeg -i host.mp4 -i previous.mp4 -filter_complex "[0:v]chromakey=0x00ff00:0.18:0.08[k];[1:v]scale=1080:1920,setsar=1[b];[b][k]overlay=shortest=1" -c:v libx264 -crf 16 out.mp4`.
The previous clip stays fixed behind the phone instead of staying locked to its screen: the screen shows a window of it, which looks right when the phone is large in the frame and wrong when the phone moves a lot (tracking is not built). Use `out.mp4` as a normal scene.

### Dolly zoom (backlog)
**Seen** at 2.17-3.63 s: a clock in a thick red rounded frame; over 44 frames the frame closes in (the border grows from about 6 % to 14 % of the width) while the picture inside is scaled up so that the clock keeps its size and the ceiling lines
around it converge. On a real shot it is a dolly move against a zoom; here it is a still-camera copy: the subject at constant size (a cut-out), the background scaled 1.0 to 1.4. A cream flash (1 frame, vignette) opened the technique.
It needs a full-frame matte of the subject: `technique-backlog.md`.

## 3. Sound (from the timelines and the spectrum; nothing was listened to)

- The soundtrack is one beat-driven track with markers on the beat. Cuts and techniques land on or just before the markers; the frame-click cuts are about 1 s apart (2 to 3 beats at 150 bpm).
- Effect sounds are short clips under each transition: a camera-flash charge, a flash, a shutter tick (the match cut: one per cut), a digital blur, a cinematic hit on the biggest change, a low rise before a reveal.
- Kit equivalents: `--auto-sfx` rotates the CC0 bank and the 17 `make_sfx.py` sounds; put a click on every flash and a whoosh under every wipe (`references/sound-design.md`). The measured reference dips the music for about a second under the mosaic (a dark band in the spectrum at 3.4-4.4 s): `--music-levels` and the ducking do that.

## 4. How to plan a showreel or a montage with these

1. One technique per beat (1.2-4 s), the name on screen at the start of its first shot; keep a technique long enough to be understood once (frame click: 4 cuts; grid: 0.6 s reveal and 1 s of hold).
2. Order for energy: a fast match-cut montage first, mosaic and reveals in the middle, a hit and a fade last.
3. Check every transition on stills with `stills.mjs` at 8 positions across the transition and `montage.py` (`references/transitions.md`); look for: a black frame where there should be none, a window that starts outside the frame, a cream flash that is white.
4. Say what was not verified: the sounds were chosen by name, the music was not listened to, `gridFlash`, `cropPop`, `cropNegative`, `flashWipe`, `blackFlicker` and `zoomFade` were rendered as stills on two test clips and nobody has judged them on real footage.
