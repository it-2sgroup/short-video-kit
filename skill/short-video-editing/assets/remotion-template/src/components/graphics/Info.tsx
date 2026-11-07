// Information graphics: a row of facts with icons (`specs`), a dropping location pin (`pin`), a room or
// item label (`label`), a count-up figure (`stat`) and growing bars (`chart`). No boxes behind text:
// outlined type and soft shadows, like every other text in the kit (references/typography.md).
import React from "react";
import { AbsoluteFill, Easing, interpolate, useVideoConfig } from "remotion";
import type { Overlay } from "../../project";
import { fonts, frame as size, info, palette, safe, toneColor, zones } from "../../theme";
import { clamp, pop, smooth, useEnterExit } from "../anim";
import { GradientText, OutlineText } from "../text/primitives";

type Base = { ov: Overlay; dur: number; instant: boolean };

// 24x24 stroke icons. Names are what a plan writes before the colon: `items=area:85 m² / bed:3 PN`.
const ICONS: Record<string, string> = {
  area: "M4 9V4h5 M15 4h5v5 M20 15v5h-5 M9 20H4v-5 M8 8l8 8 M16 8l-8 8",
  bed: "M3 18V7 M3 14h18v4 M21 14v-2a3 3 0 0 0-3-3h-7v5 M6.5 11.5a1.5 1.5 0 1 0 0-.01",
  bath: "M4 12h16v2a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5z M6 12V6a2 2 0 0 1 4 0 M7 19l-1 2 M17 19l1 2",
  compass: "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18 M15.5 8.5l-2 5-5 2 2-5z",
  car: "M5 16h14v-4l-2-5H7l-2 5z M5 12h14 M7 16v2 M17 16v2 M8 14h.01 M16 14h.01",
  floor: "M4 20h4v-4h4v-4h4V8h4 M4 20h16",
  tree: "M12 21v-6 M12 3l6 9H6z M9 15h6",
  pool: "M3 16c2 0 2-1.5 4.5-1.5S10 16 12 16s2-1.5 4.5-1.5S19 16 21 16 M3 20c2 0 2-1.5 4.5-1.5S10 20 12 20s2-1.5 4.5-1.5S19 20 21 20 M8 13V5a2 2 0 0 1 4 0 M14 13V5",
  clock: "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18 M12 7v5l3 2",
  tag: "M3 12V4h8l10 10-8 8z M7.5 8a.5.5 0 1 0 0-.01",
  pin: "M12 21s-7-6.5-7-12a7 7 0 0 1 14 0c0 5.5-7 12-7 12z M12 9a2 2 0 1 0 0-.01",
  star: "M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z",
};

