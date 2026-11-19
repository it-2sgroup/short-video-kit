// A text box: text placed in a box you give (x, y, width, optional height, as fractions of the frame), MEASURED with the real font and
// wrapped at word boundaries, shrunk until it fits, never drawn outside the box sideways. This is what a reference video's text needs:
// the position and size of a box the sample measured, with the words of the new video. Where `phrase`/`title` size a line by counting
// characters, this measures with @remotion/layout-utils after the font has loaded (the frame waits for it), so a long Vietnamese
// line wraps and shrinks instead of running off the frame.
//   box=0.1,0.4,0.8        x, y (top-left), width as fractions of the frame; a 4th number is the height (text shrinks to fit it)
//   text=Line one / Line two   a list is explicit lines (each is wrapped on its own if it is too wide); a plain string wraps by itself
//   size=72 min=30 maxLines=3  largest and smallest font size in px, most lines (0 = no limit); lineHeight=1.12
//   align=left|center|right  valign=top|middle|bottom (with a height)  case=upper|lower  rotate=-3
//   color=#FFD21A | white|yellow|red|ink   stroke=#111 | none   strokeW=0.12   bg=#112233 (a box behind the text; pad=18 radius=16)
//   font=<id from fonts.ts>  weight=800  in=<any text effect of Fx.tsx: rise blurin typewriter elastic ...>  out=fade|scatter|none
// A line has to fit inside the box width at `min`; below that the size keeps shrinking so no word is ever cut or drawn outside sideways.
// Pure function of the frame (the fit is computed once from the text, the font and the box, never from the clock).
import React, { useEffect, useMemo, useState } from "react";
import { AbsoluteFill, interpolate, useDelayRender, useVideoConfig } from "remotion";
import { measureText } from "@remotion/layout-utils";
import type { Overlay } from "../../project";
import { fonts, frame as size, palette, textShadow } from "../../theme";
import { clamp, useEnterExit } from "../anim";
import { pickFont } from "../../fonts";
import { fontsLoaded } from "../../fontReady";
import { FxText, fxFrames, type FxName } from "./Fx";

type Base = { ov: Overlay; dur: number; instant: boolean };

export type TextBoxProps = {
  text: string | string[];
  box?: [number, number, number] | [number, number, number, number];
  size?: number; min?: number; maxLines?: number; lineHeight?: number;
  align?: "left" | "center" | "right"; valign?: "top" | "middle" | "bottom"; case?: "upper" | "lower" | "none"; rotate?: number;
  color?: string; stroke?: string; strokeW?: number; bg?: string; pad?: number; radius?: number;
  font?: string; weight?: number; in?: FxName; out?: "fade" | "scatter" | "none";
};

const NAMED: Record<string, string> = { white: palette.white, yellow: palette.sky, red: palette.royal, ink: palette.ink };
const colour = (c: string | undefined, fallback: string) => (c ? NAMED[c] ?? c : fallback);

// Perceived brightness of #rrggbb (0..255), to pick an outline that contrasts with the fill. Unknown strings count as dark.
const brightness = (c: string): number => {
  const m = /^#?([0-9a-f]{6})$/i.exec(c.trim());
  if (!m) return 60;
  const n = parseInt(m[1], 16);
  return 0.299 * ((n >> 16) & 255) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255);
};

// Wait for the fonts before measuring: a measurement taken with the fallback font would be cached and wrong for every frame
// (`loadFont` returns at once; fontReady.ts holds the promises of the loads in flight).
const useFontReady = (family: string, weight: number, sample: string): boolean => {
  const { delayRender, continueRender } = useDelayRender();
  const [ready, setReady] = useState(false);
  const [handle] = useState(() => delayRender(`textbox font ${family}`));
  useEffect(() => {
    const done = () => { setReady(true); continueRender(handle); };
    if (typeof document === "undefined" || !document.fonts) { done(); return; }
    fontsLoaded().then(() => document.fonts.load(`${weight} 40px ${family}`, sample)).then(done, done);
  }, [family, weight, sample, handle, continueRender]);
  return ready;
};

export type Fit = { lines: string[]; fontSize: number; width: number; height: number; overflowY: boolean };

// Greedy wrap of one paragraph at word boundaries; a single word wider than `avail` stays on its own line (the size loop shrinks it).
const wrap = (para: string, avail: number, w: (s: string) => number): string[] => {
  const words = para.split(/\s+/).filter(Boolean);
  const out: string[] = [];
  let cur = "";
  for (const word of words) {
    const next = cur ? `${cur} ${word}` : word;
    if (cur && w(next) > avail) { out.push(cur); cur = word; } else cur = next;
  }
  if (cur) out.push(cur);
  return out.length ? out : [""];
};

