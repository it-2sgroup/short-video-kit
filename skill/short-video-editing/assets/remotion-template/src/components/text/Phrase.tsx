// Statement text: large lines that mirror the speech, shown the moment the speaker says it. Where Title is a calm heading,
// these move: letters that scatter in and fly apart again, a typed pill, an arc of echoing letters, one handwritten
// phrase. Everything is a pure function of the frame; sizes and colours come from the theme.
//   phrase  a white lead line over a loud red (or yellow) emphasis line, e.g. "Lead line" / "EMPHASIS LINE"
//   pill    a rounded label (white with red text, or red with white text) whose text types in
//   arc     curved letters with echoes fanning out behind them (the opening shout)
//   script  one handwritten phrase in the highlight colour (Pacifico), letters scatter in
//   tag     a small red label with outlined text, anchored over a card ("LABEL")
import React from "react";
import { AbsoluteFill, interpolate, spring, useVideoConfig } from "remotion";
import type { Overlay } from "../../project";
import { fonts, frame as size, palette, textShadow, zones } from "../../theme";
import { clamp, fitSize, pop, useEnterExit } from "../anim";
import { pickFont } from "../../fonts";
import { FxText, fxFrames, type FxName, type StrokeProps } from "./Fx";

type Base = { ov: Overlay; dur: number; instant: boolean };

// Back-compat name: a line of text with an effect (default scatter). The engine lives in Fx.tsx.
export const ScatterText: React.FC<StrokeProps & { text: string; k: number; x: number; seed?: number; spread?: number; fx?: FxName; frame?: number }> = ({ fx = "scatter", frame = 0, ...rest }) => (
  <FxText fx={fx} frame={frame} {...rest} />
);

const timing = (dur: number, enterF: number, exitF: number, frame: number) => ({
  k: interpolate(frame, [0, enterF], [0, 1], clamp),
  x: interpolate(frame, [dur - exitF, dur], [0, 1], clamp),
});

// ------------------------------------------------------------------------------------------------ phrase
// emphAt: seconds after the overlay starts when the emphasis line arrives (the lead line comes first); y: top of the block
// as a fraction of the frame height (default: just under the title strip). With no emph, only the lead line shows.
// fx / leadFx: the effect of the emphasis and the lead line (Fx.tsx: scatter drop wave elastic flip slam stamp glitch neon shine
// maskwipe split typewriter rise scramble blurin tracking slice popword flap strike draw). exit: scatter (letters fly apart) or fade.
// font / leadFont: a library font id (fonts.ts) for both lines / for the lead line alone; default: the sans lead over the condensed emphasis.
export type PhraseProps = { lead?: string; emph?: string; emphAt?: number; y?: number; emphColor?: "red" | "yellow" | "white"; fx?: FxName; leadFx?: FxName; enter?: "scatter" | "rise"; exit?: "scatter" | "fade"; font?: string; leadFont?: string };

