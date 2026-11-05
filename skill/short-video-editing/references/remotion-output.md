# Remotion Output

Remotion renders React components to MP4. In this pipeline it is the **graphics layer** —
captions, titles, counters, overlays, transitions — composited over footage that ffmpeg has
already cut. It is not a replacement for ffmpeg: cutting and concatenating raw clips in Remotion
is slow and awkward, and ffmpeg does it in one pass.

---

## Licence — read before building

Remotion is **source-available, not open source**. From its `LICENSE.md`:

> Free License applies to: *"an individual"* or *"a for-profit organization with **up to 3
> employees**"*

Above three employees a **Company License** is required: **$25/month per seat**, where a seat is
*"per person who writes Remotion code themselves or using agentic coding tools."*

That last clause matters and is easy to miss: **having an AI agent write the Remotion code still
consumes a seat.** It is not a way around the licence.

Confirm the organisation's headcount before starting. If it is over three and nobody has bought a
seat, say so rather than shipping a licence liability. Sources: `remotion.dev/license`,
`remotion.dev/docs/license/faq`.

---

## Setup

```bash
npx create-video@latest --blank my-video
cd my-video && npm install
npm run dev      # Remotion Studio, live preview
```

Requires Node 18+ and ffmpeg. Remotion downloads its own Chromium headless shell on first render.

---

## Composition shape for a 30-40s vertical short

```tsx
// src/Root.tsx
import { Composition } from "remotion";
import { Short } from "./Short";

export const RemotionRoot = () => (
  <Composition
    id="Short"
    component={Short}
    durationInFrames={35 * 30}   // runtime x fps — derive, never hardcode a guess
    fps={30}
    width={1080}
    height={1920}
  />
);
```

**Everything is driven by the frame number.** There is no wall clock, no CSS transition, no
`setTimeout`. A component asks `useCurrentFrame()` and returns what the picture looks like at that
frame. This is what makes renders deterministic and seekable, and it is the one mental shift that
catches people coming from CSS animation.

```tsx
import { useCurrentFrame, useVideoConfig, interpolate, Sequence, OffthreadVideo, staticFile } from "remotion";

export const Short = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const opacity = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  return (
    <>
      <Sequence from={0} durationInFrames={Math.round(2.2 * fps)}>
        <OffthreadVideo src={staticFile("seg_01.mp4")} />
      </Sequence>
      <div style={{ opacity, position: "absolute", bottom: 560 }}>Cùng 1 cái áo</div>
    </>
  );
};
```

Use `<OffthreadVideo>` rather than `<Video>` for footage during a render — it decodes frames with
ffmpeg instead of relying on the browser's video element, which is both faster and avoids frames
being skipped on seek.

---

## Mapping the edit plan onto Remotion

The edit plan's scene table converts directly. A scene at `Start 10.0 / End 12.2` becomes:

```tsx
<Sequence from={Math.round(10.0 * fps)} durationInFrames={Math.round(2.2 * fps)}>
```

Generate this from the plan rather than typing it. A small script that reads the markdown table
and emits the `<Sequence>` list removes a whole class of off-by-one-frame errors, and keeps the
plan as the single source of truth when timings change.

Keep `fps` from `useVideoConfig()` instead of writing `30` inline — an fps change then does not
silently desynchronise every scene.

---

## Captions

Feed the SRT produced by `scripts/align_captions.py`. Parse it once, then render each group as its
own `<Sequence>`:

```tsx
{cues.map((c, i) => (
  <Sequence key={i} from={Math.round(c.start * fps)}
            durationInFrames={Math.round((c.end - c.start) * fps)}>
    <CaptionPill text={c.text} />
  </Sequence>
))}
```

Safe zone on a 1080x1920 frame: keep captions inside **y 250-1410, x 60-940**. See
`captions-and-text.md` for why, and `platform-specs.md` §6 for what occupies the rest.

---

## Rendering

```bash
npx remotion render Short out/video.mp4 --codec=h264 --crf=18
npx remotion still Short out/frame.png --frame=45      # check a moment before committing
```

Useful flags: `--concurrency` to trade RAM for speed, `--scale` for a fast low-res proof,
`--frames=0-120` to render a range while iterating. Render a still first — a 35-second render
to discover a caption is off-screen is an expensive way to find out.

---

## Determinism

The renderer screenshots each frame in headless Chromium. Anything that varies between frames
for reasons other than the frame number breaks reproducibility:

- No `Date.now()`, no `new Date()`, no unseeded `Math.random()` — Remotion patches `Math.random`
  to be deterministic per composition, but seed anything else yourself.
- No network fetches at render time. Put assets in `public/` and reference them with
  `staticFile()`.
- Load fonts via `@remotion/google-fonts` or `delayRender()`/`continueRender()`, so the frame is
  not captured before the font has arrived. A caption that renders in a fallback face for the
  first few frames is the usual symptom.

---

## Where the boundary with ffmpeg sits

| Job | Tool |
|---|---|
| Cut clips to in/out points, concat, conform fps/resolution | **ffmpeg** (`footage-ingest.md` §4) |
| Speed ramps, time compression on long waits | **ffmpeg** |
| Audio mix: voiceover + music bed + ducking | **ffmpeg** |
| Captions, titles, counters, overlays, animated graphics | **Remotion** |
| Final mux of graphics over cut footage | **Remotion** (`<OffthreadVideo>`) or ffmpeg overlay |

The practical order: ffmpeg produces clean segments → Remotion composites graphics and renders →
ffmpeg muxes the finished audio if it was not embedded. Doing the cutting inside Remotion works
but costs render time for something ffmpeg does near-instantly.