// The largest size in [min, max] at which the text fits (lines, width, height), then, if even `min` does not fit sideways, the size at which
// the widest line does. Exported so the same arithmetic can be checked without a browser (selftest) by passing a width function.
export const fitBox = (paras: string[], avail: number, maxH: number | undefined, max: number, min: number, maxLines: number, lh: number,
  widthAt: (s: string, fontSize: number) => number): Fit => {
  let fs = max;
  for (; fs >= min; fs -= 2) {
    const lines = paras.flatMap((p) => wrap(p, avail, (s) => widthAt(s, fs)));
    const wide = Math.max(...lines.map((l) => widthAt(l, fs)));
    const h = lines.length * fs * lh;
    if (wide <= avail && (!maxLines || lines.length <= maxLines) && (maxH === undefined || h <= maxH)) return { lines, fontSize: fs, width: wide, height: h, overflowY: false };
  }
  fs = Math.max(8, Math.min(min, max)); // the smallest size tried
  let lines = paras.flatMap((p) => wrap(p, avail, (s) => widthAt(s, fs)));
  let wide = Math.max(...lines.map((l) => widthAt(l, fs)));
  if (wide > avail) { // a word wider than the box even at `min`: shrink just enough that it fits sideways
    fs = Math.max(8, Math.floor((fs * avail) / wide));
    lines = paras.flatMap((p) => wrap(p, avail, (s) => widthAt(s, fs)));
    wide = Math.max(...lines.map((l) => widthAt(l, fs)));
  }
  const h = lines.length * fs * lh;
  return { lines, fontSize: fs, width: Math.min(wide, avail), height: h, overflowY: (maxH !== undefined && h > maxH + 1) || (!!maxLines && lines.length > maxLines) };
};

export const TextBox: React.FC<Base> = ({ ov, dur, instant }) => {
  const p = (ov.props ?? {}) as TextBoxProps;
  const { fps } = useVideoConfig();
  const { frame, exit } = useEnterExit(dur, { instant, exit: 6 });
  const pf = pickFont(p.font, p.weight ?? 800, fonts.sans);
  const raw = (Array.isArray(p.text) ? p.text : [p.text ?? ""]).map(String);
  const tx = (s: string) => (p.case === "upper" ? s.toLocaleUpperCase("vi") : p.case === "lower" ? s.toLocaleLowerCase("vi") : s).normalize("NFC");
  const paras = raw.map(tx);
  const ready = useFontReady(pf.family, pf.weight, paras.join(" "));
  const [bx, by, bw, bh] = p.box ?? [0.1, 0.4, 0.8];
  const boxW = bw * size.width;
  const boxH = bh !== undefined ? bh * size.height : undefined;
  const maxSize = p.size ?? 64;
  const lh = p.lineHeight ?? 1.12;
  const fill = colour(p.color, palette.white);
  const strokeCol = p.stroke === "none" ? fill : colour(p.stroke, brightness(fill) > 150 ? palette.ink : palette.white);
  const sw = p.stroke === "none" ? 0 : p.strokeW ?? 0.12;
  const pad = p.bg ? p.pad ?? 18 : 0;

  const fit = useMemo(() => {
    if (!ready) return null;
    const avail = boxW - 2 * pad - maxSize * sw * 0.5; // the outline grows half its width outside the glyphs
    const widthAt = (s: string, fontSize: number) => measureText({ text: s, fontFamily: pf.family, fontWeight: pf.weight, fontSize }).width;
    return fitBox(paras, avail, boxH !== undefined ? boxH - 2 * pad : undefined, maxSize, p.min ?? 30, p.maxLines ?? 3, lh, widthAt);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, paras.join("\n"), pf.family, pf.weight, boxW, boxH, maxSize, p.min, p.maxLines, lh, pad, sw]);
  if (!fit) return null;
  if (fit.overflowY && frame === 0) console.warn(`textbox "${paras.join(" / ").slice(0, 40)}": does not fit its box at the smallest size; shorten the text or enlarge the box`);

  const blockH = fit.height + 2 * pad;
  const top = by * size.height + (boxH !== undefined ? ((p.valign ?? "top") === "middle" ? (boxH - blockH) / 2 : p.valign === "bottom" ? boxH - blockH : 0) : 0);
  const align = p.align ?? "center";
  const blockW = Math.min(boxW, fit.width + 2 * pad + fit.fontSize * sw);
  const left = bx * size.width + (align === "center" ? (boxW - blockW) / 2 : align === "right" ? boxW - blockW : 0);
  const fx: FxName = p.in ?? "rise";
  const outMode = p.out ?? "fade";
  const exitK = interpolate(frame, [dur - 9, dur], [0, 1], clamp);
  const fade = outMode === "fade" ? 1 - exitK : 1;
  const lineGap = Math.round(fit.fontSize * lh);
  return (
    <AbsoluteFill style={{ opacity: outMode === "fade" ? Math.min(exit, fade) : 1 }}>
      <div style={{ position: "absolute", left, top, width: blockW, height: blockH, rotate: p.rotate ? `${p.rotate}deg` : undefined }}>
        {p.bg ? <div style={{ position: "absolute", inset: 0, background: p.bg, borderRadius: p.radius ?? 16, opacity: instant ? 1 : interpolate(frame, [0, 6], [0, 1], clamp) }} /> : null}
        <div style={{ position: "absolute", left: pad, right: pad, top: pad, display: "flex", flexDirection: "column", alignItems: align === "center" ? "center" : align === "right" ? "flex-end" : "flex-start" }}>
          {fit.lines.map((line, i) => {
            const k = instant ? 1 : interpolate(frame, [i * 4, i * 4 + fxFrames(fx, line)], [0, 1], clamp);
            return (
              <div key={i} style={{ height: lineGap, display: "flex", alignItems: "center" }}>
                <FxText text={line} fx={fx} frame={Math.max(0, frame - i * 4)} fps={fps} size={fit.fontSize} family={pf.family} fill={fill} stroke={strokeCol}
                  weight={pf.weight} width={sw} shadow={textShadow} k={k} x={outMode === "scatter" ? exitK : 0} seed={i + 3} spread={0.8} />
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};
