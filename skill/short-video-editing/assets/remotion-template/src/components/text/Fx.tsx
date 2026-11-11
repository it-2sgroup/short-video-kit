// Text effects. One engine, many looks: `FxText` draws a line of text (a stroke layer under a fill layer, so the outline
// never eats the letters) and animates it with a named effect. Every effect has an entrance driven by `k` (0..1), an exit
// driven by `x` (0..1, letters fly apart or the effect's own way out), and some have a loop that runs on `frame`.
// A pure function of its props: nothing here reads the clock.
//   scatter  letters fly in from random places and settle            drop     letters fall and bounce
//   wave     letters rise in a ripple, then keep rippling            elastic  rubbery overshoot, letter by letter
//   flip     letters flip up in 3D                                   slam     the whole line slams in big and shakes
//   stamp    a tilted rubber stamp with an ink ring                  glitch   RGB-split jitter that settles
//   neon     flickers on, then glows                                 shine    a light sweep runs across after it lands
//   maskwipe a coloured bar wipes the text into view                 split    two halves slide in and join
//   typewriter letters appear one by one with a cursor               rise     a quiet rise (the calm default)
import React from "react";
import { Easing, interpolate } from "remotion";
import { fonts } from "../../theme";
import { clamp } from "../anim";

export const rand = (i: number, k: number) => {
  const x = Math.sin(i * 127.1 + k * 311.7) * 43758.5453;
  return x - Math.floor(x);
};

export type FxName = "scatter" | "drop" | "wave" | "elastic" | "flip" | "slam" | "stamp" | "glitch" | "neon" | "shine" | "maskwipe" | "split" | "typewriter" | "rise";
export const FX_NAMES: FxName[] = ["scatter", "drop", "wave", "elastic", "flip", "slam", "stamp", "glitch", "neon", "shine", "maskwipe", "split", "typewriter", "rise"];

export type StrokeProps = { size: number; fill: string; stroke: string; family?: string; weight?: number; width?: number; shadow?: string; tracking?: string; glow?: string };

const base = (p: StrokeProps): React.CSSProperties => ({
  fontFamily: p.family ?? fonts.sans,
  fontWeight: p.weight ?? 900,
  fontSize: p.size,
  letterSpacing: p.tracking ?? "0",
  lineHeight: 1.12,
  whiteSpace: "pre",
});

const easeOutBack = Easing.bezier(0.34, 1.56, 0.64, 1);
const easeOutExpo = Easing.bezier(0.16, 1, 0.3, 1);

type FxProps = StrokeProps & { text: string; fx?: FxName; frame: number; k: number; x: number; seed?: number; spread?: number; fps?: number };

