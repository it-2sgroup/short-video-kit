// Text building blocks. No boxes or pills behind words: contrast comes from an outline layer
// drawn UNDER the fill, gradients, and soft drop shadows (see references/typography.md).
import React from "react";
import { fonts, palette, textShadow } from "../../theme";

type TextProps = {
  size: number;
  weight?: number;
  color?: string;
  family?: string;
  italic?: boolean;
  tracking?: string;
  lineHeight?: number;
  align?: "left" | "center" | "right";
  wordSpacing?: string;
  children: React.ReactNode;
};

const base = (p: TextProps): React.CSSProperties => ({
  fontFamily: p.family ?? fonts.sans,
  fontWeight: p.weight ?? 800,
  fontStyle: p.italic ? "italic" : "normal",
  fontSize: p.size,
  letterSpacing: p.tracking ?? "-0.02em",
  lineHeight: p.lineHeight ?? 1.12, // Vietnamese stacked marks (Ấ, Ộ) need >= 1.05
  textAlign: p.align ?? "center",
  whiteSpace: "pre-wrap",
  wordSpacing: p.wordSpacing,
});

// Solid fill with a dark outline layer underneath, so the stroke never eats into the letters.
export const OutlineText: React.FC<TextProps> = (p) => (
  <div style={{ position: "relative", ...base(p) }}>
    <div
      aria-hidden
      style={{
        ...base(p),
        position: "absolute",
        inset: 0,
        color: palette.ink,
        WebkitTextStroke: `${Math.round(p.size / 7)}px ${palette.ink}`,
        textShadow: "0 8px 22px rgba(0,0,0,0.5)",
      }}
    >
      {p.children}
    </div>
    <div style={{ ...base(p), position: "relative", color: p.color ?? palette.white }}>{p.children}</div>
  </div>
);

// Gradient fill. text-shadow would show through the transparent glyphs, so the shadow is a
// drop-shadow filter on the wrapper instead.
export const GradientText: React.FC<TextProps & { stops: string; angle?: number; shadow?: boolean }> = (p) => (
  <div style={{ filter: p.shadow === false ? undefined : textShadow }}>
    <div
      style={{
        ...base(p),
        backgroundImage: `linear-gradient(${p.angle ?? 180}deg, ${p.stops})`,
        WebkitBackgroundClip: "text",
        backgroundClip: "text",
        color: "transparent",
        paddingRight: p.italic ? "0.15em" : undefined, // italic overhang
      }}
    >
      {p.children}
    </div>
  </div>
);

// Reveal text rising through a mask. Top padding keeps diacritics from being clipped.
export const MaskRise: React.FC<{ progress: number; children: React.ReactNode }> = ({ progress, children }) => (
  <div style={{ overflow: "hidden", paddingTop: "0.28em", marginTop: "-0.28em" }}>
    <div style={{ translate: `0 ${(1 - progress) * 105}%` }}>{children}</div>
  </div>
);

// Splits a line around the accent word so it can be styled differently.
export const splitAccent = (line: string, accent?: string): [string, string, string] => {
  if (!accent) return [line, "", ""];
  const i = line.toLocaleLowerCase("vi").indexOf(accent.toLocaleLowerCase("vi"));
  if (i < 0) return [line, "", ""];
  return [line.slice(0, i), line.slice(i, i + accent.length), line.slice(i + accent.length)];
};
