// Light on the picture: a band of light crossing a zone or a word (`sweep`), a lens flare (`flare`) and an anamorphic streak (`streak`).
// All three are screen-blended gradients over the footage: pure functions of the frame, no media, nothing to decode. One per beat, not
// continuous: a flare on every cut reads as a template.
import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import type { Overlay } from "../../project";
import { fonts, frame as size, motion, zones } from "../../theme";
import { clamp } from "../anim";

type Base = { ov: Overlay; dur: number; instant: boolean };
type Point = [number, number];

const lines = (t: unknown): string[] => (Array.isArray(t) ? t.map(String) : String(t ?? "").split(" / "));
const unit = (v: number) => Math.min(1, Math.max(0, v));

// ------------------------------------------------------------------------------------------------ sweep
export type SweepProps = { at?: Point; width?: number; height?: number; band?: number; angle?: number; color?: string; opacity?: number; text?: string | string[]; size?: number; fill?: string };

// A diagonal band of light that crosses once, in the overlay's own life (give it 0.6-0.8 s: 18-24 frames). Without `text` it crosses a
// box (`at` its centre as fractions of the frame, `width` x `height` px; default the top strip) and lightens what is under it. With
// `text` it draws those words (`fill`, default white) and the band shines only on the letters.
export const Sweep: React.FC<Base> = ({ ov, dur }) => {
  const p = (ov.props ?? {}) as SweepProps;
  const frame = useCurrentFrame();
  const band = p.band ?? 16; // half-width of the band in percent of the box
  const pos = -band + (100 + 2 * band) * motion.easeInOut(unit(frame / Math.max(1, dur - 1)));
  const lean = 90 + (p.angle ?? 15); // the gradient's angle: 90 is a vertical band
  const col = p.color ?? "#FFFFFF";
  const k = p.opacity ?? 0.6;
  const w = p.width ?? 900;
  const h = p.height ?? 220;
  const [ax, ay] = p.at ?? [0.5, (zones[ov.zone ?? "top"] + h / 2) / size.height];
  const shine = `linear-gradient(${lean}deg, transparent ${pos - band}%, ${col} ${pos}%, transparent ${pos + band}%)`;
  const feather = "linear-gradient(transparent, #000 30%, #000 70%, transparent)"; // the box has soft top and bottom edges
  const place: React.CSSProperties = { position: "absolute", left: ax * size.width, top: ay * size.height, translate: "-50% -50%" };

  if (p.text !== undefined) {
    const rows = lines(p.text);
    const px = p.size ?? 150;
    const fill = p.fill ?? "#FFFFFF";
    return (
      <AbsoluteFill>
        <div
          style={{
            ...place,
            fontFamily: fonts.sans,
            fontWeight: 900,
            fontSize: px,
            lineHeight: 1.05,
            textAlign: "center",
            whiteSpace: "pre",
            color: "transparent",
            WebkitBackgroundClip: "text",
            backgroundClip: "text",
            backgroundImage: `${shine}, linear-gradient(${fill}, ${fill})`,
          }}
        >
          {rows.join("\n")}
        </div>
      </AbsoluteFill>
    );
  }
  return (
    <AbsoluteFill style={{ mixBlendMode: "screen", opacity: k }}>
      <div style={{ ...place, width: w, height: h, backgroundImage: shine, WebkitMaskImage: feather, maskImage: feather }} />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------------------------------------ flare
export type FlareProps = { at?: Point; drift?: Point; color?: string; size?: number; ghosts?: number; flash?: boolean; opacity?: number };

// Positions of the ghosts along the line from the source through the centre of the frame, as multiples of that distance (1 = the centre, 2 = the source mirrored), and their sizes
// as fractions of the flare's size: what a lens does with a bright point, drawn from the geometry only.
const GHOSTS: { m: number; s: number; ring: boolean; tint: string | null }[] = [
  { m: 0.5, s: 0.34, ring: false, tint: null },
  { m: 1.0, s: 0.2, ring: true, tint: "#9FD8FF" },
  { m: 1.45, s: 0.5, ring: true, tint: "#FFB3E6" },
  { m: 1.9, s: 0.16, ring: false, tint: "#B6FFD0" },
  { m: 2.35, s: 0.3, ring: true, tint: null },
];

// A bright source (soft disc) that rises in 5 frames and decays over the rest of the overlay, drifting by `drift` (fractions of the
// frame) while its ghosts slide the opposite way. `flash` adds one white frame at the peak. One per video: it is a shot of a bright
// source (a window, a lamp, the sun), so aim `at` at one that is in the picture.
export const Flare: React.FC<Base> = ({ ov, dur }) => {
  const p = (ov.props ?? {}) as FlareProps;
  const frame = useCurrentFrame();
  const up = motion.easeOut(unit(frame / 5));
  const down = motion.easeInOut(unit((frame - 5) / Math.max(1, dur - 5)));
  const level = up * (1 - down) * (p.opacity ?? 0.9);
  const life = unit(frame / Math.max(1, dur - 1));
  const [sx0, sy0] = p.at ?? [0.8, 0.22];
  const [dx, dy] = p.drift ?? [-0.05, 0.035];
  const sx = (sx0 + dx * life) * size.width;
  const sy = (sy0 + dy * life) * size.height;
  const cx = size.width / 2;
  const cy = size.height / 2;
  const col = p.color ?? "#FFD9A0";
  const big = p.size ?? 460;
  const disc = (x: number, y: number, d: number, ring: boolean, tint: string, a: number) => (
    <div
      key={`${x}${y}${d}`}
      style={{
        position: "absolute",
        left: x,
        top: y,
        width: d,
        height: d,
        translate: "-50% -50%",
        borderRadius: "50%",
        opacity: a,
        background: ring
          ? `radial-gradient(circle, ${tint}22 0%, transparent 58%, ${tint}AA 76%, transparent 80%)`
          : `radial-gradient(circle, ${tint}CC 0%, ${tint}55 45%, transparent 70%)`,
      }}
    />
  );
  return (
    <AbsoluteFill style={{ mixBlendMode: "screen" }}>
      {/* the source: a white-hot core inside a wide soft halo */}
      <div style={{ position: "absolute", left: sx, top: sy, width: big, height: big, translate: "-50% -50%", opacity: level, background: `radial-gradient(circle, #FFFFFF 0%, ${col} 14%, ${col}66 38%, transparent 68%)` }} />
      {GHOSTS.slice(0, Math.min(GHOSTS.length, Math.max(0, p.ghosts ?? 4))).map((g) => disc(sx + (cx - sx) * g.m, sy + (cy - sy) * g.m, big * g.s, g.ring, g.tint ?? col, level * 0.7))}
      {p.flash && Math.round(frame) === 4 ? <AbsoluteFill style={{ background: "#FFFFFF", opacity: 0.45 }} /> : null}
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------------------------------------ streak
export type StreakProps = { at?: Point; color?: string; length?: number; thickness?: number; opacity?: number };

// The horizontal blue line a cinema anamorphic lens draws through a bright light: a thin white core inside a coloured halo, `length` x the
// frame width, growing from the centre in 7 frames, holding, fading over the last 10 frames of the overlay.
export const Streak: React.FC<Base> = ({ ov, dur }) => {
  const p = (ov.props ?? {}) as StreakProps;
  const frame = useCurrentFrame();
  const grow = motion.easeOut(unit(frame / 7));
  const fade = interpolate(frame, [dur - 10, dur], [1, 0], clamp);
  const [ax, ay] = p.at ?? [0.5, 0.45];
  const col = p.color ?? "#6EA8FF";
  const t = p.thickness ?? 8;
  const len = (p.length ?? 1.15) * size.width;
  const bar = (h: number, c: string, blur: number, a: number) => (
    <div style={{ position: "absolute", left: ax * size.width, top: ay * size.height, width: len, height: h, translate: "-50% -50%", transform: `scaleX(${grow})`, opacity: a, filter: `blur(${blur}px)`, background: `linear-gradient(90deg, transparent 0%, ${c} 50%, transparent 100%)` }} />
  );
  return (
    <AbsoluteFill style={{ mixBlendMode: "screen", opacity: fade * (p.opacity ?? 0.9) }}>
      {bar(t * 3, col, t * 0.8, 0.75)}
      {bar(t * 0.5, "#FFFFFF", 1.5, 1)}
    </AbsoluteFill>
  );
};
