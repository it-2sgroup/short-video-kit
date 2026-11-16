// Transition registry. Built-in Remotion presentations where they exist (`@remotion/transitions`: the shader ones need the
// angle GL renderer and HTML-in-canvas), and custom ones written with the documented custom-presentation API (zoomThrough,
// blurDissolve, whip, blinds, diamond, doors, glitchSlice, spinZoom, inkBleed, lumaWipe, cutCurve, gridFlash, cropPop, cropNegative, flashWipe,
// blackFlicker, zoomFade, cardSlide, cardSwirl), plus the
// GL Transitions shaders of engine/glTransitions.tsx (glPixelate, glSwirl... one .glsl file each).
import React from "react";
import { AbsoluteFill, Easing, interpolate } from "remotion";
import type { TransitionPresentation, TransitionPresentationComponentProps } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide, type SlideDirection } from "@remotion/transitions/slide";
import { wipe, type WipeDirection } from "@remotion/transitions/wipe";
import { iris } from "@remotion/transitions/iris";
import { pushCut } from "@remotion/transitions/push-cut";
import { flip, type FlipDirection } from "@remotion/transitions/flip";
import { crossZoom } from "@remotion/transitions/cross-zoom";
import { filmBurn } from "@remotion/transitions/film-burn";
import { zoomBlur } from "@remotion/transitions/zoom-blur";
import { dreamyZoom } from "@remotion/transitions/dreamy-zoom";
import { linearBlur } from "@remotion/transitions/linear-blur";
import { crosswarp } from "@remotion/transitions/crosswarp";
import { zoomInOut } from "@remotion/transitions/zoom-in-out";
import { blurSlide } from "@remotion/transitions/blur-slide";
import { clockWipe } from "@remotion/transitions/clock-wipe";
import { ripple } from "@remotion/transitions/ripple";
import { dissolve } from "@remotion/transitions/dissolve";
import { cube } from "@remotion/transitions/cube";
import { bookFlip } from "@remotion/transitions/book-flip";
import { swap } from "@remotion/transitions/swap";
import type { Direction, SceneTransition } from "../project";
import { glTransition, isGlTransition } from "./glTransitions";

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

// whip: a velocity-matched pan. Both shots travel together on one eased curve, so the seam moves at the speed of the move
// (no gap, no pause); only the faster part of the move is smeared, by a DIRECTIONAL blur (an SVG filter blurring along the
// axis of travel: a CSS blur() would blur both axes and read as a soft slide) and a small rolling-shutter skew.
type WhipProps = { dx: number; dy: number; blur: number };
const Whip: React.FC<TransitionPresentationComponentProps<WhipProps>> = ({
  children,
  presentationDirection,
  presentationProgress: p,
  passedProps,
}) => {
  const exiting = presentationDirection === "exiting";
  const t = exiting ? interpolate(p, [0, 1], [0, -100]) : interpolate(p, [0, 1], [100, 0]);
  const speed = Math.min(1, (p < 0.5 ? 12 * p * p : 12 * (1 - p) * (1 - p)) / 3); // 0..1, 1 at the middle of the move
  const sigma = passedProps.blur * speed;
  const horizontal = passedProps.dx !== 0;
  const id = `whip${exiting ? "x" : "e"}`;
  return (
    <AbsoluteFill style={{ translate: `${t * passedProps.dx}% ${t * passedProps.dy}%` }}>
      <svg width={0} height={0} style={{ position: "absolute" }}>
        <defs>
          <filter id={id} x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation={horizontal ? `${sigma} 0` : `0 ${sigma}`} />
          </filter>
        </defs>
      </svg>
      <AbsoluteFill style={{ filter: sigma > 0.5 ? `url(#${id})` : undefined, transform: horizontal ? `skewX(${(-passedProps.dx * 5 * speed).toFixed(2)}deg)` : undefined }}>{children}</AbsoluteFill>
    </AbsoluteFill>
  );
};