export const Phrase: React.FC<Base> = ({ ov, dur, instant }) => {
  const p = (ov.props ?? {}) as PhraseProps;
  const { frame } = useEnterExit(dur, { instant });
  const { fps } = useVideoConfig();
  const emphFx: FxName = p.fx ?? (p.enter === "rise" ? "rise" : "scatter");
  const leadFx: FxName = p.leadFx ?? (p.enter === "rise" ? "rise" : "scatter");
  const exitMode = p.exit ?? "scatter";
  const top = p.y !== undefined ? p.y * size.height : zones[ov.zone ?? "top"] + 100;
  const emph = p.emph ?? "";
  const leadFont = pickFont(p.leadFont ?? p.font, 800, fonts.sans);
  const emphFont = pickFont(p.font, 900, fonts.condensed);
  const emphSize = fitSize(emph, 940, 118, 64, emphFont.ratio ?? 0.43);
  const emphF = Math.round((p.emphAt ?? 0.13) * fps); // frames before the emphasis line starts
  const emphFill = p.emphColor === "yellow" ? palette.sky : p.emphColor === "white" ? palette.white : palette.royal;
  const emphStroke = p.emphColor === "yellow" || p.emphColor === "white" ? palette.ink : palette.white;
  const lk = instant ? 1 : interpolate(frame, [0, fxFrames(leadFx, p.lead ?? "")], [0, 1], clamp);
  const ek = interpolate(frame, [emphF, emphF + fxFrames(emphFx, emph)], [0, 1], clamp);
  const exit = interpolate(frame, [dur - 9, dur], [0, 1], clamp);
  const scatterOut = exitMode === "scatter" ? exit : 0;
  const fade = exitMode === "fade" ? 1 - exit : 1;
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top, left: 40, width: size.width - 80, display: "flex", flexDirection: "column", alignItems: "center", gap: 4, opacity: fade }}>
        {p.lead ? (
          <FxText text={p.lead} fx={leadFx} frame={frame} fps={fps} size={fitSize(p.lead, 900, 62, 40, leadFont.ratio ?? 0.5)} family={leadFont.family} fill={palette.white} stroke={palette.ink} weight={leadFont.weight} width={0.13} shadow={textShadow} k={lk} x={scatterOut} seed={3} spread={0.8} />
        ) : null}
        {emph ? (
          <FxText text={emph} fx={emphFx} frame={Math.max(0, frame - emphF)} fps={fps} size={emphSize} family={emphFont.family} fill={emphFill} stroke={emphStroke} weight={emphFont.weight} width={0.14} shadow={`drop-shadow(0 8px 14px rgba(40,0,6,0.45))`} k={ek} x={scatterOut} seed={11} spread={1} />
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------------------------------------ pill
export type PillProps = { text: string; variant?: "white" | "red" | "yellow" | "ink"; type?: boolean; at?: [number, number]; size?: number; font?: string };

export const Pill: React.FC<Base> = ({ ov, dur, instant }) => {
  const { fps } = useVideoConfig();
  const p = (ov.props ?? {}) as PillProps;
  const { frame, exit } = useEnterExit(dur, { instant, exit: 6 });
  const v = p.variant ?? "white";
  const bg = v === "white" ? palette.white : v === "yellow" ? palette.sky : v === "ink" ? palette.ink : palette.royal;
  const fg = v === "white" ? palette.royal : v === "yellow" ? palette.ink : palette.white;
  const fontSize = p.size ?? 46;
  const pf = pickFont(p.font, 900, fonts.sans);
  const k = instant ? 1 : pop(frame, fps, 0);
  const chars = Array.from(p.text);
  const shown = p.type === false ? chars.length : Math.min(chars.length, Math.max(0, Math.floor((frame - 2) / 0.8)));
  const [ax, ay] = p.at ?? [0.5, 0.0];
  const top = p.at ? ay * size.height : zones[ov.zone ?? "top"] + 96;
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <div
        style={{
          position: "absolute",
          left: ax * size.width,
          top,
          translate: "-50% 0",
          scale: String(Math.min(1.06, 0.8 + 0.2 * k)),
          padding: "10px 32px 12px",
          borderRadius: 16,
          background: bg,
          boxShadow: "0 10px 26px rgba(30,0,6,0.38)",
          fontFamily: pf.family,
          fontWeight: pf.weight,
          fontSize,
          letterSpacing: "0.01em",
          color: fg,
          whiteSpace: "nowrap",
        }}
      >
        {/* the full text sizes the pill; the typed part is drawn over it */}
        <span style={{ visibility: "hidden" }}>{p.text}</span>
        <span style={{ position: "absolute", left: 32, top: 10 }}>{chars.slice(0, shown).join("")}</span>
      </div>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------------------------------------ arc
export type ArcProps = { text: string; echoes?: number; at?: [number, number]; fill?: string; stroke?: string };

// Letters along an upward arc with echoes: copies of the arc, each larger and fainter, fanning out and waving.
export const Arc: React.FC<Base> = ({ ov, dur, instant }) => {
  const p = (ov.props ?? {}) as ArcProps;
  const { frame, exit } = useEnterExit(dur, { instant, exit: 8 });
  const echoes = p.echoes ?? 3;
  const [ax, ay] = p.at ?? [0.5, 0.2];
  const fill = p.fill ?? "#1B2A86";
  const stroke = p.stroke ?? palette.sky;
  const W = 980;
  // frame 0 is the feed thumbnail: an arc that opens the video is already there, only the echoes fan out
  const grow = instant ? 1 : interpolate(frame, [0, 16], [0, 1], { ...clamp, easing: (t) => 1 - Math.pow(1 - t, 3) });
  const fan = instant ? interpolate(frame, [0, 16], [0.25, 1], { ...clamp, easing: (t) => 1 - Math.pow(1 - t, 3) }) : grow;
  const copies = Array.from({ length: echoes + 1 }, (_, i) => i);
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <svg width={size.width} height={size.height} style={{ position: "absolute", inset: 0, overflow: "visible" }}>
        <defs>
          {copies.map((i) => {
            const lift = i * 58 * fan; // each echo sits higher and wider than the one before
            const sag = 170 + i * 26;
            const wave = Math.sin(frame / 7 - i * 0.9) * 8 * i;
            const x0 = (size.width - W) / 2 - i * 26;
            const x1 = (size.width + W) / 2 + i * 26;
            const y = ay * size.height - lift + wave;
            return <path key={i} id={`arc${i}-${ov.start}`} d={`M ${x0} ${y + sag} Q ${size.width / 2} ${y - sag} ${x1} ${y + sag}`} />;
          })}
        </defs>
        {copies
          .slice()
          .reverse()
          .map((i) => {
            const o = i === 0 ? 1 : 0.55 / i;
            const fs = 150 - i * 8;
            return (
              <text
                key={i}
                fontFamily={fonts.condensed}
                fontWeight={900}
                fontSize={fs}
                textAnchor="middle"
                opacity={o * grow}
                fill={i === 0 ? fill : stroke}
                stroke={i === 0 ? stroke : "none"}
                strokeWidth={i === 0 ? 9 : 0}
                paintOrder="stroke"
                strokeLinejoin="round"
                style={{ filter: i === 0 ? "drop-shadow(0 6px 10px rgba(0,0,0,0.35))" : "blur(1.2px)" }}
              >
                <textPath href={`#arc${i}-${ov.start}`} startOffset={`${50 + (ax - 0.5) * 20}%`}>
                  {p.text}
                </textPath>
              </text>
            );
          })}
      </svg>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------------------------------------ script
export type ScriptProps = { text: string; at?: [number, number]; rotate?: number; size?: number; font?: string };

export const Script: React.FC<Base> = ({ ov, dur, instant }) => {
  const p = (ov.props ?? {}) as ScriptProps;
  const { frame } = useEnterExit(dur, { instant });
  const { k, x } = timing(dur, instant ? 0.001 : 15, 9, frame);
  const [ax, ay] = p.at ?? [0.5, 0.0];
  const top = p.at ? ay * size.height : zones[ov.zone ?? "top"] + 160;
  const sf = p.font ? pickFont(p.font, 700, fonts.script) : pickFont(undefined, 400, fonts.script);
  const fs = p.size ?? fitSize(p.text, 860, 76, 48, sf.ratio ?? 0.55);
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: ax * size.width, top, translate: "-50% 0", rotate: `${p.rotate ?? -3}deg` }}>
        <ScatterText text={p.text} size={fs} family={sf.family} weight={sf.weight} fill={palette.sky} stroke={palette.ink} width={0.09} shadow={textShadow} k={k} x={x} seed={21} spread={0.9} />
      </div>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------------------------------------ tag
export type TagProps = { text: string; at?: [number, number]; fx?: FxName; font?: string };

// A short loud label for a card ("LABEL", "TAG"): red condensed letters with a white outline, popping in.
export const Tag: React.FC<Base> = ({ ov, dur, instant }) => {
  const { fps } = useVideoConfig();
  const p = (ov.props ?? {}) as TagProps;
  const { frame, exit } = useEnterExit(dur, { instant, exit: 6 });
  const k = instant ? 1 : spring({ frame, fps, config: { damping: 11, stiffness: 240, mass: 0.6 } });
  const [ax, ay] = p.at ?? [0.5, 0.235];
  const tf = pickFont(p.font, 900, fonts.condensed);
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <div style={{ position: "absolute", left: ax * size.width, top: ay * size.height, translate: "-50% -50%", scale: String(k), rotate: "-2deg" }}>
        <ScatterText text={p.text} fx={p.fx ?? "rise"} frame={frame} k={interpolate(frame, [0, fxFrames(p.fx ?? "rise", p.text)], [0, 1], clamp)} x={0} size={64} family={tf.family} fill={palette.royal} stroke={palette.white} weight={tf.weight} width={0.17} shadow="drop-shadow(0 6px 10px rgba(30,0,6,0.5))" />
      </div>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------------------------------------ burst
export type BurstProps = { text: string; copies?: number; at?: [number, number]; fill?: string; stroke?: string; hold?: boolean; speed?: number };

// The opening shout as a pile of copies: a gray ghost appears small underneath, then more and more copies pop up around it, each
// larger, tilted differently and nearer the frame edge, until the pile fills the top of the frame (letters that seem to jump
// up from behind each other). Colour copies carry the fill and outline; the ghosts are a washed gray. All spring in with an overshoot
// and then drift a little. `copies` 4-9; `at` moves the whole pile (its centre, as fractions of the frame).
const BURST = [
  { dx: 0.0, dy: 0.06, rot: -2, size: 0.42, ghost: true, at: 0 },
  { dx: -0.1, dy: 0.0, rot: -20, size: 0.62, ghost: false, at: 3 },
  { dx: 0.12, dy: 0.05, rot: -8, size: 0.46, ghost: true, at: 5 },
  { dx: 0.08, dy: -0.02, rot: -15, size: 0.82, ghost: false, at: 8 },
  { dx: -0.03, dy: 0.03, rot: 4, size: 0.5, ghost: true, at: 10 },
  { dx: -0.17, dy: -0.01, rot: -17, size: 1.08, ghost: false, at: 12 },
  { dx: 0.16, dy: -0.035, rot: -8, size: 1.06, ghost: false, at: 15 },
  { dx: -0.05, dy: -0.025, rot: -3, size: 1.28, ghost: false, at: 17 },
  { dx: 0.22, dy: -0.05, rot: -6, size: 1.2, ghost: false, at: 19 },
];

export const Burst: React.FC<Base> = ({ ov, dur, instant }) => {
  const { fps } = useVideoConfig();
  const p = (ov.props ?? {}) as BurstProps;
  const { frame } = useEnterExit(dur, { instant });
  const [cx, cy] = p.at ?? [0.5, 0.215];
  const count = Math.min(BURST.length, p.copies ?? BURST.length);
  const fill = p.fill ?? "#1B2A86";
  const stroke = p.stroke ?? palette.sky;
  const base = fitSize(p.text, 760, 118, 70, 0.55);
  const out = p.hold ? 0 : interpolate(frame, [dur - 4, dur], [0, 1], clamp);
  return (
    <AbsoluteFill style={{ opacity: 1 - out }}>
      {BURST.slice(0, count).map((c, i) => {
        const f = (instant ? frame * (p.speed ?? 1) + c.at : frame * (p.speed ?? 1) - c.at);
        const k = f < 0 ? 0 : spring({ frame: f, fps, config: { damping: 9, stiffness: 190, mass: 0.7 } });
        const drift = Math.sin((frame + i * 9) / 11) * 4;
        return (
          <div key={i} style={{ position: "absolute", left: (cx + c.dx) * size.width, top: (cy + c.dy) * size.height + drift, translate: "-50% -50%", rotate: `${c.rot + (1 - Math.min(1, k)) * -14}deg`, scale: String(Math.max(0, k)), opacity: Math.min(1, k * 3) }}>
            {c.ghost ? (
              <div style={{ fontFamily: fonts.condensed, fontWeight: 900, fontSize: base * c.size, whiteSpace: "pre", color: "rgba(88,104,150,0.55)", WebkitTextStroke: "0px", textShadow: "0 0 10px rgba(255,255,255,0.35)" }}>{p.text}</div>
            ) : (
              <FxText text={p.text} fx="rise" frame={frame} k={1} x={0} size={base * c.size} family={fonts.condensed} fill={fill} stroke={stroke} weight={900} width={0.2} shadow="drop-shadow(0 6px 8px rgba(0,30,90,0.35))" />
            )}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
