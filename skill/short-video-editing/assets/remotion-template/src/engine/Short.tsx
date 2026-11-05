// The composition: scenes (with centred transitions and a continuous virtual camera), accents on
// cuts, overlays on their own timeline, captions, and the soundtrack. Pure function of a Project.
import React from "react";
import { AbsoluteFill, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { LightLeak } from "@remotion/light-leaks";
import type { Project, Scene } from "../project";
import { motion, palette } from "../theme";
import { resolveOverlay } from "../components/registry";
import { Captions } from "../components/text/Captions";
import { cameraStyle, type ScenePunch } from "./camera";
import { layoutScenes, toFrames } from "./timeline";
import { presentationFor } from "./transitions";
import { Soundtrack } from "./audio";

const SceneMedia: React.FC<{ scene: Scene; startFrom: number; duration: number; punches: ScenePunch[] }> = ({
  scene,
  startFrom,
  duration,
  punches,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ background: palette.ink, overflow: "hidden" }}>
      <AbsoluteFill style={cameraStyle(frame, duration, fps, scene.camera, punches)}>
        {scene.clip ? (
          <OffthreadVideo src={staticFile(`clips/${scene.clip}.mp4`)} startFrom={startFrom} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        ) : (
          // No footage yet (layout preview): a neutral gradient instead of a broken video.
          <AbsoluteFill style={{ background: `linear-gradient(160deg, #3A4A6B 0%, #1B2338 60%, #0E1322 100%)` }} />
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Flash: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 3, 10], [0, 0.55, 0], { extrapolateRight: "clamp", easing: motion.easeInOut });
  return <AbsoluteFill style={{ background: palette.white, opacity }} />;
};

export const Short: React.FC<Project> = (project) => {
  const { fps, width, height } = useVideoConfig();
  const slots = layoutScenes(project.scenes, fps);
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
        <SceneMedia scene={slot.scene} startFrom={slot.startFrom} duration={slot.duration} punches={mine} />
      </TransitionSeries.Sequence>,
    );
  });

  return (
    <AbsoluteFill style={{ background: palette.ink }}>
      <TransitionSeries>{series}</TransitionSeries>

      {slots.map((slot) =>
        slot.index > 0 && slot.scene.accent ? (
          <Sequence key={`a${slot.index}`} from={slot.cut - 10} durationInFrames={20} layout="none">
            {slot.scene.accent === "lightLeak" ? (
              <AbsoluteFill style={{ opacity: 0.6, mixBlendMode: "screen" }}>
                <LightLeak seed={slot.index} hueShift={30} />
              </AbsoluteFill>
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
        <Captions captions={project.captions} words={project.words ?? []} mode={project.captionStyle === "plain" ? "plain" : "karaoke"} />
      ) : null}

      <Soundtrack voice={project.voice} music={project.music} sfx={project.sfx} words={project.words} fps={fps} />
    </AbsoluteFill>
  );
};
