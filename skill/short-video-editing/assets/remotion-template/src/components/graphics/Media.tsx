// Graphics that show pictures: a magnifier lens on a detail, a recap row of frozen thumbnails, the
// before/after comparison card, and a still image (logo, floor plan, packshot) from public/images.
import React from "react";
import { AbsoluteFill, Freeze, Img, OffthreadVideo, interpolate, staticFile, useVideoConfig } from "remotion";
import type { Overlay } from "../../project";
import { compare, frame as size, motion, palette, safe, thumb as THUMB, toneColor, zones } from "../../theme";
import { clamp, smooth, useEnterExit } from "../anim";
import { OutlineText } from "../text/primitives";

type Base = { ov: Overlay; dur: number; instant: boolean };

export type MagnifierProps = { clip: string; in: number; target: [number, number]; at?: [number, number]; zoom?: number; diameter?: number };

export const Magnifier: React.FC<Base> = ({ ov, dur, instant }) => {
  const { fps } = useVideoConfig();
  const p = (ov.props ?? {}) as MagnifierProps;
  const { frame, exit } = useEnterExit(dur, { instant });
  const k = instant ? 1 : smooth(frame, fps, 0, 10);
  const dia = p.diameter ?? 400;
  const [cx, cy] = p.at ?? [0.32, 0.3];
  const [tx, ty] = p.target;
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <div
        style={{
          position: "absolute",
          left: cx * size.width - dia / 2,
          top: cy * size.height - dia / 2,
          width: dia,
          height: dia,
          borderRadius: "50%",
          overflow: "hidden",
          border: `8px solid ${palette.white}`,
          boxShadow: "0 18px 50px rgba(0,0,0,0.45)",
          scale: String(interpolate(k, [0, 1], [0.6, 1])),
          opacity: k,
        }}
      >
        <div
          style={{
            position: "absolute",
            width: size.width,
            height: size.height,
            left: dia / 2 - tx * size.width,
            top: dia / 2 - ty * size.height,
            transformOrigin: `${tx * 100}% ${ty * 100}%`,
            scale: String(p.zoom ?? 2.2),
          }}
        >
          <OffthreadVideo src={staticFile(`clips/${p.clip}.mp4`)} trimBefore={Math.round(p.in * fps)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

type Point = [number, number];
export type CompareProps = {
  before: { clip: string; at: number };
  after: { clip: string; at: number };
  mode?: "side" | "slider" | "stack"; // side: two panels; slider: left/right divider; stack: top/bottom divider
  beforeLabel?: string;
  afterLabel?: string;
  note?: string; // honest label under the card, e.g. "sau 1-2 tiếng ngâm · đã rút gọn thời gian"
  focus?: Point; // point of the source frame (0..1) shown at the centre of each side's area
  beforeFocus?: Point; // overrides focus for the BEFORE side (the stain is rarely where the clean cloth is)
  afterFocus?: Point;
  zoom?: number; // 1 = the whole frame fits the area; 1.5 magnifies the stain
};

// One frozen frame of a clip, scaled so that `focus` lands on (cx, cy) inside a w x h window and
// the window is always filled (the frame is never dragged past its edge).
const Still: React.FC<{ clip: string; at: number; focus: Point; zoom: number; cx: number; cy: number; w: number; h: number }> = ({ clip, at, focus, zoom, cx, cy, w, h }) => {
  const { fps } = useVideoConfig();
  const W = Math.max(w * zoom, w, (h * size.width) / size.height);
  const H = (W * size.height) / size.width;
  const left = Math.min(0, Math.max(w - W, cx - focus[0] * W));
  const top = Math.min(0, Math.max(h - H, cy - focus[1] * H));
  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden" }}>
      <div style={{ position: "absolute", width: W, height: H, left, top }}>
        <Freeze frame={0}>
          <OffthreadVideo src={staticFile(`clips/${clip}.mp4`)} trimBefore={Math.round(at * fps)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        </Freeze>
      </div>
    </div>
  );
};

const Handle: React.FC<{ rotate?: number }> = ({ rotate = 0 }) => (
  <div
    style={{
      width: compare.handle,
      height: compare.handle,
      borderRadius: "50%",
      background: palette.white,
      boxShadow: "0 8px 22px rgba(0,0,0,0.45)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      rotate: `${rotate}deg`,
    }}
  >
    <svg width={44} height={44} viewBox="0 0 44 44">
      <path d="M16 12 L6 22 L16 32 M28 12 L38 22 L28 32" fill="none" stroke={palette.navy} strokeWidth={5} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  </div>
);

export const Compare: React.FC<Base> = ({ ov, dur, instant }) => {
  const p = (ov.props ?? {}) as CompareProps;
  const { frame, enter, exit } = useEnterExit(dur, { instant });
  const mode = p.mode ?? "side";
  const b = compare.border;
  const total = safe.right - safe.left; // outer width of the whole graphic
  const h = compare.height; // picture height inside the border
  const zoom = p.zoom ?? 1;
  const fb = p.beforeFocus ?? p.focus ?? [0.5, 0.5];
  const fa = p.afterFocus ?? p.focus ?? [0.5, 0.5];
  const start = instant ? 0 : compare.holdFrames;
  const sweep = interpolate(frame, [start, start + compare.sweepFrames], [0, 1], { ...clamp, easing: motion.easeInOut });
  const afterIn = interpolate(sweep, [0.45, 0.9], [0, 1], clamp);
  const top = zones[ov.zone ?? "top"];
  const frameStyle: React.CSSProperties = {
    position: "absolute",
    top,
    height: h + 2 * b,
    borderRadius: compare.radius,
    overflow: "hidden",
    border: `${b}px solid ${palette.white}`,
    boxSizing: "border-box",
    boxShadow: "0 20px 54px rgba(0,0,0,0.5)",
  };
  const label = (text: string, color: string, pos: React.CSSProperties, opacity: number, width: number, align: "left" | "right" = "left") => (
    <div style={{ position: "absolute", ...pos, opacity, width }}>
      <OutlineText size={48} weight={900} color={color} align={align}>{text}</OutlineText>
    </div>
  );
  const beforeText = p.beforeLabel ?? "TRƯỚC";
  const afterText = p.afterLabel ?? "SAU";
  const scrim = <div style={{ position: "absolute", inset: 0, background: `rgba(8,16,36,${compare.scrim})`, opacity: enter }} />;
  const note = p.note ? (
    <div style={{ position: "absolute", left: safe.left, width: total, top: top + h + 2 * b + 22, opacity: Math.min(enter, exit) }}>
      <OutlineText size={32} weight={700}>{p.note}</OutlineText>
    </div>
  ) : null;

  if (mode === "side") {
    const gap = 24;
    const outer = (total - gap) / 2;
    const iw = outer - 2 * b;
    const panel = (side: "before" | "after", left: number, opacity: number, shift: number) => (
      <div style={{ ...frameStyle, left, width: outer, opacity, translate: `${shift}px 0` }}>
        <Still {...p[side]} focus={side === "before" ? fb : fa} zoom={zoom} cx={iw / 2} cy={h / 2} w={iw} h={h} />
        {side === "before"
          ? label(beforeText, toneColor.before, { left: 18, top: 16 }, 1, iw - 36)
          : label(afterText, toneColor.after, { left: 18, top: 16 }, afterIn, iw - 36)}
      </div>
    );
    return (
      <AbsoluteFill style={{ opacity: exit }}>
        {scrim}
        {panel("before", safe.left, enter, (1 - enter) * -40)}
        {panel("after", safe.left + outer + gap, Math.min(enter, interpolate(sweep, [0, 0.6], [0, 1], clamp)), (1 - sweep) * 90)}
        <div style={{ position: "absolute", left: safe.left + outer + gap / 2 - compare.handle / 2, top: top + b + h / 2 - compare.handle / 2, opacity: afterIn }}>
          <Handle />
        </div>
        {note}
      </AbsoluteFill>
    );
  }

  // slider / stack: one card, BEFORE on top of AFTER, clipped at the divider.
  const stack = mode === "stack";
  const iw = total - 2 * b;
  const d = 1 - (1 - compare.settle) * sweep; // share of the card still showing BEFORE
  const centre = (side: "before" | "after"): Point => {
    const t = side === "before" ? compare.settle / 2 : (1 + compare.settle) / 2; // middle of that side's final area
    return stack ? [iw / 2, t * h] : [t * iw, h / 2];
  };
  const still = (side: "before" | "after") => {
    const [cx, cy] = centre(side);
    return <Still {...p[side]} focus={side === "before" ? fb : fa} zoom={zoom} cx={cx} cy={cy} w={iw} h={h} />;
  };
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      {scrim}
      <div style={{ ...frameStyle, left: safe.left, width: total, opacity: enter, scale: String(0.94 + 0.06 * enter) }}>
        {still("after")}
        <div style={{ position: "absolute", inset: 0, clipPath: stack ? `inset(0 0 ${(1 - d) * 100}% 0)` : `inset(0 ${(1 - d) * 100}% 0 0)` }}>{still("before")}</div>
        <div
          style={{
            position: "absolute",
            background: palette.white,
            boxShadow: "0 0 18px rgba(0,0,0,0.45)",
            ...(stack ? { left: 0, right: 0, top: d * h - compare.divider / 2, height: compare.divider } : { top: 0, bottom: 0, left: d * iw - compare.divider / 2, width: compare.divider }),
          }}
        />
        <div style={{ position: "absolute", left: (stack ? iw / 2 : d * iw) - compare.handle / 2, top: (stack ? d * h : h / 2) - compare.handle / 2 }}>
          <Handle rotate={stack ? 90 : 0} />
        </div>
        {label(beforeText, toneColor.before, { left: 24, top: 18 }, 1, iw / 2 - 30)}
        {stack
          ? label(afterText, toneColor.after, { left: 24, bottom: 18 }, afterIn, iw / 2 - 30)
          : label(afterText, toneColor.after, { right: 24, top: 18 }, afterIn, iw / 2 - 30, "right")}
      </div>
      {note}
    </AbsoluteFill>
  );
};

// A strip of up to 3 framed stills with a caption under each (the "three small photos at the top"
// header). `delay` (seconds after the strip starts) lets each card land on the word it names; without
// it the cards follow each other every 4 frames. `focus`/`zoom` frame the stain inside the small card.
export type ThumbsProps = { cards: { clip: string; at: number; caption?: string; delay?: number; focus?: Point; zoom?: number }[] };


export const Thumbs: React.FC<Base> = ({ ov, dur, instant }) => {
  const { fps } = useVideoConfig();
  const p = (ov.props ?? {}) as ThumbsProps;
  const { frame, exit } = useEnterExit(dur, { instant });
  const cards = (p.cards ?? []).slice(0, 3);
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <div style={{ position: "absolute", top: zones[ov.zone ?? "top"], left: 70, right: 70, display: "flex", gap: 22, justifyContent: "center" }}>
        {cards.map((c, i) => {
          const at = c.delay === undefined ? i * 4 : Math.round(c.delay * fps);
          const k = instant && at === 0 ? 1 : smooth(frame, fps, at, 14);
          const cap = interpolate(frame, [at + 4, at + 12], [0, 1], clamp);
          return (
            <div key={i} style={{ width: THUMB.width, display: "flex", flexDirection: "column", alignItems: "center", gap: 10, translate: `0 ${(1 - k) * 40}px`, opacity: k }}>
              <div style={{ position: "relative", width: THUMB.width, height: THUMB.height, borderRadius: 22, overflow: "hidden", border: `5px solid ${palette.white}`, boxShadow: "0 10px 26px rgba(0,0,0,0.38)", boxSizing: "border-box" }}>
                <Still clip={c.clip} at={c.at} focus={c.focus ?? [0.5, 0.5]} zoom={c.zoom ?? 1} cx={(THUMB.width - 10) / 2} cy={(THUMB.height - 10) / 2} w={THUMB.width - 10} h={THUMB.height - 10} />
              </div>
              {c.caption ? (
                <div style={{ opacity: cap }}>
                  <OutlineText size={30} weight={800} lineHeight={1.05}>{c.caption}</OutlineText>
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// image: a still from public/ (e.g. images/floorplan.png, images/logo.png) that scales in. `frame=card`
// (white border, rounded, shadow) suits floor plans and packshots; `frame=none` suits logos with
// transparency. `at` is the centre as fractions of the frame; `width` in pixels.
export type ImageProps = { src: string; at?: Point; width?: number; frame?: "card" | "none"; caption?: string };

export const ImageCard: React.FC<Base> = ({ ov, dur, instant }) => {
  const { fps } = useVideoConfig();
  const p = (ov.props ?? {}) as ImageProps;
  const { frame, exit } = useEnterExit(dur, { instant });
  const k = instant ? 1 : smooth(frame, fps, 0, 12);
  const width = Math.min(p.width ?? 520, safe.right - safe.left);
  const [cx, cy] = p.at ?? [0.5, 0.3];
  const card = (p.frame ?? "card") === "card";
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <div style={{ position: "absolute", left: cx * size.width - width / 2, top: cy * size.height, translate: "0 -50%", width, display: "flex", flexDirection: "column", alignItems: "center", gap: 12, opacity: k, scale: String(interpolate(k, [0, 1], [0.85, 1])) }}>
        <Img
          src={staticFile(p.src)}
          style={{
            width: "100%",
            borderRadius: card ? 22 : 0,
            border: card ? `${compare.border}px solid ${palette.white}` : undefined,
            boxShadow: card ? "0 18px 50px rgba(0,0,0,0.45)" : undefined,
            filter: card ? undefined : "drop-shadow(0 8px 24px rgba(0,0,0,0.45))",
          }}
        />
        {p.caption ? <OutlineText size={38} weight={800}>{p.caption}</OutlineText> : null}
      </div>
    </AbsoluteFill>
  );
};
