// The composition: scenes (with centred transitions and a continuous virtual camera), accents on
// cuts, overlays on their own timeline, captions, and the soundtrack. Pure function of a Project.
import React from "react";
import { AbsoluteFill, Freeze, OffthreadVideo, Sequence, Solid, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { lightLeak } from "@remotion/effects";
import type { Face, FaceGlow, Look, Project, Scene } from "../project";
import { captionTopFor, captions, card, frame as size, motion, palette } from "../theme";
import { resolveOverlay } from "../components/registry";
import { Captions } from "../components/text/Captions";
import { GridBackground } from "../components/graphics/Grid";
import { cameraStyle, type ScenePunch } from "./camera";
import { layoutScenes, toFrames, type SceneSlot } from "./timeline";
import { presentationFor } from "./transitions";
import { Soundtrack } from "./audio";
import { SubjectFx } from "./Subject";

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const isCard = (s: Scene) => (s.layout ?? "full") !== "full";

// A card scene plays the whole 9:16 frame (camera moves included) scaled into a rounded card. "expand" starts as that
// card and grows to the full frame over card.expandFrames after the planned cut, wobbling like a sheet of fabric
// (an SVG displacement filter whose strength peaks mid-growth).
export const lookFilter = (look?: Look) => (look ? `saturate(${look.saturate ?? 1}) contrast(${look.contrast ?? 1}) brightness(${look.brightness ?? 1})${look.warm ? ` sepia(${look.warm})` : ""}` : undefined);

// A feathered patch over the head that brightens, desaturates a touch and softens what is behind it.
const FaceLight: React.FC<{ face: Face; glow: FaceGlow }> = ({ face, glow }) => {
  const k = glow.size ?? 1;
  const rx = face.r * 1.45 * k * size.width;
  const ry = face.r * 1.9 * k * size.width;
  return (
    <div
      style={{
        position: "absolute",
        left: face.x * size.width - rx,
        top: face.y * size.height - ry,
        width: 2 * rx,
        height: 2 * ry,
        zIndex: 1,
        background: `rgba(255,240,234,${glow.veil ?? 0.1})`, // a pale pink veil: lifts the shadows of the skin
        backdropFilter: `brightness(${glow.brightness ?? 1.16}) saturate(${glow.saturate ?? 0.92}) contrast(0.94) blur(${glow.blur ?? 0.8}px)${glow.warm ? ` sepia(${glow.warm})` : ""}`,
        WebkitMaskImage: "radial-gradient(ellipse 50% 50% at 50% 50%, #000 55%, transparent 100%)",
        maskImage: "radial-gradient(ellipse 50% 50% at 50% 50%, #000 55%, transparent 100%)",
      }}
    />
  );
};

const SceneMedia: React.FC<{ slot: SceneSlot; punches: ScenePunch[]; look?: Look; glow?: FaceGlow }> = ({ slot, punches, look, glow }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { scene, startFrom, duration } = slot;
  const layout = scene.layout ?? "full";
  // Constant speed plays natively; a ramp re-times the source frame by frame inside a <Freeze>.
  const ramped = Boolean(scene.ramp && scene.ramp.length > 1);
  const video = scene.clip ? (
    <OffthreadVideo
      src={staticFile(`clips/${scene.clip}.mp4`)}
      trimBefore={startFrom}
      playbackRate={ramped ? 1 : scene.speed ?? 1}
      muted
      style={{ width: "100%", height: "100%", objectFit: "cover", filter: lookFilter(look) }}
    />
  ) : null;
  // subject effect (silhouette flash, outline, glow, spotlight...): drawn inside the camera framing, offset counted from the planned cut
  const at = frame - (slot.cut - slot.begin);
  // Echo trail: the same clip again, `k * delay` frames behind the live frame, above it and fainter each time. A Freeze re-times the copy
  // (the slot's own advance() for a ramp, plain frames for a constant speed, which the video's playbackRate then scales).
  const echo = scene.echo && scene.clip ? scene.echo : null;
  const trail =
    echo && video && at >= 0 && (!echo.frames || at < echo.frames)
      ? Array.from({ length: Math.min(3, Math.max(1, Math.round(echo.copies))) }, (_, i) => i + 1).map((k) => {
          const behind = Math.max(0, frame - k * echo.delay);
          const fade = echo.frames ? Math.min(1, Math.max(0, (echo.frames - at) / 6)) : 1;
          return (
            <AbsoluteFill key={`echo${k}`} style={{ opacity: (echo.decay ?? 0.5) ** k * fade }}>
              <Freeze frame={ramped ? slot.advance(behind) : behind}>{video}</Freeze>
            </AbsoluteFill>
          );
        })
      : null;
  const inner = (
    <AbsoluteFill style={cameraStyle(frame, duration, fps, scene.camera, punches, slot.cut - slot.begin)}>
      {scene.subject ? <SubjectFx fx={scene.subject} at={at} id={`subject${slot.index}`} video={video} /> : null}
      {glow && scene.face ? <FaceLight face={scene.face} glow={glow} /> : null}
      {video ? (
        ramped ? <Freeze frame={slot.advance(frame)}>{video}</Freeze> : video
      ) : (
        // No footage yet (layout preview): a neutral gradient instead of a broken video.
        <AbsoluteFill style={{ background: `linear-gradient(160deg, #3A4A6B 0%, #1B2338 60%, #0E1322 100%)` }} />
      )}
      {trail}
    </AbsoluteFill>
  );
  // Jolt: on the planned cut the whole picture is smeared sideways and shaken, both decaying to nothing (the hit of a landing, scene.jolt).
  const j = scene.jolt;
  const decay = j && at >= 0 && at < j.frames ? (1 - at / j.frames) ** 2 : 0;
  const sigma = decay * (j?.blur ?? 36);
  const amp = decay * (j?.shake ?? 26);
  const jolted =
    decay > 0 ? (
      <AbsoluteFill
        style={{
          translate: `${(amp * Math.sin(at * 2.9 + 1.3)).toFixed(2)}px ${(amp * 0.8 * Math.cos(at * 3.7 + 0.4)).toFixed(2)}px`,
          scale: String(1 + (2 * amp) / size.width),
          filter: sigma > 0.5 ? `url(#jolt${slot.index})` : undefined,
        }}
      >
        <svg width={0} height={0} style={{ position: "absolute" }}>
          <defs>
            <filter id={`jolt${slot.index}`} x="-10%" y="-5%" width="120%" height="110%">
              <feGaussianBlur stdDeviation={`${sigma.toFixed(2)} 0`} />
            </filter>
          </defs>
        </svg>
        {inner}
      </AbsoluteFill>
    ) : (
      inner
    );
  if (layout === "full") return <AbsoluteFill style={{ background: palette.ink, overflow: "hidden" }}>{jolted}</AbsoluteFill>;
  if (!scene.clip) return <AbsoluteFill />; // grid only: overlays draw their own cards

  const p = layout === "expand" ? motion.easeInOut(Math.min(1, Math.max(0, at / card.expandFrames))) : 0;
  const w = lerp(card.width, size.width, p);
  const h = lerp(card.height, size.height, p);
  const warp = layout === "expand" ? Math.sin(Math.PI * p) * 130 : 0;
  return (
    <AbsoluteFill>
      {warp > 0.5 ? (
        <svg width={0} height={0} style={{ position: "absolute" }}>
          <defs>
            <filter id={`warp${slot.index}`} x="-15%" y="-15%" width="130%" height="130%">
              <feTurbulence type="fractalNoise" baseFrequency={`${0.0014 + at * 0.00004} 0.0042`} numOctaves={1} seed={slot.index + 3} result="n" />
              <feDisplacementMap in="SourceGraphic" in2="n" scale={warp} xChannelSelector="R" yChannelSelector="G" />
            </filter>
          </defs>
        </svg>
      ) : null}
      <div
        style={{
          position: "absolute",
          left: (size.width - w) / 2,
          top: lerp(card.top, 0, p),
          width: w,
          height: h,
          borderRadius: lerp(card.radius, 0, p),
          overflow: "hidden",
          boxShadow: p < 1 ? card.shadow : undefined,
          filter: warp > 0.5 ? `url(#warp${slot.index})` : undefined,
        }}
      >
        <div style={{ position: "absolute", left: 0, top: 0, width: size.width, height: size.height, transformOrigin: "0 0", scale: String(w / size.width) }}>{inner}</div>
      </div>
    </AbsoluteFill>
  );
};

// vignette and grain over the picture (project `look`): the edge darkens, fine noise changes every frame of six.
const LookLayer: React.FC<{ look: Look }> = ({ look }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {look.vignette ? <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 45%, transparent 52%, rgba(0,0,0,${0.6 * look.vignette}) 100%)` }} /> : null}
      {look.grain ? (
        <svg width="100%" height="100%" style={{ position: "absolute", left: 0, top: 0, mixBlendMode: "overlay", opacity: look.grain }}>
          <filter id="grain" x="0" y="0" width="100%" height="100%">
            <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={1 + (frame % 6)} stitchTiles="stitch" />
            <feColorMatrix type="saturate" values="0" />
          </filter>
          <rect width="100%" height="100%" filter="url(#grain)" />
        </svg>
      ) : null}
    </AbsoluteFill>
  );
};

// A procedural light leak (Remotion's `lightLeak` effect on a black solid, WebGL): it grows in the first half of the accent and retracts in the second.
const Leak: React.FC<{ seed: number; length: number }> = ({ seed, length }) => {
  const frame = useCurrentFrame();
  return <Solid width={size.width} height={size.height} color="#000000" effects={[lightLeak({ seed, hueShift: 30, progress: frame / Math.max(1, length - 1) })]} style={{ opacity: 0.6, mixBlendMode: "screen" }} />;
};

const Flash: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 3, 10], [0, 0.55, 0], { extrapolateRight: "clamp", easing: motion.easeInOut });
  return <AbsoluteFill style={{ background: palette.white, opacity }} />;
};

export const Short: React.FC<Project> = (project) => {
  const { fps, width, height } = useVideoConfig();
  const frame = useCurrentFrame();
  const slots = layoutScenes(project.scenes, fps);
  // The cart arrow owns the bottom-left corner: lift the captions while it is on screen.
  const lift = (project.overlays ?? [])
    .filter((o) => o.component === "cart")
    .reduce((m, o) => {
      const a = toFrames(o.start, fps);
      const b = toFrames(o.end, fps);
      return Math.max(m, interpolate(frame, [a - 4, a + 4, b - 4, b + 4], [0, captions.lift, captions.lift, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
    }, 0);
  const punchFrames = (project.punches ?? []).map((p) => ({ frame: toFrames(p.at, fps), scale: p.scale ?? 1.12 }));

  const series: React.ReactNode[] = [];
  slots.forEach((slot) => {
    if (slot.index > 0 && slot.transitionIn > 0) {
      series.push(
        <TransitionSeries.Transition
          key={`t${slot.index}`}
          presentation={presentationFor(slot.scene.transition ?? { type: "fade" }, width, height)}
          timing={linearTiming({ durationInFrames: slot.transitionIn, easing: motion.easeInOut })}
        />,
      );
    }
    const next = slots[slot.index + 1];
    const mine = punchFrames
      .filter((p) => p.frame >= slot.cut && (!next || p.frame < next.cut))
      .map((p) => ({ frame: p.frame - slot.begin, scale: p.scale }));
    series.push(
      <TransitionSeries.Sequence key={`s${slot.index}`} durationInFrames={slot.duration}>
        <SceneMedia slot={slot} punches={mine} look={project.look} glow={project.faceGlow} />
      </TransitionSeries.Sequence>,
    );
  });

  // The grid sits under the whole series and shows wherever a card scene is transparent: one run per stretch of
  // consecutive card scenes, covering their transition handles.
  const runs: { from: number; to: number }[] = [];
  slots.forEach((s) => {
    if (!isCard(s.scene)) return;
    const last = runs[runs.length - 1];
    const to = s.begin + s.duration;
    if (last && slots[s.index - 1] && isCard(slots[s.index - 1].scene)) last.to = Math.max(last.to, to);
    else runs.push({ from: s.begin, to });
  });

  return (
    <AbsoluteFill style={{ background: palette.ink }}>
      {runs.map((r, i) => (
        <Sequence key={`g${i}`} from={r.from} durationInFrames={r.to - r.from}>
          <GridBackground offset={r.from} />
        </Sequence>
      ))}
      <TransitionSeries>{series}</TransitionSeries>
      {project.look?.vignette || project.look?.grain ? <LookLayer look={project.look} /> : null}

      {slots.map((slot) =>
        slot.index > 0 && slot.scene.accent ? (
          <Sequence key={`a${slot.index}`} from={slot.cut - 10} durationInFrames={20} layout="none">
            {slot.scene.accent === "lightLeak" ? (
              <Leak seed={slot.index} length={20} />
            ) : (
              <Sequence from={7} layout="none">
                <Flash />
              </Sequence>
            )}
          </Sequence>
        ) : null,
      )}

      {(project.overlays ?? []).map((ov, i) => {
        const from = toFrames(ov.start, fps);
        const dur = Math.max(1, toFrames(ov.end, fps) - from);
        const Component = resolveOverlay(ov.component);
        return (
          <Sequence key={`o${i}`} from={from} durationInFrames={dur}>
            <Component ov={ov} dur={dur} instant={from === 0} />
          </Sequence>
        );
      })}

      {project.captionStyle !== "none" && project.captions?.length ? (
        <Captions captions={project.captions} words={project.words ?? []} mode={project.captionStyle ?? "karaoke"} top={captionTopFor[project.layout ?? "feed"]} lift={lift} bands={project.captionBands} highlight={project.captionHighlight} keywords={project.captionKeywords} />
      ) : null}

      <Soundtrack voice={project.voice} music={project.music} sfx={project.sfx} words={project.words} fps={fps} />
    </AbsoluteFill>
  );
};
