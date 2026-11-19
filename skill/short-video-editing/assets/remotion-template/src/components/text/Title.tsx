// Titles and labels in five styles. Content (lines, accent word, sub-line) comes from props.
//   outline  - coloured fill + dark outline. The default: reads over most footage without a box.
//   stack    - small lead line over a huge heavy line; one accent word in serif italic gradient.
//   gradient - big heavy white->sky gradient title with soft shadow, no outline.
//   glass    - frosted light card with a dark gradient main line (navy->royal, or brown->vermilion in the warm theme). For busy footage only.
//   marker   - heavy outline text with a highlighter sweep behind the accent word.
import React from "react";
import { AbsoluteFill, interpolate, useVideoConfig } from "remotion";
import type { Overlay } from "../../project";
import { fonts, palette, titleColors, toneColor, zones } from "../../theme";
import { clamp, fitSize, smooth, useEnterExit } from "../anim";
import { fontRatio, pickFont } from "../../fonts";
import { GradientText, MaskRise, OutlineText, splitAccent } from "./primitives";

export type TitleStyle = "outline" | "stack" | "gradient" | "glass" | "marker";
// font: a library font id (fonts.ts) for every line except the accent word, which keeps the serif; default: Be Vietnam Pro.
export type TitleProps = { style?: TitleStyle; lines: string[]; accent?: string; sub?: string; font?: string };

const SKY = titleColors.sky;
const ACCENT = titleColors.accent;
const NAVY = titleColors.glassText;

