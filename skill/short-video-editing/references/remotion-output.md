# Remotion Output

The kit renders with a data-driven Remotion project: `assets/remotion-template`. The edit plan is
compiled to `project.json`; one composition (`Short`) renders any video from it. Nobody edits React
code to make a video — changing a video means changing the plan.

---

## Licence — read before building

Remotion is **source-available, not open source**. Its `LICENSE.md` grants the free licence to
*"an individual"* or *"a for-profit organization with up to 3 employees"*. Above that a Company
License is **$25/month per seat**, a seat being *"per person who writes Remotion code themselves or
using agentic coding tools"* — an AI agent writing Remotion code still consumes a seat. Confirm the
headcount before building; if it is over three and nobody has a seat, say so. Sources:
`remotion.dev/license`, `remotion.dev/docs/license/faq`.

---

## Pipeline

```bash
# 1. Scaffold once per batch (ask before --install: it downloads npm packages + Chromium)
python scripts/new_remotion_project.py ~/renders/saiza --install --proxies "/path/to/raw clips"
cp voice.mp3 ~/renders/saiza/public/audio/kb7.mp3

# 2. Captions + word timings (step 5 of SKILL.md)
python scripts/align_captions.py voice.mp3 --script script.txt --out captions.srt --words-out words.json

# 3. Compile the plan
python scripts/plan_to_project.py edit-plan.md --out ~/renders/saiza/kb7.json \
    --voice audio/kb7.mp3 --captions captions.srt --words words.json --auto-camera \
    --punch-keywords "saiza,chai xanh"

# 4. Look before rendering, then render
cd ~/renders/saiza
npx remotion still src/index.ts Short out/check.png --frame=45 --props=kb7.json
npx remotion render src/index.ts Short out/kb7.mp4 --props=kb7.json --codec=h264 --crf=18

# 5. Look at the result (scene middles + every cut), then check durations with ffprobe
python <skill>/scripts/contact_sheet.py out/kb7.mp4 --project kb7.json --out out/sheet.png
```

`plan_to_project.py` lists any clip, voice or music file the project needs that is not yet under
`public/` when `--out` sits inside the render project, so a missing asset shows up before the render.

`npm run studio` opens Remotion Studio with `project.example.json`, a footage-free gallery of every
component — the quickest way to see what each style looks like.

---

## Template layout

| Path | Role |
|---|---|
| `src/project.ts` | The input contract (`Project`, `Scene`, `Overlay`, …). |
| `src/theme.ts` | Design tokens: fonts, palette, layout zones, safe area, cart point, motion curves, camera limits. Change the look here. |
| `src/engine/timeline.ts` | Scene layout with transitions centred on cuts; reading-time and dB helpers. |
| `src/engine/camera.ts` | Push / pull / pan / hold + keyword punches, perceptual scale. |
| `src/engine/transitions.tsx` | Transition registry (built-ins + `zoomThrough`, `blurDissolve`, `whip`). |
| `src/engine/audio.tsx` | Voice, ducked music, SFX — outside the transitions so they never shift. |
| `src/engine/Short.tsx` | The composition. |
| `src/components/text/` | `Title` (5 styles), `Captions` (karaoke/plain), text primitives. |
| `src/components/graphics/` | Callout, CheckList, Step, Price, CartPointer, Highlight, Sticker, Magnifier, Thumbs, Ranking, Progress, LowerThird. |
| `src/components/registry.tsx` | Component names used in `project.json`; unknown names throw. |

To add a component: write it under `components/graphics/` taking `{ov, dur, instant}`, read its
content from `ov.props`, take every colour/size/curve from `theme.ts`, register it, and document
its content keys in `layout-and-motion-graphics.md`. No video text in code.

---

## Rules that keep renders correct

These follow Remotion's own agent rules (`remotion-dev/skills`, `remotion-best-practices`) [D]:

- Everything animates from `useCurrentFrame()`. No CSS transitions/animations, no `Date.now()`,
  no unseeded randomness.
- Footage with `<OffthreadVideo>`; transform a **wrapper**, never the video element.
- Scale animations use `interpolate(..., {output: "perceptual-scale"})`.
- Fonts through `@remotion/google-fonts` with explicit weights and subsets (`latin` +
  `vietnamese`), so no frame renders in a fallback face.
- Assets in `public/`, referenced with `staticFile()`; no network fetches at render time.
- Shader transitions and light leaks need `Config.setChromiumOpenGlRenderer("angle")` (set in
  `remotion.config.ts`).
- Render a still at every transition before a full render; a full 35 s render takes ~2 minutes on
  the reference Windows machine, a still a few seconds.

---

## Where the boundary with ffmpeg sits

| Job | Tool |
|---|---|
| Proxies, conform fps/resolution, rotation | **ffmpeg** (`new_remotion_project.py --proxies`) |
| Trimming the voiceover at pauses | **ffmpeg** via `scripts/trim_voice.py` (`atrim` + `concat`, cut points from `silencedetect`) |
| Looking at footage or at the render | **ffmpeg** via `scripts/contact_sheet.py` |
| Scene cuts, transitions, camera, graphics, captions, mix | **Remotion** |
| Loudness check, scene-cut detection on the output | **ffmpeg** (`ebur128`, `select='gt(scene,0.3)'`) |
| Handing to a human editor | `edit-plan.md` + `captions.srt` → CapCut / Premiere / DaVinci |
