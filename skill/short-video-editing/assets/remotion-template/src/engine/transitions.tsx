// Transition registry. Built-in Remotion presentations where they exist, three custom ones
// (zoomThrough, blurDissolve, whip) written with the documented custom-presentation API.
import React from "react";
import { AbsoluteFill, interpolate } from "remotion";
import type { TransitionPresentation, TransitionPresentationComponentProps } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide, type SlideDirection } from "@remotion/transitions/slide";
import { wipe, type WipeDirection } from "@remotion/transitions/wipe";
import { iris } from "@remotion/transitions/iris";
import { pushCut } from "@remotion/transitions/push-cut";
import { flip, type FlipDirection } from "@remotion/transitions/flip";
import { crossZoom } from "@remotion/transitions/cross-zoom";
import type { Direction, SceneTransition } from "../project";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// "left" = the new shot travels leftwards, i.e. it enters from the right.
const from: Record<Direction, SlideDirection & WipeDirection & FlipDirection> = {
  left: "from-right",
  right: "from-left",
  up: "from-bottom",
  down: "from-top",
};

type ZoomProps = { scale: number; blur: number };
const ZoomThrough: React.FC<TransitionPresentationComponentProps<ZoomProps>> = ({
  children,
  presentationDirection,
  presentationProgress: p,
  passedProps,
}) => {
  const exiting = presentationDirection === "exiting";
  const s = exiting ? interpolate(p, [0, 1], [1, passedProps.scale]) : interpolate(p, [0, 1], [passedProps.scale, 1]);
  const opacity = exiting ? 1 : interpolate(p, [0.4, 0.6], [0, 1], clamp);
  const blur = Math.sin(Math.PI * p) * passedProps.blur; // peaks mid-transition
  return <AbsoluteFill style={{ opacity, scale: String(s), filter: `blur(${blur}px)` }}>{children}</AbsoluteFill>;
};

type BlurProps = { blur: number };
const BlurDissolve: React.FC<TransitionPresentationComponentProps<BlurProps>> = ({
  children,
  presentationDirection,
  presentationProgress: p,
  passedProps,
}) => {
  const exiting = presentationDirection === "exiting";
  const opacity = exiting ? 1 : interpolate(p, [0.3, 0.7], [0, 1], clamp);
  return (
    <AbsoluteFill style={{ opacity, filter: `blur(${Math.sin(Math.PI * p) * passedProps.blur}px)` }}>{children}</AbsoluteFill>
  );
};

type WhipProps = { dx: number; dy: number; blur: number };
const Whip: React.FC<TransitionPresentationComponentProps<WhipProps>> = ({
  children,
  presentationDirection,
  presentationProgress: p,
  passedProps,
}) => {
  const exiting = presentationDirection === "exiting";
  const t = exiting ? interpolate(p, [0, 1], [0, -100]) : interpolate(p, [0, 1], [100, 0]);
  const blur = Math.sin(Math.PI * p) * passedProps.blur;
  return (
    <AbsoluteFill style={{ translate: `${t * passedProps.dx}% ${t * passedProps.dy}%`, filter: `blur(${blur}px)` }}>
      {children}
    </AbsoluteFill>
  );
};

// cardSlide: card scenes are transparent outside their card, so the whole scene can travel. The outgoing card slides
// off to one side, the incoming card slides in from the other; each leaves two fading copies of itself behind (the
// stepped trail of the agency-pitch look). Ghosts are the same children rendered again, only while the transition runs.
type CardSlideProps = { dx: number };
const CardSlide: React.FC<TransitionPresentationComponentProps<CardSlideProps>> = ({
  children,
  presentationDirection,
  presentationProgress: p,
  passedProps,
}) => {
  const exiting = presentationDirection === "exiting";
  const W = 1080 * 1.18;
  const at = (q: number) => (exiting ? interpolate(q, [0, 1], [0, W * passedProps.dx], clamp) : interpolate(q, [0, 1], [-W * passedProps.dx, 0], clamp));
  const lag = exiting ? [0.085, 0.17] : [-0.085, -0.17]; // exiting ghosts stay behind (earlier on the path); entering ghosts trail ahead
  const alpha = [0.5, 0.26];
  return (
    <AbsoluteFill>
      {lag.map((l, i) => (p > 0 && p < 1 ? (
        <AbsoluteFill key={i} style={{ translate: `${at(p + l)}px 0`, opacity: alpha[i] }}>
          {children}
        </AbsoluteFill>
      ) : null))}
      <AbsoluteFill style={{ translate: `${at(p)}px 0` }}>{children}</AbsoluteFill>
    </AbsoluteFill>
  );
};