export const Title: React.FC<{ ov: Overlay; dur: number; instant: boolean }> = ({ ov, dur, instant }) => {
  const { fps } = useVideoConfig();
  const p = (ov.props ?? {}) as TitleProps;
  const style = p.style ?? "outline";
  const mf = (weight: number) => pickFont(p.font, weight, fonts.sans); // { family, weight, ratio } for a wanted weight
  const ratio = fontRatio(p.font) ?? 0.56;
  const lines = (p.lines ?? []).filter(Boolean);
  const tone = toneColor[ov.tone ?? "neutral"];
  const { frame, enter, exit } = useEnterExit(dur, { delay: instant ? 0 : 4, instant });
  const rise = instant ? 1 : smooth(frame, fps, 4, 14);
  const accentIn = instant ? 1 : smooth(frame, fps, 10, 12);
  const top = zones[ov.zone ?? "top"];
  const width = ov.zone === "lower" || ov.zone === "center" ? 820 : 900; // keep clear of the right rail

  const lead = lines.length > 1 ? lines.slice(0, -1).join(" ") : undefined; // every line but the last is the small lead: a third line is no longer dropped
  const main = lines[lines.length - 1] ?? "";
  const [pre, acc, post] = splitAccent(main, p.accent);

  const exitStyle: React.CSSProperties = { opacity: exit, translate: `0 ${(1 - exit) * -12}px` };

  const accentWord = (size: number) =>
    acc ? (
      <span
        style={{
          display: "inline-block",
          opacity: accentIn,
          filter: `blur(${(1 - accentIn) * 12}px)`,
          scale: String(interpolate(accentIn, [0, 1], [1.08, 1], clamp)),
        }}
      >
        <GradientText size={size * 1.08} family={fonts.accent} weight={700} italic stops={ACCENT} tracking="0">
          {acc}
        </GradientText>
      </span>
    ) : null;

  const subLine = p.sub ? (
    <div style={{ opacity: enter, marginTop: 8 }}>
      <OutlineText size={32} family={mf(700).family} weight={mf(700).weight}>
        {p.sub}
      </OutlineText>
    </div>
  ) : null;

  let body: React.ReactNode;
  if (style === "stack") {
    const size = fitSize(main, width, 112, 68, ratio);
    body = (
      <>
        {lead ? (
          <div style={{ opacity: enter, translate: `0 ${(1 - enter) * 24}px`, alignSelf: "flex-start", marginLeft: 24 }}>
            <GradientText size={40} family={mf(500).family} weight={mf(500).weight} stops={`${palette.white}, ${palette.white}`}>
              {lead}
            </GradientText>
          </div>
        ) : null}
        <MaskRise progress={rise}>
          <div style={{ display: "flex", alignItems: "baseline", justifyContent: "center", gap: Math.round(size * 0.22) }}>
            {pre.trim() ? (
              <GradientText size={size} family={mf(900).family} weight={mf(900).weight} stops={SKY} tracking="-0.035em" lineHeight={1.05}>
                {pre.trim()}
              </GradientText>
            ) : null}
            {accentWord(size)}
            {post.trim() ? (
              <GradientText size={size} family={mf(900).family} weight={mf(900).weight} stops={SKY} tracking="-0.035em" lineHeight={1.05}>
                {post.trim()}
              </GradientText>
            ) : null}
          </div>
        </MaskRise>
      </>
    );
  } else if (style === "gradient") {
    body = lines.map((line, i) => (
      <MaskRise key={i} progress={instant ? 1 : smooth(frame, fps, 4 + i * 3, 15)}>
        <div style={{ scale: String(interpolate(frame, [0, 20], [1.04, 1], clamp)) }}>
          <GradientText size={i === lines.length - 1 ? fitSize(line, width, 104, 62, ratio) : 42} family={mf(i === lines.length - 1 ? 900 : 700).family} weight={mf(i === lines.length - 1 ? 900 : 700).weight} stops={SKY} tracking="-0.04em">
            {line}
          </GradientText>
        </div>
      </MaskRise>
    ));
  } else if (style === "glass") {
    const card = instant ? 1 : smooth(frame, fps, 0, 18);
    body = (
      <div
        style={{
          width: Math.min(width, 740),
          padding: "20px 34px 24px",
          borderRadius: 32,
          background: titleColors.glassBg,
          border: titleColors.glassBorder,
          boxShadow: titleColors.glassShadow,
          scale: String(interpolate(card, [0, 1], [0.92, 1])),
          translate: `0 ${(1 - card) * 40}px`,
          opacity: card,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        {lead ? (
          <div style={{ fontFamily: mf(500).family, fontWeight: mf(500).weight, fontSize: 32, color: titleColors.glassLead }}>{lead}</div>
        ) : null}
        <MaskRise progress={rise}>
          <GradientText size={fitSize(main, 740 - 68, 84, 50, ratio)} family={mf(900).family} weight={mf(900).weight} angle={90} stops={NAVY} tracking="-0.04em" shadow={false}>
            {main}
          </GradientText>
        </MaskRise>
      </div>
    );
  } else if (style === "marker") {
    const sweep = instant ? 1 : interpolate(frame, [10, 22], [0, 1], clamp);
    const size = fitSize(main, width, 80, 54, ratio);
    body = (
      <MaskRise progress={rise}>
        <div style={{ fontFamily: mf(900).family, fontWeight: mf(900).weight, fontSize: size, display: "flex", gap: Math.round(size * 0.22), justifyContent: "center", flexWrap: "wrap" }}>
          {pre.trim() ? <OutlineText size={size} family={mf(900).family} weight={mf(900).weight}>{pre.trim()}</OutlineText> : null}
          {acc ? (
            // A real highlighter: a solid block sweeps in behind the word, which turns to ink.
            // (An outline here would bury the block, so the accent word has none.)
            <span style={{ position: "relative", display: "inline-block", padding: "0 0.12em" }}>
              <span
                style={{
                  position: "absolute",
                  inset: "0.16em 0 0.02em 0",
                  background: tone === palette.white ? toneColor.cta : tone,
                  borderRadius: "0.14em",
                  transformOrigin: "left center",
                  scale: `${sweep} 1`,
                  rotate: "-1.5deg",
                  boxShadow: "0 8px 22px rgba(0,0,0,0.35)",
                }}
              />
              <span style={{ position: "relative", fontFamily: mf(900).family, fontWeight: mf(900).weight, fontSize: size, lineHeight: 1.12, color: sweep > 0.5 ? palette.ink : palette.white }}>
                {acc}
              </span>
            </span>
          ) : null}
          {post.trim() ? <OutlineText size={size} family={mf(900).family} weight={mf(900).weight}>{post.trim()}</OutlineText> : null}
        </div>
      </MaskRise>
    );
  } else {
    const size = fitSize(main, width, 76, 50, ratio);
    body = (
      <>
        {lead ? (
          <div style={{ opacity: enter }}>
            <OutlineText size={38} family={mf(700).family} weight={mf(700).weight}>{lead}</OutlineText>
          </div>
        ) : null}
        <div style={{ opacity: enter, translate: `0 ${(1 - enter) * 24}px` }}>
          <OutlineText size={size} family={mf(800).family} weight={mf(800).weight} color={tone}>
            {main}
          </OutlineText>
        </div>
      </>
    );
  }

  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          top,
          left: (1080 - width) / 2,
          width,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          ...exitStyle,
        }}
      >
        {body}
        {subLine}
      </div>
    </AbsoluteFill>
  );
};
