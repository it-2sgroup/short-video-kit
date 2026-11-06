// Spoken captions in their own band at the bottom, so the middle of the frame stays free for the
// footage. One group on screen at a time; groups cut, they never pop or bounce. "karaoke"
// highlights the word being spoken when word timings are available.
import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import type { Caption, Word } from "../../project";
import { captionTop, captions as layout, toneColor } from "../../theme";
import { clamp } from "../anim";
import { OutlineText } from "./primitives";

export const Captions: React.FC<{ captions: Caption[]; words: Word[]; mode: "karaoke" | "plain"; lift?: number }> = ({
  captions,
  words,
  mode,
  lift = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const idx = captions.findIndex((c, i) => {
    const next = captions[i + 1]?.start ?? Infinity;
    return t >= c.start && t < Math.max(c.end, Math.min(next, c.end + 0.25));
  });
  if (idx < 0) return null;
  const c = captions[idx];
  const opacity = interpolate(frame - Math.round(c.start * fps), [0, 4], [0, 1], clamp);
  const groupWords = mode === "karaoke" ? words.filter((w) => w.start >= c.start - 0.02 && w.start < c.end) : [];

  return (
    // The right margin keeps long groups clear of TikTok's action rail; lift moves the band up while
    // the cart arrow needs the bottom-left corner.
    <div style={{ position: "absolute", top: captionTop - lift, left: layout.left, right: layout.right, display: "flex", justifyContent: "center", opacity }}>
      <OutlineText size={layout.size} weight={800}>
        {groupWords.length
          ? groupWords.map((w, i) => {
              // Only one word is active at a time: the next word's start ends this one, so two scaled
              // neighbours never squeeze the space between them to nothing ("chocombo").
              const active = t >= w.start && t < Math.min(w.end + 0.05, groupWords[i + 1]?.start ?? Infinity);
              // Real spaces between words (not margins): the active word's scale must not eat them.
              return (
                <React.Fragment key={i}>
                  {i > 0 ? " " : null}
                  <span style={{ display: "inline-block", color: active ? toneColor.cta : undefined, scale: active ? "1.08" : "1" }}>
                    {w.text}
                  </span>
                </React.Fragment>
              );
            })
          : c.text}
      </OutlineText>
    </div>
  );
};
