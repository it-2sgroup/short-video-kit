// Brand and proof graphics of the agency-pitch look: the logo that blurs in, a "5 -> 10" counter, the little
// pictograms (target, megaphone, !!!, search, check), the hand-circled label, and the RAW / FINAL pair of cards.
import React from "react";
import { AbsoluteFill, Img, OffthreadVideo, interpolate, spring, staticFile, useVideoConfig } from "remotion";
import { evolvePath } from "@remotion/paths";
import type { Overlay } from "../../project";
import { card, fonts, frame as size, palette, textShadow, zones } from "../../theme";
import { clamp, pop, useEnterExit } from "../anim";
import { ScatterText } from "../text/Phrase";
import { Glyph } from "./Glyph";

type Base = { ov: Overlay; dur: number; instant: boolean };

// ------------------------------------------------------------------------------------------------ logo
export type LogoProps = { src?: string; at?: [number, number]; width?: number; tint?: "white"; hold?: boolean };

// The brand mark (public/images/logo.png, a transparent PNG) arriving out of a motion blur: it starts large, smeared
// sideways and soft, and snaps sharp. Use it on the beats that name the brand and at the end.
export const Logo: React.FC<Base> = ({ ov, dur, instant }) => {
  const p = (ov.props ?? {}) as LogoProps;
  const { frame, exit: fade } = useEnterExit(dur, { instant, exit: 8 });
  const exit = p.hold ? 1 : fade; // hold: stay to the very last frame (an end card does not fade)
  const k = instant ? 1 : interpolate(frame, [0, 14], [0, 1], { ...clamp, easing: (t) => 1 - Math.pow(1 - t, 3) });
  const [ax, ay] = p.at ?? [0.5, 0.17];
  const width = p.width ?? 400;
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <div
        style={{
          position: "absolute",
          left: ax * size.width,
          top: ay * size.height,
          translate: "-50% -50%",
          width,
          opacity: Math.min(1, k * 2.4),
          filter: `${p.tint === "white" ? "brightness(0) invert(1) " : ""}blur(${(1 - k) * 22}px) drop-shadow(0 8px 18px rgba(60,0,10,0.35))`,
          transform: `scale(${1 + 0.45 * (1 - k)}, ${1 + 0.05 * (1 - k)})`,
        }}
      >
        <Img src={staticFile(p.src ?? "images/logo.png")} style={{ width: "100%", display: "block" }} />
      </div>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------------------------------------ counter
export type CounterProps = { from: number; to: number; label?: string; at?: [number, number] };

// "5 -> 10": the first number pops, the arrow draws itself, the second number pops, the unit slides up.
export const Counter: React.FC<Base> = ({ ov, dur, instant }) => {
  const { fps } = useVideoConfig();
  const p = (ov.props ?? {}) as CounterProps;
  const { frame, exit } = useEnterExit(dur, { instant, exit: 8 });
  const [ax, ay] = p.at ?? [0.5, 0.0];
  const top = p.at ? ay * size.height : zones[ov.zone ?? "top"] + 110;
  const a = pop(frame, fps, 0);
  const draw = evolvePath(interpolate(frame, [6, 18], [0, 1], clamp), "M 0 50 L 190 50");
  const head = interpolate(frame, [15, 21], [0, 1], clamp);
  const b = pop(frame, fps, 17);
  const unit = interpolate(frame, [22, 32], [0, 1], { ...clamp, easing: (t) => 1 - Math.pow(1 - t, 3) });
  const num = (v: number, k: number) => (
    <div style={{ scale: String(Math.max(0, k)), fontFamily: fonts.number, fontSize: 190, lineHeight: 1, color: palette.white, WebkitTextStroke: `10px ${palette.royal}`, paintOrder: "stroke fill", filter: textShadow }}>{v}</div>
  );
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <div style={{ position: "absolute", left: ax * size.width, top, translate: "-50% 0", display: "flex", alignItems: "center", gap: 18 }}>
        {num(p.from, a)}
        <svg width={230} height={100} viewBox="-10 0 230 100" style={{ overflow: "visible" }}>
          {[{ w: 26, c: palette.white }, { w: 15, c: palette.royal }].map((s, i) => (
            <g key={i} fill="none" stroke={s.c} strokeWidth={s.w} strokeLinecap="round" strokeLinejoin="round">
              <path d="M 0 50 L 190 50" strokeDasharray={draw.strokeDasharray} strokeDashoffset={draw.strokeDashoffset} />
              <path d="M 150 12 L 196 50 L 150 88" opacity={head} />
            </g>
          ))}
        </svg>
        {num(p.to, b)}
      </div>
      {p.label ? (
        <div style={{ position: "absolute", left: ax * size.width, top: top + 200, translate: "-50% 0", opacity: unit, transform: `translateY(${(1 - unit) * 30}px)` }}>
          <ScatterText text={p.label} size={70} family={fonts.condensed} fill={palette.white} stroke={palette.royal} weight={900} width={0.2} shadow="drop-shadow(0 6px 10px rgba(30,0,6,0.45))" k={1} x={0} />
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------------------------------------ icons
export type IconProps = { name: string; at?: [number, number]; size?: number; rotate?: number };

// A pictogram that pops in at a point of the frame and wobbles slightly: target, megaphone, bang (!!!), search, check.
export const Icon: React.FC<Base> = ({ ov, dur, instant }) => {
  const { fps } = useVideoConfig();
  const p = (ov.props ?? {}) as IconProps;
  const { frame, exit } = useEnterExit(dur, { instant, exit: 6 });
  const k = instant ? 1 : pop(frame, fps, 0);
  const [ax, ay] = p.at ?? [0.5, 0.18];
  const s = p.size ?? 150;
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <svg
        viewBox="0 0 110 100"
        width={s * 1.1}
        height={s}
        style={{
          position: "absolute",
          left: ax * size.width,
          top: ay * size.height,
          translate: "-50% -50%",
          scale: String(k),
          rotate: `${(p.rotate ?? -6) + Math.sin(frame / 9) * 3}deg`,
          filter: "drop-shadow(0 8px 12px rgba(30,0,6,0.45))",
          overflow: "visible",
        }}
      >
        <Glyph name={p.name} />
      </svg>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------------------------------------ circled
export type CircledProps = { text: string; at?: [number, number]; icon?: string };

// A label that a red hand-drawn ellipse is drawn around, with a pictogram popping in below it ("HỖ TRỢ" + search).
export const Circled: React.FC<Base> = ({ ov, dur, instant }) => {
  const { fps } = useVideoConfig();
  const p = (ov.props ?? {}) as CircledProps;
  const { frame, exit } = useEnterExit(dur, { instant, exit: 6 });
  const [ax, ay] = p.at ?? [0.5, 0.2];
  const fs = 54;
  const chars = Array.from(p.text);
  const shown = Math.min(chars.length, Math.max(0, Math.floor((frame - 8) / 0.9)));
  const w = chars.length * fs * 0.66 + 70;
  const h = fs * 1.5;
  const rx = w / 2 + 26;
  const ry = h / 2 + 18;
  const ring = `M ${rx} 0 C ${rx} ${-ry * 1.35}, ${-rx * 1.04} ${-ry * 1.4}, ${-rx * 1.03} 0 C ${-rx} ${ry * 1.4}, ${rx * 1.08} ${ry * 1.35}, ${rx * 0.92} ${-ry * 0.4}`;
  const draw = evolvePath(interpolate(frame, [0, 12], [0, 1], clamp), ring);
  const icon = pop(frame, fps, 16);
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      {/* the anchor is the centre of the label; the ring and the icon are positioned from it */}
      <div style={{ position: "absolute", left: ax * size.width, top: ay * size.height, width: 0, height: 0 }}>
        <svg width={2 * rx + 60} height={2 * ry + 60} viewBox={`${-rx - 30} ${-ry - 30} ${2 * rx + 60} ${2 * ry + 60}`} style={{ position: "absolute", left: -(rx + 30), top: -(ry + 30), overflow: "visible", filter: "drop-shadow(0 4px 8px rgba(30,0,6,0.4))" }}>
          <path d={ring} stroke={palette.royal} strokeWidth={8} fill="none" strokeLinecap="round" strokeDasharray={draw.strokeDasharray} strokeDashoffset={draw.strokeDashoffset} />
        </svg>
        <div style={{ position: "absolute", left: -w / 2, top: -h / 2, width: w, height: h, borderRadius: 14, background: palette.white, boxShadow: "0 8px 20px rgba(30,0,6,0.3)", fontFamily: fonts.sans, fontWeight: 900, fontSize: fs, color: palette.royal, display: "flex", alignItems: "center", justifyContent: "center", whiteSpace: "nowrap" }}>
          <span style={{ visibility: "hidden" }}>{p.text}</span>
          <span style={{ position: "absolute" }}>{chars.slice(0, shown).join("")}</span>
        </div>
        {p.icon ? (
          <svg viewBox="0 0 110 100" width={190} height={170} style={{ position: "absolute", left: -95, top: ry + 14, scale: String(icon), overflow: "visible", filter: "drop-shadow(0 8px 12px rgba(30,0,6,0.45))" }}>
            <Glyph name={p.icon} />
          </svg>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------------------------------------ raw / final
export type RawFinalProps = { raw: string; final: string; at: number; rawLabel?: string; finalLabel?: string; saturate?: number; contrast?: number; brightness?: number };

// Two cards side by side playing the same moment: the unedited clip (public/raw/…) and the finished look. It is the
// honest version of "before/after": the same take, only the edit differs. Use it with a card scene whose clip is null.
export const RawFinal: React.FC<Base> = ({ ov, dur, instant }) => {
  const { fps } = useVideoConfig();
  const p = (ov.props ?? {}) as RawFinalProps;
  const { frame, exit } = useEnterExit(dur, { instant, exit: 8 });
  const a = spring({ frame, fps, config: { damping: 15, stiffness: 150 } });
  const b = spring({ frame: frame - 5, fps, config: { damping: 15, stiffness: 150 } });
  const w = 472;
  const h = Math.round((w * 16) / 9);
  const top = card.top + (card.height - h) / 2 + 20;
  const gap = 22;
  const left0 = (size.width - 2 * w - gap) / 2;
  const trim = Math.round(p.at * fps);
  const finalLook = `saturate(${p.saturate ?? 1}) contrast(${p.contrast ?? 1}) brightness(${p.brightness ?? 1})`;
  const cardBox = (x: number, k: number, src: string, label: string, hot: boolean, dir: number) => (
    <div style={{ position: "absolute", left: x + dir * (1 - k) * 700, top, width: w, height: h, borderRadius: 38, overflow: "hidden", boxShadow: card.shadow, outline: hot ? `7px solid ${palette.sky}` : undefined, outlineOffset: -1 }}>
      <OffthreadVideo src={staticFile(src)} trimBefore={trim} muted style={{ width: "100%", height: "100%", objectFit: "cover", filter: hot ? finalLook : undefined }} />
      <div style={{ position: "absolute", left: 0, right: 0, top: 22, display: "flex", justifyContent: "center" }}>
        <ScatterText text={label} size={62} family={fonts.condensed} fill={hot ? palette.sky : palette.white} stroke={palette.ink} weight={900} width={0.16} shadow="drop-shadow(0 6px 10px rgba(0,0,0,0.5))" k={1} x={0} />
      </div>
    </div>
  );
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      {cardBox(left0, a, p.raw, p.rawLabel ?? "RAW", false, -1)}
      {cardBox(left0 + w + gap, b, p.final, p.finalLabel ?? "FINAL", true, 1)}
    </AbsoluteFill>
  );
};
