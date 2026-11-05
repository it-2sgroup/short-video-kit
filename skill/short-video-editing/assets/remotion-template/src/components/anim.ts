// Shared enter/exit maths so every component moves with the same rhythm (theme.motion).
import { interpolate, spring, useCurrentFrame } from "remotion";
import { motion } from "../theme";

export const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

export type EnterExit = { frame: number; enter: number; exit: number; opacity: number };

// enter: 0 -> 1 over `enter` frames after `delay`; exit: 1 -> 0 over the last `exit` frames.
// `instant` skips the entrance (frame 0 is the feed thumbnail and must never be empty).
export const useEnterExit = (
  duration: number,
  opts: { delay?: number; enter?: number; exit?: number; instant?: boolean } = {},
): EnterExit => {
  const frame = useCurrentFrame();
  const delay = opts.delay ?? 0;
  const inF = opts.enter ?? motion.enterFrames;
  const outF = opts.exit ?? motion.exitFrames;
  const enter = opts.instant ? 1 : interpolate(frame, [delay, delay + inF], [0, 1], { ...clamp, easing: motion.easeOut });
  const exit = interpolate(frame, [duration - outF, duration], [1, 0], { ...clamp, easing: motion.exit });
  return { frame, enter, exit, opacity: Math.min(enter, exit) };
};

export const pop = (frame: number, fps: number, delay = 0) =>
  spring({ frame: frame - delay, fps, config: motion.pop });

export const smooth = (frame: number, fps: number, delay = 0, durationInFrames?: number) =>
  spring({ frame: frame - delay, fps, config: motion.smooth, durationInFrames });

// Largest font size (px) that keeps `text` on one line inside `width`, assuming a heavy sans
// averages ~0.56em per character. Cheap and deterministic; good enough for 1-6 word titles.
export const fitSize = (text: string, width: number, max: number, min: number, emPerChar = 0.56) =>
  Math.max(min, Math.min(max, width / Math.max(1, text.length * emPerChar)));
