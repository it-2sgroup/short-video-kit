// Product callout: dot pops on the part, leader line draws out, frosted label slides in from the
// side margin. Coordinates are fractions of the frame so they survive any resolution.
import React from "react";
import { AbsoluteFill, interpolate, useVideoConfig } from "remotion";
import { evolvePath } from "@remotion/paths";
import type { Overlay } from "../../project";
import { fonts, frame as size, palette, safe } from "../../theme";
import { clamp, pop, useEnterExit } from "../anim";

export type CalloutProps = { label: string; target: [number, number]; side?: "left" | "right"; labelY?: number };

export const Callout: React.FC<{ ov: Overlay; dur: number; instant: boolean }> = ({ ov, dur, instant }) => {
  const { fps } = useVideoConfig();
  const p = (ov.props ?? {}) as CalloutProps;
  const { frame, exit } = useEnterExit(dur, { instant });
  const tx = p.target[0] * size.width;
  const ty = p.target[1] * size.height;
  const side = p.side ?? (tx > size.width / 2 ? "left" : "right");
  const ly = (p.labelY ?? p.target[1]) * size.height;
  const labelW = 380;
  const lx = side === "left" ? safe.left + labelW : safe.right - labelW; // inner edge of the label
  const d = `M ${tx} ${ty} L ${lx} ${ly}`;

  const dot = instant ? 1 : pop(frame, fps, 0);
  const line = instant ? 1 : interpolate(frame, [4, 14], [0, 1], clamp);
  const label = instant ? 1 : interpolate(frame, [10, 20], [0, 1], clamp);
  const path = evolvePath(line, d);

  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <svg width={size.width} height={size.height} style={{ position: "absolute", inset: 0 }}>
        <path d={d} stroke={palette.white} strokeWidth={4} fill="none" strokeLinecap="round" strokeDasharray={path.strokeDasharray} strokeDashoffset={path.strokeDashoffset} style={{ filter: "drop-shadow(0 2px 6px rgba(0,0,0,0.45))" }} />
        <circle cx={tx} cy={ty} r={22 * dot} fill="rgba(255,255,255,0.35)" />
        <circle cx={tx} cy={ty} r={10 * dot} fill={palette.white} />
      </svg>
      <div
        style={{
          position: "absolute",
          top: ly - 40,
          left: side === "left" ? safe.left : undefined,
          right: side === "right" ? size.width - safe.right : undefined,
          width: labelW, // fixed, so the leader line always meets the label's inner edge
          boxSizing: "border-box",
          textAlign: side === "left" ? "left" : "right",
          padding: "10px 20px",
          borderRadius: 18,
          background: "linear-gradient(160deg, rgba(255,255,255,0.95), rgba(226,236,250,0.9))",
          boxShadow: "0 10px 30px rgba(20,40,80,0.3)",
          fontFamily: fonts.sans,
          fontWeight: 800,
          fontSize: 34,
          lineHeight: 1.15,
          color: palette.navy,
          opacity: label,
          translate: `${(1 - label) * (side === "left" ? -30 : 30)}px 0`,
        }}
      >
        {p.label}
      </div>
    </AbsoluteFill>
  );
};
