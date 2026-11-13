// Subject effects: a matte of the subject (a white-on-transparent PNG per frame offset, scripts/person_matte.py) shapes an effect
// that is drawn inside the scene's camera framing, so it follows every push and pan. A pure function of the frame.
//   fill      the subject filled with a colour: the "silhouette flash" opener when it blinks on a few frames
//   outline   a ring of `width` px around the subject (never over it)
//   glow      a soft halo of `width` px around the subject
//   dim       everything except the subject darkened by `opacity`: a spotlight
//   colorpop  everything except the subject turned grey: the subject keeps its colour
//   behind    big text between the footage and a cut-out copy of the subject: the subject stands in front of the words
//   blur      rack focus: the background blurs (width px, animated over the window) while the subject stays sharp
//   lift      depth pop: a cut-out copy of the subject grows a few percent above the unchanged picture, with a soft shadow
// Visible on the offsets of `frames` (a blink) or, with `show: [from, to]`, on every frame of that window; the matte used is the latest
// one at or before the current offset, so a still pose can serve a whole window.
import React from "react";
import { Img, staticFile } from "remotion";
import type { Subject } from "../project";
import { fonts, frame as size, motion } from "../theme";

const fillAll: React.CSSProperties = { position: "absolute", inset: 0, width: "100%", height: "100%" };

const mask = (url: string, invert = false): React.CSSProperties => {
  const layers = invert ? `url(${url}), linear-gradient(#000, #000)` : `url(${url})`;
  const common = { WebkitMaskImage: layers, maskImage: layers, WebkitMaskSize: "100% 100%", maskSize: "100% 100%", WebkitMaskRepeat: "no-repeat", maskRepeat: "no-repeat" };
  // Inverted: the solid layer minus the subject's shape.
  return invert ? { ...common, WebkitMaskComposite: "xor", maskComposite: "exclude" } : common;
};

export const matteOffset = (fx: Subject, at: number): number | null => {
  if (fx.show ? at < fx.show[0] || at > fx.show[1] : !fx.frames.includes(at)) return null;
  const have = fx.frames.filter((f) => f <= at);
  return have.length ? Math.max(...have) : null;
};

// Progress through the `show` window, eased (1 for a blink, which has no window).
const windowProgress = (fx: Subject, at: number, ease: (t: number) => number) =>
  fx.show ? ease(Math.min(1, Math.max(0, (at - fx.show[0]) / Math.max(1, fx.show[1] - fx.show[0])))) : 1;

// `video` is the scene's footage element: the behind and lift modes draw a second, masked copy of it above the picture.
export const SubjectFx: React.FC<{ fx: Subject; at: number; id: string; video?: React.ReactNode }> = ({ fx, at, id, video }) => {
  const off = matteOffset(fx, at);
  if (off === null) return null;
  const url = staticFile(`${fx.matte}_${off}.png`);
  const color = fx.color ?? "#FFFFFF";
  const width = fx.width ?? 14;
  const opacity = fx.opacity ?? 0.96;
  const mode = fx.mode ?? "fill";
  const z: React.CSSProperties = { ...fillAll, zIndex: 2 };

  if (mode === "behind") {
    const t0 = fx.show ? fx.show[0] : Math.min(...fx.frames);
    const k = motion.easeOut(Math.min(1, Math.max(0, (at - t0) / 8)));
    return (
      <>
        <div style={{ ...fillAll, zIndex: 1, display: "flex", alignItems: "center", justifyContent: "center", top: `${(fx.y ?? 0.38) * 100 - 50}%`, opacity: k }}>
          <div style={{ fontFamily: fonts.sans, fontWeight: 900, fontSize: fx.size ?? 360, lineHeight: 0.95, textAlign: "center", color, whiteSpace: "pre", maxWidth: size.width, transform: `translateY(${(1 - k) * 60}px)` }}>{fx.text ?? ""}</div>
        </div>
        <div style={{ ...fillAll, zIndex: 2, ...mask(url) }}>{video}</div>
      </>
    );
  }
  if (mode === "blur") {
    // The picture behind the element is blurred (backdrop filter), the subject's own shape cut out of it: one video decode, no second copy.
    const px = (fx.from ?? 0) + ((fx.width ?? 14) - (fx.from ?? 0)) * windowProgress(fx, at, motion.easeInOut);
    return px < 0.3 ? null : <div style={{ ...z, backdropFilter: `blur(${px}px)`, ...mask(url, true) }} />;
  }
  if (mode === "lift") {
    // The cut-out and its shadow scale together about (50%, y): the mask is part of the scaled element, so the copy grows and its edge with it.
    const t = windowProgress(fx, at, motion.easeOut);
    const k = 1 + ((fx.width ?? 4) / 100) * t;
    return (
      <div style={{ ...z, transform: `scale(${k})`, transformOrigin: `50% ${(fx.y ?? 0.5) * 100}%`, filter: `drop-shadow(0 14px 26px rgba(0,0,0,${(fx.opacity ?? 0.4) * t}))` }}>
        <div style={{ ...fillAll, ...mask(url) }}>{video}</div>
      </div>
    );
  }
  if (mode === "fill") return <div style={{ ...z, background: color, opacity, ...mask(url) }} />;
  if (mode === "dim") return <div style={{ ...z, background: "#000", opacity: fx.opacity ?? 0.6, ...mask(url, true) }} />;
  if (mode === "colorpop") return <div style={{ ...z, backdropFilter: "grayscale(1) contrast(1.05)", ...mask(url, true) }} />;

  // outline / glow: grow the alpha (dilate or blur), paint it, and cut the subject's own shape out of it.
  const grow =
    mode === "outline" ? (
      <feMorphology in="SourceAlpha" operator="dilate" radius={width} result="g" />
    ) : (
      <>
        <feGaussianBlur in="SourceAlpha" stdDeviation={width} result="b" />
        <feComponentTransfer in="b" result="g">
          <feFuncA type="linear" slope="2.4" />
        </feComponentTransfer>
      </>
    );
  return (
    <>
      <svg width={0} height={0} style={{ position: "absolute" }}>
        <defs>
          <filter id={id} x="-10%" y="-10%" width="120%" height="120%" colorInterpolationFilters="sRGB">
            {grow}
            <feFlood floodColor={color} result="c" />
            <feComposite in="c" in2="g" operator="in" result="ring" />
            <feComposite in="ring" in2="SourceAlpha" operator="out" />
          </filter>
        </defs>
      </svg>
      <Img src={url} style={{ ...z, objectFit: "cover", filter: `url(#${id})`, opacity }} />
    </>
  );
};