// blinds: the new shot opens through N horizontal bands that widen until they meet.
type BlindsProps = { bands: number };
const Blinds: React.FC<TransitionPresentationComponentProps<BlindsProps>> = ({ children, presentationDirection, presentationProgress: p, passedProps }) => {
  if (presentationDirection === "exiting") return <AbsoluteFill>{children}</AbsoluteFill>;
  const band = 1920 / passedProps.bands;
  const open = p * band;
  const m = `repeating-linear-gradient(to bottom, #000 0px, #000 ${open}px, transparent ${open}px, transparent ${band}px)`;
  return <AbsoluteFill style={{ WebkitMaskImage: m, maskImage: m }}>{children}</AbsoluteFill>;
};

// diamond: a diamond opens from the centre of the frame onto the new shot.
const Diamond: React.FC<TransitionPresentationComponentProps<Record<string, never>>> = ({ children, presentationDirection, presentationProgress: p }) => {
  if (presentationDirection === "exiting") return <AbsoluteFill>{children}</AbsoluteFill>;
  const r = p * 100;
  return <AbsoluteFill style={{ clipPath: `polygon(50% ${50 - r}%, ${50 + r}% 50%, 50% ${50 + r}%, ${50 - r}% 50%)` }}>{children}</AbsoluteFill>;
};

// doors: the old shot splits down the middle and the halves slide apart, uncovering the new shot (which settles from 1.05).
const Doors: React.FC<TransitionPresentationComponentProps<Record<string, never>>> = ({ children, presentationDirection, presentationProgress: p }) => {
  if (presentationDirection === "entering") return <AbsoluteFill style={{ scale: String(1.05 - 0.05 * p) }}>{children}</AbsoluteFill>;
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ clipPath: "inset(0 50% 0 0)", translate: `${-p * 52}% 0` }}>{children}</AbsoluteFill>
      <AbsoluteFill style={{ clipPath: "inset(0 0 0 50%)", translate: `${p * 52}% 0` }}>{children}</AbsoluteFill>
    </AbsoluteFill>
  );
};

// glitchSlice: through the cut the picture is cut into horizontal bands that jump sideways by different amounts (decaying
// toward each end) with a hue split; the old shot shows in the first half, the new one in the second.
const SLICES = 7;
const glitchRand = (i: number, step: number) => {
  const x = Math.sin(i * 127.1 + step * 311.7) * 43758.5453;
  return x - Math.floor(x);
};
const GlitchSlice: React.FC<TransitionPresentationComponentProps<Record<string, never>>> = ({ children, presentationDirection, presentationProgress: p }) => {
  const exiting = presentationDirection === "exiting";
  if (exiting ? p >= 0.5 : p < 0.5) return null;
  const amp = Math.sin(Math.PI * p) * 220;
  const step = Math.floor(p * 12);
  return (
    <AbsoluteFill>
      {Array.from({ length: SLICES }, (_, i) => (
        <AbsoluteFill
          key={i}
          style={{
            clipPath: `inset(${(i / SLICES) * 100}% 0 ${100 - ((i + 1) / SLICES) * 100}% 0)`,
            translate: `${(glitchRand(i, step) - 0.5) * 2 * amp}px 0`,
            filter: `hue-rotate(${(glitchRand(i, step + 7) - 0.5) * 120 * Math.sin(Math.PI * p)}deg) saturate(${1 + 0.6 * Math.sin(Math.PI * p)})`,
          }}
        >
          {children}
        </AbsoluteFill>
      ))}
    </AbsoluteFill>
  );
};

