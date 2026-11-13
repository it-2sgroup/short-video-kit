// Progress bar (fills across the overlay's life, e.g. "Ready in 20 minutes") and a lower-third name tag.
import React from "react";
import { AbsoluteFill, interpolate } from "remotion";
import type { Overlay } from "../../project";
import { fonts, palette, safe, toneColor, zones } from "../../theme";
import { pickFont } from "../../fonts";
import { clamp, useEnterExit } from "../anim";
import { OutlineText } from "../text/primitives";

type Base = { ov: Overlay; dur: number; instant: boolean };

export const Progress: React.FC<Base> = ({ ov, dur, instant }) => {
  const p = (ov.props ?? {}) as { label?: string };
  const { frame, enter, exit } = useEnterExit(dur, { instant });
  const fill = interpolate(frame, [6, dur - 8], [0, 1], clamp);
  return (
    <AbsoluteFill style={{ opacity: Math.min(enter, exit) }}>
      <div style={{ position: "absolute", top: ov.zone ? zones[ov.zone] : safe.top + 20, left: safe.left + 20, right: 1080 - safe.right + 20, display: "flex", flexDirection: "column", gap: 12 }}>
        {p.label ? <OutlineText size={44} weight={800}>{p.label}</OutlineText> : null}
        <div style={{ height: 18, borderRadius: 9, background: "rgba(255,255,255,0.35)", overflow: "hidden", boxShadow: "0 4px 14px rgba(0,0,0,0.35)" }}>
          <div style={{ height: "100%", width: `${fill * 100}%`, borderRadius: 9, background: `linear-gradient(90deg, ${palette.sky}, ${toneColor.after})` }} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const LowerThird: React.FC<Base> = ({ ov, dur, instant }) => {
  const p = (ov.props ?? {}) as { name: string; role?: string; font?: string };
  const { frame, exit } = useEnterExit(dur, { instant });
  const nf = pickFont(p.font, 900, fonts.sans);
  const rf = pickFont(p.font, 600, fonts.sans);
  const bar = instant ? 1 : interpolate(frame, [0, 8], [0, 1], clamp);
  const text = instant ? 1 : interpolate(frame, [5, 13], [0, 1], clamp);
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <div style={{ position: "absolute", top: zones[ov.zone ?? "lower"], left: safe.left, display: "flex", alignItems: "stretch", gap: 18 }}>
        <div style={{ width: 10, borderRadius: 5, background: toneColor.cta, transformOrigin: "top", scale: `1 ${bar}` }} />
        <div style={{ opacity: text, translate: `${(1 - text) * -20}px 0`, textAlign: "left" }}>
          <div style={{ fontFamily: nf.family, fontWeight: nf.weight, fontSize: 56, color: palette.white, filter: "drop-shadow(0 4px 12px rgba(0,0,0,0.6))" }}>{p.name}</div>
          {p.role ? <div style={{ fontFamily: rf.family, fontWeight: rf.weight, fontSize: 36, color: palette.ice, filter: "drop-shadow(0 3px 8px rgba(0,0,0,0.6))" }}>{p.role}</div> : null}
        </div>
      </div>
    </AbsoluteFill>
  );
};
