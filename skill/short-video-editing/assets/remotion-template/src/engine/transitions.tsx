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
    case "fade":
    case "cut":
    default:
      return any(fade());
  }
};
