// Spoken captions in their own band at the bottom, so the middle of the frame stays free for the
// footage. One group on screen at a time; groups cut, they never bounce.
//   karaoke  the group, with the word being spoken highlighted (needs word timings)
//   pop      one short phrase (<= 5 words, one line) at a time, bigger and bolder, the spoken word
//            popping and coloured: the talking-head style. The whole phrase is visible from its first
//            word, because viewers read ahead; revealing one word at a time hurts comprehension
//            (references/captions-and-text.md). Needs word timings.
//   plain    the group only
import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Caption, CaptionBand, CaptionHighlight, CaptionStyle, Word } from "../../project";
import { captions as layout, motion, palette, toneColor } from "../../theme";
import { clamp } from "../anim";
import { OutlineText } from "./primitives";

// Pop phrases: break a group's words into runs of <= popWords words and <= popChars characters,
// starting a new run after a pause or a punctuation mark so a chunk never straddles two thoughts.
const chunks = (words: Word[]) => {
  const out: Word[][] = [];
  for (const w of words) {
    const cur = out[out.length - 1];
    const prev = cur?.[cur.length - 1];
    const chars = cur ? cur.reduce((n, x) => n + x.text.length + 1, 0) + w.text.length : 0;
    const breakHere = !cur || cur.length >= layout.popWords || chars > layout.popChars || w.start - prev!.end > 0.25 || /[,.!?…:;]$/.test(prev!.text);
    if (breakHere) out.push([w]);
    else cur.push(w);
  }
  return out;
};

const Pop: React.FC<{ words: Word[]; t: number; frame: number; fps: number; top: number }> = ({ words, t, frame, fps, top }) => {
  const groups = chunks(words);
  const idx = groups.findIndex((g, i) => t >= g[0].start - 0.05 && t < (groups[i + 1]?.[0].start ?? g[g.length - 1].end + 0.3) - 0.05);
  if (idx < 0) return null;
  const g = groups[idx];
  return (
    <div style={{ position: "absolute", top: top - 20, left: layout.left, right: layout.right, display: "flex", justifyContent: "center" }}>
      <OutlineText size={layout.popSize} weight={900}>
        {g.map((w, i) => {
          const active = t >= w.start && t < (g[i + 1]?.start ?? w.end + 0.3);
          // the spoken word springs from 1.0 to 1.12 and settles back once the next word starts
          const k = active ? spring({ frame: frame - Math.round(w.start * fps), fps, config: motion.pop }) : 0;
          return (
            <React.Fragment key={i}>
              {i > 0 ? " " : null}
              <span style={{ display: "inline-block", scale: String(1 + 0.12 * Math.min(1, k)), color: active ? toneColor.cta : undefined }}>
                {w.text}
              </span>
            </React.Fragment>
          );
        })}
      </OutlineText>
    </div>
  );
};

const fold = (s: string) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/đ/g, "d").toLowerCase().replace(/[^a-z0-9]/g, "");

export const Captions: React.FC<{ captions: Caption[]; words: Word[]; mode: CaptionStyle; top: number; lift?: number; bands?: CaptionBand[]; highlight?: CaptionHighlight; keywords?: string[] }> = ({
  captions,
  words,
  mode,
  top: defaultTop,
  lift = 0,
  bands = [],
  highlight = "color",
  keywords = [],
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  if (mode === "none") return null;
  // A caption band (project.captionBands) moves the captions while its window is open, e.g. to a strip above a card.
  const band = bands.find((b) => t >= b.start && t < b.end);
  if (band?.hide) return null;
  const top = band ? band.top + lift : defaultTop;
  const fontSize = band?.size ?? layout.size;
  const idx = captions.findIndex((c, i) => {
    const next = captions[i + 1]?.start ?? Infinity;
    return t >= c.start && t < Math.max(c.end, Math.min(next, c.end + 0.25));
  });
  if (idx < 0) return null;
  const c = captions[idx];
  const groupWords = mode === "plain" ? [] : words.filter((w) => w.start >= c.start - 0.02 && w.start < c.end);
  if (mode === "pop" && groupWords.length) return <Pop words={groupWords} t={t} frame={frame} fps={fps} top={top - lift} />;
  const opacity = interpolate(frame - Math.round(c.start * fps), [0, 4], [0, 1], clamp);

  return (
    // The right margin keeps long groups clear of the platforms' action rail; lift moves the band up
    // while the cart arrow needs the bottom-left corner.
    <div style={{ position: "absolute", top: top - lift, left: layout.left, right: layout.right, display: "flex", justifyContent: "center", opacity }}>
      <OutlineText size={fontSize} weight={800} wordSpacing={band ? "0.16em" : undefined}>
        {groupWords.length
          ? groupWords.map((w, i) => {
              // Only one word is active at a time: the next word's start ends this one, so two scaled
              // neighbours never squeeze the space between them to nothing ("chocombo").
              const active = t >= w.start && t < Math.min(w.end + 0.05, groupWords[i + 1]?.start ?? Infinity);
              const key = keywords.some((k) => fold(k) === fold(w.text));
              // Real spaces between words (not margins): the active word's scale must not eat them.
              const hot = active ? band?.highlight ?? highlight : null;
              const style: React.CSSProperties = { display: "inline-block", position: "relative" };
              if (key) Object.assign(style, { color: toneColor.cta, scale: "1.12" });
              if (hot === "color") Object.assign(style, { color: toneColor.cta, scale: "1.08" });
              if (hot === "box") Object.assign(style, { color: palette.white, scale: "1.06", background: palette.royal, borderRadius: "0.3em", padding: "0 0.28em", margin: "0 0.04em", boxShadow: "0 6px 16px rgba(30,0,6,0.4)" });
              if (hot === "glow") Object.assign(style, { color: toneColor.cta, scale: "1.06", textShadow: `0 0 0.35em ${toneColor.cta}, 0 0 0.9em ${toneColor.cta}` });
              if (hot === "underline") Object.assign(style, { color: toneColor.cta, scale: "1.05", boxShadow: `0 0.14em 0 ${toneColor.cta}` });
              return (
                <React.Fragment key={i}>
                  {i > 0 ? " " : null}
                  <span style={style}>{w.text}</span>
                </React.Fragment>
              );
            })
          : c.text}
      </OutlineText>
    </div>
  );
};