export const FxText: React.FC<FxProps> = ({ text, fx = "scatter", frame, k, x, seed = 0, spread = 1, fps = 30, ...p }) => {
  const t = text.normalize("NFC");
  const words = t.split(" ");
  const starts: number[] = [];
  let acc = 0;
  words.forEach((w) => {
    starts.push(acc);
    acc += Array.from(w).length;
  });
  const n = Math.max(1, acc);
  const sec = frame / fps;
  const stagger = (i: number, per: number, win = 0.45) => interpolate(k, [Math.min(0.55, i * per), Math.min(0.55, i * per) + win], [0, 1], clamp);
  const away = (i: number) => (x > 0 ? interpolate(x, [Math.min(0.5, i * 0.012), Math.min(0.5, i * 0.012) + 0.5], [0, 1], clamp) : 0);

  // the style of letter i (a scatter-style exit is shared by all letter effects)
  const letter = (i: number, layer: "stroke" | "fill"): React.CSSProperties => {
    const a = away(i);
    const exitDx = (rand(i + seed, 4) - 0.5) * 520 * a;
    const exitDy = (rand(i + seed, 5) - 0.5) * 420 * a - 40 * a;
    const exitRot = (rand(i + seed, 6) - 0.5) * 220 * a;
    const exitScale = 1 - 0.5 * a;
    let dx = 0;
    let dy = 0;
    let rot = 0;
    let sc = 1;
    let op = 1;
    let blur = 0;
    let extra: React.CSSProperties = {};
    switch (fx) {
      case "scatter": {
        const e = stagger(i, 0.022, 0.4);
        const out = (1 - e) * spread;
        dx = (rand(i + seed, 1) - 0.5) * 360 * out;
        dy = (rand(i + seed, 2) - 0.5) * 300 * out;
        rot = (rand(i + seed, 3) - 0.5) * 140 * out;
        sc = 0.45 + 0.55 * e;
        op = Math.min(1, e * 2.2);
        blur = (1 - e) * 7;
        break;
      }
      case "drop": {
        const e = stagger(i, 0.035, 0.5);
        dy = -380 * (1 - Easing.bounce(e));
        op = Math.min(1, e * 6);
        rot = (rand(i + seed, 3) - 0.5) * 30 * (1 - e);
        break;
      }
      case "wave": {
        const e = stagger(i, 0.03, 0.4);
        dy = (1 - easeOutBack(e)) * 90 + (k >= 1 ? Math.sin(sec * 7 + i * 0.55) * (p.size * 0.045) : 0);
        op = Math.min(1, e * 3);
        break;
      }
      case "elastic": {
        const e = stagger(i, 0.03, 0.5);
        sc = interpolate(easeOutBack(e), [0, 1], [0, 1]);
        dy = (1 - e) * 40;
        op = Math.min(1, e * 4);
        rot = (rand(i + seed, 3) - 0.5) * 40 * (1 - e);
        break;
      }
      case "flip": {
        const e = stagger(i, 0.04, 0.45);
        extra = { transform: `perspective(500px) rotateX(${(1 - easeOutBack(e)) * -95}deg)`, transformOrigin: "50% 100%", backfaceVisibility: "hidden" };
        op = Math.min(1, e * 4);
        break;
      }
      case "slam": {
        // the whole line: scale from huge to 1 over the entrance, then a short shake
        const e = easeOutExpo(Math.min(1, k * 1.15));
        sc = 1 + (1 - e) * 2.4;
        op = Math.min(1, k * 8);
        const shake = k >= 0.85 ? Math.max(0, 1 - (sec * fps - 9) / 8) * 7 : 0;
        dx = Math.sin(frame * 3.1 + i) * shake;
        dy = Math.cos(frame * 2.7 + i) * shake;
        break;
      }
      case "stamp": {
        const e = easeOutBack(Math.min(1, k * 1.2));
        sc = 1 + (1 - e) * 1.8;
        rot = -7 + (1 - e) * 14;
        op = Math.min(1, k * 7);
        break;
      }
      case "glitch": {
        const settled = k >= 1;
        const burst = settled ? (Math.floor(frame / 24) % 3 === 0 && frame % 24 < 3 ? 1 : 0) : 1 - k * 0.6;
        const j = burst > 0 ? burst : 0;
        dx = (rand(i + Math.floor(frame / 2), 1) - 0.5) * 26 * j;
        dy = (rand(i + Math.floor(frame / 2), 2) - 0.5) * 10 * j;
        op = settled ? 1 : rand(i + Math.floor(frame / 2), 7) > 0.18 ? 1 : 0.15;
        extra = j > 0.15 && layer === "fill" ? { textShadow: `${-5 * j}px 0 #00E5FF, ${5 * j}px 0 #FF2BD6` } : {};
        break;
      }
      case "neon": {
        const flick = k < 1 ? (Math.floor(frame * 0.7 + i * 1.7) % 4 === 0 ? 0.3 : 1) * Math.min(1, 0.55 + k * 2) : 1; // most letters are lit; a few stutter
        op = flick;
        if (layer === "fill") {
          const glow = p.glow ?? p.fill;
          const pulse = 0.75 + 0.25 * Math.sin(sec * 5);
          extra = { textShadow: `0 0 ${p.size * 0.12}px ${glow}, 0 0 ${p.size * 0.3 * pulse}px ${glow}, 0 0 ${p.size * 0.6}px ${glow}` };
        }
        break;
      }
      case "shine":
      case "typewriter":
      case "maskwipe":
      case "split":
      case "rise":
      default: {
        break;
      }
    }
    if (fx === "typewriter") op = i < Math.floor(k * (n + 1) * 1.02) ? 1 : 0;
    return {
      display: "inline-block",
      translate: `${dx + exitDx}px ${dy + exitDy}px`,
      rotate: `${rot + exitRot}deg`,
      scale: String(sc * exitScale),
      opacity: Math.max(0, op * (1 - a)),
      filter: blur + a * 5 > 0.05 ? `blur(${blur + a * 5}px)` : undefined,
      ...extra,
    };
  };

  const strokePx = Math.round(p.size * (p.width ?? 0.16));
  const render = (layer: "stroke" | "fill") => {
    const color = layer === "stroke" ? p.stroke : p.fill;
    const style: React.CSSProperties = {
      ...base(p),
      color,
      ...(layer === "stroke" ? { WebkitTextStroke: `${strokePx}px ${p.stroke}` } : {}),
    };
    if (fx === "shine" && layer === "fill") {
      // a diagonal highlight travels across the finished text: clip a gradient to the glyphs
      const prog = interpolate(frame, [Math.round(fps * 0.45), Math.round(fps * 0.45) + 18], [-0.3, 1.3], clamp);
      return (
        <div style={{ ...style, position: "relative" }}>
          {renderLetters(layer)}
          <div style={{ position: "absolute", inset: 0, backgroundImage: `linear-gradient(105deg, transparent ${prog * 100 - 14}%, rgba(255,255,255,0.95) ${prog * 100}%, transparent ${prog * 100 + 14}%)`, WebkitBackgroundClip: "text", backgroundClip: "text", color: "transparent" }}>
            {t}
          </div>
        </div>
      );
    }
    return <div style={style}>{renderLetters(layer)}</div>;
  };
  const renderLetters = (layer: "stroke" | "fill") => [
    ...words.map((w, wi) => (
      <React.Fragment key={wi}>
        {wi > 0 ? " " : null}
        <span style={{ display: "inline-block" }}>
          {Array.from(w).map((ch, ci) => (
            <span key={ci} style={letter(starts[wi] + ci, layer)}>
              {ch}
            </span>
          ))}
        </span>
      </React.Fragment>
    )),
    fx === "typewriter" && x === 0 ? (
      <span key="cursor" style={{ opacity: layer === "fill" && Math.floor(frame / 8) % 2 === 0 ? 1 : 0, marginLeft: "0.05em" }}>
        |
      </span>
    ) : null,
  ];

  // container-level effects: a wipe bar, a split in two halves, a cursor
  let wrapStyle: React.CSSProperties = { position: "relative", textAlign: "center", filter: p.shadow };
  let bar: React.ReactNode = null;
  if (fx === "maskwipe") {
    const e = easeOutExpo(Math.min(1, k * 1.1));
    wrapStyle = { ...wrapStyle, clipPath: `inset(-20% ${(1 - e) * 100}% -20% 0)` };
    bar = e < 1 && x === 0 ? <div style={{ position: "absolute", top: "-4%", bottom: "-4%", left: `${e * 100}%`, width: "0.14em", background: p.fill, transform: "skewX(-12deg)", boxShadow: `0 0 18px ${p.fill}` }} /> : null;
  }
  if (fx === "split") {
    const e = easeOutExpo(Math.min(1, k * 1.15));
    const half = (clip: string, dir: number) => (
      <div style={{ position: "absolute", inset: 0, clipPath: clip, translate: `${dir * (1 - e) * 700}px 0` }}>
        <div aria-hidden style={{ position: "absolute", inset: 0 }}>{render("stroke")}</div>
        {render("fill")}
      </div>
    );
    return (
      <div style={{ position: "relative", textAlign: "center", filter: p.shadow, opacity: 1 - (x > 0 ? x : 0) }}>
        <div style={{ visibility: "hidden" }}>{render("fill")}</div>
        {half("inset(0 0 50% 0)", -1)}
        {half("inset(50% 0 0 0)", 1)}
      </div>
    );
  }
  // the stamp's frame: a double rule round the line, pressed in a hair after the text lands
  const ring =
    fx === "stamp" ? (
      <div style={{ position: "absolute", inset: "-0.12em -0.28em", border: `${Math.max(3, p.size * 0.045)}px solid ${p.fill}`, borderRadius: "0.22em", outline: `${Math.max(2, p.size * 0.025)}px solid ${p.fill}`, outlineOffset: `${p.size * 0.05}px`, opacity: interpolate(k, [0.45, 0.8], [0, 0.9], clamp), scale: String(interpolate(k, [0.45, 1], [1.25, 1], clamp)), rotate: "-1.5deg" }} />
    ) : null;
  return (
    <div style={wrapStyle}>
      {ring}
      <div aria-hidden style={{ position: "absolute", inset: 0 }}>
        {render("stroke")}
      </div>
      {render("fill")}
      {bar}
    </div>
  );
};