const Icon: React.FC<{ name: string; px: number; color?: string }> = ({ name, px, color }) => (
  <svg width={px} height={px} viewBox="0 0 24 24" style={{ filter: "drop-shadow(0 3px 8px rgba(0,0,0,0.5))", flexShrink: 0 }}>
    <path d={ICONS[name] ?? ICONS.star} fill="none" stroke={color ?? palette.white} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const list = (v: unknown): string[] => (Array.isArray(v) ? v.map(String) : v ? [String(v)] : []);
const splitIcon = (item: string): [string | null, string] => {
  const m = item.match(/^(\w+):\s*(.+)$/);
  return m && ICONS[m[1]] ? [m[1], m[2]] : [null, item];
};
const top = (ov: Overlay, fallback: keyof typeof zones) => zones[ov.zone ?? fallback];

// specs: up to 6 facts with icons, two per row when more than 3, each popping in 5 frames apart.
export const Specs: React.FC<Base> = ({ ov, dur, instant }) => {
  const { fps } = useVideoConfig();
  const p = (ov.props ?? {}) as { items?: string[] | string; title?: string };
  const items = list(p.items).slice(0, 6);
  const { frame, exit } = useEnterExit(dur, { instant });
  const perRow = items.length > 3 ? 2 : items.length;
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <div style={{ position: "absolute", top: top(ov, "upper"), left: safe.left, width: safe.right - safe.left, display: "flex", flexDirection: "column", alignItems: "center", gap: 18 }}>
        {p.title ? <OutlineText size={50} weight={900}>{p.title}</OutlineText> : null}
        <div style={{ display: "grid", gridTemplateColumns: `repeat(${perRow}, auto)`, columnGap: info.specGap * 2, rowGap: info.specGap, justifyContent: "center" }}>
          {items.map((it, i) => {
            const [icon, text] = splitIcon(it);
            const k = instant ? 1 : pop(frame, fps, 4 + i * 5);
            return (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 14, opacity: Math.min(1, k * 1.5), scale: String(interpolate(k, [0, 1], [0.7, 1])) }}>
                {icon ? <Icon name={icon} px={info.iconSize} color={toneColor.product} /> : null}
                <OutlineText size={info.labelSize + 4} weight={800} align="left">{text}</OutlineText>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// pin: a map pin drops (with a ring on landing) beside the place name and a second line (district,
// address, distance). Default position: the top-left of the top zone.
export const Pin: React.FC<Base> = ({ ov, dur, instant }) => {
  const { fps } = useVideoConfig();
  const p = (ov.props ?? {}) as { title?: string; sub?: string; at?: [number, number] };
  const { frame, exit } = useEnterExit(dur, { instant });
  const x = (p.at?.[0] ?? 0.1) * size.width;
  const y = p.at ? p.at[1] * size.height : top(ov, "top") + 40;
  const drop = instant ? 1 : smooth(frame, fps, 0, 12);
  const ring = instant ? 1 : interpolate(frame, [11, 26], [0, 1], clamp);
  const text = instant ? 1 : interpolate(frame, [8, 18], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  const px = 84;
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <div style={{ position: "absolute", left: x - px / 2, top: y - px, translate: `0 ${(1 - drop) * -120}px`, opacity: Math.min(1, drop * 2) }}>
        <Icon name="pin" px={px} color={toneColor.cta} />
      </div>
      <div style={{ position: "absolute", left: x - 40 * (1 + ring), top: y - 8 - 10 * (1 + ring), width: 80 * (1 + ring), height: 20 * (1 + ring), borderRadius: "50%", border: `3px solid ${toneColor.cta}`, opacity: (1 - ring) * 0.8 }} />
      <div style={{ position: "absolute", left: x + px / 2 + 8, top: y - px + 6, maxWidth: safe.right - x - px, opacity: text, translate: `${(1 - text) * -24}px 0`, display: "flex", flexDirection: "column", gap: 4 }}>
        {p.title ? <OutlineText size={50} weight={900} align="left">{p.title}</OutlineText> : null}
        {p.sub ? <OutlineText size={34} weight={600} color={palette.ice} align="left">{p.sub}</OutlineText> : null}
      </div>
    </AbsoluteFill>
  );
};

// label: a quiet tag for a room, a dish or an item (name + one detail), with a line drawing under it.
// Default: bottom-left of the picture, above the caption band.
export const Label: React.FC<Base> = ({ ov, dur, instant }) => {
  const p = (ov.props ?? {}) as { text?: string; sub?: string; at?: [number, number]; align?: "left" | "right" };
  const { frame, exit } = useEnterExit(dur, { instant });
  const right = p.align === "right";
  const x = (p.at?.[0] ?? (right ? 0.8 : 0.08)) * size.width;
  const y = p.at ? p.at[1] * size.height : (ov.zone ? zones[ov.zone] : 1130);
  const line = instant ? 1 : interpolate(frame, [0, 10], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  const text = instant ? 1 : interpolate(frame, [4, 13], [0, 1], clamp);
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <div style={{ position: "absolute", top: y, left: right ? undefined : x, right: right ? size.width - x : undefined, display: "flex", flexDirection: "column", alignItems: right ? "flex-end" : "flex-start", gap: 6 }}>
        <div style={{ opacity: text, translate: `0 ${(1 - text) * 14}px` }}>
          <OutlineText size={info.labelSize + 6} weight={900} align={right ? "right" : "left"}>{p.text}</OutlineText>
        </div>
        <div style={{ height: 5, width: 200, borderRadius: 3, background: toneColor.cta, transformOrigin: right ? "right" : "left", scale: `${line} 1`, boxShadow: "0 2px 8px rgba(0,0,0,0.4)" }} />
        {p.sub ? (
          <div style={{ opacity: text }}>
            <OutlineText size={info.labelSize - 6} weight={600} color={palette.ice} align={right ? "right" : "left"}>{p.sub}</OutlineText>
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

const number = (v: number, decimals: number) =>
  new Intl.NumberFormat("vi-VN", { minimumFractionDigits: decimals, maximumFractionDigits: decimals }).format(v);

// stat: one figure counting up (vi-VN format) with a unit and a label: "85 m²", "5 phút", "73%".
export const Stat: React.FC<Base> = ({ ov, dur, instant }) => {
  const p = (ov.props ?? {}) as { value?: number; unit?: string; label?: string; prefix?: string; decimals?: number };
  const { frame, enter, exit } = useEnterExit(dur, { instant });
  const k = instant ? 1 : interpolate(frame, [0, 22], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  const pulse = interpolate(frame, [22, 25, 28], [1, 1.06, 1], clamp);
  const decimals = p.decimals ?? 0;
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <div style={{ position: "absolute", top: top(ov, "upper"), left: safe.left, width: safe.right - safe.left, display: "flex", flexDirection: "column", alignItems: "center", opacity: enter }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 10, scale: String(pulse) }}>
          {p.prefix ? <OutlineText size={60} weight={800}>{p.prefix}</OutlineText> : null}
          <GradientText size={info.statSize} family={fonts.number} weight={400} stops={`${palette.white} 0%, ${toneColor.cta} 100%`} tracking="0" lineHeight={1}>
            {number((p.value ?? 0) * k, decimals)}
          </GradientText>
          {p.unit ? <OutlineText size={70} weight={800} color={toneColor.cta}>{p.unit}</OutlineText> : null}
        </div>
        {p.label ? <OutlineText size={44} weight={700}>{p.label}</OutlineText> : null}
      </div>
    </AbsoluteFill>
  );
};

// chart: 2-5 horizontal bars growing in turn, each with its label and its value counting up.
// `items=Tự làm#45 / Thuê dịch vụ#120`, `unit= phút`, `title=`. Bars scale to the largest value.
export const Chart: React.FC<Base> = ({ ov, dur, instant }) => {
  const p = (ov.props ?? {}) as { items?: string[] | string; unit?: string; title?: string; highlight?: number };
  const rows = list(p.items).slice(0, 5).map((s) => {
    const [label, v] = s.split("#");
    return { label: label.trim(), value: Number(v) || 0 };
  });
  const max = Math.max(1, ...rows.map((r) => r.value));
  const { frame, exit } = useEnterExit(dur, { instant });
  const best = p.highlight ?? rows.findIndex((r) => r.value === max) + 1;
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <div style={{ position: "absolute", top: top(ov, "upper"), left: (size.width - info.chartWidth) / 2 - 30, width: info.chartWidth, display: "flex", flexDirection: "column", gap: info.barGap }}>
        {p.title ? <OutlineText size={46} weight={900} align="left">{p.title}</OutlineText> : null}
        {rows.map((r, i) => {
          const grow = instant ? 1 : interpolate(frame, [4 + i * 6, 22 + i * 6], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
          const color = i + 1 === best ? toneColor.cta : palette.sky;
          return (
            <div key={i} style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <OutlineText size={36} weight={800} align="left">{r.label}</OutlineText>
                <OutlineText size={36} weight={800} color={color}>{`${number(r.value * grow, 0)}${p.unit ?? ""}`}</OutlineText>
              </div>
              <div style={{ height: info.barHeight, borderRadius: info.barHeight / 2, background: "rgba(255,255,255,0.22)", overflow: "hidden", boxShadow: "0 4px 14px rgba(0,0,0,0.35)" }}>
                <div style={{ height: "100%", width: `${(r.value / max) * grow * 100}%`, borderRadius: info.barHeight / 2, background: `linear-gradient(90deg, ${palette.white}, ${color})` }} />
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
