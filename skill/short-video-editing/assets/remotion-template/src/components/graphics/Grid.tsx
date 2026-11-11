// The animated backdrop of card scenes: a net of fine lines on a deep gradient, blown by a slow wind like a
// banner (the "red checkered cloth" of agency pitch videos). A pure function of the frame: every line point is
// displaced by two travelling waves, with soft light and shade drifting over it. Colours come from the theme.
import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { frame as size, grid, palette } from "../../theme";

const COLS = Math.ceil(size.width / grid.cell) + 3;
const ROWS = Math.ceil(size.height / grid.cell) + 3;
const STEPS = 28; // segments per line: smooth enough for the wave lengths below

// Where the wind pushes the point (x, y) at time t (seconds). Stronger toward the bottom, like a hanging cloth.
const warp = (x: number, y: number, t: number): [number, number] => {
  const k = grid.speed;
  const a = grid.amplitude * (0.55 + 0.9 * (y / size.height));
  const dx = a * Math.sin(y * 0.0075 + t * 1.5 * k + x * 0.0021) + a * 0.5 * Math.sin(y * 0.0033 - t * 0.9 * k);
  const dy = a * 0.8 * Math.sin(x * 0.0068 - t * 1.2 * k + y * 0.0016) + a * 0.45 * Math.sin(x * 0.0029 + t * 0.7 * k);
  return [x + dx, y + dy];
};

const line = (pts: [number, number][]) => pts.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)}`).join(" ");

export const GridBackground: React.FC<{ offset?: number }> = ({ offset = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = (frame + offset) / fps;
  const cell = grid.cell;
  const horizontals: string[] = [];
  const verticals: string[] = [];
  for (let j = -1; j < ROWS; j++) {
    const y = j * cell;
    const pts: [number, number][] = [];
    for (let s = 0; s <= STEPS; s++) pts.push(warp(-cell + (s / STEPS) * (size.width + 2 * cell), y, t));
    horizontals.push(line(pts));
  }
  for (let i = -1; i < COLS; i++) {
    const x = i * cell;
    const pts: [number, number][] = [];
    for (let s = 0; s <= STEPS; s++) pts.push(warp(x, -cell + (s / STEPS) * (size.height + 2 * cell), t));
    verticals.push(line(pts));
  }
  const all = [...horizontals, ...verticals];
  // Slow drifts of light: a warm bloom near the top, a deeper one low, and a diagonal sheen sweeping across.
  const bloomA = `radial-gradient(ellipse 75% 34% at ${50 + 26 * Math.sin(t * 0.55)}% ${26 + 8 * Math.sin(t * 0.43)}%, rgba(255,80,80,0.26), transparent 72%)`;
  const bloomB = `radial-gradient(ellipse 80% 40% at ${50 + 30 * Math.sin(t * 0.37 + 2)}% ${78 + 7 * Math.sin(t * 0.5)}%, rgba(255,40,70,0.3), transparent 70%)`;
  const sheen = `linear-gradient(112deg, transparent ${28 + 14 * Math.sin(t * 0.5)}%, rgba(255,255,255,0.075) ${44 + 14 * Math.sin(t * 0.5)}%, transparent ${60 + 14 * Math.sin(t * 0.5)}%)`;
  return (
    <AbsoluteFill style={{ background: `linear-gradient(180deg, ${palette.ink} 0%, ${palette.navy} 52%, ${palette.royal} 135%)` }}>
      <AbsoluteFill style={{ background: bloomA }} />
      <AbsoluteFill style={{ background: bloomB }} />
      <svg width={size.width} height={size.height} style={{ position: "absolute", inset: 0 }}>
        <g fill="none" strokeLinecap="round" strokeLinejoin="round">
          <g stroke="rgba(255,120,120,0.10)" strokeWidth={9}>
            {all.map((d, i) => (
              <path key={`g${i}`} d={d} />
            ))}
          </g>
          <g stroke="rgba(255,190,190,0.34)" strokeWidth={2.2}>
            {all.map((d, i) => (
              <path key={`l${i}`} d={d} />
            ))}
          </g>
        </g>
      </svg>
      <AbsoluteFill style={{ background: sheen }} />
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 95% 80% at 50% 50%, transparent 55%, rgba(0,0,0,0.42) 100%)" }} />
    </AbsoluteFill>
  );
};
