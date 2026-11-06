// Virtual camera. Each scene gets one continuous move (push, pull, pan or hold, optionally with a
// slow roll) evaluated over the WHOLE scene including its transition handles, so motion never resets
// on a cut. Keyword punch-ins multiply on top and stay until the scene ends (a punch that springs
// back reads as a glitch). Scale is interpolated perceptually so equal time = equal apparent zoom.
import { interpolate, spring } from "remotion";
import type { Camera } from "../project";
import { camera as tokens, frame as frameSize, motion } from "../theme";

export type ScenePunch = { frame: number; scale: number }; // frame relative to the scene sequence

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const range = (cam: Camera | undefined): [number, number] => {
  const move = cam?.move ?? "push";
  if (move === "pull") return [cam?.from ?? tokens.defaultPull[0], cam?.to ?? tokens.defaultPull[1]];
  if (move === "hold") return [cam?.from ?? 1.04, cam?.from ?? 1.04];
  if (move === "pan") return [cam?.from ?? 1.1, cam?.to ?? cam?.from ?? 1.1];
  return [cam?.from ?? tokens.defaultPush[0], cam?.to ?? tokens.defaultPush[1]];
};

export const cameraStyle = (
  frame: number,
  duration: number,
  fps: number,
  cam: Camera | undefined,
  punches: ScenePunch[],
): React.CSSProperties => {
  const [a, b] = range(cam);
  let scale = interpolate(frame, [0, duration], [a, b], {
    ...clamp,
    easing: motion.camera,
    output: "perceptual-scale",
  });
  for (const p of punches) {
    const k = spring({ frame: frame - p.frame, fps, config: motion.smooth, durationInFrames: tokens.punchFrames });
    scale *= 1 + (p.scale - 1) * k;
  }

  const [px, py] = cam?.move === "pan" ? cam.pan ?? [-tokens.defaultPan, 0] : [0, 0];
  const progress = interpolate(frame, [0, duration], [0, 1], { ...clamp, easing: motion.camera });
  const [r0, r1] = cam?.roll ?? [0, 0];
  const roll = r0 + (r1 - r0) * progress;
  // A pan needs spare image on the side it travels to, and a roll needs spare image in the corners
  // (cos + sin * 16/9 for a 9:16 frame); never reveal the frame edge.
  const rad = (Math.max(Math.abs(r0), Math.abs(r1)) * Math.PI) / 180;
  scale = Math.max(scale, 1 + 2 * Math.max(Math.abs(px), Math.abs(py)), Math.cos(rad) + Math.sin(rad) * (16 / 9));
  scale = Math.min(scale, tokens.maxScale);

  const [fx, fy] = cam?.focus ?? [0.5, 0.5];
  return {
    transformOrigin: `${fx * 100}% ${fy * 100}%`,
    translate: `${px * progress * frameSize.width}px ${py * progress * frameSize.height}px`,
    rotate: roll ? `${roll}deg` : undefined,
    scale: String(scale),
  };
};
