// HyperFrames renderer for a project.json: scenes with centred transitions, a continuous virtual
// camera, accents on cuts, overlays, captions. The same maths as the Remotion template
// (assets/remotion-template/src), written as one pure function of the frame: render(frame) sets
// every element's style from the project, so any seek (forward, backward, random) is exact.
// The generated index.html embeds the project as window.__SVK_PROJECT__ before this file loads;
// GSAP only drives the playhead. Nothing here reads a clock or a random number.
(function () {
  "use strict";
  const P = window.__SVK_PROJECT__;
  const W = P.width, H = P.height, FPS = P.fps, DUR = P.duration;

  // ---------- tokens (assets/remotion-template/src/theme.ts) ----------
  const THEMES = {
    cool: {
      palette: { white: "#FFFFFF", ice: "#DCE7F4", sky: "#A8D0FF", royal: "#2F64E0", navy: "#15224C", ink: "#0B1020", shadow: "rgba(10,25,60,0.45)" },
      tones: { before: "#FF7A6E", after: "#4AE3A4", cta: "#FFD23F", product: "#FF8FC2" },
      title: { sky: "#FFFFFF 0%, #FFFFFF 40%, #C4DBFF 100%", accent: "#FFFFFF 0%, #E3EEFF 45%, #8FB8FF 100%", glassText: "#0B1F4D 0%, #2F64E0 100%", glassLead: "#1B2A4A", glassBg: "linear-gradient(160deg, rgba(255,255,255,0.93), rgba(226,236,250,0.86))", glassBorder: "1.5px solid rgba(255,255,255,0.75)", glassShadow: "0 20px 60px rgba(10,30,80,0.28)" },
    },
    warm: {
      palette: { white: "#FFF6E4", ice: "#F1DFC0", sky: "#F3C06A", royal: "#B8322A", navy: "#4A2415", ink: "#1C0F08", shadow: "rgba(40,16,4,0.5)" },
      tones: { before: "#E8735A", after: "#F3C06A", cta: "#F6B94A", product: "#E8896B" },
      title: { sky: "#FFF6E4 0%, #FFF6E4 40%, #F7D9A0 100%", accent: "#FFF1D0 0%, #F6C46A 50%, #E39A3B 100%", glassText: "#4A1A10 0%, #B8322A 100%", glassLead: "#4A2415", glassBg: "linear-gradient(160deg, rgba(255,247,230,0.94), rgba(243,224,188,0.88))", glassBorder: "1.5px solid rgba(255,238,205,0.8)", glassShadow: "0 20px 60px rgba(60,25,5,0.32)" },
    },
    luxe: {
      palette: { white: "#FFFCF5", ice: "#EDE4D3", sky: "#D9BF8C", royal: "#9C7A3C", navy: "#23211E", ink: "#141210", shadow: "rgba(15,12,8,0.5)" },
      tones: { before: "#C98B6B", after: "#B9D3B0", cta: "#E8C77E", product: "#D9BF8C" },
      title: { sky: "#FFFCF5 0%, #FFFCF5 45%, #EBDDBF 100%", accent: "#FFF6E0 0%, #E8CF95 50%, #C49A4A 100%", glassText: "#23211E 0%, #6E5426 100%", glassLead: "#3A342A", glassBg: "linear-gradient(160deg, rgba(255,252,245,0.94), rgba(237,228,211,0.88))", glassBorder: "1.5px solid rgba(255,248,230,0.8)", glassShadow: "0 20px 60px rgba(20,15,5,0.3)" },
    },
  };
  const T = THEMES[P.theme] || THEMES.cool;
  const pal = T.palette;
  const toneColor = Object.assign({ neutral: pal.white }, T.tones);
  const FONT = { sans: '"Be Vietnam Pro", sans-serif', accent: '"Playfair Display", serif', number: '"Anton", sans-serif' };
  const safe = { left: 60, right: 900, top: 220, bottom: 1400 };
  const zones = { top: 236, upper: 470, center: 860, lower: 1230 };
  const CAP = { size: 58, left: 90, right: 190, lift: 120, popSize: 66, popWords: 5, popChars: 20 };
  const captionTop = P.layout === "reels-ad" ? 1100 : 1340;
  const cartPoint = { x: 112, y: 1677 };
  const INFO = { iconSize: 54, specGap: 26, labelSize: 40, statSize: 150, barHeight: 34, barGap: 22, chartWidth: 760 };
  const CAM = { defaultPush: [1.0, 1.16], defaultPull: [1.24, 1.0], defaultPan: 0.08, punchFrames: 6, maxScale: 1.7 };

  // ---------- maths: easing, interpolate, spring (Remotion semantics) ----------
  const clamp01 = (x) => Math.min(1, Math.max(0, x));
  const bezier = (x1, y1, x2, y2) => {
    const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx;
    const cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
    const sx = (t) => ((ax * t + bx) * t + cx) * t;
    const sy = (t) => ((ay * t + by) * t + cy) * t;
    const dx = (t) => (3 * ax * t + 2 * bx) * t + cx;
    return (x) => {
      if (x <= 0) return 0;
      if (x >= 1) return 1;
      let t = x;
      for (let i = 0; i < 8; i++) {
        const e = sx(t) - x;
        if (Math.abs(e) < 1e-6) return sy(t);
        const d = dx(t);
        if (Math.abs(d) < 1e-6) break;
        t -= e / d;
      }
      let lo = 0, hi = 1;
      t = x;
      for (let i = 0; i < 40; i++) {
        const e = sx(t);
        if (Math.abs(e - x) < 1e-6) break;
        if (e < x) lo = t; else hi = t;
        t = (lo + hi) / 2;
      }
      return sy(t);
    };
  };
  const EASE = {
    out: bezier(0.16, 1, 0.3, 1), inOut: bezier(0.65, 0, 0.35, 1), exit: bezier(0.4, 0, 1, 1), camera: bezier(0.33, 0, 0.67, 1),
    outCubic: (t) => 1 - Math.pow(1 - clamp01(t), 3),
    inOutSin: (t) => { const s = (u) => 1 - Math.cos((u * Math.PI) / 2); return t < 0.5 ? s(t * 2) / 2 : 1 - s((1 - t) * 2) / 2; },
  };
  // Multi-point clamped interpolation: interp(x, [x0,x1,..], [y0,y1,..], ease?)
  const interp = (x, xs, ys, ease) => {
    if (x <= xs[0]) return ys[0];
    if (x >= xs[xs.length - 1]) return ys[ys.length - 1];
    let i = 0;
    while (x > xs[i + 1]) i++;
    let t = (x - xs[i]) / (xs[i + 1] - xs[i]);
    if (ease) t = ease(t);
    return ys[i] + (ys[i + 1] - ys[i]) * t;
  };
  const SPRINGS = { smooth: { damping: 200, mass: 1, stiffness: 100 }, pop: { damping: 12, stiffness: 220, mass: 0.6 } };
  const springAt = (t, c) => {
    const w0 = Math.sqrt(c.stiffness / c.mass), z = c.damping / (2 * Math.sqrt(c.stiffness * c.mass));
    if (z < 1) {
      const w1 = w0 * Math.sqrt(1 - z * z);
      return 1 - Math.exp(-z * w0 * t) * (Math.cos(w1 * t) + ((z * w0) / w1) * Math.sin(w1 * t));
    }
    if (z === 1) return 1 - Math.exp(-w0 * t) * (1 + w0 * t);
    const s = Math.sqrt(z * z - 1), r1 = -w0 * (z - s), r2 = -w0 * (z + s);
    return 1 - (r2 * Math.exp(r1 * t) - r1 * Math.exp(r2 * t)) / (r2 - r1);
  };
  const settleCache = {};
  const settleFrames = (c) => {
    const key = c.damping + "/" + c.stiffness + "/" + c.mass;
    if (settleCache[key]) return settleCache[key];
    let last = 1;
    for (let f = 1; f < 900; f++) if (Math.abs(1 - springAt(f / FPS, c)) > 0.005) last = f + 1;
    return (settleCache[key] = last);
  };
  const spring = (frame, cfg, durationInFrames) => {
    if (frame <= 0) return 0;
    let f = frame;
    if (durationInFrames) f = (frame * settleFrames(cfg)) / durationInFrames;
    return springAt(f / FPS, cfg);
  };
  const pop = (f, delay) => spring(f - (delay || 0), SPRINGS.pop);
  const smooth = (f, delay, dur) => spring(f - (delay || 0), SPRINGS.smooth, dur);
  // enter 0->1 after `delay`, exit 1->0 over the last frames; `instant` skips the entrance (frame 0 is the thumbnail)
  const enterExit = (f, dur, o) => {
    o = o || {};
    const d = o.delay || 0, a = o.enter || 10, b = o.exit || 8;
    const enter = o.instant ? 1 : interp(f, [d, d + a], [0, 1], EASE.out);
    const exit = interp(f, [dur - b, dur], [1, 0], EASE.exit);
    return { enter, exit };
  };
  const fitSize = (text, width, max, min) => Math.max(min, Math.min(max, width / Math.max(1, text.length * 0.56)));
  const num = (v, dec) => new Intl.NumberFormat("vi-VN", { minimumFractionDigits: dec, maximumFractionDigits: dec }).format(v);

  // ---------- DOM helpers ----------
  const $ = (id) => document.getElementById(id);
  const mk = (tag, style, parent, text) => {
    const e = document.createElement(tag);
    if (style) Object.assign(e.style, style);
    if (text != null) e.textContent = text;
    if (parent) parent.appendChild(e);
    return e;
  };
  const svg = (parent, style) => {
    const s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    s.setAttribute("width", W); s.setAttribute("height", H);
    Object.assign(s.style, { position: "absolute", left: 0, top: 0 }, style || {});
    parent.appendChild(s);
    return s;
  };
  const path = (parent, d, attrs) => {
    const p = document.createElementNS("http://www.w3.org/2000/svg", "path");
    p.setAttribute("d", d);
    p.setAttribute("fill", "none");
    for (const k in attrs || {}) p.setAttribute(k, attrs[k]);
    parent.appendChild(p);
    p._len = p.getTotalLength();
    return p;
  };
  const evolve = (p, k) => { p.setAttribute("stroke-dasharray", p._len); p.setAttribute("stroke-dashoffset", p._len * (1 - clamp01(k))); };
  const base = (o) => ({
    fontFamily: o.family || FONT.sans, fontWeight: String(o.weight || 800), fontStyle: o.italic ? "italic" : "normal", fontSize: o.size + "px",
    letterSpacing: o.tracking != null ? o.tracking : "-0.02em", lineHeight: String(o.lineHeight || 1.12), textAlign: o.align || "center", whiteSpace: "pre-wrap",
  });
  // Solid fill over a dark outline layer, so the stroke never eats the letters. Returns {root, set(text)}.
  const outlineText = (parent, text, o) => {
    const root = mk("div", Object.assign({ position: "relative" }, base(o)), parent);
    const under = mk("div", Object.assign(base(o), { position: "absolute", inset: "0", color: pal.ink, webkitTextStroke: Math.round(o.size / 7) + "px " + pal.ink, textShadow: "0 8px 22px rgba(0,0,0,0.5)" }), root, text);
    under.setAttribute("data-layout-ignore", ""); // the outline layer repeats the text: not a second text block for `check`
    under.setAttribute("aria-hidden", "true");
    const over = mk("div", Object.assign(base(o), { position: "relative", color: o.color || pal.white }), root, text);
    return { root, set: (t) => { under.textContent = t; over.textContent = t; }, over };
  };
  const gradientText = (parent, text, o) => {
    const wrap = mk("div", { filter: o.shadow === false ? "" : "drop-shadow(0 6px 18px " + pal.shadow + ") drop-shadow(0 2px 4px rgba(0,0,0,0.35))" }, parent);
    const t = mk("div", Object.assign(base(o), { backgroundImage: "linear-gradient(" + (o.angle == null ? 180 : o.angle) + "deg, " + o.stops + ")", webkitBackgroundClip: "text", backgroundClip: "text", color: "transparent", paddingRight: o.italic ? "0.15em" : "" }), wrap, text);
    return { root: wrap, set: (s) => { t.textContent = s; } };
  };
  const maskRise = (parent) => {
    const outer = mk("div", { overflow: "hidden", paddingTop: "0.28em", marginTop: "-0.28em" }, parent);
    const inner = mk("div", null, outer);
    return { outer, inner, set: (k) => { inner.style.translate = "0 " + (1 - k) * 105 + "%"; } };
  };
  const splitAccent = (line, accent) => {
    if (!accent) return [line, "", ""];
    const i = line.toLocaleLowerCase("vi").indexOf(accent.toLocaleLowerCase("vi"));
    return i < 0 ? [line, "", ""] : [line.slice(0, i), line.slice(i, i + accent.length), line.slice(i + accent.length)];
  };
  const list = (v) => (Array.isArray(v) ? v.map(String) : v ? [String(v)] : []);
  const topOf = (ov, fallback) => zones[ov.zone || fallback];

  // ---------- overlays: each factory returns update(f, dur, instant) ----------
  const ICONS = {
    area: "M4 9V4h5 M15 4h5v5 M20 15v5h-5 M9 20H4v-5 M8 8l8 8 M16 8l-8 8", bed: "M3 18V7 M3 14h18v4 M21 14v-2a3 3 0 0 0-3-3h-7v5 M6.5 11.5a1.5 1.5 0 1 0 0-.01",
    bath: "M4 12h16v2a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5z M6 12V6a2 2 0 0 1 4 0 M7 19l-1 2 M17 19l1 2", compass: "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18 M15.5 8.5l-2 5-5 2 2-5z",
    car: "M5 16h14v-4l-2-5H7l-2 5z M5 12h14 M7 16v2 M17 16v2 M8 14h.01 M16 14h.01", floor: "M4 20h4v-4h4v-4h4V8h4 M4 20h16", tree: "M12 21v-6 M12 3l6 9H6z M9 15h6",
    pool: "M3 16c2 0 2-1.5 4.5-1.5S10 16 12 16s2-1.5 4.5-1.5S19 16 21 16 M3 20c2 0 2-1.5 4.5-1.5S10 20 12 20s2-1.5 4.5-1.5S19 20 21 20 M8 13V5a2 2 0 0 1 4 0 M14 13V5",
    clock: "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18 M12 7v5l3 2", tag: "M3 12V4h8l10 10-8 8z M7.5 8a.5.5 0 1 0 0-.01", pin: "M12 21s-7-6.5-7-12a7 7 0 0 1 14 0c0 5.5-7 12-7 12z M12 9a2 2 0 1 0 0-.01",
    star: "M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z",
  };
  const icon = (parent, name, px, color) => {
    const s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    s.setAttribute("width", px); s.setAttribute("height", px); s.setAttribute("viewBox", "0 0 24 24");
    Object.assign(s.style, { filter: "drop-shadow(0 3px 8px rgba(0,0,0,0.5))", flexShrink: "0" });
    const p = document.createElementNS("http://www.w3.org/2000/svg", "path");
    p.setAttribute("d", ICONS[name] || ICONS.star); p.setAttribute("fill", "none"); p.setAttribute("stroke", color || pal.white);
    p.setAttribute("stroke-width", 1.8); p.setAttribute("stroke-linecap", "round"); p.setAttribute("stroke-linejoin", "round");
    s.appendChild(p); parent.appendChild(s);
    return s;
  };
  const layer = (parent) => mk("div", { position: "absolute", inset: "0" }, parent);
  const col = (parent, style) => mk("div", Object.assign({ position: "absolute", display: "flex", flexDirection: "column" }, style), parent);

  const FACTORY = {
    title(root, ov) {
      const p = ov.props || {}, style = p.style || "outline", lines = (p.lines || []).filter(Boolean);
      const tone = toneColor[ov.tone || "neutral"];
      const width = ov.zone === "lower" || ov.zone === "center" ? 820 : 900;
      const lead = lines.length > 1 ? lines[0] : undefined, main = lines[lines.length - 1] || "";
      const [pre, acc, post] = splitAccent(main, p.accent);
      const box = col(root, { top: topOf(ov, "top") + "px", left: (W - width) / 2 + "px", width: width + "px", alignItems: "center" });
      const parts = { enterEls: [], rises: [] };
      const addRise = (parent) => { const m = maskRise(parent); parts.rises.push(m); return m.inner; };
      let accentEl = null, sweepEl = null, sweepTxt = null, glassEl = null, leadEl = null, mainEls = [];
      if (style === "stack") {
        const size = fitSize(main, width, 112, 68);
        if (lead) { leadEl = mk("div", { alignSelf: "flex-start", marginLeft: "24px" }, box); gradientText(leadEl, lead, { size: 40, weight: 500, stops: pal.white + ", " + pal.white }); }
        const inner = addRise(box);
        const row = mk("div", { display: "flex", alignItems: "baseline", justifyContent: "center", gap: Math.round(size * 0.22) + "px" }, inner);
        if (pre.trim()) gradientText(row, pre.trim(), { size, weight: 900, stops: T.title.sky, tracking: "-0.035em", lineHeight: 1.05 });
        if (acc) { accentEl = mk("span", { display: "inline-block" }, row); gradientText(accentEl, acc, { size: size * 1.08, family: FONT.accent, weight: 700, italic: true, stops: T.title.accent, tracking: "0" }); }
        if (post.trim()) gradientText(row, post.trim(), { size, weight: 900, stops: T.title.sky, tracking: "-0.035em", lineHeight: 1.05 });
      } else if (style === "gradient") {
        lines.forEach((line, i) => {
          const last = i === lines.length - 1;
          const inner = addRise(box);
          const wrap = mk("div", null, inner); mainEls.push(wrap);
          gradientText(wrap, line, { size: last ? fitSize(line, width, 104, 62) : 42, weight: last ? 900 : 700, stops: T.title.sky, tracking: "-0.04em" });
        });
      } else if (style === "glass") {
        glassEl = mk("div", { width: Math.min(width, 740) + "px", padding: "20px 34px 24px", borderRadius: "32px", background: T.title.glassBg, border: T.title.glassBorder, boxShadow: T.title.glassShadow, display: "flex", flexDirection: "column", alignItems: "center", boxSizing: "border-box" }, box);
        if (lead) mk("div", { fontFamily: FONT.sans, fontWeight: "500", fontSize: "32px", color: T.title.glassLead }, glassEl, lead);
        const inner = addRise(glassEl);
        gradientText(inner, main, { size: fitSize(main, 740 - 68, 84, 50), weight: 900, angle: 90, stops: T.title.glassText, tracking: "-0.04em", shadow: false });
      } else if (style === "marker") {
        const size = fitSize(main, width, 80, 54);
        const inner = addRise(box);
        const row = mk("div", { fontFamily: FONT.sans, fontWeight: "900", fontSize: size + "px", display: "flex", gap: Math.round(size * 0.22) + "px", justifyContent: "center", flexWrap: "wrap" }, inner);
        if (pre.trim()) outlineText(row, pre.trim(), { size, weight: 900 });
        if (acc) {
          const holder = mk("span", { position: "relative", display: "inline-block", padding: "0 0.12em" }, row);
          sweepEl = mk("span", { position: "absolute", inset: "0.16em 0 0.02em 0", background: tone === pal.white ? toneColor.cta : tone, borderRadius: "0.14em", transformOrigin: "left center", rotate: "-1.5deg", boxShadow: "0 8px 22px rgba(0,0,0,0.35)" }, holder);
          sweepTxt = mk("span", { position: "relative", fontFamily: FONT.sans, fontWeight: "900", fontSize: size + "px", lineHeight: "1.12" }, holder, acc);
        }
        if (post.trim()) outlineText(row, post.trim(), { size, weight: 900 });
      } else {
        const size = fitSize(main, width, 76, 50);
        if (lead) { leadEl = mk("div", null, box); outlineText(leadEl, lead, { size: 38, weight: 700 }); }
        const m = mk("div", null, box); mainEls.push(m);
        outlineText(m, main, { size, weight: 800, color: tone });
      }
      let subEl = null;
      if (p.sub) { subEl = mk("div", { marginTop: "8px" }, box); outlineText(subEl, p.sub, { size: 32, weight: 700 }); }
      return (f, dur, instant) => {
        const { enter, exit } = enterExit(f, dur, { delay: instant ? 0 : 4, instant });
        const rise = instant ? 1 : smooth(f, 4, 14), accentIn = instant ? 1 : smooth(f, 10, 12);
        box.style.opacity = exit; box.style.translate = "0 " + (1 - exit) * -12 + "px";
        if (style === "stack") {
          if (leadEl) { leadEl.style.opacity = enter; leadEl.style.translate = "0 " + (1 - enter) * 24 + "px"; }
          parts.rises[0].set(rise);
          if (accentEl) { accentEl.style.opacity = accentIn; accentEl.style.filter = "blur(" + (1 - accentIn) * 12 + "px)"; accentEl.style.scale = String(interp(accentIn, [0, 1], [1.08, 1])); }
        } else if (style === "gradient") {
          parts.rises.forEach((m, i) => m.set(instant ? 1 : smooth(f, 4 + i * 3, 15)));
          mainEls.forEach((e) => { e.style.scale = String(interp(f, [0, 20], [1.04, 1])); });
        } else if (style === "glass") {
          const card = instant ? 1 : smooth(f, 0, 18);
          glassEl.style.scale = String(interp(card, [0, 1], [0.92, 1])); glassEl.style.translate = "0 " + (1 - card) * 40 + "px"; glassEl.style.opacity = card;
          parts.rises[0].set(rise);
        } else if (style === "marker") {
          parts.rises[0].set(rise);
          const sweep = instant ? 1 : interp(f, [10, 22], [0, 1]);
          if (sweepEl) { sweepEl.style.scale = sweep + " 1"; sweepTxt.style.color = sweep > 0.5 ? pal.ink : pal.white; }
        } else {
          if (leadEl) leadEl.style.opacity = enter;
          mainEls.forEach((e) => { e.style.opacity = enter; e.style.translate = "0 " + (1 - enter) * 24 + "px"; });
        }
        if (subEl) subEl.style.opacity = enter;
      };
    },

    callout(root, ov) {
      const p = ov.props || {};
      const tx = p.target[0] * W, ty = p.target[1] * H;
      const side = p.side || (tx > W / 2 ? "left" : "right");
      const ly = (p.labelY != null ? p.labelY : p.target[1]) * H, labelW = 380;
      const lx = side === "left" ? safe.left + labelW : safe.right - labelW;
      const el = layer(root), s = svg(el);
      const line = path(s, "M " + tx + " " + ty + " L " + lx + " " + ly, { stroke: pal.white, "stroke-width": 4, "stroke-linecap": "round" });
      line.style.filter = "drop-shadow(0 2px 6px rgba(0,0,0,0.45))";
      const outer = document.createElementNS("http://www.w3.org/2000/svg", "circle"), inner = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      [[outer, "rgba(255,255,255,0.35)"], [inner, pal.white]].forEach(([c, fill]) => { c.setAttribute("cx", tx); c.setAttribute("cy", ty); c.setAttribute("fill", fill); s.appendChild(c); });
      const lab = mk("div", { position: "absolute", top: ly - 40 + "px", width: labelW + "px", boxSizing: "border-box", textAlign: side === "left" ? "left" : "right", padding: "10px 20px", borderRadius: "18px", background: "linear-gradient(160deg, rgba(255,255,255,0.95), rgba(226,236,250,0.9))", boxShadow: "0 10px 30px rgba(20,40,80,0.3)", fontFamily: FONT.sans, fontWeight: "800", fontSize: "34px", lineHeight: "1.15", color: pal.navy }, el, p.label);
      if (side === "left") lab.style.left = safe.left + "px"; else lab.style.right = W - safe.right + "px";
      return (f, dur, instant) => {
        const { exit } = enterExit(f, dur, { instant });
        const dot = instant ? 1 : pop(f, 0), ln = instant ? 1 : interp(f, [4, 14], [0, 1]), lb = instant ? 1 : interp(f, [10, 20], [0, 1]);
        el.style.opacity = exit; outer.setAttribute("r", 22 * dot); inner.setAttribute("r", 10 * dot); evolve(line, ln);
        lab.style.opacity = lb; lab.style.translate = (1 - lb) * (side === "left" ? -30 : 30) + "px 0";
      };
    },

    highlight(root, ov) {
      const p = ov.props || {}, x = p.target[0] * W, y = p.target[1] * H, r = (p.size || 0.12) * W, shape = p.shape || "circle";
      const d = shape === "underline" ? "M " + (x - r) + " " + y + " Q " + x + " " + (y + 18) + " " + (x + r) + " " + (y - 6)
        : shape === "arrow" ? "M " + (x - r * 1.6) + " " + (y - r * 1.6) + " Q " + (x - r * 0.4) + " " + (y - r * 1.4) + " " + (x - 10) + " " + (y - 10) + " M " + (x - 10) + " " + (y - 10) + " L " + (x - 60) + " " + (y - 22) + " M " + (x - 10) + " " + (y - 10) + " L " + (x - 24) + " " + (y - 62)
        : "M " + (x + r) + " " + y + " C " + (x + r) + " " + (y - r * 0.9) + ", " + (x - r) + " " + (y - r * 1.05) + ", " + (x - r * 1.02) + " " + y + " C " + (x - r) + " " + (y + r) + ", " + (x + r * 1.1) + " " + (y + r * 0.95) + ", " + (x + r * 0.9) + " " + (y - r * 0.3);
      const color = ov.tone && ov.tone !== "neutral" ? toneColor[ov.tone] : toneColor.cta;
      const el = layer(root), s = svg(el, { filter: "drop-shadow(0 3px 8px rgba(0,0,0,0.5))" });
      const pa = path(s, d, { stroke: color, "stroke-width": 10, "stroke-linecap": "round", "stroke-linejoin": "round" });
      return (f, dur, instant) => { el.style.opacity = enterExit(f, dur, { instant }).exit; evolve(pa, instant ? 1 : interp(f, [0, 10], [0, 1])); };
    },

    step(root, ov) {
      const p = ov.props || {};
      const row = mk("div", { position: "absolute", top: topOf(ov, "top") + "px", left: "60px", right: "60px", display: "flex", alignItems: "center", justifyContent: "center", gap: "24px" }, root);
      const chip = mk("div", { width: "80px", height: "80px", borderRadius: "40px", background: "linear-gradient(180deg, " + pal.royal + ", " + pal.navy + ")", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 8px 22px rgba(10,25,60,0.45)", flexShrink: "0" }, row);
      mk("span", { fontFamily: FONT.number, fontSize: "52px", color: pal.white, lineHeight: "1" }, chip, String(p.n));
      const txt = mk("div", { textAlign: "left" }, row);
      outlineText(txt, p.text, { size: 46, weight: 800 });
      return (f, dur, instant) => {
        const { enter, exit } = enterExit(f, dur, { instant, delay: 3 });
        row.style.opacity = exit; chip.style.scale = String(instant ? 1 : pop(f, 0)); txt.style.opacity = enter; txt.style.translate = (1 - enter) * 20 + "px 0";
      };
    },

    checklist(root, ov) {
      const p = ov.props || {}, items = p.items || [];
      const rows = items.reduce((n, it) => n + Math.ceil(it.length / 26), 0);
      const height = rows * 52 + items.length * 14 + (p.title ? 64 : 0);
      const top = Math.min(zones[ov.zone || "lower"], captionTop - 30 - height);
      const box = col(root, { top: top + "px", left: "90px", right: "200px", gap: "14px" });
      if (p.title) outlineText(box, p.title, { size: 44, weight: 800 });
      const TICK = "M 8 26 L 22 40 L 48 12";
      const rowsEl = items.map((item) => {
        const r = mk("div", { display: "flex", alignItems: "center", gap: "22px" }, box);
        const s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        s.setAttribute("width", 52); s.setAttribute("height", 46); s.setAttribute("viewBox", "0 0 56 52"); Object.assign(s.style, { flexShrink: "0", filter: "drop-shadow(0 3px 8px rgba(0,0,0,0.5))" });
        r.appendChild(s);
        const tick = path(s, TICK, { stroke: toneColor.after, "stroke-width": 9, "stroke-linecap": "round", "stroke-linejoin": "round" });
        outlineText(r, item, { size: 42, weight: 800, align: "left" });
        return { r, tick };
      });
      return (f, dur, instant) => {
        box.style.opacity = enterExit(f, dur, { instant }).exit;
        rowsEl.forEach((o, i) => {
          const t = instant ? 1 : interp(f, [i * 9, i * 9 + 8], [0, 1]);
          o.r.style.opacity = t; o.r.style.translate = (1 - t) * -24 + "px 0"; evolve(o.tick, instant ? 1 : interp(f, [i * 9 + 3, i * 9 + 11], [0, 1]));
        });
      };
    },

    price(root, ov) {
      const p = ov.props || {};
      const box = col(root, { top: topOf(ov, "lower") + "px", left: "60px", width: "840px", alignItems: "center" });
      if (p.label) outlineText(box, p.label, { size: 46, weight: 700 });
      const row = mk("div", { display: "flex", alignItems: "baseline", gap: "10px" }, box);
      if (p.prefix) outlineText(row, p.prefix, { size: 60, weight: 800 });
      const g = gradientText(row, "0", { size: 190, family: FONT.number, weight: 400, stops: "#FFF6C9 0%, " + toneColor.cta + " 100%", tracking: "0", lineHeight: 1 });
      if (p.unit) outlineText(row, p.unit, { size: 84, weight: 800, color: toneColor.cta });
      let strikeEl = null;
      if (p.old) {
        const o = mk("div", { position: "relative", marginTop: "6px" }, box);
        outlineText(o, p.old, { size: 48, weight: 700 });
        strikeEl = mk("div", { position: "absolute", left: "-6px", right: "-6px", top: "52%", height: "6px", background: toneColor.before, transformOrigin: "left", borderRadius: "3px" }, o);
      }
      const dec = p.decimals || 0;
      return (f, dur, instant) => {
        const { enter, exit } = enterExit(f, dur, { instant });
        const count = instant ? 1 : interp(f, [0, 24], [0, 1], EASE.outCubic);
        row.style.scale = String(interp(f, [24, 27, 30], [1, 1.08, 1]));
        g.set(num((p.value || 0) * count, dec));
        if (strikeEl) strikeEl.style.scale = interp(f, [14, 22], [0, 1]) + " 1";
        box.style.opacity = Math.min(enter, exit);
      };
    },

    cart(root, ov) {
      const p = ov.props || {};
      const tip = { x: cartPoint.x, y: cartPoint.y - 58 }, tail = { x: tip.x + 120, y: tip.y - 100 };
      const curve = "M " + tail.x + " " + tail.y + " Q " + tip.x + " " + tail.y + " " + tip.x + " " + tip.y;
      const head = "M " + (tip.x - 40) + " " + (tip.y - 46) + " L " + tip.x + " " + tip.y + " L " + (tip.x + 40) + " " + (tip.y - 46);
      const el = layer(root);
      let label = null;
      if (p.text) {
        label = mk("div", { position: "absolute", top: (ov.zone ? zones[ov.zone] : tail.y - 32) + "px", left: tail.x + 26 + "px", width: "600px", transformOrigin: "left center" }, el);
        outlineText(label, p.text, { size: 50, weight: 900, color: toneColor.cta, align: "left" });
      }
      const s = svg(el, { filter: "drop-shadow(0 4px 10px rgba(0,0,0,0.45))" });
      const paths = [{ w: 24, c: pal.ink }, { w: 14, c: toneColor.cta }].map((st) => {
        const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
        g.setAttribute("fill", "none"); g.setAttribute("stroke", st.c); g.setAttribute("stroke-width", st.w); g.setAttribute("stroke-linecap", "round"); g.setAttribute("stroke-linejoin", "round");
        s.appendChild(g);
        return { body: path(g, curve), head: path(g, head) };
      });
      return (f, dur, instant) => {
        el.style.opacity = enterExit(f, dur, { instant }).exit;
        if (label) label.style.scale = String(instant ? 1 : pop(f, 0));
        s.style.translate = "0px " + Math.sin((f / 15) * Math.PI * 2) * 9 + "px";
        const d = instant ? 1 : interp(f, [0, 12], [0, 1]), h = instant ? 1 : interp(f, [9, 15], [0, 1]);
        paths.forEach((o) => { evolve(o.body, d); o.head.setAttribute("opacity", h); });
      };
    },

    sticker(root, ov) {
      const p = ov.props || {}, at = p.at || [0.7, 0.24];
      const el = mk("div", { position: "absolute", left: at[0] * W + "px", top: at[1] * H + "px", translate: "-50% -50%", padding: "16px 30px", borderRadius: "24px", background: toneColor.cta, boxShadow: "0 12px 30px rgba(0,0,0,0.35)", fontFamily: FONT.sans, fontWeight: "900", fontSize: "52px", color: pal.ink, whiteSpace: "nowrap" }, root, p.text);
      return (f, dur, instant) => {
        el.style.opacity = enterExit(f, dur, { instant, exit: 5 }).exit;
        el.style.scale = String(instant ? 1 : pop(f, 0));
        el.style.rotate = (p.rotate != null ? p.rotate : -4) + Math.sin((f / 60) * Math.PI * 2) * 1.5 + "deg";
      };
    },

    specs(root, ov) {
      const p = ov.props || {}, items = list(p.items).slice(0, 6), perRow = items.length > 3 ? 2 : items.length;
      const box = col(root, { top: topOf(ov, "upper") + "px", left: safe.left + "px", width: safe.right - safe.left + "px", alignItems: "center", gap: "18px" });
      if (p.title) outlineText(box, p.title, { size: 50, weight: 900 });
      const grid = mk("div", { display: "grid", gridTemplateColumns: "repeat(" + perRow + ", auto)", columnGap: INFO.specGap * 2 + "px", rowGap: INFO.specGap + "px", justifyContent: "center" }, box);
      const cells = items.map((it) => {
        const m = it.match(/^(\w+):\s*(.+)$/), has = m && ICONS[m[1]];
        const c = mk("div", { display: "flex", alignItems: "center", gap: "14px" }, grid);
        if (has) icon(c, m[1], INFO.iconSize, toneColor.product);
        outlineText(c, has ? m[2] : it, { size: INFO.labelSize + 4, weight: 800, align: "left" });
        return c;
      });
      return (f, dur, instant) => {
        box.style.opacity = enterExit(f, dur, { instant }).exit;
        cells.forEach((c, i) => { const k = instant ? 1 : pop(f, 4 + i * 5); c.style.opacity = Math.min(1, k * 1.5); c.style.scale = String(interp(k, [0, 1], [0.7, 1])); });
      };
    },

    pin(root, ov) {
      const p = ov.props || {}, x = (p.at ? p.at[0] : 0.1) * W, y = p.at ? p.at[1] * H : topOf(ov, "top") + 40, px = 84;
      const el = layer(root);
      const ic = mk("div", { position: "absolute", left: x - px / 2 + "px", top: y - px + "px" }, el);
      icon(ic, "pin", px, toneColor.cta);
      const ring = mk("div", { position: "absolute", borderRadius: "50%", border: "3px solid " + toneColor.cta }, el);
      const txt = col(el, { left: x + px / 2 + 8 + "px", top: y - px + 6 + "px", maxWidth: safe.right - x - px + "px", gap: "4px" });
      if (p.title) outlineText(txt, p.title, { size: 50, weight: 900, align: "left" });
      if (p.sub) outlineText(txt, p.sub, { size: 34, weight: 600, color: pal.ice, align: "left" });
      return (f, dur, instant) => {
        el.style.opacity = enterExit(f, dur, { instant }).exit;
        const drop = instant ? 1 : smooth(f, 0, 12), r = instant ? 1 : interp(f, [11, 26], [0, 1]), t = instant ? 1 : interp(f, [8, 18], [0, 1], EASE.outCubic);
        ic.style.translate = "0 " + (1 - drop) * -120 + "px"; ic.style.opacity = Math.min(1, drop * 2);
        Object.assign(ring.style, { left: x - 40 * (1 + r) + "px", top: y - 8 - 10 * (1 + r) + "px", width: 80 * (1 + r) + "px", height: 20 * (1 + r) + "px", opacity: (1 - r) * 0.8 });
        txt.style.opacity = t; txt.style.translate = (1 - t) * -24 + "px 0";
      };
    },

    label(root, ov) {
      const p = ov.props || {}, right = p.align === "right";
      const x = (p.at ? p.at[0] : right ? 0.8 : 0.08) * W, y = p.at ? p.at[1] * H : ov.zone ? zones[ov.zone] : 1130;
      const box = col(root, { top: y + "px", alignItems: right ? "flex-end" : "flex-start", gap: "6px" });
      if (right) box.style.right = W - x + "px"; else box.style.left = x + "px";
      const t = mk("div", null, box); outlineText(t, p.text, { size: INFO.labelSize + 6, weight: 900, align: right ? "right" : "left" });
      const ln = mk("div", { height: "5px", width: "200px", borderRadius: "3px", background: toneColor.cta, transformOrigin: right ? "right" : "left", boxShadow: "0 2px 8px rgba(0,0,0,0.4)" }, box);
      let sub = null;
      if (p.sub) { sub = mk("div", null, box); outlineText(sub, p.sub, { size: INFO.labelSize - 6, weight: 600, color: pal.ice, align: right ? "right" : "left" }); }
      return (f, dur, instant) => {
        box.style.opacity = enterExit(f, dur, { instant }).exit;
        const l = instant ? 1 : interp(f, [0, 10], [0, 1], EASE.outCubic), tx = instant ? 1 : interp(f, [4, 13], [0, 1]);
        ln.style.scale = l + " 1"; t.style.opacity = tx; t.style.translate = "0 " + (1 - tx) * 14 + "px"; if (sub) sub.style.opacity = tx;
      };
    },

    stat(root, ov) {
      const p = ov.props || {};
      const box = col(root, { top: topOf(ov, "upper") + "px", left: safe.left + "px", width: safe.right - safe.left + "px", alignItems: "center" });
      const row = mk("div", { display: "flex", alignItems: "baseline", gap: "10px" }, box);
      if (p.prefix) outlineText(row, p.prefix, { size: 60, weight: 800 });
      const g = gradientText(row, "0", { size: INFO.statSize, family: FONT.number, weight: 400, stops: pal.white + " 0%, " + toneColor.cta + " 100%", tracking: "0", lineHeight: 1 });
      if (p.unit) outlineText(row, p.unit, { size: 70, weight: 800, color: toneColor.cta });
      if (p.label) outlineText(box, p.label, { size: 44, weight: 700 });
      return (f, dur, instant) => {
        const { enter, exit } = enterExit(f, dur, { instant });
        const k = instant ? 1 : interp(f, [0, 22], [0, 1], EASE.outCubic);
        row.style.scale = String(interp(f, [22, 25, 28], [1, 1.06, 1])); g.set(num((p.value || 0) * k, p.decimals || 0));
        box.style.opacity = Math.min(enter, exit);
      };
    },

    chart(root, ov) {
      const p = ov.props || {};
      const rows = list(p.items).slice(0, 5).map((s) => { const [label, v] = s.split("#"); return { label: label.trim(), value: Number(v) || 0 }; });
      const max = Math.max(1, ...rows.map((r) => r.value)), best = p.highlight || rows.findIndex((r) => r.value === max) + 1;
      const box = col(root, { top: topOf(ov, "upper") + "px", left: (W - INFO.chartWidth) / 2 - 30 + "px", width: INFO.chartWidth + "px", gap: INFO.barGap + "px" });
      if (p.title) outlineText(box, p.title, { size: 46, weight: 900, align: "left" });
      const els = rows.map((r, i) => {
        const color = i + 1 === best ? toneColor.cta : pal.sky;
        const wrap = col(box, { position: "relative", gap: "6px" });
        const head = mk("div", { display: "flex", justifyContent: "space-between" }, wrap);
        outlineText(head, r.label, { size: 36, weight: 800, align: "left" });
        const v = outlineText(head, "", { size: 36, weight: 800, color });
        const track = mk("div", { height: INFO.barHeight + "px", borderRadius: INFO.barHeight / 2 + "px", background: "rgba(255,255,255,0.22)", overflow: "hidden", boxShadow: "0 4px 14px rgba(0,0,0,0.35)" }, wrap);
        const fill = mk("div", { height: "100%", borderRadius: INFO.barHeight / 2 + "px", background: "linear-gradient(90deg, " + pal.white + ", " + color + ")" }, track);
        return { r, v, fill };
      });
      return (f, dur, instant) => {
        box.style.opacity = enterExit(f, dur, { instant }).exit;
        els.forEach((o, i) => {
          const g = instant ? 1 : interp(f, [4 + i * 6, 22 + i * 6], [0, 1], EASE.outCubic);
          o.v.set(num(o.r.value * g, 0) + (p.unit || "")); o.fill.style.width = (o.r.value / max) * g * 100 + "%";
        });
      };
    },

    progress(root, ov) {
      const p = ov.props || {};
      const box = col(root, { top: (ov.zone ? zones[ov.zone] : safe.top + 20) + "px", left: safe.left + 20 + "px", right: W - safe.right + 20 + "px", gap: "12px" });
      if (p.label) outlineText(box, p.label, { size: 44, weight: 800 });
      const track = mk("div", { height: "18px", borderRadius: "9px", background: "rgba(255,255,255,0.35)", overflow: "hidden", boxShadow: "0 4px 14px rgba(0,0,0,0.35)" }, box);
      const fill = mk("div", { height: "100%", borderRadius: "9px", background: "linear-gradient(90deg, " + pal.sky + ", " + toneColor.after + ")" }, track);
      return (f, dur, instant) => {
        const { enter, exit } = enterExit(f, dur, { instant });
        box.style.opacity = Math.min(enter, exit); fill.style.width = interp(f, [6, dur - 8], [0, 1]) * 100 + "%";
      };
    },

    lowerThird(root, ov) {
      const p = ov.props || {};
      const row = mk("div", { position: "absolute", top: topOf(ov, "lower") + "px", left: safe.left + "px", display: "flex", alignItems: "stretch", gap: "18px" }, root);
      const bar = mk("div", { width: "10px", borderRadius: "5px", background: toneColor.cta, transformOrigin: "top" }, row);
      const txt = mk("div", { textAlign: "left" }, row);
      mk("div", { fontFamily: FONT.sans, fontWeight: "900", fontSize: "56px", color: pal.white, filter: "drop-shadow(0 4px 12px rgba(0,0,0,0.6))" }, txt, p.name);
      if (p.role) mk("div", { fontFamily: FONT.sans, fontWeight: "600", fontSize: "36px", color: pal.ice, filter: "drop-shadow(0 3px 8px rgba(0,0,0,0.6))" }, txt, p.role);
      return (f, dur, instant) => {
        row.style.opacity = enterExit(f, dur, { instant }).exit;
        bar.style.scale = "1 " + (instant ? 1 : interp(f, [0, 8], [0, 1]));
        const t = instant ? 1 : interp(f, [5, 13], [0, 1]); txt.style.opacity = t; txt.style.translate = (1 - t) * -20 + "px 0";
      };
    },

    image(root, ov) {
      const p = ov.props || {}, at = p.at || [0.5, 0.4], width = p.width || 600, card = (p.frame || "card") !== "none";
      const box = col(root, { left: at[0] * W + "px", top: at[1] * H + "px", translate: "-50% -50%", alignItems: "center", gap: "10px" });
      const img = mk("img", { width: width + "px", display: "block" }, box);
      img.src = p.src;
      if (card) Object.assign(img.style, { border: "8px solid " + pal.white, borderRadius: "24px", boxShadow: "0 18px 50px rgba(0,0,0,0.45)", background: pal.white });
      if (p.caption) outlineText(box, p.caption, { size: 38, weight: 800 });
      return (f, dur, instant) => { const { exit } = enterExit(f, dur, { instant }); const k = instant ? 1 : smooth(f, 0, 10); box.style.opacity = Math.min(exit, k); box.style.scale = String(interp(k, [0, 1], [0.9, 1])); };
    },
  };

  // ---------- timeline: scene slots, centred transitions (timeline.ts) ----------
  const slots = P.slots; // computed by project_to_hyperframes.py with the same rules as timeline.ts
  const scenes = slots.map((s) => {
    const tr = $("tr" + s.index), cam = $("cam" + s.index);
    return Object.assign({ tr, cam }, s);
  });
  const dirVec = { left: [1, 0], right: [-1, 0], up: [0, 1], down: [0, -1] };
  const fromDir = { left: "from-right", right: "from-left", up: "from-bottom", down: "from-top" };

  // Keyframed camera (plan: `keys 0=1.0 ; 0.4=1.35@0.3,0.45 out ; 1=1.1`): the same maths as engine/camera.ts.
  const KEY_EASE = {
    linear: (t) => t, in: bezier(0.42, 0, 1, 1), out: bezier(0, 0, 0.58, 1), inOut: EASE.camera, soft: bezier(0.45, 0.05, 0.55, 0.95),
    snap: EASE.out, back: bezier(0.34, 1.4, 0.64, 1), hold: (t) => (t < 1 ? 0 : 1),
  };
  const framingAt = (f, cutOffset, keys) => {
    const ks = keys.slice().sort((a, b) => a.ts - b.ts).map((k) => ({ f: cutOffset + k.ts * FPS, zoom: Math.max(1, k.zoom), at: k.at || [0.5, 0.5], roll: k.roll || 0, ease: k.ease || "inOut" }));
    if (f <= ks[0].f) return ks[0];
    if (f >= ks[ks.length - 1].f) return ks[ks.length - 1];
    let i = 0;
    while (f > ks[i + 1].f) i++;
    const a = ks[i], b = ks[i + 1], e = KEY_EASE[b.ease]((f - a.f) / Math.max(1e-6, b.f - a.f));
    return { zoom: Math.sqrt(Math.max(1e-6, a.zoom * a.zoom + e * (b.zoom * b.zoom - a.zoom * a.zoom))), at: [a.at[0] + (b.at[0] - a.at[0]) * e, a.at[1] + (b.at[1] - a.at[1]) * e], roll: a.roll + (b.roll - a.roll) * e };
  };
  const keyedCamera = (s, f) => {
    const k = framingAt(f, s.cut - s.begin, s.scene.camera.keys);
    const rad = (Math.abs(k.roll) * Math.PI) / 180, need = Math.cos(rad) + Math.sin(rad) * (16 / 9);
    let scale = Math.max(k.zoom, need);
    for (const pu of s.punches) scale *= 1 + (pu.scale - 1) * spring(f - pu.frame, SPRINGS.smooth, CAM.punchFrames);
    scale = Math.min(scale, CAM.maxScale);
    // centre the chosen point of the footage, then keep the frame edge covered
    const th = (k.roll * Math.PI) / 180, px = scale * (k.at[0] - 0.5) * W, py = scale * (k.at[1] - 0.5) * H;
    const room = Math.max(0, scale - need);
    const tx = Math.max(-room * W * 0.5, Math.min(room * W * 0.5, -(Math.cos(th) * px - Math.sin(th) * py)));
    const ty = Math.max(-room * H * 0.5, Math.min(room * H * 0.5, -(Math.sin(th) * px + Math.cos(th) * py)));
    return { origin: "50% 50%", tx: tx, ty: ty, rot: k.roll, scale: scale };
  };

  const cameraFor = (s, f) => {
    if (s.scene.camera && s.scene.camera.keys && s.scene.camera.keys.length) return keyedCamera(s, f);
    const cam = s.scene.camera || {}, move = cam.move || "push";
    let a, b;
    if (move === "pull") [a, b] = [cam.from != null ? cam.from : CAM.defaultPull[0], cam.to != null ? cam.to : CAM.defaultPull[1]];
    else if (move === "hold") [a, b] = [cam.from != null ? cam.from : 1.04, cam.from != null ? cam.from : 1.04];
    else if (move === "pan") [a, b] = [cam.from != null ? cam.from : 1.1, cam.to != null ? cam.to : cam.from != null ? cam.from : 1.1];
    else [a, b] = [cam.from != null ? cam.from : CAM.defaultPush[0], cam.to != null ? cam.to : CAM.defaultPush[1]];
    // Remotion's "perceptual-scale": the zoom is eased in AREA (scale squared), so equal time = equal apparent zoom
    const e = EASE.camera(clamp01(f / s.duration));
    let scale = Math.sqrt(a * a + e * (b * b - a * a));
    for (const pu of s.punches) scale *= 1 + (pu.scale - 1) * spring(f - pu.frame, SPRINGS.smooth, CAM.punchFrames);
    const [px, py] = move === "pan" ? cam.pan || [-CAM.defaultPan, 0] : [0, 0];
    const progress = EASE.camera(clamp01(f / s.duration));
    const [r0, r1] = cam.roll || [0, 0], roll = r0 + (r1 - r0) * progress;
    const rad = (Math.max(Math.abs(r0), Math.abs(r1)) * Math.PI) / 180;
    scale = Math.max(scale, 1 + 2 * Math.max(Math.abs(px), Math.abs(py)), Math.cos(rad) + Math.sin(rad) * (16 / 9));
    scale = Math.min(scale, CAM.maxScale);
    const [fx, fy] = cam.focus || [0.5, 0.5];
    return { origin: fx * 100 + "% " + fy * 100 + "%", tx: px * progress * W, ty: py * progress * H, rot: roll, scale: scale };
  };

  // CapCut-style hits on a scene's first frames (plan: "+shake +glitch +rgb +pulse" in the Transition cell).
  // Deterministic: sums of sines of the frame count, no random numbers.
  const GLITCH_DX = [-26, 30, -12, 22, -8, 10, 0, 0];
  // Channel split: red shifted one way, green+blue the other, screen-blended (a real RGB split, not a shadow).
  const defs = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  defs.setAttribute("width", 0); defs.setAttribute("height", 0); defs.style.position = "absolute";
  defs.innerHTML = '<filter id="svkRgb" x="-5%" y="-5%" width="110%" height="110%" color-interpolation-filters="sRGB">' +
    '<feColorMatrix in="SourceGraphic" type="matrix" values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0" result="r"/><feOffset id="svkRgbR" in="r" dx="0" result="ro"/>' +
    '<feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 1 0" result="gb"/><feOffset id="svkRgbB" in="gb" dx="0" result="bo"/>' +
    '<feBlend in="ro" in2="bo" mode="screen"/></filter>';
  document.body.appendChild(defs);
  const rgbR = defs.querySelector("#svkRgbR"), rgbB = defs.querySelector("#svkRgbB");
  const fxFor = (s, frame) => {
    const out = { dx: 0, dy: 0, rot: 0, scale: 1, filter: "", split: 0 };
    const fxs = s.scene.fx;
    if (!fxs || !fxs.length) return out;
    const d = frame - s.cut;
    if (d < 0) return out;
    if (fxs.indexOf("shake") >= 0 && d < 14) {
      const k = 1 - d / 14;
      out.dx += (Math.sin(d * 5.1) + Math.sin(d * 2.3 + 1)) * 14 * k; out.dy += (Math.sin(d * 4.3 + 2) + Math.sin(d * 6.7)) * 12 * k;
      out.rot += Math.sin(d * 3.1) * 1.2 * k; out.scale *= 1.07; // spare image so the edge never shows
    }
    if (fxs.indexOf("pulse") >= 0 && d < 10) out.scale *= 1 + 0.08 * Math.sin((Math.PI * d) / 10);
    if (fxs.indexOf("rgb") >= 0 && d < 9) out.split = Math.max(out.split, Math.sin((Math.PI * d) / 9) * 14);
    if (fxs.indexOf("glitch") >= 0 && d < 8) {
      const k = 1 - d / 8;
      out.dx += GLITCH_DX[d] * k; out.scale *= 1.04; out.split = Math.max(out.split, 18 * k);
      out.filter += " hue-rotate(" + (d % 2 ? 24 : -18) * k + "deg) contrast(" + (1 + 0.25 * k) + ")";
    }
    return out;
  };

  // Presentation state of one scene's wrapper for transition progress p (0..1): entering or exiting.
  const present = (type, dir, enteringScene, p) => {
    const st = { opacity: 1, transform: "", filter: "", clip: "", mask: "" };
    const e = enteringScene;
    const dv = dirVec[dir] || [1, 0];
    switch (type) {
      case "slide": {
        const d = dir || "up", v = dirVec[d];
        // the new shot travels in the direction given: "left" = it enters from the right
        const t = e ? (1 - p) * 100 : -p * 100;
        st.transform = "translate(" + t * v[0] + "%, " + t * v[1] + "%)";
        break;
      }
      case "wipe": {
        if (e) {
          // the new shot grows from the edge it comes from, with a soft edge 30 % wide
          const v = dirVec[dir || "right"], q = p * 1.3 - 0.3;
          const ang = v[0] === 1 ? "to left" : v[0] === -1 ? "to right" : v[1] === 1 ? "to top" : "to bottom";
          st.mask = "linear-gradient(" + ang + ", #000 " + q * 100 + "%, transparent " + (q + 0.3) * 100 + "%)";
        }
        break;
      }
      case "iris":
        if (e) st.clip = "circle(" + p * Math.hypot(W, H) / 2 + "px at 50% 50%)";
        break;
      case "pushCut": {
        // hard cut at the middle: the old shot punches in, the new one settles from a punch
        if (e) { st.opacity = p >= 0.5 ? 1 : 0; st.transform = "scale(" + interp(p, [0.5, 1], [1.12, 1]) + ")"; }
        else st.transform = "scale(" + interp(p, [0, 0.5], [1, 1.12]) + ")";
        break;
      }
      case "zoomThrough": {
        const s = e ? interp(p, [0, 1], [1.2, 1]) : interp(p, [0, 1], [1, 1.2]);
        st.opacity = e ? interp(p, [0.4, 0.6], [0, 1]) : 1; st.transform = "scale(" + s + ")"; st.filter = "blur(" + Math.sin(Math.PI * p) * 10 + "px)";
        break;
      }
      case "crossZoom": { // Remotion uses a WebGL radial blur; this is a zoom-blur dissolve with the same feel
        const s = e ? interp(p, [0, 1], [1.35, 1]) : interp(p, [0, 1], [1, 1.35]);
        st.opacity = e ? interp(p, [0.2, 0.8], [0, 1]) : 1; st.transform = "scale(" + s + ")"; st.filter = "blur(" + Math.sin(Math.PI * p) * 22 + "px)";
        break;
      }
      case "blurDissolve":
        st.opacity = e ? interp(p, [0.3, 0.7], [0, 1]) : 1; st.filter = "blur(" + Math.sin(Math.PI * p) * 16 + "px)";
        break;
      case "whip": {
        const t = e ? (1 - p) * 100 : -p * 100;
        st.transform = "translate(" + t * dv[0] + "%, " + t * dv[1] + "%)"; st.filter = "blur(" + Math.sin(Math.PI * p) * 24 + "px)";
        break;
      }
      case "flip": {
        const axis = dv[0] !== 0 ? "Y" : "X", sign = dv[0] + dv[1] >= 0 ? 1 : -1;
        if (e) { st.opacity = p >= 0.5 ? 1 : 0; st.transform = "perspective(1800px) rotate" + axis + "(" + sign * (1 - p) * 180 + "deg)"; }
        else { st.opacity = p < 0.5 ? 1 : 0; st.transform = "perspective(1800px) rotate" + axis + "(" + -sign * p * 180 + "deg)"; }
        break;
      }
      default: // fade, cut
        st.opacity = e ? p : 1;
    }
    return st;
  };
  const apply = (el, st) => {
    el.style.opacity = st.opacity; el.style.transform = st.transform; el.style.filter = st.filter;
    el.style.clipPath = st.clip; el.style.webkitMaskImage = st.mask; el.style.maskImage = st.mask;
  };

  // ---------- overlays, captions, accents ----------
  const overlayRoot = $("overlays");
  const overlays = (P.overlays || []).filter((ov) => FACTORY[ov.component]).map((ov) => {
    const host = mk("div", { position: "absolute", inset: "0", display: "none" }, overlayRoot);
    const from = Math.round(ov.start * FPS), dur = Math.max(1, Math.round(ov.end * FPS) - from);
    return { host, from, dur, instant: from === 0, update: FACTORY[ov.component](host, ov) };
  });
  const cartWindows = (P.overlays || []).filter((o) => o.component === "cart").map((o) => [Math.round(o.start * FPS), Math.round(o.end * FPS)]);
  const accents = scenes.filter((s) => s.index > 0 && s.scene.accent).map((s) => ({ s, el: mk("div", { position: "absolute", inset: "0", display: "none" }, $("accents")) }));
  accents.forEach((a) => {
    if (a.s.scene.accent === "lightLeak") { a.el.style.background = "radial-gradient(ellipse at " + (30 + (a.s.index * 37) % 50) + "% 20%, rgba(255,190,90,0.95), rgba(255,110,60,0.5) 40%, transparent 70%)"; a.el.style.mixBlendMode = "screen"; }
    else a.el.style.background = pal.white;
  });

  const capEl = mk("div", { position: "absolute", display: "none", left: CAP.left + "px", right: CAP.right + "px", justifyContent: "center" }, $("captions"));
  let capKey = "";
  const capCaptions = P.captions || [], capWords = P.words || [], capMode = P.captionStyle || "karaoke";
  const popChunks = (words) => {
    const out = [];
    for (const w of words) {
      const cur = out[out.length - 1], prev = cur && cur[cur.length - 1];
      const chars = cur ? cur.reduce((n, x) => n + x.text.length + 1, 0) + w.text.length : 0;
      if (!cur || cur.length >= CAP.popWords || chars > CAP.popChars || w.start - prev.end > 0.25 || /[,.!?…:;]$/.test(prev.text)) out.push([w]); else cur.push(w);
    }
    return out;
  };
  const renderCaptions = (frame) => {
    const t = frame / FPS;
    let cue = null;
    if (capMode !== "none") {
      for (let i = 0; i < capCaptions.length; i++) {
        const c = capCaptions[i], next = capCaptions[i + 1] ? capCaptions[i + 1].start : Infinity;
        if (t >= c.start && t < Math.max(c.end, Math.min(next, c.end + 0.25))) { cue = { c, i }; break; }
      }
    }
    if (!cue) { capEl.style.display = "none"; return; }
    let lift = 0;
    cartWindows.forEach(([a, b]) => { lift = Math.max(lift, interp(frame, [a - 4, a + 4, b - 4, b + 4], [0, CAP.lift, CAP.lift, 0])); });
    const c = cue.c, gw = capMode === "plain" ? [] : capWords.filter((w) => w.start >= c.start - 0.02 && w.start < c.end);
    capEl.style.display = "flex";
    if (capMode === "pop" && gw.length) {
      const groups = popChunks(gw);
      const idx = groups.findIndex((g, i) => t >= g[0].start - 0.05 && t < (groups[i + 1] ? groups[i + 1][0].start : g[g.length - 1].end + 0.3) - 0.05);
      if (idx < 0) { capEl.style.display = "none"; return; }
      const g = groups[idx], key = "pop" + cue.i + ":" + idx;
      if (key !== capKey) { capEl.textContent = ""; capKey = key; const o = outlineText(capEl, "", { size: CAP.popSize, weight: 900 }); capEl._o = o; capEl._spans = []; [o.root.children[0], o.root.children[1]].forEach((layerEl, li) => { layerEl.textContent = ""; g.forEach((w, i) => { if (i) layerEl.appendChild(document.createTextNode(" ")); const sp = mk("span", { display: "inline-block" }, layerEl, w.text); (capEl._spans[li] = capEl._spans[li] || []).push(sp); }); }); }
      capEl.style.top = captionTop - lift - 20 + "px";
      g.forEach((w, i) => {
        const active = t >= w.start && t < (g[i + 1] ? g[i + 1].start : w.end + 0.3);
        const k = active ? pop(frame - Math.round(w.start * FPS), 0) : 0;
        capEl._spans.forEach((arr, li) => { arr[i].style.scale = String(1 + 0.12 * Math.min(1, k)); if (li === 1) arr[i].style.color = active ? toneColor.cta : ""; });
      });
      return;
    }
    const key = "k" + cue.i;
    if (key !== capKey) {
      capEl.textContent = ""; capKey = key;
      const o = outlineText(capEl, "", { size: CAP.size, weight: 800 }); capEl._spans = [];
      [o.root.children[0], o.root.children[1]].forEach((layerEl, li) => {
        layerEl.textContent = "";
        if (!gw.length) { layerEl.textContent = c.text; return; }
        gw.forEach((w, i) => { if (i) layerEl.appendChild(document.createTextNode(" ")); const sp = mk("span", { display: "inline-block" }, layerEl, w.text); (capEl._spans[li] = capEl._spans[li] || []).push(sp); });
      });
    }
    capEl.style.top = captionTop - lift + "px";
    capEl.style.opacity = interp(frame - Math.round(c.start * FPS), [0, 4], [0, 1]);
    if (gw.length) gw.forEach((w, i) => {
      const active = t >= w.start && t < Math.min(w.end + 0.05, gw[i + 1] ? gw[i + 1].start : Infinity);
      capEl._spans.forEach((arr, li) => { arr[i].style.scale = active ? "1.08" : "1"; if (li === 1) arr[i].style.color = active ? toneColor.cta : ""; });
    });
  };

  // ---------- look: a vignette and film grain over the footage (project "look": {vignette, grain}, 0..1) ----------
  const look = P.look || {}, lookRoot = $("look");
  let grainSeed = null;
  if (look.vignette) mk("div", { position: "absolute", inset: "0", background: "radial-gradient(ellipse at 50% 45%, transparent 52%, rgba(0,0,0," + 0.6 * look.vignette + ") 100%)" }, lookRoot);
  if (look.grain) {
    const NS = "http://www.w3.org/2000/svg";
    const s = document.createElementNS(NS, "svg");
    s.setAttribute("width", W); s.setAttribute("height", H); Object.assign(s.style, { position: "absolute", left: 0, top: 0, mixBlendMode: "overlay", opacity: String(look.grain) });
    s.innerHTML = '<filter id="grain" x="0" y="0" width="100%" height="100%"><feTurbulence id="grainSeed" type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="1" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter><rect width="100%" height="100%" filter="url(#grain)"/>';
    lookRoot.appendChild(s);
    grainSeed = s.querySelector("#grainSeed");
  }
  const renderLook = (frame) => { if (grainSeed) grainSeed.setAttribute("seed", String(1 + (frame % 6))); };

  // ---------- the frame ----------
  const render = (frame) => {
    scenes.forEach((s) => {
      const f = frame - s.begin;
      if (f < 0 || f >= s.duration) { s.tr.style.display = "none"; return; }
      s.tr.style.display = "block"; s.tr.style.zIndex = String(s.index);
      const c = cameraFor(s, f), x = fxFor(s, frame);
      Object.assign(s.cam.style, { transformOrigin: c.origin, translate: c.tx + x.dx + "px " + (c.ty + x.dy) + "px", rotate: c.rot + x.rot + "deg", scale: String(Math.min(c.scale * x.scale, CAM.maxScale * 1.1)) });
      let st = { opacity: 1, transform: "", filter: "", clip: "", mask: "" };
      const t = s.scene.transition || { type: "fade" };
      if (s.index > 0 && s.transitionIn > 0 && f < s.transitionIn) {
        st = present(t.type, t.direction || (t.type === "slide" ? "up" : t.type === "wipe" ? "right" : "left"), true, EASE.inOut(f / s.transitionIn));
      }
      const nx = scenes[s.index + 1];
      if (nx && nx.transitionIn > 0 && frame >= nx.begin && frame < nx.begin + nx.transitionIn) {
        const nt = nx.scene.transition || { type: "fade" };
        st = present(nt.type, nt.direction || (nt.type === "slide" ? "up" : nt.type === "wipe" ? "right" : "left"), false, EASE.inOut((frame - nx.begin) / nx.transitionIn));
      }
      let extra = x.filter;
      if (x.split > 0.01) { rgbR.setAttribute("dx", x.split); rgbB.setAttribute("dx", -x.split); extra += " url(#svkRgb)"; }
      if (extra) st.filter = (st.filter + " " + extra).trim();
      apply(s.tr, st);
    });
    renderLook(frame);
    accents.forEach((a) => {
      const f = frame - (a.s.cut - 10);
      if (f < 0 || f >= 20) { a.el.style.display = "none"; return; }
      a.el.style.display = "block";
      if (a.s.scene.accent === "lightLeak") a.el.style.opacity = 0.6 * Math.sin((Math.PI * f) / 20);
      else a.el.style.opacity = f < 7 ? 0 : interp(f - 7, [0, 3, 10], [0, 0.55, 0], EASE.inOut);
    });
    overlays.forEach((o) => {
      const f = frame - o.from;
      if (f < 0 || f >= o.dur) { o.host.style.display = "none"; return; }
      o.host.style.display = "block"; o.update(f, o.dur, o.instant);
    });
    renderCaptions(frame);
  };

  // GSAP only moves the playhead: the accessor receives every seek, so nothing depends on callbacks.
  let current = 0;
  const driver = { get t() { return current; }, set t(v) { current = v; render(Math.round(v * FPS)); } };
  const tl = gsap.timeline({ paused: true });
  tl.to(driver, { t: DUR, duration: DUR, ease: "none" }, 0);
  window.__timelines = window.__timelines || {};
  window.__timelines[P.compositionId || "main"] = tl;
  render(0);
})();
