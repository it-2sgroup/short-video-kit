// Text effects. One engine, many looks: `FxText` draws a line of text (a stroke layer under a fill layer, so the outline
// never eats the letters) and animates it with a named effect. Every effect has an entrance driven by `k` (0..1, over
// `fxFrames(fx, text)` frames), an exit driven by `x` (0..1, letters fly apart or the effect's own way out), and some have
// a loop that runs on `frame`. A pure function of its props: nothing here reads the clock.
//   scatter  letters fly in from random places and settle            drop     letters fall and bounce
//   wave     letters rise in a ripple, then keep rippling            elastic  rubbery overshoot, letter by letter
//   flip     letters flip up in 3D                                   slam     the whole line slams in big and shakes
//   stamp    a tilted rubber stamp with an ink ring                  glitch   RGB-split jitter that settles
//   neon     flickers on, then glows                                 shine    a light sweep runs across after it lands
//   maskwipe a coloured bar wipes the text into view                 split    two halves slide in and join
//   typewriter letters appear one by one with a cursor               rise     a quiet rise (the calm default)
//   scramble random glyphs lock into the real letters, left to right blurin   words sharpen out of a soft blur, one after another
//   tracking letters glide together from wide spacing                slice    three bands slide in from alternating sides and snap together
//   popword  each word springs in, tilted, then settles              flap     split-flap board: every cell flips through glyphs
//   strike   "OLD -> NEW": a bar strikes the old text, the new pops  draw     a hand-drawn wavy underline strokes in under the line
import React from "react";
import { Easing, interpolate, spring } from "remotion";
import { fonts, toneColor } from "../../theme";
import { clamp } from "../anim";

export const rand = (i: number, k: number) => {
  const x = Math.sin(i * 127.1 + k * 311.7) * 43758.5453;
  return x - Math.floor(x);
};

export type FxName =
  | "scatter" | "drop" | "wave" | "elastic" | "flip" | "slam" | "stamp" | "glitch" | "neon" | "shine" | "maskwipe" | "split" | "typewriter" | "rise"
  | "scramble" | "blurin" | "tracking" | "slice" | "popword" | "flap" | "strike" | "draw";
export const FX_NAMES: FxName[] = [
  "scatter", "drop", "wave", "elastic", "flip", "slam", "stamp", "glitch", "neon", "shine", "maskwipe", "split", "typewriter", "rise",
  "scramble", "blurin", "tracking", "slice", "popword", "flap", "strike", "draw",
];

const wordCount = (text: string) => Math.max(1, text.trim().split(/\s+/).filter(Boolean).length);

// Frames an effect needs to land (the callers turn this into `k`). The ones that stagger words or letters depend on the text.
const FRAMES: Record<FxName, number | ((text: string) => number)> = {
  scatter: 11, drop: 18, wave: 16, elastic: 16, flip: 16, slam: 9, stamp: 12, glitch: 14, neon: 10, shine: 12, maskwipe: 12, split: 12, rise: 10,
  typewriter: (t) => Math.max(8, Math.round(Array.from(t).length * 0.75)),
  scramble: 26,
  blurin: (t) => 14 + 3 * (wordCount(t) - 1),
  tracking: 18,
  slice: 18,
  popword: (t) => 14 + 4 * (wordCount(t) - 1),
  flap: 26,
  strike: 24,
  draw: 24,
};
export const fxFrames = (fx: FxName, text: string): number => {
  const f = FRAMES[fx];
  return typeof f === "number" ? f : f(text);
};

// Split a word into letters the way a reader sees them (a base letter and its marks stay together).
const glyphs = (w: string): string[] => {
  const Seg = (Intl as unknown as { Segmenter?: new (l: string, o: { granularity: string }) => { segment: (s: string) => Iterable<{ segment: string }> } }).Segmenter;
  return Seg ? Array.from(new Seg("vi", { granularity: "grapheme" }).segment(w), (s) => s.segment) : Array.from(w);
};
const plain = (s: string) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/đ/g, "d").replace(/Đ/g, "D");

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
const easeBar = Easing.bezier(0.5, 0, 0.1, 1);
const unit = (v: number) => Math.min(1, Math.max(0, v));

type FxProps = StrokeProps & { text: string; fx?: FxName; frame: number; k: number; x: number; seed?: number; spread?: number; fps?: number };