// cardSwirl: the incoming (full-frame) shot arrives as three tilted cards that converge, straighten, square their
// corners and fill the frame; the outgoing shot dims and sinks underneath. Hero entrance after a card sequence.
type SwirlProps = { tilt: number };
const CardSwirl: React.FC<TransitionPresentationComponentProps<SwirlProps>> = ({
  children,
  presentationDirection,
  presentationProgress: p,
  passedProps,
}) => {
  if (presentationDirection === "exiting") {
    return (
      <AbsoluteFill style={{ filter: `brightness(${1 - 0.45 * p}) blur(${p * 6}px)`, scale: String(1 - 0.05 * p) }}>{children}</AbsoluteFill>
    );
  }
  const layers = [
    { lag: 0.2, rot: passedProps.tilt * -1.5, dx: -70, alpha: 0.4 },
    { lag: 0.1, rot: passedProps.tilt * 1.1, dx: 60, alpha: 0.6 },
    { lag: 0, rot: 0, dx: 0, alpha: 1 },
  ];
  return (
    <AbsoluteFill>
      {layers.map((l, i) => {
        const q0 = Math.min(1, Math.max(0, p - l.lag) / (1 - 0.2));
        if (l.lag > 0 && (q0 <= 0 || p >= 1)) return null;
        const q = Math.pow(q0, 1.7); // arrive late: the stack stays visibly tilted for most of the transition
        const k = 1 - q; // 1 at the start, 0 when settled
        return (
          <AbsoluteFill
            key={i}
            style={{
              opacity: l.lag > 0 ? l.alpha * Math.min(1, q * 4) * (1 - Math.max(0, (q - 0.7) / 0.3)) : Math.min(1, q * 3),
              scale: String(0.52 + 0.48 * q),
              rotate: `${(l.rot !== 0 ? l.rot : passedProps.tilt) * k}deg`,
              translate: `${l.dx * k}px ${-40 * k}px`,
              borderRadius: 64 * k,
              overflow: "hidden",
              boxShadow: k > 0.02 ? "0 24px 60px rgba(0,0,0,0.45)" : undefined,
            }}
          >
            {children}
          </AbsoluteFill>
        );
      })}
    </AbsoluteFill>
  );
};

const custom = <P extends Record<string, unknown>>(
  component: React.FC<TransitionPresentationComponentProps<P>>,
  props: P,
): TransitionPresentation<P> => ({ component, props });

const unit: Record<Direction, [number, number]> = { left: [1, 0], right: [-1, 0], up: [0, 1], down: [0, -1] };

export const presentationFor = (
  t: SceneTransition,
  width: number,
  height: number,
): TransitionPresentation<Record<string, unknown>> => {
  const dir = t.direction ?? "left";
  // The registry is heterogeneous by design; each branch is type-checked where it is built.
  const any = (x: unknown) => x as TransitionPresentation<Record<string, unknown>>;
  switch (t.type) {
    case "slide":
      return any(slide({ direction: from[t.direction ?? "up"] }));
    case "wipe":
      return any(wipe({ direction: from[t.direction ?? "right"] }));
    case "iris":
      return any(iris({ width, height }));
    case "pushCut":
      return any(pushCut());
    case "flip":
      return any(flip({ direction: from[dir] }));
    case "crossZoom":
      return any(crossZoom({ strength: 0.35 }));
    case "zoomThrough":
      return any(custom(ZoomThrough, { scale: 1.2, blur: 10 }));
    case "blurDissolve":
      return any(custom(BlurDissolve, { blur: 16 }));
    case "whip":
      return any(custom(Whip, { dx: unit[dir][0], dy: unit[dir][1], blur: 24 }));
    case "cardSlide":
      return any(custom(CardSlide, { dx: dir === "right" ? -1 : 1 })); // default: the old card leaves to the right
    case "cardSwirl":
      return any(custom(CardSwirl, { tilt: 20 }));
    case "fade":
    case "cut":
    default:
      return any(fade());
  }
};
