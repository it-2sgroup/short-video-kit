// Things that point: the cart CTA arrow, hand-drawn circles/arrows/underlines, and stickers.
import React from "react";
import { AbsoluteFill, interpolate, useVideoConfig } from "remotion";
import { evolvePath } from "@remotion/paths";
import type { Overlay } from "../../project";
import { cartPoint, fonts, frame as size, palette, toneColor, zones } from "../../theme";
import { clamp, pop, useEnterExit } from "../anim";
import { OutlineText } from "../text/primitives";

type Base = { ov: Overlay; dur: number; instant: boolean };

// Hand-drawn arrow that curves down onto TikTok Shop's real product bar (the yellow bag at the
// bottom-left, theme.cartPoint) with the label above its start. Never draw a fake cart UI.
// The arrow draws on over 12 frames, then bobs gently toward the cart.
export const CartPointer: React.FC<Base> = ({ ov, dur, instant }) => {
  const { fps } = useVideoConfig();
  const p = (ov.props ?? {}) as { text?: string };
  const { frame, exit } = useEnterExit(dur, { instant });
  const k = instant ? 1 : pop(frame, fps, 0);
  const bob = Math.sin((frame / 15) * Math.PI * 2) * 9;
  const tip = { x: cartPoint.x, y: cartPoint.y - 58 }; // just above the bag tile
  const tail = { x: tip.x + 120, y: tip.y - 100 }; // short: the captions are lifted clear while it shows
  const curve = `M ${tail.x} ${tail.y} Q ${tip.x} ${tail.y} ${tip.x} ${tip.y}`; // leaves leftward, lands pointing down
  const head = `M ${tip.x - 40} ${tip.y - 46} L ${tip.x} ${tip.y} L ${tip.x + 40} ${tip.y - 46}`;
  const draw = evolvePath(instant ? 1 : interpolate(frame, [0, 12], [0, 1], clamp), curve);
  const headIn = instant ? 1 : interpolate(frame, [9, 15], [0, 1], clamp);
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      {p.text ? (
        // The label sits to the right of the arrow's start unless a zone is given.
        <div style={{ position: "absolute", top: ov.zone ? zones[ov.zone] : tail.y - 32, left: tail.x + 26, width: 600, scale: String(k), transformOrigin: "left center" }}>
          <OutlineText size={50} weight={900} color={toneColor.cta} align="left">{p.text}</OutlineText>
        </div>
      ) : null}
      <svg width={size.width} height={size.height} style={{ position: "absolute", inset: 0, translate: `0px ${bob}px`, filter: "drop-shadow(0 4px 10px rgba(0,0,0,0.45))" }}>
        {[{ w: 24, c: palette.ink }, { w: 14, c: toneColor.cta }].map((s, i) => (
          <g key={i} fill="none" stroke={s.c} strokeWidth={s.w} strokeLinecap="round" strokeLinejoin="round">
            <path d={curve} strokeDasharray={draw.strokeDasharray} strokeDashoffset={draw.strokeDashoffset} />
            <path d={head} opacity={headIn} />
          </g>
        ))}
      </svg>
    </AbsoluteFill>
  );
};

export type HighlightProps = { shape?: "circle" | "underline" | "arrow"; target: [number, number]; size?: number };

export const Highlight: React.FC<Base> = ({ ov, dur, instant }) => {
  const p = (ov.props ?? {}) as HighlightProps;
  const { frame, exit } = useEnterExit(dur, { instant });
  const x = p.target[0] * size.width;
  const y = p.target[1] * size.height;
  const r = (p.size ?? 0.12) * size.width;
  const shape = p.shape ?? "circle";
  // Slightly open, slightly wobbly loop reads as hand-drawn rather than a vector ring.
  const d =
    shape === "underline"
      ? `M ${x - r} ${y} Q ${x} ${y + 18} ${x + r} ${y - 6}`
      : shape === "arrow"
        ? `M ${x - r * 1.6} ${y - r * 1.6} Q ${x - r * 0.4} ${y - r * 1.4} ${x - 10} ${y - 10} M ${x - 10} ${y - 10} L ${x - 60} ${y - 22} M ${x - 10} ${y - 10} L ${x - 24} ${y - 62}`
        : `M ${x + r} ${y} C ${x + r} ${y - r * 0.9}, ${x - r} ${y - r * 1.05}, ${x - r * 1.02} ${y} C ${x - r} ${y + r}, ${x + r * 1.1} ${y + r * 0.95}, ${x + r * 0.9} ${y - r * 0.3}`;
  const draw = evolvePath(instant ? 1 : interpolate(frame, [0, 10], [0, 1], clamp), d);
  const color = ov.tone && ov.tone !== "neutral" ? toneColor[ov.tone] : toneColor.cta;
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <svg width={size.width} height={size.height} style={{ position: "absolute", inset: 0, filter: "drop-shadow(0 3px 8px rgba(0,0,0,0.5))" }}>
        <path d={d} stroke={color} strokeWidth={10} fill="none" strokeLinecap="round" strokeLinejoin="round" strokeDasharray={draw.strokeDasharray} strokeDashoffset={draw.strokeDashoffset} />
      </svg>
    </AbsoluteFill>
  );
};

export type StickerProps = { text: string; at?: [number, number]; rotate?: number };

export const Sticker: React.FC<Base> = ({ ov, dur, instant }) => {
  const { fps } = useVideoConfig();
  const p = (ov.props ?? {}) as StickerProps;
  const { frame, exit } = useEnterExit(dur, { instant, exit: 5 });
  const k = instant ? 1 : pop(frame, fps, 0);
  const wobble = Math.sin((frame / 60) * Math.PI * 2) * 1.5;
  const [ax, ay] = p.at ?? [0.7, 0.24];
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <div
        style={{
          position: "absolute",
          left: ax * size.width,
          top: ay * size.height,
          translate: "-50% -50%",
          rotate: `${(p.rotate ?? -4) + wobble}deg`,
          scale: String(k),
          padding: "16px 30px",
          borderRadius: 24,
          background: toneColor.cta,
          boxShadow: "0 12px 30px rgba(0,0,0,0.35)",
          fontFamily: fonts.sans,
          fontWeight: 900,
          fontSize: 52,
          color: palette.ink,
          whiteSpace: "nowrap",
        }}
      >
        {p.text}
      </div>
    </AbsoluteFill>
  );
};