// spinZoom: the old shot spins and grows into a blur, the new one spins in from the other side and settles.
type SpinProps = { turn: number; blur: number };
const SpinZoom: React.FC<TransitionPresentationComponentProps<SpinProps>> = ({ children, presentationDirection, presentationProgress: p, passedProps }) => {
  const exiting = presentationDirection === "exiting";
  const q = exiting ? p : 1 - p;
  const sign = exiting ? -1 : 1;
  return (
    <AbsoluteFill
      style={{
        opacity: exiting ? interpolate(p, [0.5, 1], [1, 0], clamp) : interpolate(p, [0, 0.5], [0, 1], clamp),
        rotate: `${sign * passedProps.turn * q}deg`,
        scale: String(1 + 0.6 * q),
        filter: `blur(${passedProps.blur * q}px)`,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

// cardSlide: card scenes are transparent outside their card, so the whole scene can travel. The outgoing card slides
// off to one side, the incoming card slides in from the other; each leaves two fading copies of itself behind (a
// stepped trail). Ghosts are the same children rendered again, only while the transition runs.
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

// A mask drawn as an SVG image (filters work inside it): a pure function of the progress, so a still, a render and the HyperFrames
// kit all draw the same frame. The mask is the picture's alpha channel.
const svgMask = (w: number, h: number, body: string) =>
  `url("data:image/svg+xml,${encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}">${body}</svg>`)}")`;

// inkBleed: ink drops grow from a few points, swell and merge into the new shot. Circles are blurred and thresholded (SVG "goo"),
// then the edge is torn by a noise displacement; the last stretch fills whatever is left so the end is always the full frame.
const INK_DROPS = 7;
const inkMask = (p: number, w: number, h: number) => {
  const reach = Math.hypot(w, h) * 0.45;
  const drops = Array.from({ length: INK_DROPS }, (_, i) => {
    const delay = 0.3 * glitchRand(i, 3);
    const q = Math.min(1, Math.max(0, (p - delay) / (1 - delay)));
    return `<circle cx="${((0.12 + 0.76 * glitchRand(i, 1)) * w).toFixed(1)}" cy="${((0.1 + 0.8 * glitchRand(i, 2)) * h).toFixed(1)}" r="${(reach * Math.pow(q, 1.1)).toFixed(1)}"/>`;
  }).join("");
  const fill = Math.min(1, Math.max(0, (p - 0.86) / 0.12));
  return svgMask(
    w,
    h,
    `<filter id="g" x="-15%" y="-15%" width="130%" height="130%" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="26"/>` +
      `<feColorMatrix values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 24 -9" result="goo"/>` +
      `<feTurbulence type="fractalNoise" baseFrequency="0.012" numOctaves="2" seed="4" result="n"/>` +
      `<feDisplacementMap in="goo" in2="n" scale="80" xChannelSelector="R" yChannelSelector="G"/></filter>` +
      `<g filter="url(#g)" fill="#fff">${drops}</g><rect width="${w}" height="${h}" fill="#fff" opacity="${fill.toFixed(3)}"/>`,
  );
};
type InkProps = { width: number; height: number };
const InkBleed: React.FC<TransitionPresentationComponentProps<InkProps>> = ({ children, presentationDirection, presentationProgress: p, passedProps }) => {
  if (presentationDirection === "exiting") return <AbsoluteFill>{children}</AbsoluteFill>;
  const m = inkMask(p, passedProps.width, passedProps.height);
  return <AbsoluteFill style={{ WebkitMaskImage: m, maskImage: m, maskSize: "100% 100%" }}>{children}</AbsoluteFill>;
};

// lumaWipe: a luma mask (a gradient across the frame from the side the new shot comes from, broken up by noise) is thresholded
// at a level that rises with the progress: darker places of the mask show the new shot first, with a soft edge. Pure SVG filter.
const lumaMask = (p: number, w: number, h: number, vx: number, vy: number) => {
  const K = 9; // edge sharpness
  const level = -0.05 + 1.15 * p;
  return svgMask(
    w,
    h,
    `<defs><linearGradient id="a" x1="${0.5 + 0.5 * vx}" y1="${0.5 + 0.5 * vy}" x2="${0.5 - 0.5 * vx}" y2="${0.5 - 0.5 * vy}"><stop offset="0" stop-color="#000"/><stop offset="1" stop-color="#fff"/></linearGradient>` +
      `<filter id="l" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB">` +
      `<feTurbulence type="fractalNoise" baseFrequency="0.0045 0.003" numOctaves="3" seed="7" result="t"/>` +
      `<feColorMatrix in="t" type="matrix" values="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 0 0 0 0 1" result="n"/>` +
      `<feComposite in="SourceGraphic" in2="n" operator="arithmetic" k1="0" k2="0.6" k3="0.4" k4="0" result="luma"/>` +
      `<feColorMatrix in="luma" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 ${-K} 0 0 0 ${(K * level + 0.5).toFixed(3)}"/></filter></defs>` +
      `<rect width="${w}" height="${h}" fill="url(#a)" filter="url(#l)"/>`,
  );
};
type LumaProps = { width: number; height: number; vx: number; vy: number };
const LumaWipe: React.FC<TransitionPresentationComponentProps<LumaProps>> = ({ children, presentationDirection, presentationProgress: p, passedProps }) => {
  if (presentationDirection === "exiting") return <AbsoluteFill>{children}</AbsoluteFill>;
  const m = lumaMask(p, passedProps.width, passedProps.height, passedProps.vx, passedProps.vy);
  return <AbsoluteFill style={{ WebkitMaskImage: m, maskImage: m, maskSize: "100% 100%" }}>{children}</AbsoluteFill>;
};

// cutCurve: a hard cut hidden in a move. The old shot accelerates along the axis (quadratic in the already eased progress), at the peak
// of its speed the picture is swapped, and the new shot arrives travelling at the same speed in the same direction and settles (the mirror): the eye
// follows the motion across the cut. No blur; both shots are scaled up while they are off centre so no edge shows.
type CutCurveProps = { vx: number; vy: number; travel: number };
const CutCurve: React.FC<TransitionPresentationComponentProps<CutCurveProps>> = ({ children, presentationDirection, presentationProgress: p, passedProps }) => {
  const exiting = presentationDirection === "exiting";
  if (exiting ? p >= 0.5 : p < 0.5) return null;
  const q = exiting ? 2 * p : 2 * (1 - p); // 0..1 toward the swap
  const off = q * q * passedProps.travel * (exiting ? -1 : 1); // fraction of the frame, along the axis
  return (
    <AbsoluteFill style={{ translate: `${off * passedProps.vx * 100}% ${off * passedProps.vy * 100}%`, scale: String(1 + 2 * Math.abs(off)) }}>
      {children}
    </AbsoluteFill>
  );
};

// ---- Showreel transitions (measured on two technique-breakdown videos: references/transition-pack.md) ----
// The white of every measured flash is a warm cream, never pure white.
const CREAM = "#FFFBEF";

// gridFlash: the frame is a grid of cells. In a random order each cell flashes cream for about one frame, then shows the new shot; a thin dark line is
// left between the cells until a last cream flash of two frames ends it. The new shot is drawn once, behind a mask of the cells that are open.
type GridProps = { cols: number; rows: number; width: number; height: number };
const GridFlash: React.FC<TransitionPresentationComponentProps<GridProps>> = ({ children, presentationDirection, presentationProgress: p, passedProps: g }) => {
  if (presentationDirection === "exiting") return <AbsoluteFill>{children}</AbsoluteFill>;
  const n = g.cols * g.rows;
  const order = Array.from({ length: n }, (_, i) => i).sort((a, b) => glitchRand(a, 9) - glitchRand(b, 9));
  const cw = g.width / g.cols;
  const ch = g.height / g.rows;
  const FLASH = 0.09; // a cell stays cream for this share of the transition
  const open: string[] = [];
  const flashing: { x: number; y: number }[] = [];
  order.forEach((cell, r) => {
    const a = 0.04 + 0.74 * (r / n);
    const x = (cell % g.cols) * cw;
    const y = Math.floor(cell / g.cols) * ch;
    if (p >= a + FLASH) open.push(`<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${cw.toFixed(1)}" height="${ch.toFixed(1)}" fill="#fff"/>`);
    else if (p >= a) flashing.push({ x, y });
  });
  const mask = svgMask(g.width, g.height, open.join(""));
  const lines = p > 0.12 && p < 0.88;
  const last = p >= 0.88 && p < 0.96;
  return (
    <AbsoluteFill>
      <AbsoluteFill style={p >= 0.9 ? undefined : { WebkitMaskImage: mask, maskImage: mask, maskSize: "100% 100%" }}>{children}</AbsoluteFill>
      {flashing.map((f, i) => (
        <div key={i} style={{ position: "absolute", left: f.x, top: f.y, width: cw, height: ch, background: CREAM }} />
      ))}
      {lines &&
        Array.from({ length: g.cols - 1 }, (_, i) => <div key={`v${i}`} style={{ position: "absolute", left: (i + 1) * cw - 1.5, top: 0, width: 3, height: g.height, background: "rgba(0,0,0,0.55)" }} />)}
      {lines &&
        Array.from({ length: g.rows - 1 }, (_, i) => <div key={`h${i}`} style={{ position: "absolute", top: (i + 1) * ch - 1.5, left: 0, height: 3, width: g.width, background: "rgba(0,0,0,0.55)" }} />)}
      {last && <AbsoluteFill style={{ background: CREAM, opacity: 0.92 }} />}
    </AbsoluteFill>
  );
};

// cropPop: the whole new shot, scaled down, pops open as a small window (x, y = its top-left, w = its width as fractions of the frame) over the old
// shot and grows to the full frame with an ease-out. `negative` shows it as an inverted black-and-white picture for the first half of the growth.
type CropProps = { x: number; y: number; w: number; width: number; height: number; negative: boolean };
const CropPop: React.FC<TransitionPresentationComponentProps<CropProps>> = ({ children, presentationDirection, presentationProgress: p, passedProps: c }) => {
  if (presentationDirection === "exiting") return <AbsoluteFill>{children}</AbsoluteFill>;
  const q = 1 - Math.pow(1 - p, 3);
  const s = c.w + (1 - c.w) * q;
  const neg = c.negative ? (p < 0.5 ? 1 : Math.max(0, 1 - (p - 0.5) / 0.3)) : 0;
  return (
    <AbsoluteFill
      style={{
        transformOrigin: "0 0",
        transform: `translate(${c.x * c.width * (1 - q)}px, ${c.y * c.height * (1 - q)}px) scale(${s})`,
        filter: neg > 0 ? `invert(${neg.toFixed(2)}) grayscale(${neg.toFixed(2)})` : undefined,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

// flashWipe: a cream band wider than the frame sweeps across (soft edges, `vx` = 1 travels right to left); the picture is swapped while it covers
// everything, at the middle of the transition. The band is drawn by the incoming layer, which sits on top for the whole transition. The progress is
// eased (fast in the middle), so a cream wash over the whole frame peaks at the swap: the cut is covered even when the band jumps between two frames.
type FlashProps = { vx: number };
const FlashWipe: React.FC<TransitionPresentationComponentProps<FlashProps>> = ({ children, presentationDirection, presentationProgress: p, passedProps }) => {
  if (presentationDirection === "exiting") return <AbsoluteFill>{p < 0.5 ? children : null}</AbsoluteFill>;
  const BW = 140; // band width, % of the frame
  const wash = Math.max(0, 1 - Math.pow((p - 0.5) / 0.2, 2));
  const left = passedProps.vx > 0 ? 100 - (100 + BW) * p : -BW + (100 + BW) * p;
  return (
    <AbsoluteFill>
      {p >= 0.5 ? children : null}
      <div
        style={{
          position: "absolute",
          top: 0,
          bottom: 0,
          left: `${left}%`,
          width: `${BW}%`,
          background: `linear-gradient(to right, rgba(255,251,239,0) 0%, ${CREAM} 22%, ${CREAM} 78%, rgba(255,251,239,0) 100%)`,
        }}
      />
      <AbsoluteFill style={{ background: CREAM, opacity: wash }} />
    </AbsoluteFill>
  );
};

// blackFlicker: through the change the picture flickers to black and back, a deterministic pattern per frame (the transition's progress is eased, so the
// frame number is recovered by inverting the easing of engine/Short.tsx: `steps` must be the number of frames of the transition, 14 by default). The frames
// next to a black one are dimmed (the "mix"). The old shot shows in the first part, the new one in the rest; the first and last two frames stay clean.
const SHORT_EASE = Easing.bezier(0.65, 0, 0.35, 1); // = motion.easeInOut, the easing of every transition
const unease = (p: number) => {
  let lo = 0;
  let hi = 1;
  for (let i = 0; i < 14; i++) {
    const m = (lo + hi) / 2;
    if (SHORT_EASE(m) < p) lo = m;
    else hi = m;
  }
  return (lo + hi) / 2;
};
type FlickerProps = { steps: number };
const BlackFlicker: React.FC<TransitionPresentationComponentProps<FlickerProps>> = ({ children, presentationDirection, presentationProgress: p, passedProps }) => {
  const exiting = presentationDirection === "exiting";
  const n = passedProps.steps;
  const s = Math.min(n - 1, Math.round(unease(p) * n));
  const black = (k: number) => k >= 1 && k < n - 2 && glitchRand(k, 3) > 0.42;
  const swap = Math.floor(n * 0.55);
  if (exiting ? s >= swap : s < swap) return null;
  const opacity = black(s) ? 0 : black(s - 1) || black(s + 1) ? 0.55 : 1;
  return <AbsoluteFill style={{ opacity }}>{children}</AbsoluteFill>;
};

// zoomFade: the old shot grows a little and dips to black; the new one fades up from black while it grows from 0.9 to the full frame, so a dark
// border shows around it for a few frames.
const ZoomFade: React.FC<TransitionPresentationComponentProps<Record<string, never>>> = ({ children, presentationDirection, presentationProgress: p }) => {
  if (presentationDirection === "exiting") {
    return <AbsoluteFill style={{ opacity: interpolate(p, [0, 0.5], [1, 0], clamp), scale: String(interpolate(p, [0, 1], [1, 1.07], clamp)) }}>{children}</AbsoluteFill>;
  }
  return (
    <AbsoluteFill
      style={{
        opacity: interpolate(p, [0.4, 0.9], [0, 1], clamp),
        scale: String(interpolate(p, [0.4, 1], [0.9, 1], clamp)),
        filter: `brightness(${interpolate(p, [0.4, 1], [0.4, 1], clamp)})`,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

// custom() wraps one of the components above as a presentation.
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
  // GL Transitions shaders: the plan's Direction is the side the new shot comes from, y up
  if (isGlTransition(t.type)) return any(glTransition(t.type, { direction: [unit[dir][0], -unit[dir][1]] }));
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
      return any(custom(Whip, { dx: unit[dir][0], dy: unit[dir][1], blur: 46 }));
    case "cardSlide":
      return any(custom(CardSlide, { dx: dir === "right" ? -1 : 1 })); // default: the old card leaves to the right
    case "cardSwirl":
      return any(custom(CardSwirl, { tilt: 20 }));
    case "filmBurn":
      return any(filmBurn({ seed: 1 }));
    case "zoomBlur":
      return any(zoomBlur({}));
    case "dreamyZoom":
      return any(dreamyZoom({}));
    case "linearBlur":
      return any(linearBlur({}));
    case "crosswarp":
      return any(crosswarp({}));
    case "zoomInOut":
      return any(zoomInOut({}));
    case "blurSlide":
      return any(blurSlide({ direction: from[dir] }));
    case "clockWipe":
      return any(clockWipe({ width, height }));
    case "ripple":
      return any(ripple({}));
    case "burnDissolve":
      return any(dissolve({}));
    case "cube":
      return any(cube({ direction: from[dir] }));
    case "bookFlip":
      return any(bookFlip({ direction: from[dir] }));
    case "swap":
      return any(swap({}));
    case "blinds":
      return any(custom(Blinds, { bands: 8 }));
    case "diamond":
      return any(custom(Diamond, {}));
    case "doors":
      return any(custom(Doors, {}));
    case "glitchSlice":
      return any(custom(GlitchSlice, {}));
    case "spinZoom":
      return any(custom(SpinZoom, { turn: 28, blur: 16 }));
    case "inkBleed":
      return any(custom(InkBleed, { width, height }));
    case "lumaWipe":
      return any(custom(LumaWipe, { width, height, vx: unit[dir][0], vy: unit[dir][1] }));
    case "cutCurve":
      return any(custom(CutCurve, { vx: unit[dir][0], vy: unit[dir][1], travel: 0.16 }));
    case "gridFlash":
      return any(custom(GridFlash, { cols: 3, rows: 3, width, height }));
    case "cropPop":
      return any(custom(CropPop, { x: 0.27, y: 0.52, w: 0.46, width, height, negative: false }));
    case "cropNegative":
      return any(custom(CropPop, { x: 0.56, y: 0.5, w: 0.22, width, height, negative: true }));
    case "flashWipe":
      return any(custom(FlashWipe, { vx: unit[dir][0] }));
    case "blackFlicker":
      return any(custom(BlackFlicker, { steps: 14 }));
    case "zoomFade":
      return any(custom(ZoomFade, {}));
    case "fade":
    case "cut":
    default:
      return any(fade());
  }
};
