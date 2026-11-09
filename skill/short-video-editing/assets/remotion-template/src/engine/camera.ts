// Virtual camera. Each scene gets one continuous move (push, pull, pan or hold, optionally with a
// slow roll) evaluated over the WHOLE scene including its transition handles, so motion never resets
// on a cut. Keyword punch-ins multiply on top and stay until the scene ends (a punch that springs
// back reads as a glitch). Scale is interpolated perceptually so equal time = equal apparent zoom.
// A scene with `keys` is keyframed instead: a list of framings (zoom, centre, roll) with an easing per
// segment, the CapCut way (references/camera-moves.md, "Keyframes").
import { Easing, interpolate, spring } from "remotion";
import type { Camera, CameraEase } from "../project";
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

// The easing of the segment that arrives at a key. `hold` keeps the previous framing until the key's time and
// then jumps: a hard cut-in inside the shot (use it with a short segment before it, or not at all).
export const KEY_EASE: Record<CameraEase, (t: number) => number> = {
  linear: (t) => t,
  in: Easing.bezier(0.42, 0, 1, 1),
  out: Easing.bezier(0, 0, 0.58, 1),
  inOut: motion.camera,
  soft: Easing.bezier(0.45, 0.05, 0.55, 0.95),
  snap: motion.easeOut, // fast start, long settle: the punch-in
  back: Easing.bezier(0.34, 1.4, 0.64, 1), // overshoots about 8 % and settles; once per video at most
  hold: (t) => (t < 1 ? 0 : 1),
};

type Framing = { zoom: number; at: [number, number]; roll: number };

// The framing at `frame`: zoom eased in AREA (the same "perceptual" scale as a plain push), centre and roll linearly.
const framingAt = (frame: number, cutOffset: number, fps: number, cam: Camera): Framing => {
  const ks = [...(cam.keys ?? [])]
    .sort((a, b) => a.ts - b.ts)
    .map((k) => ({ f: cutOffset + k.ts * fps, zoom: Math.max(1, k.zoom), at: k.at ?? ([0.5, 0.5] as [number, number]), roll: k.roll ?? 0, ease: k.ease ?? "inOut" }));
  const first = ks[0];
  const last = ks[ks.length - 1];
  if (frame <= first.f) return first;
  if (frame >= last.f) return last;
  let i = 0;
  while (frame > ks[i + 1].f) i++;
  const a = ks[i];
  const b = ks[i + 1];
  const e = KEY_EASE[b.ease]((frame - a.f) / Math.max(1e-6, b.f - a.f));
  return {
    zoom: Math.sqrt(Math.max(1e-6, a.zoom * a.zoom + e * (b.zoom * b.zoom - a.zoom * a.zoom))),
    at: [a.at[0] + (b.at[0] - a.at[0]) * e, a.at[1] + (b.at[1] - a.at[1]) * e],
    roll: a.roll + (b.roll - a.roll) * e,
  };
};

export const cameraStyle = (
  frame: number,
  duration: number,
  fps: number,
  cam: Camera | undefined,
  punches: ScenePunch[],
  cutOffset = 0, // frames from the start of the scene's sequence to its planned cut (the pre-roll handle)
): React.CSSProperties => {
  if (cam?.keys?.length) {
    const k = framingAt(frame, cutOffset, fps, cam);
    const rad = (Math.abs(k.roll) * Math.PI) / 180;
    const need = Math.cos(rad) + Math.sin(rad) * (16 / 9); // scale a roll needs so the corners stay covered
    let scale = Math.max(k.zoom, need);
    for (const p of punches) {
      const s = spring({ frame: frame - p.frame, fps, config: motion.smooth, durationInFrames: tokens.punchFrames });
      scale *= 1 + (p.scale - 1) * s;
    }
    scale = Math.min(scale, tokens.maxScale);
    // Put the chosen point of the footage at the centre of the frame, then keep the frame edge covered.
    const th = (k.roll * Math.PI) / 180;
    const px = scale * (k.at[0] - 0.5) * frameSize.width;
    const py = scale * (k.at[1] - 0.5) * frameSize.height;
    let tx = -(Math.cos(th) * px - Math.sin(th) * py);
    let ty = -(Math.sin(th) * px + Math.cos(th) * py);
    const room = Math.max(0, scale - need);
    tx = Math.max(-room * frameSize.width * 0.5, Math.min(room * frameSize.width * 0.5, tx));
    ty = Math.max(-room * frameSize.height * 0.5, Math.min(room * frameSize.height * 0.5, ty));
    return { transformOrigin: "50% 50%", translate: `${tx}px ${ty}px`, rotate: k.roll ? `${k.roll}deg` : undefined, scale: String(scale) };
  }

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
