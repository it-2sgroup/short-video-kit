// Count-up price with an optional struck-through old price and a small label.
import React from "react";
import { AbsoluteFill, Easing, interpolate } from "remotion";
import type { Overlay } from "../../project";
import { fonts, toneColor, zones } from "../../theme";
import { clamp, useEnterExit } from "../anim";
import { GradientText, OutlineText } from "../text/primitives";

export type PriceProps = { value: number; unit?: string; label?: string; old?: string; prefix?: string; decimals?: number };

export const Price: React.FC<{ ov: Overlay; dur: number; instant: boolean }> = ({ ov, dur, instant }) => {
  const p = (ov.props ?? {}) as PriceProps;
  const { frame, enter, exit } = useEnterExit(dur, { instant });
  const count = instant ? 1 : interpolate(frame, [0, 24], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  const pulse = interpolate(frame, [24, 27, 30], [1, 1.08, 1], clamp);
  const strike = interpolate(frame, [14, 22], [0, 1], clamp);
  const decimals = p.decimals ?? 0; // 1 for "5,2 tỷ" (value=5.2; decimals=1; unit= tỷ)
  const vnd = new Intl.NumberFormat("vi-VN", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
  const value = (p.value ?? 0) * count;
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <div style={{ position: "absolute", top: zones[ov.zone ?? "lower"], left: 60, width: 840, display: "flex", flexDirection: "column", alignItems: "center", opacity: enter }}>
        {p.label ? <OutlineText size={46} weight={700}>{p.label}</OutlineText> : null}
        <div style={{ scale: String(pulse), display: "flex", alignItems: "baseline", gap: 10 }}>
          {p.prefix ? <OutlineText size={60} weight={800}>{p.prefix}</OutlineText> : null}
          <GradientText size={190} family={fonts.number} weight={400} stops={`#FFF6C9 0%, ${toneColor.cta} 100%`} tracking="0" lineHeight={1}>
            {vnd.format(value)}
          </GradientText>
          {p.unit ? <OutlineText size={84} weight={800} color={toneColor.cta}>{p.unit}</OutlineText> : null}
        </div>
        {p.old ? (
          <div style={{ position: "relative", marginTop: 6 }}>
            <OutlineText size={48} weight={700}>{p.old}</OutlineText>
            <div style={{ position: "absolute", left: -6, right: -6, top: "52%", height: 6, background: toneColor.before, transformOrigin: "left", scale: `${strike} 1`, borderRadius: 3 }} />
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
