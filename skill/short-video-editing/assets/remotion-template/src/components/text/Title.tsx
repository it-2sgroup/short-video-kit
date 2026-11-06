// Titles and labels in five styles. Content (lines, accent word, sub-line) comes from props.
//   outline  - coloured fill + dark outline. Default for product demos (client-approved look).
//   stack    - small lead line over a huge heavy line; one accent word in serif italic gradient.
//   gradient - big heavy white->sky gradient title with soft shadow, no outline.
//   glass    - frosted light card with navy->royal gradient text. For busy footage only.
//   marker   - heavy outline text with a highlighter sweep behind the accent word.
import React from "react";
import { AbsoluteFill, interpolate, useVideoConfig } from "remotion";
import type { Overlay } from "../../project";
import { fonts, palette, toneColor, zones } from "../../theme";
import { clamp, fitSize, smooth, useEnterExit } from "../anim";
import { GradientText, MaskRise, OutlineText, splitAccent } from "./primitives";

export type TitleStyle = "outline" | "stack" | "gradient" | "glass" | "marker";
export type TitleProps = { style?: TitleStyle; lines: string[]; accent?: string; sub?: string };

const SKY = `${palette.white} 0%, ${palette.white} 40%, #C4DBFF 100%`;
const ACCENT = `#FFFFFF 0%, #E3EEFF 45%, #8FB8FF 100%`;
const NAVY = `#0B1F4D 0%, ${palette.royal} 100%`;

export const Title: React.FC<{ ov: Overlay; dur: number; instant: boolean }> = ({ ov, dur, instant }) => {
  const { fps } = useVideoConfig();
  const p = (ov.props ?? {}) as TitleProps;
  const style = p.style ?? "outline";
  const lines = (p.lines ?? []).filter(Boolean);
  const tone = toneColor[ov.tone ?? "neutral"];
  const { frame, enter, exit } = useEnterExit(dur, { delay: instant ? 0 : 4, instant });
  const rise = instant ? 1 : smooth(frame, fps, 4, 14);
  const accentIn = instant ? 1 : smooth(frame, fps, 10, 12);
  const top = zones[ov.zone ?? "top"];
  const width = ov.zone === "lower" || ov.zone === "center" ? 820 : 900; // keep clear of the right rail

  const lead = lines.length > 1 ? lines[0] : undefined;
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
      <OutlineText size={32} weight={700}>
        {p.sub}
      </OutlineText>
    </div>
  ) : null;

  let body: React.ReactNode;
  if (style === "stack") {
    const size = fitSize(main, width, 112, 68);
    body = (
      <>
        {lead ? (
          <div style={{ opacity: enter, translate: `0 ${(1 - enter) * 24}px`, alignSelf: "flex-start", marginLeft: 24 }}>
            <GradientText size={40} weight={500} stops={`${palette.white}, ${palette.white}`}>
              {lead}
            </GradientText>
          </div>
        ) : null}
        <MaskRise progress={rise}>
          <div style={{ display: "flex", alignItems: "baseline", justifyContent: "center", gap: Math.round(size * 0.22) }}>
            {pre.trim() ? (
              <GradientText size={size} weight={900} stops={SKY} tracking="-0.035em" lineHeight={1.05}>
                {pre.trim()}
              </GradientText>
            ) : null}
            {accentWord(size)}
            {post.trim() ? (
              <GradientText size={size} weight={900} stops={SKY} tracking="-0.035em" lineHeight={1.05}>
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
          <GradientText size={i === lines.length - 1 ? fitSize(line, width, 104, 62) : 42} weight={i === lines.length - 1 ? 900 : 700} stops={SKY} tracking="-0.04em">
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
          background: "linear-gradient(160deg, rgba(255,255,255,0.93), rgba(226,236,250,0.86))",
          border: "1.5px solid rgba(255,255,255,0.75)",
          boxShadow: "0 20px 60px rgba(10,30,80,0.28)",
          scale: String(interpolate(card, [0, 1], [0.92, 1])),
          translate: `0 ${(1 - card) * 40}px`,
          opacity: card,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        {lead ? (
          <div style={{ fontFamily: fonts.sans, fontWeight: 500, fontSize: 32, color: "#1B2A4A" }}>{lead}</div>
        ) : null}
        <MaskRise progress={rise}>
          <GradientText size={fitSize(main, 740 - 68, 84, 50)} weight={900} angle={90} stops={NAVY} tracking="-0.04em" shadow={false}>
            {main}
          </GradientText>
        </MaskRise>
      </div>
    );
  } else if (style === "marker") {
    const sweep = instant ? 1 : interpolate(frame, [10, 22], [0, 1], clamp);
    const size = fitSize(main, width, 80, 54);
    body = (
      <MaskRise progress={rise}>
        <div style={{ fontFamily: fonts.sans, fontWeight: 900, fontSize: size, display: "flex", gap: Math.round(size * 0.22), justifyContent: "center", flexWrap: "wrap" }}>
          {pre.trim() ? <OutlineText size={size} weight={900}>{pre.trim()}</OutlineText> : null}
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
              <span style={{ position: "relative", fontFamily: fonts.sans, fontWeight: 900, fontSize: size, lineHeight: 1.12, color: sweep > 0.5 ? palette.ink : palette.white }}>
                {acc}
              </span>
            </span>
          ) : null}
          {post.trim() ? <OutlineText size={size} weight={900}>{post.trim()}</OutlineText> : null}
        </div>
      </MaskRise>
    );
  } else {
    const size = fitSize(main, width, 76, 50);
    body = (
      <>
        {lead ? (
          <div style={{ opacity: enter }}>
            <OutlineText size={38} weight={700}>{lead}</OutlineText>
          </div>
        ) : null}
        <div style={{ opacity: enter, translate: `0 ${(1 - enter) * 24}px` }}>
          <OutlineText size={size} weight={800} color={tone}>
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
