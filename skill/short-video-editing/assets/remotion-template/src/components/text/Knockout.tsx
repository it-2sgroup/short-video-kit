// Knockout text: a colour plate over the whole frame with the words cut out of it, so the footage shows through the letters. The
// letters are a hole in an SVG mask, so the footage underneath keeps playing inside them. Optional zoom-through: the letters grow about a
// point inside one stroke until their hole fills the frame, which is a reveal of the next picture.
import React, { useId } from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import type { Overlay } from "../../project";
import { fonts, frame as size, motion, palette } from "../../theme";
import { clamp, fitSize } from "../anim";

export type KnockoutProps = {
  text: string | string[];
  color?: string; // the plate (default the theme's ink)
  opacity?: number; // plate opacity: 1 hides the picture outside the letters, 0.85 lets it ghost through
  size?: number; // font size in px (default: fits 940 px, at most 340)
  at?: [number, number]; // centre of the words, as fractions of the frame
  stroke?: string; // a thin outline round the letters, for busy footage
  zoom?: number; // end scale of the zoom-through (40 fills the frame); 1 = none
  through?: [number, number]; // the point the zoom grows about, as fractions of the frame: on a stroke of a letter, its hole then fills the frame (default: the middle letter; the plate also fades over the last 30% of the zoom)
  zoomFrames?: number; // length of the zoom at the end of the overlay (default 20)
};

type Base = { ov: Overlay; dur: number; instant: boolean };

export const Knockout: React.FC<Base> = ({ ov, dur, instant }) => {
  const p = (ov.props ?? {}) as KnockoutProps;
  const frame = useCurrentFrame();
  const id = useId().replace(/[^\w]/g, "");
  const rows = (Array.isArray(p.text) ? p.text : String(p.text ?? "").split(" / ")).map(String);
  const px = p.size ?? fitSize(rows.reduce((a, b) => (b.length > a.length ? b : a), ""), 940, 340, 90, 0.74); // a heavy uppercase letter is ~0.74 em wide
  const lh = px * 1.02;
  const [ax, ay] = p.at ?? [0.5, 0.45];
  const cx = ax * size.width;
  const cy = ay * size.height;
  // Default zoom point: the middle letter of the longest row, taking every letter as 0.6 em wide (the point must sit on a stroke, not in a gap).
  const longest = rows.reduce((a, b) => (b.length > a ? b.length : a), 0);
  const rowY = cy + (rows.findIndex((r) => r.length === longest) - (rows.length - 1) / 2) * lh;
  const [tx, ty] = p.through ? [p.through[0] * size.width, p.through[1] * size.height] : [cx + ((Math.floor(longest / 2) + 0.5) / Math.max(1, longest) - 0.5) * longest * 0.6 * px, rowY];

  // The plate fades in over 6 frames while the letters settle from 1.1x; at the end the letters grow about the through point, easing in.
  const enter = instant ? 1 : motion.easeOut(interpolate(frame, [0, 6], [0, 1], clamp));
  const zoomLen = Math.min(p.zoomFrames ?? 20, dur);
  const zoomK = (p.zoom ?? 1) > 1 ? motion.easeInOut(interpolate(frame, [dur - zoomLen, dur], [0, 1], clamp)) : 0;
  const scale = (1.1 - 0.1 * enter) * Math.exp(Math.log(Math.max(1, p.zoom ?? 1)) * zoomK);
  const grow = `translate(${tx} ${ty}) scale(${scale}) translate(${-tx} ${-ty})`;
  const words = (extra: React.SVGProps<SVGTextElement>) => (
    <text x={cx} y={cy - ((rows.length - 1) * lh) / 2} textAnchor="middle" dominantBaseline="central" fontFamily={fonts.sans} fontWeight={900} fontSize={px} {...extra}>
      {rows.map((r, i) => (
        <tspan key={i} x={cx} dy={i === 0 ? 0 : lh}>
          {r}
        </tspan>
      ))}
    </text>
  );
  return (
    <AbsoluteFill>
      <svg width={size.width} height={size.height} style={{ position: "absolute", inset: 0 }}>
        <defs>
          <mask id={`ko${id}`} maskUnits="userSpaceOnUse" x={0} y={0} width={size.width} height={size.height}>
            <rect width={size.width} height={size.height} fill="#fff" />
            <g transform={grow}>{words({ fill: "#000" })}</g>
          </mask>
        </defs>
        <rect width={size.width} height={size.height} fill={p.color ?? palette.ink} opacity={(p.opacity ?? 1) * enter * (1 - Math.max(0, (zoomK - 0.7) / 0.3))} mask={`url(#ko${id})`} />
        {p.stroke ? <g transform={grow} opacity={enter}>{words({ fill: "none", stroke: p.stroke, strokeWidth: Math.max(2, px / 70) })}</g> : null}
      </svg>
    </AbsoluteFill>
  );
};
