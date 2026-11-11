// Timing maths. Transitions overlap their two scenes, so naively feeding plan lengths into
// <TransitionSeries> shortens the video (total = sum of scenes - sum of transitions) and drifts
// the voiceover. Here every transition is centred on the planned cut instead:
//   begin[k]  = cut[k] - T[k]/2            (scene 0 begins at 0)
//   finish[k] = cut[k+1] + T[k+1]/2        (last scene ends at its planned end)
// so the cut lands exactly where the plan (and the voice) put it.
// A scene with `speed` or `ramp` reads its source faster or slower; the source frame at the planned
// cut is still `in`, so the handles before the cut are read at the scene's own speed.
import { Easing } from "remotion";
import type { Scene, SceneTransition, TransitionType } from "../project";

export const toFrames = (seconds: number, fps: number) => Math.round(seconds * fps);

export const DEFAULT_FRAMES: Record<TransitionType, number> = {
  cut: 0,
  fade: 12,
  slide: 14,
  wipe: 14,
  iris: 18,
  pushCut: 11,
  zoomThrough: 12,
  blurDissolve: 14,
  whip: 9,
  flip: 16,
  crossZoom: 16,
  cardSlide: 10,
  cardSwirl: 16,
};

const DEFAULT_TRANSITION: SceneTransition = { type: "fade" };

const even = (n: number) => (n <= 0 ? 0 : Math.max(2, Math.round(n / 2) * 2));

export type SceneSlot = {
  scene: Scene;
  index: number;
  begin: number; // first frame on screen (inside the incoming transition)
  duration: number; // frames, including both transition handles
  cut: number; // planned cut frame
  transitionIn: number; // frames of the incoming transition (0 = hard cut)
  startFrom: number; // source frame to start reading, including the pre-roll handle
  advance: (frame: number) => number; // source frames read after `frame` frames of this slot
};

const ease = Easing.inOut(Easing.sin); // symmetric, so a segment's average speed is the mean of its ends

// Speed at slot frame f: constant `speed`, or the ramp's points spread evenly over the slot.
const speedAt = (scene: Scene, f: number, duration: number) => {
  const r = scene.ramp;
  if (!r || r.length < 2) return scene.speed ?? 1;
  const x = Math.min(Math.max(f / Math.max(1, duration), 0), 1) * (r.length - 1);
  const i = Math.min(Math.floor(x), r.length - 2);
  return r[i] + (r[i + 1] - r[i]) * ease(x - i);
};

// Cumulative source frames after each slot frame (midpoint rule, exact for constant speed).
const advancer = (scene: Scene, duration: number) => {
  if (!scene.ramp || scene.ramp.length < 2) {
    const v = scene.speed ?? 1;
    return (f: number) => f * v;
  }
  const acc = [0];
  for (let f = 0; f < duration + 1; f++) acc.push(acc[f] + speedAt(scene, f + 0.5, duration));
  return (f: number) => acc[Math.min(Math.max(0, Math.round(f)), acc.length - 1)];
};

export const layoutScenes = (scenes: Scene[], fps: number): SceneSlot[] => {
  const cuts = scenes.map((s) => toFrames(s.start, fps));
  const ends = scenes.map((s) => toFrames(s.end, fps));
  const T = scenes.map((s, k) => {
    if (k === 0) return 0;
    const t = s.transition ?? DEFAULT_TRANSITION;
    const wanted = even(t.frames ?? DEFAULT_FRAMES[t.type]);
    // A transition may not be longer than either neighbour; keep it to half of the shorter one.
    const room = Math.min(cuts[k] - cuts[k - 1], ends[k] - cuts[k]);
    return Math.min(wanted, even(room / 2));
  });
  return scenes.map((scene, k) => {
    const begin = k === 0 ? 0 : cuts[k] - T[k] / 2;
    const finish = k === scenes.length - 1 ? ends[k] : cuts[k + 1] + T[k + 1] / 2;
    const advance = advancer(scene, finish - begin);
    return {
      scene,
      index: k,
      begin,
      duration: finish - begin,
      cut: cuts[k],
      transitionIn: T[k],
      startFrom: Math.max(0, Math.round(toFrames(scene.in, fps) - advance(cuts[k] - begin))),
      advance,
    };
  });
};

export const dbToGain = (db: number) => Math.pow(10, db / 20);