// A line drawn as an outline layer under a fill layer (the strike effect draws two of them side by side).
const Dual: React.FC<{ p: StrokeProps; text: string; fillStyle?: React.CSSProperties }> = ({ p, text, fillStyle }) => (
  <div style={{ position: "relative" }}>
    <div aria-hidden style={{ ...base(p), position: "absolute", inset: 0, color: p.stroke, WebkitTextStroke: `${Math.round(p.size * (p.width ?? 0.16))}px ${p.stroke}` }}>
      {text}
    </div>
    <div style={{ ...base(p), position: "relative", color: p.fill, ...fillStyle }}>{text}</div>
  </div>
);

export const FxText: React.FC<FxProps> = ({ text, fx = "scatter", frame, k, x, seed = 0, spread = 1, fps = 30, ...p }) => {
  const t = text.normalize("NFC");
  const words = t.split(" ");
  const starts: number[] = [];
  const wordOf: number[] = []; // letter index -> word index
  let acc = 0;
  words.forEach((w, wi) => {
    starts.push(acc);
    const len = glyphs(w).length;
    for (let c = 0; c < len; c++) wordOf.push(wi);
    acc += len;
  });
  const n = Math.max(1, acc);
  const sec = frame / fps;
  const ef = k * fxFrames(fx, t); // frames since the effect began (float)
  const stagger = (i: number, per: number, win = 0.45) => interpolate(k, [Math.min(0.55, i * per), Math.min(0.55, i * per) + win], [0, 1], clamp);
  const away = (i: number) => (x > 0 ? interpolate(x, [Math.min(0.5, i * 0.012), Math.min(0.5, i * 0.012) + 0.5], [0, 1], clamp) : 0);
  const pool = Array.from(new Set(plain(t).replace(/\s/g, ""))).concat("#@%&*".split("")); // scramble: the letters of the line, plain Latin, plus symbols

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
      case "scramble": {
        // letter i locks at frame 4 + i * step (the whole line is done by ~22 f); until then it flickers at half strength
        const lockAt = 4 + i * Math.min(2, 18 / n);
        const since = ef - lockAt;
        op = k <= 0 ? 0 : since >= 0 ? 1 : 0.55;
        if (since >= 0 && since < 3) sc = 1 + 0.16 * (1 - since / 3); // a small pop as it locks
        break;
      }
      case "tracking":
        op = unit(ef / 8);
        break;
      case "flap":
        op = k > 0 ? 1 : 0;
        break;
      case "shine":
      case "typewriter":
      case "maskwipe":
      case "split":
      case "slice":
      case "strike":
      case "draw":
      case "blurin":
      case "popword":
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

  // the style of a whole word (blurin and popword move words, not letters)
  const wordStyle = (wi: number): React.CSSProperties => {
    if (fx === "blurin") {
      const lf = ef - wi * 3;
      const e = easeOutExpo(unit(lf / 14));
      const b = (1 - e) * p.size * 0.22;
      return { opacity: unit(lf / 6), scale: String(1.12 - 0.12 * e), filter: b > 0.05 ? `blur(${b}px)` : undefined };
    }
    if (fx === "popword") {
      const lf = ef - wi * 4;
      const s = lf >= 14 ? 1 : spring({ frame: Math.max(0, lf), fps, config: { mass: 1, damping: 9, stiffness: 170 }, durationInFrames: 14 });
      return { opacity: lf <= 0 ? 0 : unit(lf / 2), scale: String(0.6 + 0.4 * s), rotate: `${-5 * (1 - s)}deg`, translate: `0 ${18 * (1 - s)}px` };
    }
    return {};
  };

  // scramble: the glyph a cell shows right now, and the split-flap cell (flap)
  const scrambled = (ch: string, i: number) => {
    if (ef >= 4 + i * Math.min(2, 18 / n)) return ch;
    const g = pool[Math.floor(rand(i + seed * 3, Math.floor(frame / 2) + 1) * pool.length)];
    return ch !== ch.toLowerCase() ? g.toUpperCase() : g;
  };
  const flapCell = (ch: string, i: number, layer: "stroke" | "fill") => {
    const cls = /\d/.test(ch) ? "0123456789" : ch !== ch.toLowerCase() ? "ABCDEGHKLMNOPRSTUVXY" : ch !== ch.toUpperCase() ? "abcdeghkmnoprsuvxy" : "";
    const flips = cls ? 3 + Math.floor(rand(i + seed, 9) * 3) : 0;
    const per = 3; // frames per flip
    const local = ef - i * Math.min(1.2, 8 / n);
    if (!cls || local >= per * flips) return <span key={i} style={letter(i, layer)}>{ch}</span>;
    const seq = Array.from({ length: flips }, (_, j) => cls[Math.floor(rand(i + seed, 20 + j) * cls.length)]).concat(ch);
    const j = Math.min(flips - 1, Math.max(0, Math.floor(local / per)));
    const tt = local < 0 ? 0 : (local - j * per) / per; // 0..1 inside flip j
    const topAngle = tt < 0.5 ? -90 * Easing.in(Easing.quad)(tt * 2) : -90;
    const botAngle = tt < 0.5 ? 90 : 90 * (1 - Easing.out(Easing.quad)((tt - 0.5) * 2));
    const half = (g: string, which: "top" | "bottom", angle?: number, hidden?: boolean) => (
      <span
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          justifyContent: "center",
          alignItems: "flex-start",
          clipPath: which === "top" ? "inset(-30% -30% 50% -30%)" : "inset(50% -30% -30% -30%)",
          transform: angle === undefined ? undefined : `perspective(${p.size * 5}px) rotateX(${angle}deg)`,
          backfaceVisibility: "hidden",
          visibility: hidden ? "hidden" : "visible",
        }}
      >
        {g}
      </span>
    );
    return (
      <span key={i} style={{ ...letter(i, layer), position: "relative" }}>
        <span style={{ visibility: "hidden" }}>{ch}</span>
        {half(seq[j + 1], "top")}
        {half(seq[j], "bottom")}
        {half(seq[j], "top", topAngle, tt >= 0.5)}
        {half(seq[j + 1], "bottom", botAngle, tt < 0.5)}
        {layer === "fill" ? <span style={{ position: "absolute", left: "-3%", right: "-3%", top: "50%", height: Math.max(2, p.size * 0.014), background: "rgba(0,0,0,0.5)" }} /> : null}
      </span>
    );
  };

  const strokePx = Math.round(p.size * (p.width ?? 0.16));
  const render = (layer: "stroke" | "fill") => {
    const color = layer === "stroke" ? p.stroke : p.fill;
    const style: React.CSSProperties = {
      ...base(p),
      color,
      ...(layer === "stroke" ? { WebkitTextStroke: `${strokePx}px ${p.stroke}` } : {}),
    };
    if (fx === "tracking") {
      // wide spacing closes to none; the trailing space of the last letter is padded on the left so the line stays centred
      const ls = Math.min(0.35, 3 / n) * (1 - easeOutExpo(unit(ef / 18)));
      style.letterSpacing = p.tracking ? `calc(${p.tracking} + ${ls}em)` : `${ls}em`;
      style.paddingLeft = `${ls}em`;
    }
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
        <span style={{ display: "inline-block", ...wordStyle(wi) }}>
          {glyphs(w).map((ch, ci) => {
            const i = starts[wi] + ci;
            if (fx === "flap") return flapCell(ch, i, layer);
            return (
              <span key={ci} style={fx === "scramble" ? { ...letter(i, layer), position: "relative" } : letter(i, layer)}>
                {fx === "scramble" ? (
                  <>
                    <span style={{ visibility: "hidden" }}>{ch}</span>
                    <span style={{ position: "absolute", inset: 0, display: "flex", justifyContent: "center", alignItems: "flex-start" }}>{scrambled(ch, i)}</span>
                  </>
                ) : (
                  ch
                )}
              </span>
            );
          })}
        </span>
      </React.Fragment>
    )),
    fx === "typewriter" && x === 0 ? (
      <span key="cursor" style={{ opacity: layer === "fill" && Math.floor(frame / 8) % 2 === 0 ? 1 : 0, marginLeft: "0.05em" }}>
        |
      </span>
    ) : null,
  ];

  // container-level effects: a wipe bar, halves, bands, a strike bar, an underline
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
  if (fx === "slice") {
    // three bands cut across the line (the top one whole, so the marks over capitals are never split) slide in from alternating
    // sides, 2 f apart; the cuts overlap by half a percent so no seam shows
    const bands = [
      { clip: "inset(-30% -15% 60% -15%)", dir: -1 },
      { clip: "inset(39.5% -15% 34% -15%)", dir: 1 },
      { clip: "inset(65.5% -15% -40% -15%)", dir: -1 },
    ];
    return (
      <div style={{ position: "relative", textAlign: "center", filter: p.shadow, opacity: 1 - (x > 0 ? x : 0) }}>
        <div style={{ visibility: "hidden" }}>{render("fill")}</div>
        {bands.map((b, bi) => {
          const bf = ef - bi * 2;
          return (
            <div key={bi} style={{ position: "absolute", inset: 0, clipPath: b.clip, translate: `${b.dir * (1 - easeOutExpo(unit(bf / 12))) * 140}px 0`, opacity: unit(bf / 3) }}>
              <div aria-hidden style={{ position: "absolute", inset: 0 }}>{render("stroke")}</div>
              {render("fill")}
            </div>
          );
        })}
      </div>
    );
  }
  if (fx === "strike") {
    // "OLD -> NEW": a tilted bar strikes OLD out (OLD dims), then NEW springs in beside it; without an arrow the whole line is struck
    const parts = t.split(/\s*(?:→|->|=>)\s*/);
    const oldText = parts[0];
    const newText = parts.length > 1 ? parts.slice(1).join(" ") : "";
    const bar0 = easeBar(unit((ef - 2) / 8));
    const dim = 1 - 0.45 * unit((ef - 2) / 8);
    const s = ef >= 22 ? 1 : spring({ frame: Math.max(0, ef - 8), fps, config: { mass: 1, damping: 8, stiffness: 170 }, durationInFrames: 14 });
    const thick = Math.max(6, p.size * 0.1);
    return (
      <div style={{ position: "relative", display: "flex", justifyContent: "center", alignItems: "baseline", gap: p.size * 0.5, filter: p.shadow, opacity: 1 - (x > 0 ? x : 0) }}>
        <div style={{ position: "relative", opacity: k > 0 ? 1 : 0 }}>
          <Dual p={p} text={oldText} fillStyle={{ opacity: dim }} />
          <div style={{ position: "absolute", left: "-0.1em", right: "-0.1em", top: "56%", height: thick, marginTop: -thick / 2, borderRadius: thick / 2, background: toneColor.before, boxShadow: `0 0 0 ${Math.max(2, p.size * 0.025)}px ${p.stroke}`, transformOrigin: "left center", scale: `${bar0} 1`, rotate: "-4deg" }} />
        </div>
        {newText ? (
          <div style={{ opacity: ef <= 8 ? 0 : unit((ef - 8) / 3), scale: String(0.6 + 0.4 * s), rotate: `${-4 * (1 - s)}deg`, transformOrigin: "50% 80%" }}>
            <Dual p={p} text={newText} />
          </div>
        ) : null}
      </div>
    );
  }
  if (fx === "draw") {
    // the line sits still; a wavy underline is wiped in under it, left to right (a tiled wave, so it fits any width), low enough to
    // clear the Vietnamese dots below the baseline
    const prog = easeOutExpo(unit((ef - 8) / 14));
    const wave = "M-20 8 Q-10 0 0 8 T 20 8 T 40 8 T 60 8";
    const tile = (color: string, w: number) => `<path d='${wave}' fill='none' stroke='${color}' stroke-width='${w}' stroke-linecap='round'/>`;
    const svg = `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 16'>${tile(p.stroke, 8)}${tile(toneColor.cta, 4)}</svg>`;
    const tw = p.size * 0.6;
    return (
      <div style={{ ...wrapStyle, opacity: unit(ef / 6) * (1 - (x > 0 ? x : 0)) }}>
        <div aria-hidden style={{ position: "absolute", inset: 0 }}>{render("stroke")}</div>
        {render("fill")}
        <div style={{ position: "absolute", left: "2%", right: "2%", top: "100%", height: tw * 0.4, backgroundImage: `url("data:image/svg+xml,${encodeURIComponent(svg)}")`, backgroundSize: `${tw}px ${tw * 0.4}px`, backgroundRepeat: "repeat-x", clipPath: `inset(0 ${(1 - prog) * 100}% 0 0)` }} />
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
