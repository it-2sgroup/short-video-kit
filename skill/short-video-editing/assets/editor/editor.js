"use strict";
/* Video editor page (vanilla JS, no build step, nothing from the network): edits a render project's project.json
   through the local server in scripts/editor.py. Sections:
   1 constants and state - 2 small helpers - 3 server calls - 4 content strings (port of plan_to_project.parse_content)
   5 project model: edits, undo, diff against the last render - 6 timeline - 7 preview and player
   8 properties panel - 9 header, dialogs, save, render - 10 keyboard and start. */
(() => {
// ============================================================================ 1. constants and state
const LABEL_W = 116; // width of the track-label column (also --label-w in the CSS)
const FRAME_W = 1080, FRAME_H = 1920;
const MIN_LEN = 0.1; // shortest scene / overlay in seconds
const ZOOM_MIN = 20, ZOOM_MAX = 400; // pixels per second
const TRACK_H = { scenes: 44, caption: 26, voice: 38, music: 38, sfx: 26 }, LANE_H = 24;
const SNAP_PX = 8;

// Used only when the render folder's src/ cannot be read; the server normally sends the template's own lists.
const FALLBACK = {
  components: ["title", "callout", "checklist", "step", "price", "cart", "highlight", "sticker", "progress", "magnifier", "thumbs", "compare",
    "ranking", "lowerThird", "specs", "pin", "label", "stat", "chart", "image", "burst", "phrase", "pill", "arc", "script", "tag", "logo",
    "counter", "icon", "circled", "rawfinal"],
  unions: {
    TransitionType: ["cut", "fade", "slide", "wipe", "iris", "pushCut", "zoomThrough", "blurDissolve", "whip", "flip", "crossZoom", "cardSlide", "cardSwirl"],
    Direction: ["left", "right", "up", "down"], CameraMove: ["push", "pull", "pan", "hold", "keys"],
    CameraEase: ["linear", "in", "out", "inOut", "soft", "snap", "back", "hold"], Layout: ["full", "card", "expand"],
    Zone: ["top", "upper", "center", "lower"], Tone: ["neutral", "before", "after", "cta", "product"],
    CaptionStyle: ["karaoke", "pop", "plain", "none"], CaptionHighlight: ["color", "box", "underline", "glow"],
  },
};
const DIRECTIONAL = new Set(["slide", "wipe", "whip", "flip", "cardSlide", "blurSlide", "cube", "bookFlip"]);
// Keys each component reads (references/layout-and-motion-graphics.md): what "Thêm thuộc tính" offers.
const COMPONENT_KEYS = {
  title: ["style", "lines", "accent", "sub"], callout: ["label", "target", "side", "labelY"], highlight: ["shape", "target", "size"],
  step: ["n", "text"], checklist: ["title", "items"], price: ["value", "unit", "label", "old", "prefix", "decimals"], cart: ["text"],
  sticker: ["text", "at", "rotate"], progress: ["label"], magnifier: ["clip", "in", "target", "at", "zoom", "diameter"], thumbs: ["cards"],
  compare: ["before", "after", "mode", "beforeFocus", "afterFocus", "zoom", "note", "beforeLabel", "afterLabel"], ranking: ["items"],
  lowerThird: ["name", "role"], specs: ["title", "items"], pin: ["title", "sub", "at"], label: ["text", "sub", "at", "align"],
  stat: ["value", "unit", "label", "prefix", "decimals"], chart: ["items", "unit", "title", "highlight"],
  image: ["src", "at", "width", "frame", "caption"], burst: ["text", "at", "copies", "speed", "fill", "stroke", "hold"],
  phrase: ["lead", "emph", "emphAt", "y", "emphColor", "enter", "exit"], pill: ["text", "variant", "at", "size", "type"],
  arc: ["text", "echoes", "at", "fill", "stroke"], script: ["text", "at", "rotate", "size"], tag: ["text", "at"],
  logo: ["at", "width", "src", "tint", "hold"], counter: ["from", "to", "label", "at"], icon: ["name", "at", "size", "rotate"],
  circled: ["text", "at", "icon"], rawfinal: ["raw", "final", "at", "saturate", "contrast", "brightness"],
};
const ENUMS = {
  "title.style": ["stack", "gradient", "outline", "marker", "glass"], "highlight.shape": ["circle", "underline", "arrow"],
  "compare.mode": ["side", "slider", "stack"], "callout.side": ["left", "right"], "label.align": ["left", "right"],
  "image.frame": ["card", "none"], "pill.variant": ["white", "red"], "phrase.emphColor": ["red", "yellow"],
  "phrase.enter": ["scatter", "rise"], "phrase.exit": ["scatter", "fade"], "logo.tint": ["white"],
};
const POINT_KEYS = new Set(["at", "target", "focus", "beforeFocus", "afterFocus"]);
const LIST_KEYS = new Set(["lines", "items"]);
const JSON_KEYS = new Set(["cards", "before", "after"]);
const NUMBER_KEYS = new Set(["n", "value", "old", "decimals", "rotate", "zoom", "diameter", "size", "width", "copies", "speed", "emphAt", "y", "from", "to", "hold", "in", "labelY", "echoes", "saturate", "contrast", "brightness"]);

const S = {
  info: { renders: [], projects: [] }, schema: { components: [], unions: {} }, assets: { clips: [], audio: [], sfx: [], images: [] },
  name: "", mtime: 0, project: null, savedText: "", baseline: null, renderState: "none", renders: [], render: null,
  sel: null, t: 0, playing: false, pps: 80, undo: [], redo: [], lastKey: null, lastAt: 0, diff: { n: 0, changed: {} },
  waves: {}, waveEls: {}, snapAt: null, rs: null, watchRender: false,
  opts: { safe: false, face: false, draft: null, snap: true, proxy: false },
};

// ============================================================================ 2. small helpers
const $ = (sel, root = document) => root.querySelector(sel);
const h = (tag, props = {}, ...kids) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v == null || v === false) continue;
    if (k === "class") e.className = v;
    else if (k === "style") e.style.cssText = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else if (["value", "checked", "disabled", "selected"].includes(k)) e[k] = v;
    else e.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat(Infinity)) if (kid != null && kid !== false) e.append(kid.nodeType ? kid : String(kid));
  return e;
};
const svgEl = (tag, attrs = {}) => {
  const e = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  return e;
};
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const r3 = (v) => Math.round(v * 1000) / 1000;
const clone = (o) => JSON.parse(JSON.stringify(o));
const enc = encodeURIComponent;
const fmt = (t) => { const m = Math.floor(t / 60); return `${m}:${(t - m * 60).toFixed(2).padStart(5, "0")}`; };
const when = (ms) => new Date(ms).toLocaleString("vi-VN", { hour12: false });
const P = () => S.project;
const fps = () => P().fps || 30;
const sceneEnd = () => P().scenes.reduce((m, s) => Math.max(m, s.end || 0), 0);
const dur = () => P().duration || sceneEnd();
const listOf = (kind) => ({ scene: P().scenes, overlay: P().overlays, caption: P().captions, sfx: P().sfx })[kind];
const selItem = () => (S.sel ? (listOf(S.sel.kind) || [])[S.sel.i] || null : null);
const U = (name) => (S.schema.unions[name] && S.schema.unions[name].length ? S.schema.unions[name] : FALLBACK.unions[name]);
const sceneIndexAt = (t) => { const sc = P().scenes; for (let i = sc.length - 1; i >= 0; i--) if (t >= sc[i].start - 1e-6) return i; return 0; };
const hue = (s) => { let x = 0; for (const c of s) x = (x * 31 + c.charCodeAt(0)) % 360; return x; };

function toast(msg, kind = "") {
  const el = h("div", { class: `toast ${kind}` }, msg);
  $("#toasts").append(el);
  setTimeout(() => el.remove(), kind === "err" ? 7000 : 3500);
}
const pref = {
  get(k) { try { return localStorage.getItem(`svk-editor-${k}`); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(`svk-editor-${k}`, v); } catch { /* storage can be blocked */ } },
};

// ============================================================================ 3. server calls
async function api(path, opts) {
  const res = await fetch(path, opts);
  let data = null;
  try { data = await res.json(); } catch { /* an error page without JSON */ }
  if (!res.ok) throw Object.assign(new Error((data && data.error) || res.statusText), { status: res.status, data });
  return data;
}
const post = (path, body) => api(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body ?? {}) });

// ============================================================================ 4. content strings
// "key=value; key=value" is how the plan's Overlays table writes `props`. These mirror plan_to_project.py so the raw
// text box shows and accepts the same notation; values the notation cannot express fall back to JSON.
const TEXT_KEYS = new Set(["accent", "sub", "text", "label", "caption", "title", "name", "role", "unit", "prefix", "note", "lines", "items"]);
const clipStem = (s) => s.split(/[\\/]/).pop().replace(/\.[^.]*$/, "").toUpperCase();
function parseValue(raw) {
  const v = raw.trim().normalize("NFC");
  if (v.includes(" / ")) return v.split(" / ").map((x) => x.trim());
  if (/^-?[\d.]+\s*,\s*-?[\d.]+$/.test(v)) { const n = v.split(",").map(Number); if (n.every(Number.isFinite)) return n; }
  if (/^-?\d+$/.test(v)) return parseInt(v, 10);
  if (/^-?\d*\.\d+$/.test(v)) return parseFloat(v);
  return v;
}
function parseContent(component, raw) {
  const props = {};
  for (const chunk of raw.split(";").map((c) => c.trim()).filter(Boolean)) {
    const eq = chunk.indexOf("=");
    if (eq < 0) continue;
    const k = chunk.slice(0, eq).trim(), text = chunk.slice(eq + 1).trim();
    let val;
    if (/^[[{]/.test(text)) { try { val = JSON.parse(text); } catch { val = parseValue(text); } } else val = parseValue(text);
    if (TEXT_KEYS.has(k) && !Array.isArray(val) && typeof val !== "object") val = text; // "accent=2026" is a word to draw
    props[k] = val;
  }
  if (component === "title" && typeof props.lines === "string") props.lines = [props.lines];
  if (component === "checklist" && typeof props.items === "string") props.items = [props.items];
  if (component === "thumbs") {
    const cards = typeof props.cards === "string" ? [props.cards] : props.cards || [];
    props.cards = cards.flatMap((c) => {
      if (typeof c === "object") return [c];
      const m = c.match(/^(\S+)@([\d.]+)(?::(.*?))?(?:\s*\+\s*(@".+?"(?:#\d+)?|[\d.]+))?(?:\s*~\s*([\d.]+)\s*,\s*([\d.]+)(?:\s*,\s*([\d.]+))?)?\s*$/);
      if (!m) return [];
      const card = { clip: clipStem(m[1]), at: parseFloat(m[2]), caption: (m[3] || "").trim() };
      if (m[4]) card.when = m[4];
      if (m[5]) { card.focus = [parseFloat(m[5]), parseFloat(m[6])]; if (m[7]) card.zoom = parseFloat(m[7]); }
      return [card];
    });
  }
  if (component === "compare") {
    for (const side of ["before", "after"]) {
      if (props[side] && typeof props[side] === "object") continue;
      const m = String(props[side] ?? "").match(/^(\S+)@([\d.]+)$/);
      if (!m) throw new Error(`compare cần ${side}=CLIP@giây (một khung của clip đã chiếu trong video)`);
      props[side] = { clip: clipStem(m[1]), at: parseFloat(m[2]) };
    }
  }
  if (component === "ranking") {
    const items = typeof props.items === "string" ? [props.items] : props.items || [];
    props.items = items.map((i) => (typeof i === "object" ? i : { label: i.split("#")[0].trim(), rank: i.includes("#") ? i.split("#")[1].trim() : null }));
  }
  if (component === "magnifier" && typeof props.clip === "string") props.clip = clipStem(props.clip);
  return props;
}
function formatValue(component, k, v) {
  if (v == null) return "";
  if (typeof v === "string") return v;
  if (typeof v === "number" || typeof v === "boolean") return String(v);
  if (Array.isArray(v)) {
    if (v.length === 0) return "[]";
    if (v.every((x) => typeof x === "string")) return v.length === 1 && !(k === "lines" && component === "title") && !(k === "items" && component === "checklist") ? null : v.join(" / ");
    if (v.length === 2 && v.every((x) => typeof x === "number")) return v.join(",");
    if (component === "thumbs" && k === "cards" && v.every((c) => c && c.clip != null)) {
      return v.map((c) => `${c.clip}@${c.at}${c.caption ? `:${c.caption}` : ""}${c.when ? `+${c.when}` : ""}${c.focus ? `~${c.focus[0]},${c.focus[1]}${c.zoom != null ? `,${c.zoom}` : ""}` : ""}`).join(" / ");
    }
    if (component === "ranking" && k === "items" && v.every((i) => i && i.label != null)) return v.map((i) => (i.rank != null ? `${i.label}#${i.rank}` : i.label)).join(" / ");
    return null;
  }
  if (component === "compare" && (k === "before" || k === "after") && v.clip != null && v.at != null) return `${v.clip}@${v.at}`;
  return null;
}
function formatContent(component, props) {
  let lossy = false;
  const chunks = Object.entries(props || {}).map(([k, v]) => {
    const s = formatValue(component, k, v);
    if (s == null) return `${k}=${JSON.stringify(v)}`;
    if (s.includes(";") || (typeof v === "string" && v.includes(" / "))) lossy = true; // the separators would split it
    return `${k}=${s}`;
  });
  return { text: chunks.join("; "), lossy };
}

// ============================================================================ 5. project model
const isDirty = () => !!S.project && JSON.stringify(S.project) !== S.savedText;

function pushUndo(key) {
  const now = Date.now();
  if (key && key === S.lastKey && now - S.lastAt < 1500) { S.lastAt = now; return; } // typing in one field is one undo step
  S.undo.push(JSON.stringify(S.project));
  if (S.undo.length > 200) S.undo.shift();
  S.redo.length = 0;
  S.lastKey = key || null;
  S.lastAt = now;
}
function edit(key, fn) { pushUndo(key); fn(S.project); refresh({ panel: false }); }
function applyHistory(from, to) {
  if (!from.length) return;
  to.push(JSON.stringify(S.project));
  S.project = JSON.parse(from.pop());
  S.lastKey = null;
  if (S.sel && !selItem()) S.sel = null;
  refresh();
  seek(S.t);
}
const undo = () => applyHistory(S.undo, S.redo);
const redo = () => applyHistory(S.redo, S.undo);

// Number of changes against the project the last render saw: items present on one side only (a moved or edited item counts once).
function computeDiff() {
  const base = S.baseline, cur = S.project;
  if (!S.render || !base) return (S.diff = { n: S.render && S.renderState === "stale" ? null : 0, changed: {} });
  let n = 0;
  const changed = {};
  for (const key of ["scenes", "overlays", "captions", "captionBands", "sfx", "punches"]) {
    const pool = new Map();
    (base[key] || []).forEach((x) => { const s = JSON.stringify(x); pool.set(s, (pool.get(s) || 0) + 1); });
    const fresh = new Set();
    (cur[key] || []).forEach((x, i) => { const s = JSON.stringify(x), c = pool.get(s) || 0; if (c > 0) pool.set(s, c - 1); else fresh.add(i); });
    const gone = [...pool.values()].reduce((a, b) => a + b, 0);
    n += Math.max(fresh.size, gone);
    changed[key] = fresh;
  }
  const lists = new Set(["scenes", "overlays", "captions", "captionBands", "sfx", "punches"]);
  for (const k of new Set([...Object.keys(base), ...Object.keys(cur)])) if (!lists.has(k) && JSON.stringify(base[k]) !== JSON.stringify(cur[k])) n++;
  return (S.diff = { n, changed });
}

// Scene editing. A cut between scene k-1 and k moves as a rolling edit: the left scene gets longer or shorter, the right
// scene's source point `in` follows so the footage stays in step with the timeline (Shift keeps `in`).
function applyCut(p, k, t, orig, keepIn) {
  const a = p.scenes[k - 1], b = p.scenes[k], a0 = orig[k - 1], b0 = orig[k];
  t = r3(clamp(t, a0.start + MIN_LEN, b0.end - MIN_LEN));
  a.end = t; b.start = t;
  if (!keepIn) b.in = r3(Math.max(0, (b0.in || 0) + (t - b0.start) * (b0.speed || 1)));
}
function setLastEnd(p, t, orig) {
  const last = p.scenes.length - 1;
  t = r3(Math.max(orig[last].start + MIN_LEN, t));
  const follows = Math.abs((p.duration || 0) - orig[last].end) < 0.002;
  p.scenes[last].end = t;
  if (follows) p.duration = t;
}
function removeScene(p, i) {
  const sc = p.scenes, s = sc[i];
  if (sc.length < 2) return false;
  if (i > 0) sc[i - 1].end = s.end;
  else { const nx = sc[1]; nx.in = r3(Math.max(0, (nx.in || 0) - (nx.start - 0) * (nx.speed || 1))); nx.start = 0; }
  sc.splice(i, 1);
  return true;
}
function splitScene() {
  const p = P(), i = sceneIndexAt(S.t), s = p.scenes[i], t = r3(S.t);
  if (!s || t < s.start + 0.2 || t > s.end - 0.2) return toast("Đặt playhead vào giữa một cảnh (cách mép ≥ 0,2 s) rồi cắt.", "err");
  pushUndo(null);
  const right = clone(s);
  delete right.accent; delete right.flash;
  right.start = t; right.in = r3((s.in || 0) + (t - s.start) * (s.speed || 1));
  right.transition = { type: "cut" };
  s.end = t;
  p.scenes.splice(i + 1, 0, right);
  S.sel = { kind: "scene", i: i + 1 };
  refresh();
}
function reorderScenes(p, orig, from, to) {
  const durs = orig.map((s) => s.end - s.start);
  const order = orig.map((_, i) => i).filter((i) => i !== from);
  order.splice(to, 0, from);
  let at = 0;
  p.scenes = order.map((i) => {
    const s = clone(orig[i]);
    s.start = r3(at); at += durs[i]; s.end = r3(at);
    return s;
  });
  const total = orig[orig.length - 1].end;
  p.scenes[p.scenes.length - 1].end = total; // keep the sum exact despite rounding
}

function newOverlay() {
  const start = r3(S.t), end = r3(Math.min(Math.max(dur(), start + 0.6), start + 2.5));
  return { component: "title", start, end, zone: "top", props: { style: "stack", lines: ["Chữ mới"] } };
}
function addItem(kind) {
  const p = P(), t = r3(S.t);
  pushUndo(null);
  if (kind === "overlay") (p.overlays ||= []).push(newOverlay());
  if (kind === "caption") (p.captions ||= []).push({ text: "Phụ đề mới", start: t, end: r3(Math.min(Math.max(dur(), t + 0.6), t + 2)) });
  if (kind === "sfx") {
    if (!S.assets.sfx.length) { S.undo.pop(); return toast("Chưa có file âm trong public/sfx/.", "err"); }
    (p.sfx ||= []).push({ src: S.assets.sfx[0], at: t, volumeDb: -16 });
  }
  S.sel = { kind, i: listOf(kind).length - 1 };
  refresh();
  setTimeout(() => { const f = $("#panel textarea, #panel input[type=text]"); if (f) { f.focus(); f.select(); } }, 60);
}
function deleteSelected() {
  if (!S.sel) return;
  const { kind, i } = S.sel;
  if (kind === "scene" && P().scenes.length < 2) return toast("Project cần ít nhất một cảnh.", "err");
  pushUndo(null);
  if (kind === "scene") removeScene(P(), i); else listOf(kind).splice(i, 1);
  S.sel = null;
  refresh();
  seek(S.t);
}
function duplicateSelected() {
  if (!S.sel || !["overlay", "caption"].includes(S.sel.kind)) return;
  const list = listOf(S.sel.kind), o = clone(list[S.sel.i]), len = o.end - o.start;
  pushUndo(null);
  o.start = r3(o.end); o.end = r3(o.start + len);
  list.push(o);
  S.sel = { kind: S.sel.kind, i: list.length - 1 };
  refresh();
}

function problems() {
  const p = P(), out = [], sc = p.scenes, comps = new Set([...S.schema.components, ...FALLBACK.components]);
  const clips = new Set(S.assets.clips.map((c) => c.name));
  sc.forEach((s, i) => {
    if (!(s.end > s.start)) out.push(`Cảnh ${i + 1}: kết thúc phải sau bắt đầu.`);
    if (i > 0 && Math.abs(s.start - sc[i - 1].end) > 0.002) out.push(`Cảnh ${i} và ${i + 1}: lệch ${r3(s.start - sc[i - 1].end)} s (lẽ ra liền nhau).`);
    if (s.clip && clips.size && !clips.has(s.clip)) out.push(`Cảnh ${i + 1}: clip "${s.clip}" không có trong public/clips/.`);
  });
  if (sc.length && Math.abs(sceneEnd() - dur()) > 0.05) out.push(`Cảnh cuối kết thúc ở ${r3(sceneEnd())} s nhưng độ dài project là ${dur()} s.`);
  (p.overlays || []).forEach((o, i) => {
    if (!(o.end > o.start)) out.push(`Chữ/đồ họa ${i + 1} (${o.component}): kết thúc phải sau bắt đầu.`);
    if (o.end > dur() + 0.05) out.push(`Chữ/đồ họa ${i + 1} (${o.component}) vượt quá độ dài project.`);
    if (!comps.has(o.component)) out.push(`Chữ/đồ họa ${i + 1}: thành phần "${o.component}" không có trong template.`);
    const src = o.props && o.props.src;
    if (typeof src === "string" && S.assets.images.length && !S.assets.images.includes(src)) out.push(`Chữ/đồ họa ${i + 1}: ảnh "${src}" không có trong public/images/.`);
  });
  return out;
}

// ============================================================================ 6. timeline
let drag = null;

function timelineDur() {
  const p = P();
  let m = Math.max(p.duration || 0, sceneEnd());
  (p.overlays || []).forEach((o) => { m = Math.max(m, o.end || 0); });
  (p.captions || []).forEach((c) => { m = Math.max(m, c.end || 0); });
  return m + 0.5;
}
function assignLanes(list) {
  const order = list.map((_, i) => i).sort((a, b) => list[a].start - list[b].start || list[a].end - list[b].end);
  const ends = [], lane = new Array(list.length).fill(0);
  for (const i of order) {
    let l = ends.findIndex((e) => e <= list[i].start + 1e-3);
    if (l < 0) { l = ends.length; ends.push(0); }
    ends[l] = list[i].end;
    lane[i] = l;
  }
  return { lane, count: Math.max(1, ends.length) };
}
function mainText(o) {
  const p = o.props || {};
  const parts = [];
  for (const k of ["lines", "lead", "emph", "text", "label", "title", "name", "value", "items", "caption", "src"]) {
    const v = p[k];
    if (v == null || v === "") continue;
    parts.push(Array.isArray(v) ? v.map((x) => (x && typeof x === "object" ? x.label || x.caption || x.clip || "" : x)).join(" · ") : String(v) + (k === "value" && p.unit ? ` ${p.unit}` : ""));
    if (k !== "lead") break;
  }
  return parts.join(" ").trim();
}

function rulerNode(W, D) {
  const key = `${S.pps}|${D}`;
  if (S.rulerKey === key) return S.rulerNode;
  const steps = [0.1, 0.2, 0.5, 1, 2, 5, 10, 15, 30, 60, 120], major = steps.find((s) => s * S.pps >= 70) || 120, minor = major / 5;
  const ruler = h("div", { class: "tl-ruler", style: `width:${W}px` });
  for (let i = 0, t = 0; t <= D + 1e-6; i++, t = r3(i * minor)) {
    const isMajor = i % 5 === 0;
    if (!isMajor && minor * S.pps < 7) continue;
    ruler.append(h("div", { class: `tick${isMajor ? " major" : ""}`, style: `left:${t * S.pps}px` }, isMajor ? h("span", {}, major >= 1 ? fmt(t).replace(/\.00$/, "") : fmt(t)) : null));
  }
  S.rulerKey = key;
  return (S.rulerNode = ruler);
}

function itemEl(kind, i, o, geo, body, extra = {}) {
  const sel = S.sel && S.sel.kind === kind && S.sel.i === i;
  const list = { scene: "scenes", overlay: "overlays", caption: "captions", sfx: "sfx" }[kind];
  const chg = S.diff.changed[list] && S.diff.changed[list].has(i);
  return h("div", {
    class: `item ${kind}${sel ? " sel" : ""}${chg ? " chg" : ""}${drag && drag.moved && drag.kind === kind && drag.i === i ? " dragging" : ""}`,
    "data-kind": kind, "data-i": i, style: `left:${geo.left}px;width:${geo.width}px;top:${geo.top}px;height:${geo.height}px;${extra.style || ""}`, title: extra.title || "",
    ...(extra.attrs || {}),
  }, extra.noHandles ? null : h("span", { class: "h-l" }), body, extra.noHandles ? null : h("span", { class: "h-r" }));
}

function renderTimeline() {
  const p = P(), pps = S.pps, D = timelineDur(), W = Math.ceil(D * pps);
  const root = $("#tlContent");
  root.style.width = `${LABEL_W + W}px`;
  const row = (id, label, sub, height, kids) => h("div", { class: "tl-row", "data-track": id },
    h("div", { class: "tl-label" }, label, sub ? h("small", {}, sub) : null),
    h("div", { class: "tl-lane", "data-track": id, style: `height:${height}px;width:${W}px` }, kids));
  const rows = [h("div", { class: "tl-row tl-ruler-row" }, h("div", { class: "tl-label" }, "Thời gian"), rulerNode(W, D))];

  const scenes = p.scenes.map((s, i) => {
    const tr = i > 0 && s.transition ? s.transition.type : "";
    return itemEl("scene", i, s, { left: s.start * pps, width: Math.max(6, (s.end - s.start) * pps), top: 3, height: TRACK_H.scenes - 6 },
      [h("span", { class: "t1" }, `${i + 1} ${s.type || ""}`.trim()), h("span", { class: "t2" }, `${s.clip || "không clip"} · ${r3(s.end - s.start)}s${tr ? ` · ${tr}` : ""}`)],
      { title: `Cảnh ${i + 1}: ${fmt(s.start)} → ${fmt(s.end)}\nClip ${s.clip || "—"} từ ${r3(s.in || 0)}s` });
  });
  rows.push(row("scenes", "Cảnh", `${p.scenes.length} cảnh`, TRACK_H.scenes, scenes));

  const ovs = p.overlays || [];
  const lanes = drag && drag.lanes && drag.lanes.lane.length === ovs.length ? drag.lanes : assignLanes(ovs);
  const ovItems = ovs.map((o, i) => itemEl("overlay", i, o, { left: o.start * pps, width: Math.max(6, (o.end - o.start) * pps), top: lanes.lane[i] * LANE_H + 2, height: LANE_H - 4 },
    [h("span", { class: "t1" }, mainText(o) ? `${o.component} · ${mainText(o)}` : o.component)],
    { style: `--h:${hue(o.component)}`, title: `${o.component}: ${fmt(o.start)} → ${fmt(o.end)}${o.zone ? ` · ${o.zone}` : ""}\n${mainText(o)}` }));
  rows.push(row("overlays", "Chữ · đồ họa", `${ovs.length} mục`, lanes.count * LANE_H + 4, ovItems));

  const caps = (p.captions || []).map((c, i) => itemEl("caption", i, c, { left: c.start * pps, width: Math.max(6, (c.end - c.start) * pps), top: 3, height: TRACK_H.caption - 6 },
    [h("span", { class: "t1" }, c.text)], { title: `${fmt(c.start)} → ${fmt(c.end)}\n${c.text}` }));
  rows.push(row("captions", "Phụ đề", `${(p.captions || []).length} dòng`, TRACK_H.caption, caps));

  const music = p.music && p.music.src;
  for (const [id, label, src, none] of [["voice", "Giọng", p.voice, "Chưa có giọng"], ["music", "Nhạc", music, "Chưa có nhạc"]]) {
    const cv = (S.waveEls[id] ||= h("canvas"));
    const w = S.waves[src];
    const hint = !src ? none : w === "loading" ? "Đang đọc sóng âm…" : w && w.error ? `Không đọc được: ${w.error}` : "";
    rows.push(row(id, label, src ? src.split("/").pop() : "", TRACK_H[id], [cv, hint ? h("span", { class: "lane-hint" }, hint) : null]));
  }

  const cues = (p.sfx || []).map((c, i) => itemEl("sfx", i, c, { left: c.at * pps - 2, width: 4, top: 4, height: TRACK_H.sfx - 8 }, null,
    { noHandles: true, title: `${c.src} tại ${fmt(c.at)}`, attrs: { "data-name": (c.src || "").split("/").pop().replace(/\.[^.]+$/, "") } }));
  rows.push(row("sfx", "Âm hiệu ứng", `${cues.length} âm`, TRACK_H.sfx, cues));

  S.phEl = h("div", { class: "playhead", style: `left:${LABEL_W + S.t * pps}px` });
  const kids = [...rows, S.phEl];
  if (S.snapAt != null) kids.push(h("div", { class: "snapline", style: `left:${LABEL_W + S.snapAt * pps}px` }));
  root.replaceChildren(...kids);
  drawWaves();
}

function drawWaves() {
  const view = $("#tlScroll"), vw = Math.max(0, view.clientWidth - LABEL_W), scroll = view.scrollLeft, dpr = window.devicePixelRatio || 1;
  for (const id of ["voice", "music"]) {
    const cv = S.waveEls[id];
    if (!cv || !cv.parentElement) continue;
    const src = id === "voice" ? P().voice : P().music && P().music.src, data = src && S.waves[src];
    const key = `${src}|${S.pps}|${scroll}|${vw}|${data && data.peaks ? data.peaks.length : 0}|${getComputedStyle(document.documentElement).getPropertyValue("--wave-voice")}|${dpr}`;
    if (cv.dataset.key === key) continue;
    cv.dataset.key = key;
    const H = TRACK_H[id];
    cv.width = Math.max(1, Math.round(vw * dpr)); cv.height = Math.round(H * dpr);
    cv.style.width = `${vw}px`; cv.style.height = `${H}px`; cv.style.left = `${scroll}px`;
    const ctx = cv.getContext("2d");
    ctx.scale(dpr, dpr);
    if (!data || !data.peaks) continue;
    ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue(id === "voice" ? "--wave-voice" : "--wave-music").trim() || "#4a8";
    const peaks = data.peaks, rate = data.rate;
    for (let x = 0; x < vw; x++) {
      const t0 = (scroll + x) / S.pps, a = Math.floor(t0 * rate), b = Math.max(a + 1, Math.ceil((t0 + 1 / S.pps) * rate));
      if (a >= peaks.length) break;
      let m = 0;
      for (let j = a; j < b && j < peaks.length; j++) if (peaks[j] > m) m = peaks[j];
      const amp = m / 255, hh = Math.max(1, amp * H * 0.9);
      ctx.fillRect(x, (H - hh) / 2, 1, hh);
    }
  }
}
function ensureWaves() {
  for (const src of [P().voice, P().music && P().music.src].filter(Boolean)) {
    if (src in S.waves) continue;
    S.waves[src] = "loading";
    api(`/api/waveform?src=${enc(src)}`).then((d) => { S.waves[src] = d; refresh({ panel: false }); })
      .catch((e) => { S.waves[src] = { error: e.message }; refresh({ panel: false }); });
  }
}

function setZoom(pps, anchorPx) {
  const view = $("#tlScroll"), old = S.pps;
  S.pps = clamp(pps, ZOOM_MIN, ZOOM_MAX);
  const ax = anchorPx == null ? (view.clientWidth - LABEL_W) / 2 : anchorPx, anchorT = (view.scrollLeft + ax) / old;
  $("#zoom").value = String(Math.round((Math.log(S.pps / ZOOM_MIN) / Math.log(ZOOM_MAX / ZOOM_MIN)) * 100));
  renderTimeline();
  view.scrollLeft = Math.max(0, anchorT * S.pps - ax);
  drawWaves();
}
function fitZoom() {
  const view = $("#tlScroll");
  S.pps = clamp((view.clientWidth - LABEL_W - 24) / timelineDur(), ZOOM_MIN, ZOOM_MAX);
  setZoom(S.pps, 0);
  view.scrollLeft = 0;
}

const xToTime = (e) => (e.clientX - $("#tlContent").getBoundingClientRect().left - LABEL_W) / S.pps;
function snapPoints(skip) {
  const p = P(), pts = [0, dur(), S.t];
  p.scenes.forEach((s, i) => { if (!skip.has(`scene:${i}:start`)) pts.push(s.start); if (!skip.has(`scene:${i}:end`)) pts.push(s.end); });
  (p.overlays || []).forEach((o, i) => { if (!skip.has(`overlay:${i}`)) pts.push(o.start, o.end); });
  (p.captions || []).forEach((c, i) => { if (!skip.has(`caption:${i}`)) pts.push(c.start, c.end); });
  (p.sfx || []).forEach((c, i) => { if (!skip.has(`sfx:${i}`)) pts.push(c.at); });
  return pts;
}
function snapTo(t, pts) {
  if (!S.opts.snap || (drag && drag.alt)) return { t, hit: null };
  let best = null, bd = SNAP_PX / S.pps;
  for (const q of pts) { const d = Math.abs(q - t); if (d < bd) { bd = d; best = q; } }
  return best == null ? { t, hit: null } : { t: best, hit: best };
}

function startItemDrag(e, node) {
  const kind = node.dataset.kind, i = +node.dataset.i, list = listOf(kind);
  const mode = e.target.classList.contains("h-l") ? "l" : e.target.classList.contains("h-r") ? "r" : "move";
  if (kind === "scene" && mode === "l" && i === 0) return;
  S.sel = { kind, i };
  drag = { kind, i, mode, x0: e.clientX, t0: xToTime(e), moved: false, orig: clone(list), origItem: clone(list[i]), alt: e.altKey, shift: e.shiftKey, lanes: kind === "overlay" ? assignLanes(P().overlays) : null };
  window.addEventListener("pointermove", onDragMove);
  window.addEventListener("pointerup", onDragEnd, { once: true });
  e.preventDefault();
  refresh();
}
function onDragMove(e) {
  const d = drag;
  if (!d) return;
  if (!d.moved) {
    if (Math.abs(e.clientX - d.x0) < 3) return;
    d.moved = true;
    S.lastKey = null; pushUndo(null);
  }
  d.alt = e.altKey; d.shift = e.shiftKey;
  const p = P(), dt = (e.clientX - d.x0) / S.pps, o = d.origItem, snapHit = [];
  const snap = (t, skip) => { const r = snapTo(t, snapPoints(skip)); if (r.hit != null) snapHit.push(r.hit); return r.t; };
  if (d.kind === "scene") {
    if (d.mode === "move") {
      const mid = (o.start + o.end) / 2 + dt, others = d.orig.map((s, k) => [k, (s.start + s.end) / 2]).filter(([k]) => k !== d.i);
      const to = others.filter(([, c]) => c < mid).length;
      reorderScenes(p, d.orig, d.i, to);
      S.sel = { kind: "scene", i: to };
    } else {
      const k = d.mode === "l" ? d.i : d.i + 1;
      const skip = new Set([`scene:${k - 1}:end`, `scene:${k}:start`]);
      if (k >= p.scenes.length) setLastEnd(p, snap(o.end + dt, new Set([`scene:${d.i}:end`])), d.orig);
      else applyCut(p, k, snap((d.mode === "l" ? o.start : o.end) + dt, skip), d.orig, d.shift);
    }
  } else if (d.kind === "sfx") {
    p.sfx[d.i].at = r3(clamp(snap(o.at + dt, new Set([`sfx:${d.i}`])), 0, dur()));
  } else {
    const it = listOf(d.kind)[d.i], skip = new Set([`${d.kind}:${d.i}`]), len = o.end - o.start;
    if (d.mode === "move") {
      const a = snapTo(o.start + dt, snapPoints(skip)), b = snapTo(o.end + dt, snapPoints(skip));
      const pick = a.hit != null && (b.hit == null || Math.abs(a.t - (o.start + dt)) <= Math.abs(b.t - (o.end + dt))) ? a.t : b.hit != null ? b.t - len : o.start + dt;
      if (a.hit != null || b.hit != null) snapHit.push(a.hit != null ? a.hit : b.hit);
      it.start = r3(clamp(pick, 0, Math.max(0, dur() - len))); it.end = r3(it.start + len);
    } else if (d.mode === "l") it.start = r3(clamp(snap(o.start + dt, skip), 0, o.end - MIN_LEN));
    else it.end = r3(Math.max(o.start + MIN_LEN, snap(o.end + dt, skip)));
  }
  S.snapAt = snapHit.length ? snapHit[0] : null;
  refresh({ panel: false });
}
function onDragEnd(e) {
  window.removeEventListener("pointermove", onDragMove);
  const d = drag;
  drag = null; S.snapAt = null;
  if (d && !d.moved) seek(xToTime(e)); // a plain click also puts the playhead there
  refresh();
}
function startScrub(e) {
  const move = (ev) => seek(clamp(xToTime(ev), 0, dur()));
  move(e);
  window.addEventListener("pointermove", move);
  window.addEventListener("pointerup", () => window.removeEventListener("pointermove", move), { once: true });
}

// ============================================================================ 7. preview and player
const vid = () => $("#vid");
const usingRender = () => !!S.render && !S.opts.proxy;
const draftOn = () => (S.opts.draft == null ? !usingRender() || S.diff.n !== 0 : S.opts.draft);
let audio = { voice: null, music: null }, lastTick = 0, clockT0 = 0, clockW0 = 0, draftKey = "";

function proxyTarget() {
  const sc = P().scenes[sceneIndexAt(S.t)];
  if (!sc) return null;
  const ramp = sc.ramp && sc.ramp.length ? sc.ramp.reduce((a, b) => a + b, 0) / sc.ramp.length : null;
  return { sc, url: sc.clip ? `/media/clips/${enc(sc.clip)}.mp4` : "", at: (sc.in || 0) + (S.t - sc.start) * (sc.speed || ramp || 1), rate: sc.speed || ramp || 1 };
}
function syncProxy(force) {
  const v = vid(), tgt = proxyTarget(), none = $("#noclip");
  if (!tgt || !tgt.url) {
    if (v.dataset.url) { v.pause(); v.removeAttribute("src"); v.dataset.url = ""; v.load(); }
    none.hidden = false;
    none.textContent = tgt ? "Cảnh này không có clip (nền lưới hoặc thẻ đồ họa)." : "";
    return;
  }
  none.hidden = true;
  v.muted = true;
  if (v.dataset.url !== tgt.url) {
    v.dataset.url = tgt.url; v.src = tgt.url;
    v.addEventListener("loadedmetadata", () => { v.currentTime = proxyTarget() ? proxyTarget().at : 0; if (S.playing) v.play().catch(() => {}); }, { once: true });
  } else if (force || Math.abs(v.currentTime - tgt.at) > 0.3) v.currentTime = tgt.at;
  v.playbackRate = clamp(tgt.rate, 0.25, 4);
}
function syncAudio(force) {
  if (usingRender()) return;
  const p = P(), want = { voice: p.voice, music: p.music && p.music.src };
  for (const id of ["voice", "music"]) {
    const src = want[id];
    if (!src) { if (audio[id]) { audio[id].pause(); audio[id] = null; } continue; }
    if (!audio[id] || audio[id].dataset.src !== src) {
      if (audio[id]) audio[id].pause();
      audio[id] = new Audio(`/media/${src.split("/").map(enc).join("/")}`);
      audio[id].dataset.src = src;
    }
    const a = audio[id];
    a.volume = id === "voice" ? 1 : clamp(Math.pow(10, ((p.music && p.music.volumeDb) ?? -14) / 20), 0, 1);
    if (S.playing) { if (force || Math.abs(a.currentTime - S.t) > 0.3) a.currentTime = S.t; if (a.paused) a.play().catch(() => {}); }
    else { a.pause(); if (force) a.currentTime = S.t; }
  }
}
function loadSource() {
  const v = vid();
  if (usingRender()) {
    const url = `${S.render.url}?v=${S.render.mtime}`;
    $("#noclip").hidden = true;
    if (v.dataset.url !== url) {
      v.dataset.url = url; v.muted = false; v.src = url;
      v.addEventListener("loadedmetadata", () => { v.currentTime = S.t; }, { once: true });
    }
    for (const id of ["voice", "music"]) if (audio[id]) { audio[id].pause(); audio[id] = null; }
  } else {
    if (v.dataset.url && v.dataset.url.startsWith("/out/")) { v.removeAttribute("src"); v.dataset.url = ""; v.load(); }
    syncProxy(true);
    syncAudio(true);
  }
}
function setPlaying(on) {
  const v = vid();
  if (on === S.playing) return;
  S.playing = on;
  $("#btnPlay").textContent = on ? "⏸" : "▶";
  if (on) {
    if (S.t >= dur() - 0.05) seek(0);
    clockT0 = S.t; clockW0 = performance.now(); lastTick = S.t;
    if (usingRender()) v.play().catch(() => setPlaying(false)); else { syncProxy(true); v.play().catch(() => {}); syncAudio(true); }
    requestAnimationFrame(tick);
  } else { v.pause(); for (const id of ["voice", "music"]) if (audio[id]) audio[id].pause(); }
}
function tick() {
  if (!S.playing) return;
  const v = vid();
  if (usingRender()) {
    S.t = v.currentTime;
    if (v.ended || S.t >= dur()) { S.t = Math.min(S.t, dur()); setPlaying(false); }
  } else {
    S.t = clockT0 + (performance.now() - clockW0) / 1000;
    if (S.t >= dur()) { S.t = dur(); setPlaying(false); }
    syncProxy(false); syncAudio(false);
    for (const c of P().sfx || []) if (c.at > lastTick && c.at <= S.t) { const a = new Audio(`/media/${c.src.split("/").map(enc).join("/")}`); a.volume = clamp(Math.pow(10, (c.volumeDb ?? -16) / 20), 0, 1); a.play().catch(() => {}); }
  }
  lastTick = S.t;
  updateHead(true);
  if (S.playing) requestAnimationFrame(tick);
}
function seek(t) {
  S.t = clamp(t, 0, Math.max(dur(), 0));
  if (S.playing) { clockT0 = S.t; clockW0 = performance.now(); lastTick = S.t; }
  if (usingRender()) { if (vid().readyState > 0) vid().currentTime = S.t; } else { syncProxy(true); syncAudio(true); }
  updateHead(false);
}
function updateHead(follow) {
  $("#timeLabel").textContent = `${fmt(S.t)} / ${fmt(dur())} · f${Math.round(S.t * fps())}`;
  if (S.phEl) S.phEl.style.left = `${LABEL_W + S.t * S.pps}px`;
  const view = $("#tlScroll"), x = S.t * S.pps;
  if (follow && (x > view.scrollLeft + view.clientWidth - LABEL_W - 30 || x < view.scrollLeft)) view.scrollLeft = Math.max(0, x - 60);
  renderDraft();
  renderZones();
}

function renderZones() {
  const svg = $("#zones"), showSafe = S.opts.safe, showFace = S.opts.face;
  const sc = P().scenes[sceneIndexAt(S.t)], key = `${showSafe}|${showFace}|${P().layout}|${sc ? JSON.stringify([sc.face, sc.camera && sc.camera.focus]) : ""}`;
  if (svg.dataset.key === key) return;
  svg.dataset.key = key;
  svg.replaceChildren();
  const red = { fill: "rgb(230 60 60 / .26)", stroke: "rgb(255 110 110)", "stroke-width": 3, "stroke-dasharray": "14 8" };
  const label = (x, y, text, color) => { const t = svgEl("text", { x, y, fill: color || "#fff", "text-anchor": "middle" }); t.textContent = text; svg.append(t); };
  if (showSafe) {
    if (P().layout === "reels-ad") { // Meta Reels ads: keep the top 14%, bottom 35% and 6% each side clear
      svg.append(svgEl("rect", { ...red, x: 0, y: 0, width: FRAME_W, height: 269 }), svgEl("rect", { ...red, x: 0, y: 1248, width: FRAME_W, height: 672 }),
        svgEl("rect", { ...red, x: 0, y: 269, width: 65, height: 979 }), svgEl("rect", { ...red, x: 1015, y: 269, width: 65, height: 979 }));
      label(540, 150, "Reels ads: trên 14%"); label(540, 1580, "Reels ads: dưới 35%");
    } else { // TikTok feed, measured on a phone (references/layout-and-motion-graphics.md)
      svg.append(svgEl("rect", { ...red, x: 0, y: 0, width: FRAME_W, height: 220 }), svgEl("rect", { ...red, x: 0, y: 1400, width: FRAME_W, height: 520 }),
        svgEl("rect", { ...red, x: 900, y: 700, width: 180, height: 700 }),
        svgEl("rect", { x: 80, y: 1644, width: 527, height: 65, rx: 12, fill: "rgb(255 200 40 / .35)", stroke: "#ffc928", "stroke-width": 3 }),
        svgEl("circle", { cx: 112, cy: 1677, r: 24, fill: "none", stroke: "#ffc928", "stroke-width": 4 }),
        svgEl("rect", { x: 90, y: 236, width: 900, height: 184, rx: 14, fill: "none", stroke: "rgb(80 220 130)", "stroke-width": 3, "stroke-dasharray": "10 8" }),
        svgEl("line", { x1: 90, x2: 990, y1: 1340, y2: 1340, stroke: "rgb(80 220 130)", "stroke-width": 3, "stroke-dasharray": "10 8" }));
      label(540, 140, "Thanh TikTok"); label(540, 1530, "Mô tả / thanh sản phẩm"); label(990, 1060, "Nút bên phải", "#ffd0d0");
      label(540, 336, "Vùng tiêu đề", "#9ff0c0"); label(540, 1320, "Phụ đề", "#9ff0c0"); label(340, 1755, "Thanh sản phẩm", "#ffe28a");
    }
  }
  if (showFace && sc) {
    if (sc.face) {
      const rx = sc.face.r * FRAME_W;
      svg.append(svgEl("ellipse", { cx: sc.face.x * FRAME_W, cy: sc.face.y * FRAME_H, rx, ry: rx * 1.3, fill: "rgb(60 190 255 / .16)", stroke: "#4cc9ff", "stroke-width": 4, "stroke-dasharray": "12 8" }));
      label(sc.face.x * FRAME_W, sc.face.y * FRAME_H - rx * 1.3 - 12, "mặt", "#bfeaff");
    }
    const f = sc.camera && sc.camera.focus;
    if (f) {
      const cx = f[0] * FRAME_W, cy = f[1] * FRAME_H;
      svg.append(svgEl("line", { x1: cx - 34, x2: cx + 34, y1: cy, y2: cy, stroke: "#ffd54a", "stroke-width": 4 }), svgEl("line", { x1: cx, x2: cx, y1: cy - 34, y2: cy + 34, stroke: "#ffd54a", "stroke-width": 4 }));
      label(cx, cy - 44, "lấy nét", "#ffeaa0");
    }
  }
}
const ZONE_BOX = { top: [236, 184], upper: [470, 150], center: [860, 220], lower: [1230, 150] }; // y of the top edge (centre for "center") and height
function renderDraft() {
  const layer = $("#draft"), on = draftOn();
  const active = on ? (P().overlays || []).map((o, i) => (S.t >= o.start && S.t < o.end ? i : -1)).filter((i) => i >= 0) : [];
  const cap = on ? (P().captions || []).findIndex((c) => S.t >= c.start && S.t < c.end) : -1;
  const key = `${on}|${active.join(",")}|${cap}|${S.sel ? `${S.sel.kind}${S.sel.i}` : ""}|${P().overlays ? JSON.stringify(active.map((i) => P().overlays[i])) : ""}|${cap >= 0 ? P().captions[cap].text : ""}`;
  if (draftKey === key) return;
  draftKey = key;
  layer.replaceChildren();
  for (const i of active) {
    const o = P().overlays[i], at = o.props && Array.isArray(o.props.at) && o.props.at.length === 2 ? o.props.at : null;
    const [y0, hh] = ZONE_BOX[o.zone || "top"] || ZONE_BOX.top, w = at ? 560 : 900;
    const top = at ? at[1] * FRAME_H - hh / 2 : o.zone === "center" ? y0 - hh / 2 : y0, left = at ? at[0] * FRAME_W - w / 2 : 90;
    const box = h("div", {
      class: `dbox${S.sel && S.sel.kind === "overlay" && S.sel.i === i ? " sel" : ""}`,
      style: `left:${(left / FRAME_W) * 100}%;top:${(top / FRAME_H) * 100}%;width:${(w / FRAME_W) * 100}%;height:${(hh / FRAME_H) * 100}%`,
      onclick: () => { S.sel = { kind: "overlay", i }; refresh(); },
    }, h("span", { class: "tag" }, o.component), h("span", { class: "txt" }, mainText(o)));
    layer.append(box);
  }
  if (cap >= 0) layer.append(h("div", { class: "dcap", style: `top:${(1340 / FRAME_H) * 100}%` }, P().captions[cap].text));
}
function renderNote() {
  const note = $("#renderNote"), n = S.diff.n;
  note.className = "note";
  if (usingRender()) {
    if (n === null) { note.textContent = "Bản render cũ: file project đã được sửa sau lần render."; note.classList.add("stale"); }
    else if (n > 0) { note.textContent = `Bản render cũ, có ${n} chỗ đã sửa. Bật "Nháp chữ" để xem tạm hoặc bấm Render lại.`; note.classList.add("stale"); }
    else note.textContent = `Đang xem bản render ${S.render.name} (${when(S.render.mtime)}).`;
  } else note.textContent = S.render ? "Đang xem clip proxy của cảnh hiện tại (không có hiệu ứng, màu, chữ thật)." : "Chưa có bản render: đang xem clip proxy của cảnh hiện tại, chữ chỉ là bản nháp.";
}
function renderSourceSelect() {
  const sel = $("#srcSelect");
  sel.replaceChildren(...S.renders.map((r) => h("option", { value: `r:${r.name}`, selected: usingRender() && S.render && S.render.name === r.name }, `Render: ${r.name}`)),
    h("option", { value: "proxy", selected: !usingRender() }, "Clip proxy (cảnh hiện tại)"));
}

// ============================================================================ 8. properties panel
const field = (label, ...ctl) => h("div", { class: "f" }, h("label", {}, label), h("div", { class: "ctl" }, ctl));
const unit = (t) => h("span", { class: "unit" }, t);
const btn = (text, fn, cls = "") => h("button", { class: cls, type: "button", onclick: fn }, text);
function numberInput(value, onSet, { step = 0.05, min, max, placeholder } = {}) {
  const inp = h("input", { type: "number", step, min, max, placeholder, value: value ?? "" });
  inp.addEventListener("input", () => { const raw = inp.value.trim(); if (raw === "") return onSet(null); const v = parseFloat(raw); if (Number.isFinite(v)) onSet(v); });
  return inp;
}
function textInput(value, onSet, { list, placeholder } = {}) {
  const inp = h("input", { type: "text", value: value ?? "", list, placeholder });
  inp.addEventListener("input", () => onSet(inp.value));
  return inp;
}
function areaInput(value, onSet, { rows = 3, mono = false } = {}) {
  const ta = h("textarea", { rows, class: mono ? "mono" : "" });
  ta.value = value ?? "";
  ta.addEventListener("input", () => onSet(ta.value, ta));
  return ta;
}
function selectInput(options, value, onSet) {
  const opts = options.map((o) => (Array.isArray(o) ? o : [o, o]));
  if (value != null && !opts.some(([v]) => v === String(value))) opts.push([String(value), `${value} (ngoài danh sách)`]);
  const sel = h("select", {}, opts.map(([v, text]) => h("option", { value: v }, text)));
  sel.value = value == null ? "" : String(value);
  sel.addEventListener("change", () => { onSet(sel.value); sel.blur(); });
  return sel;
}
function checkInput(value, onSet) {
  const c = h("input", { type: "checkbox", checked: !!value });
  c.addEventListener("change", () => { onSet(c.checked); c.blur(); });
  return c;
}
function pointInput(value, onSet) {
  const v = Array.isArray(value) ? value : [0.5, 0.5];
  const mk = (idx) => numberInput(v[idx], (n) => { if (n != null) { const next = [...v]; next[idx] = r3(n); v[idx] = next[idx]; onSet(next); } }, { step: 0.01 });
  return [mk(0), mk(1)];
}
function jsonInput(value, onSet, rows = 4) {
  return areaInput(JSON.stringify(value, null, 1), (text, ta) => {
    try { onSet(JSON.parse(text)); ta.classList.remove("bad"); } catch { ta.classList.add("bad"); }
  }, { rows, mono: true });
}
const setOrDelete = (obj, k, v) => { if (v == null || v === "") delete obj[k]; else obj[k] = v; };
const componentNames = () => [...new Set([...(S.schema.components.length ? S.schema.components : FALLBACK.components), ...(P().overlays || []).map((o) => o.component)])];
let enumId = 0;
function enumList(options) {
  const id = `dl${++enumId}`;
  $("#panel").append(h("datalist", { id }, options.map((o) => h("option", { value: o }))));
  return id;
}

function propControl(o, i, key, val) {
  const k = `overlay:${i}:p.${key}`, set = (v) => edit(k, () => { (o.props ||= {})[key] = v; });
  const enumKey = `${o.component}.${key}`;
  if (ENUMS[enumKey]) return [textInput(val, set, { list: enumList(ENUMS[enumKey]) })];
  if (key === "src" && typeof val === "string") return [textInput(val, set, { list: enumList(S.assets.images) })];
  if (typeof val === "boolean") return [checkInput(val, set)];
  if (typeof val === "number") return [numberInput(val, (n) => n != null && set(n), { step: Math.abs(val) < 5 && !Number.isInteger(val) ? 0.05 : 1 })];
  if (typeof val === "string") return [val.length > 56 || val.includes("\n") ? areaInput(val, (t) => set(t), { rows: 2 }) : textInput(val, set)];
  if (Array.isArray(val) && val.every((x) => typeof x === "string") && (LIST_KEYS.has(key) || val.length !== 2)) {
    return [areaInput(val.join("\n"), (t) => set(t.split("\n").filter((l) => l.length)), { rows: Math.max(2, val.length) })];
  }
  if (Array.isArray(val) && val.length === 2 && val.every((x) => typeof x === "number")) return pointInput(val, set);
  return [jsonInput(val, set, 4)];
}
function defaultFor(component, key) {
  if (ENUMS[`${component}.${key}`]) return ENUMS[`${component}.${key}`][0];
  if (POINT_KEYS.has(key)) return [0.5, 0.5];
  if (LIST_KEYS.has(key)) return ["…"];
  if (JSON_KEYS.has(key)) return key === "cards" ? [] : {};
  if (NUMBER_KEYS.has(key)) return 0;
  return "";
}

function overlayPanel(o, i) {
  const k = (f) => `overlay:${i}:${f}`, props = o.props || {};
  const known = (COMPONENT_KEYS[o.component] || []).filter((x) => !(x in props));
  const rawBox = formatContent(o.component, props);
  let rawText = rawBox.text;
  const raw = areaInput(rawText, (t) => { rawText = t; }, { rows: 4, mono: true });
  const rawMsg = h("div", { class: "hint" }, rawBox.lossy ? "Có giá trị chứa dấu ; hoặc ' / ' nên không thể áp dụng bằng ô này: sửa ở từng ô phía trên." : "Cùng cú pháp với cột Content của bảng Overlays trong edit-plan.");
  const propRows = Object.entries(props).map(([key, val]) => h("div", { class: "f top-aligned" }, h("label", {}, key),
    h("div", { class: "ctl" }, propControl(o, i, key, val), btn("×", () => { edit(null, () => { delete o.props[key]; }); refresh(); }, "danger"))));
  const addSel = h("select", { "aria-label": "Thêm thuộc tính" }, h("option", { value: "" }, "+ Thêm thuộc tính…"),
    known.map((x) => h("option", { value: x }, x)), h("option", { value: "__custom" }, "Khóa khác…"));
  addSel.addEventListener("change", () => {
    let key = addSel.value;
    if (key === "__custom") key = (prompt("Tên khóa (ví dụ at, size):") || "").trim();
    if (!key) return void (addSel.value = "");
    edit(null, () => { (o.props ||= {})[key] = defaultFor(o.component, key); });
    refresh();
  });
  return [
    h("h2", {}, "Chữ · đồ họa", h("span", { class: "pill" }, o.component)),
    field("Thành phần", selectInput(componentNames(), o.component, (v) => { edit(k("component"), () => { o.component = v; }); refresh(); })),
    field("Bắt đầu", numberInput(o.start, (v) => v != null && edit(k("start"), () => { o.start = r3(Math.max(0, v)); }), { min: 0 }), unit("s"),
      btn("= playhead", () => { edit(null, () => { o.start = r3(S.t); }); refresh(); })),
    field("Kết thúc", numberInput(o.end, (v) => v != null && edit(k("end"), () => { o.end = r3(Math.max(0, v)); }), { min: 0 }), unit("s"),
      btn("= playhead", () => { edit(null, () => { o.end = r3(S.t); }); refresh(); })),
    field("Vùng", selectInput([["", "(mặc định của thành phần)"], ...U("Zone")], o.zone || "", (v) => edit(k("zone"), () => setOrDelete(o, "zone", v)))),
    field("Tông", selectInput([["", "(không)"], ...U("Tone")], o.tone || "", (v) => edit(k("tone"), () => setOrDelete(o, "tone", v)))),
    h("h3", {}, "Thuộc tính (props)"), propRows.length ? propRows : h("div", { class: "hint" }, "Chưa có thuộc tính nào."), field("", addSel),
    h("h3", {}, "Nội dung thô"), raw, rawMsg,
    h("div", { class: "row-btns" }, btn("Áp dụng nội dung thô", () => {
      if (rawBox.lossy) return toast("Ô này không áp dụng được vì có dấu ; hoặc ' / ' trong giá trị.", "err");
      try { const parsed = parseContent(o.component, rawText); edit(null, () => { o.props = parsed; }); refresh(); toast("Đã áp dụng nội dung thô.", "ok"); } catch (e) { toast(e.message, "err"); }
    })),
    h("div", { class: "row-btns" }, btn("Nhân đôi (Ctrl+D)", duplicateSelected), btn("Xóa (Delete)", deleteSelected, "danger")),
  ];
}

function cameraPanel(s, i) {
  const k = (f) => `scene:${i}:camera.${f}`, cam = s.camera || {}, move = cam.move || "";
  const cm = () => (s.camera ||= {});
  const out = [field("Kiểu", selectInput([["", "(mặc định)"], ...U("CameraMove")], move, (v) => {
    edit(null, () => {
      if (!v) delete s.camera; else cm().move = v;
      if (v === "keys" && !(cm().keys && cm().keys.length)) cm().keys = [{ ts: 0, zoom: 1 }, { ts: r3(s.end - s.start), zoom: 1.15 }];
    });
    refresh();
  }))];
  if (!move) return out;
  const opt = (name, label, step = 0.01) => field(label, numberInput(cam[name], (v) => edit(k(name), () => setOrDelete(cm(), name, v == null ? null : r3(v))), { step }));
  if (move === "keys") {
    (cam.keys || []).forEach((key, n) => {
      const kk = (f) => `scene:${i}:camera.keys.${n}.${f}`;
      out.push(h("div", { class: "keyrow" },
        numberInput(key.ts, (v) => v != null && edit(kk("ts"), () => { key.ts = r3(v); }), { step: 0.1, placeholder: "giây" }),
        numberInput(key.zoom, (v) => v != null && edit(kk("zoom"), () => { key.zoom = r3(v); }), { step: 0.05, placeholder: "zoom" }),
        numberInput(key.at && key.at[0], (v) => edit(kk("ax"), () => { key.at = v == null ? undefined : [r3(v), key.at ? key.at[1] : 0.5]; if (!key.at) delete key.at; }), { step: 0.01, placeholder: "x" }),
        numberInput(key.at && key.at[1], (v) => edit(kk("ay"), () => { key.at = v == null ? undefined : [key.at ? key.at[0] : 0.5, r3(v)]; if (!key.at) delete key.at; }), { step: 0.01, placeholder: "y" }),
        btn("×", () => { edit(null, () => { cam.keys.splice(n, 1); }); refresh(); }, "danger"),
        h("div", { style: "grid-column: 1 / span 4" }, selectInput([["", "kiểu chuyển: mặc định"], ...U("CameraEase")], key.ease || "", (v) => edit(kk("ease"), () => setOrDelete(key, "ease", v))))));
    });
    out.push(h("div", { class: "row-btns" }, btn("+ Thêm khóa", () => { edit(null, () => { const last = cam.keys[cam.keys.length - 1] || { ts: 0, zoom: 1 }; cam.keys.push({ ts: r3(last.ts + 1), zoom: last.zoom }); }); refresh(); })),
      h("div", { class: "hint" }, "Mỗi hàng: giây từ đầu cảnh · zoom · x · y (điểm giữ khung, 0..1) · xóa; dòng dưới: kiểu chuyển."));
    return out;
  }
  out.push(opt("from", "Zoom đầu"), opt("to", "Zoom cuối"));
  out.push(field("Lấy nét x,y", ...pointInput(cam.focus, (v) => edit(k("focus"), () => { cm().focus = v; })), btn("×", () => { edit(null, () => { delete cm().focus; }); refresh(); })));
  if (move === "pan") out.push(field("Trượt x,y", ...pointInput(cam.pan || [0, 0], (v) => edit(k("pan"), () => { cm().pan = v; }))));
  return out;
}

function scenePanel(s, i) {
  const k = (f) => `scene:${i}:${f}`, p = P(), last = i === p.scenes.length - 1, clipInfo = S.assets.clips.find((c) => c.name === s.clip);
  const clips = [["", "(không clip — nền lưới / thẻ)"], ...S.assets.clips.map((c) => [c.name, c.name])];
  const orig = () => clone(p.scenes);
  const ramp = Array.isArray(s.ramp) ? s.ramp.join(", ") : "";
  const hasFace = !!s.face;
  const trans = s.transition || {};
  // a cut edit also moves the neighbour and `in`: keep the three inputs of this scene showing the model
  const inIn = numberInput(s.in, (v) => v != null && edit(k("in"), () => { s.in = r3(Math.max(0, v)); }), { min: 0, step: 0.1 });
  const inStart = numberInput(s.start, (v) => { if (v == null || i === 0) return; edit(k("start"), () => applyCut(p, i, v, orig(), false)); sync(inIn); }, { min: 0 });
  const inEnd = numberInput(s.end, (v) => { if (v == null) return; edit(k("end"), () => (last ? setLastEnd(p, v, orig()) : applyCut(p, i + 1, v, orig(), false))); sync(inIn); }, { min: 0 });
  const sync = (el) => { if (document.activeElement !== el) el.value = s.in; };
  if (i === 0) inStart.disabled = true;
  return [
    h("h2", {}, `Cảnh ${i + 1}`, h("span", { class: "pill" }, s.type || "cảnh")),
    field("Clip nguồn", selectInput(clips, s.clip || "", (v) => { edit(k("clip"), () => { s.clip = v || null; }); refresh(); seek(S.t); })),
    field("Từ giây", inIn, unit(clipInfo && clipInfo.duration ? `/ ${clipInfo.duration} s` : "s")),
    field("Bắt đầu", inStart, unit(i === 0 ? "cố định" : "s")),
    field("Kết thúc", inEnd, unit("s")),
    h("div", { class: "hint" }, "Đổi mép cảnh sẽ kéo cảnh kề bên theo (và dời 'Từ giây' của cảnh sau để hình khớp thời gian); giữ Shift khi kéo để không dời."),
    field("Loại", textInput(s.type || "", (v) => edit(k("type"), () => setOrDelete(s, "type", v)))),
    field("Bố cục", selectInput([["", "full (mặc định)"], ...U("Layout")], s.layout || "", (v) => edit(k("layout"), () => setOrDelete(s, "layout", v)))),
    field("Tốc độ", numberInput(s.speed, (v) => edit(k("speed"), () => setOrDelete(s, "speed", v == null ? null : r3(v))), { step: 0.1, min: 0.1, placeholder: "1" }), unit("×")),
    field("Ramp", textInput(ramp, (t) => edit(k("ramp"), () => { const a = t.split(/[,\s>]+/).map(parseFloat).filter(Number.isFinite); if (a.length > 1) s.ramp = a; else delete s.ramp; }), { placeholder: "1, 2.5, 1" })),
    field("Hiệu ứng cắt", selectInput([["", "(không)"], "flash", "lightLeak"], s.accent || "", (v) => edit(k("accent"), () => setOrDelete(s, "accent", v)))),
    h("h3", {}, "Chuyển cảnh vào"),
    i === 0 ? h("div", { class: "hint" }, "Cảnh đầu không có chuyển cảnh.") : [
      field("Kiểu", selectInput([["", "(mặc định: fade)"], ...U("TransitionType")], trans.type || "", (v) => { edit(null, () => { if (!v) delete s.transition; else (s.transition ||= {}).type = v; }); refresh(); })),
      s.transition ? field("Số khung", numberInput(trans.frames, (v) => edit(k("tframes"), () => setOrDelete(s.transition, "frames", v == null ? null : Math.round(v))), { step: 1, min: 0, placeholder: "mặc định" })) : null,
      s.transition && DIRECTIONAL.has(trans.type) ? field("Hướng", selectInput([["", "(mặc định)"], ...U("Direction")], trans.direction || "", (v) => edit(k("tdir"), () => setOrDelete(s.transition, "direction", v)))) : null,
    ],
    h("h3", {}, "Camera ảo"), cameraPanel(s, i),
    h("h3", {}, "Mặt (làm sáng da)"),
    field("Có mặt", checkInput(hasFace, (v) => { edit(null, () => { if (v) s.face = { x: 0.5, y: 0.45, r: 0.08 }; else delete s.face; }); refresh(); })),
    hasFace ? [field("x, y", ...pointInput([s.face.x, s.face.y], (v) => edit(k("face"), () => { s.face.x = v[0]; s.face.y = v[1]; }))),
      field("Bán kính", numberInput(s.face.r, (v) => v != null && edit(k("facer"), () => { s.face.r = r3(v); }), { step: 0.005, min: 0.01 }), unit("× rộng khung"))] : null,
    h("div", { class: "row-btns" }, btn("Cắt tại playhead (S)", splitScene), btn("Xóa cảnh (Delete)", deleteSelected, "danger")),
  ];
}

function captionPanel(c, i) {
  const k = (f) => `caption:${i}:${f}`;
  return [
    h("h2", {}, "Phụ đề", h("span", { class: "pill" }, `dòng ${i + 1}`)),
    field("Nội dung", areaInput(c.text, (t) => edit(k("text"), () => { c.text = t; }), { rows: 3 })),
    field("Bắt đầu", numberInput(c.start, (v) => v != null && edit(k("start"), () => { c.start = r3(Math.max(0, v)); }), { min: 0 }), unit("s"), btn("= playhead", () => { edit(null, () => { c.start = r3(S.t); }); refresh(); })),
    field("Kết thúc", numberInput(c.end, (v) => v != null && edit(k("end"), () => { c.end = r3(Math.max(0, v)); }), { min: 0 }), unit("s"), btn("= playhead", () => { edit(null, () => { c.end = r3(S.t); }); refresh(); })),
    h("div", { class: "hint" }, "Phụ đề thật được vẽ theo cụm từ và từ đang đọc (words trong project); sửa chữ ở đây chỉ đổi nội dung cụm."),
    h("div", { class: "row-btns" }, btn("Nhân đôi (Ctrl+D)", duplicateSelected), btn("Xóa (Delete)", deleteSelected, "danger")),
  ];
}

function sfxPanel(c, i) {
  const k = (f) => `sfx:${i}:${f}`;
  return [
    h("h2", {}, "Âm hiệu ứng", h("span", { class: "pill" }, `âm ${i + 1}`)),
    field("File", selectInput(S.assets.sfx, c.src, (v) => edit(k("src"), () => { c.src = v; }))),
    field("Thời điểm", numberInput(c.at, (v) => v != null && edit(k("at"), () => { c.at = r3(Math.max(0, v)); }), { min: 0 }), unit("s"), btn("= playhead", () => { edit(null, () => { c.at = r3(S.t); }); refresh(); })),
    field("Âm lượng", numberInput(c.volumeDb, (v) => edit(k("vol"), () => setOrDelete(c, "volumeDb", v == null ? null : r3(v))), { step: 1, placeholder: "-16" }), unit("dB")),
    h("div", { class: "row-btns" }, btn("Xóa (Delete)", deleteSelected, "danger")),
  ];
}

function projectPanel() {
  const p = P(), k = (f) => `project:${f}`, issues = problems();
  const music = p.music || null;
  return [
    h("h2", {}, "Project", h("span", { class: "pill" }, S.name)),
    h("div", { class: "hint" }, "Chọn một cảnh, chữ, phụ đề hoặc âm trên dòng thời gian để sửa thuộc tính của nó."),
    field("Độ dài", numberInput(p.duration, (v) => v != null && edit(k("duration"), () => { p.duration = r3(v); }), { step: 0.1, min: 1 }), unit("s")),
    field("Khung", h("span", {}, `${p.width || FRAME_W}×${p.height || FRAME_H} · ${fps()} fps`)),
    field("Bố cục", selectInput([["feed", "feed (TikTok, Reels thường)"], ["reels-ad", "reels-ad (quảng cáo Reels)"]], p.layout || "feed", (v) => edit(k("layout"), () => { p.layout = v; }))),
    field("Kiểu phụ đề", selectInput(U("CaptionStyle"), p.captionStyle || "plain", (v) => edit(k("captionStyle"), () => { p.captionStyle = v; }))),
    field("Từ đang đọc", selectInput([["", "(mặc định)"], ...U("CaptionHighlight")], p.captionHighlight || "", (v) => edit(k("captionHighlight"), () => setOrDelete(p, "captionHighlight", v)))),
    h("h3", {}, "Âm thanh"),
    field("Giọng", selectInput([["", "(không có)"], ...S.assets.audio], p.voice || "", (v) => { edit(null, () => { p.voice = v || null; }); refresh(); syncAudio(true); })),
    field("Nhạc", selectInput([["", "(không có)"], ...S.assets.audio], music ? music.src : "", (v) => { edit(null, () => { p.music = v ? { ...(p.music || {}), src: v } : null; }); refresh(); syncAudio(true); })),
    music ? [field("Âm lượng", numberInput(music.volumeDb, (v) => edit(k("mvol"), () => setOrDelete(p.music, "volumeDb", v == null ? null : r3(v))), { step: 1, placeholder: "dB" }), unit("dB")),
      field("Hạ khi có giọng", numberInput(music.duckDb, (v) => edit(k("mduck"), () => setOrDelete(p.music, "duckDb", v == null ? null : r3(v))), { step: 1, placeholder: "dB" }), unit("dB"))] : null,
    h("h3", {}, issues.length ? `Cần xem (${issues.length})` : "Kiểm tra nhanh"),
    issues.length ? h("ul", { class: "warnings" }, issues.slice(0, 14).map((t) => h("li", {}, t)), issues.length > 14 ? h("li", {}, `… và ${issues.length - 14} mục nữa`) : null) : h("div", { class: "hint" }, "Không thấy lỗi rõ ràng (cảnh liền nhau, clip và ảnh có file, thành phần có trong template)."),
    h("h3", {}, "Phím tắt"),
    h("div", { class: "help" }, [["Space", "phát / dừng"], ["← →", "lùi / tiến 1 khung (Shift: 1 giây)"], ["Delete", "xóa mục đang chọn"], ["S", "cắt cảnh tại playhead"],
      ["Ctrl+Z / Ctrl+Y", "hoàn tác / làm lại"], ["Ctrl+S", "lưu project"], ["Ctrl+D", "nhân đôi chữ / phụ đề"], ["Alt+lăn chuột", "thu phóng dòng thời gian"],
      ["Kéo mép", "đổi độ dài (cảnh: dời điểm cắt)"], ["Giữ Alt", "tắt bám mép khi kéo"], ["Home / End", "về đầu / cuối"], ["Esc", "bỏ chọn"]].map(([a, b]) => h("div", {}, h("kbd", {}, a), " ", b))),
  ];
}

function renderPanel() {
  const root = $("#panel"), keep = root.scrollTop;
  root.replaceChildren();
  const it = selItem();
  const build = !it ? projectPanel : { scene: scenePanel, overlay: overlayPanel, caption: captionPanel, sfx: sfxPanel }[S.sel.kind];
  root.append(...[].concat(it ? build(it, S.sel.i) : build()).flat(Infinity).filter(Boolean));
  root.scrollTop = keep;
}

// ============================================================================ 9. header, dialogs, save, render
let rq = 0, wantPanel = false;
function refresh(o = {}) {
  wantPanel = wantPanel || o.panel !== false;
  if (!rq) rq = requestAnimationFrame(doRefresh);
}
function doRefresh() {
  rq = 0;
  const panel = wantPanel;
  wantPanel = false;
  computeDiff();
  renderHeader();
  renderTimeline();
  ensureWaves();
  renderZones();
  draftKey = "";
  renderDraft();
  renderNote();
  updateHead(false);
  if (panel) renderPanel();
}
function renderHeader() {
  const n = S.diff.n, badge = $("#badge");
  badge.className = "badge";
  if (!S.render) badge.textContent = "Chưa có bản render";
  else if (n === null) { badge.textContent = "Bản render đã cũ"; badge.classList.add("warn"); }
  else if (n > 0) { badge.textContent = `${n} thay đổi chưa render`; badge.classList.add("warn"); }
  else { badge.textContent = "Bản render đang khớp"; badge.classList.add("ok"); }
  const dirty = isDirty();
  $("#dirty").hidden = !dirty;
  $("#btnSave").disabled = !dirty;
  $("#btnUndo").disabled = !S.undo.length;
  $("#btnRedo").disabled = !S.redo.length;
  $("#tgSafe").checked = S.opts.safe; $("#tgFace").checked = S.opts.face; $("#tgDraft").checked = draftOn(); $("#tgSnap").checked = S.opts.snap;
  const hasFace = P().scenes.some((s) => s.face || (s.camera && s.camera.focus));
  $("#tgFace").disabled = !hasFace;
  $("#tgFace").parentElement.title = hasFace ? "" : "Project này không có khóa mặt (face) hay điểm lấy nét";
  document.title = `${dirty ? "● " : ""}${S.name} — Trình sửa video`;
  const rs = S.rs, running = rs && rs.state === "running", pr = rs && rs.progress && rs.progress.total ? Math.round((rs.progress.done / rs.progress.total) * 100) : null;
  $("#btnRender").textContent = running ? `Đang render${pr != null ? ` ${pr}%` : "…"}` : "Render lại";
}

async function save(force = false) {
  if (!S.project) return;
  const body = JSON.stringify(S.project);
  try {
    const r = await api(`/api/project?name=${enc(S.name)}&base=${S.mtime}${force ? "&force=1" : ""}`, { method: "POST", headers: { "Content-Type": "application/json" }, body });
    S.mtime = r.mtime; S.savedText = body;
    toast(r.unchanged ? "Không có gì mới để lưu." : "Đã lưu. Bản cũ nằm trong Lịch sử.", "ok");
    refresh({ panel: false });
    return true;
  } catch (e) {
    if (e.status === 409 && confirm(`${e.message}\n\nGhi đè bằng bản đang sửa? (Bản trên đĩa vẫn được giữ trong Lịch sử.)`)) return save(true);
    if (e.status !== 409) toast(`Không lưu được: ${e.message}`, "err");
    return false;
  }
}
function adopt(d) { // replace the open project with one from the server (open, restore)
  S.project = d.project; S.savedText = JSON.stringify(d.project); S.mtime = d.mtime;
}
async function openProject(name) {
  const d = await api(`/api/project?name=${enc(name)}`);
  adopt(d);
  S.name = d.name; S.render = d.render; S.renderState = d.renderState; S.baseline = d.baseline || (d.renderState === "synced" ? clone(d.project) : null);
  S.renders = S.info.renders; S.opts.proxy = !d.render;
  S.undo = []; S.redo = []; S.sel = null; S.t = 0; S.waves = {};
  S.rulerKey = ""; S.snapAt = null;
  pref.set("project", name);
}
async function reloadRenderInfo() {
  const [info, d] = await Promise.all([api("/api/info"), api(`/api/project?name=${enc(S.name)}`)]);
  S.info = info; S.renders = info.renders; S.render = d.render; S.renderState = d.renderState;
  S.baseline = d.baseline || (d.renderState === "synced" ? clone(P()) : S.baseline);
  S.opts.proxy = !d.render;
  renderSourceSelect(); loadSource(); refresh({ panel: false });
}

async function openHistory() {
  const dlg = $("#dlgHistory"), list = $("#historyList");
  try {
    const d = await api(`/api/history?name=${enc(S.name)}`);
    $("#historyHint").textContent = `Mỗi lần Lưu project, bản cũ được giữ ở .editor-history/ trong thư mục render (tối đa ${S.info.historyKeep} bản gần nhất của ${S.name}).`;
    list.replaceChildren(...(d.items.length ? d.items.map((it) => h("div", { class: "li" },
      h("div", { class: "grow" }, h("strong", {}, it.time), h("div", { class: "muted" }, `${it.scenes} cảnh · ${it.overlays} chữ/đồ họa · ${it.duration ?? "?"} s · ${(it.size / 1024).toFixed(1)} KB`)),
      btn("Khôi phục", () => restore(it, dlg)))) : [h("div", { class: "li muted" }, "Chưa có bản lưu nào.")]));
    dlg.showModal();
  } catch (e) { toast(`Không mở được lịch sử: ${e.message}`, "err"); }
}
async function restore(it, dlg) {
  if (isDirty() && !confirm("Có thay đổi chưa lưu. Khôi phục sẽ thay thế chúng (bấm Hoàn tác để lấy lại). Tiếp tục?")) return;
  try {
    const r = await post("/api/history/restore", { name: S.name, id: it.id });
    pushUndo(null);
    adopt(r);
    S.sel = null; S.lastKey = null;
    dlg.close(); refresh(); seek(S.t);
    toast(`Đã khôi phục bản ${it.time}. Bản trước đó vẫn trong Lịch sử.`, "ok");
  } catch (e) { toast(`Không khôi phục được: ${e.message}`, "err"); }
}

async function startRender() {
  if (S.rs && S.rs.state === "running") return openRenderDialog();
  if (isDirty() && !(await save())) return;
  try { S.rs = await post("/api/render", { name: S.name }); } catch (e) { return toast(e.message, "err"); }
  S.watchRender = true;
  openRenderDialog();
  pollRender();
}
function openRenderDialog() { renderRenderUI(); const d = $("#dlgRender"); if (!d.open) d.showModal(); }
let pollTimer = 0;
async function pollRender() {
  clearTimeout(pollTimer);
  try { S.rs = await api("/api/render/status"); } catch { return; }
  renderRenderUI(); renderHeader();
  if (S.rs.state === "running") { S.watchRender = true; pollTimer = setTimeout(pollRender, 1000); return; }
  if (S.watchRender) {
    S.watchRender = false;
    if (S.rs.state === "done") { await reloadRenderInfo(); toast("Render xong: bản mới đã nằm trong khung xem.", "ok"); }
    else if (S.rs.state === "failed") toast("Render lỗi, xem log trong hộp Render.", "err");
  }
}
function renderRenderUI() {
  const rs = S.rs || { state: "idle", log: [], progress: {} }, pr = rs.progress && rs.progress.total ? rs.progress.done / rs.progress.total : 0;
  const text = { idle: "Chưa render.", running: "Đang render…", done: "Render xong.", failed: "Render lỗi.", cancelled: "Đã hủy render." }[rs.state] || rs.state;
  $("#renderState").textContent = `${text}${rs.name ? ` ${rs.name} → ${rs.output}` : ""}${rs.elapsed ? ` · ${Math.round(rs.elapsed)} s` : ""}${rs.progress && rs.progress.total ? ` · ${rs.progress.stage} ${rs.progress.done}/${rs.progress.total}` : ""}`;
  $("#renderBar").style.width = `${rs.state === "done" ? 100 : Math.round(pr * 100)}%`;
  const log = $("#renderLog");
  log.textContent = (rs.log || []).join("\n");
  log.scrollTop = log.scrollHeight;
  $("#btnCancelRender").disabled = rs.state !== "running";
}

// ============================================================================ 10. keyboard and start
function bind() {
  $("#btnUndo").onclick = undo; $("#btnRedo").onclick = redo; $("#btnSave").onclick = () => save();
  $("#btnHistory").onclick = openHistory; $("#btnRender").onclick = startRender;
  $("#btnCancelRender").onclick = () => post("/api/render/cancel").then((s) => { S.rs = s; renderRenderUI(); }).catch((e) => toast(e.message, "err"));
  $("#btnPlay").onclick = () => setPlaying(!S.playing);
  $("#btnAddText").onclick = () => addItem("overlay"); $("#btnAddCaption").onclick = () => addItem("caption"); $("#btnAddSfx").onclick = () => addItem("sfx");
  $("#btnSplit").onclick = splitScene; $("#btnFit").onclick = fitZoom;
  $("#btnTheme").onclick = () => {
    const dark = document.documentElement.dataset.theme ? document.documentElement.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    document.documentElement.dataset.theme = dark ? "light" : "dark"; pref.set("theme", document.documentElement.dataset.theme);
    for (const cv of Object.values(S.waveEls)) cv.dataset.key = "";
    drawWaves();
  };
  const tg = (id, key) => { $(id).onchange = (e) => { S.opts[key] = e.target.checked; e.target.blur(); const z = $("#zones"); z.dataset.key = ""; draftKey = ""; refresh({ panel: false }); }; };
  tg("#tgSafe", "safe"); tg("#tgFace", "face"); tg("#tgDraft", "draft"); tg("#tgSnap", "snap");
  $("#srcSelect").onchange = (e) => {
    setPlaying(false);
    if (e.target.value === "proxy") S.opts.proxy = true;
    else { S.opts.proxy = false; S.render = S.renders.find((r) => `r:${r.name}` === e.target.value) || S.render; }
    e.target.blur(); vid().dataset.url = ""; loadSource(); refresh({ panel: false });
  };
  $("#projectSelect").onchange = async (e) => {
    if (isDirty() && !confirm("Có thay đổi chưa lưu. Mở file khác sẽ bỏ chúng. Tiếp tục?")) { e.target.value = S.name; return; }
    setPlaying(false);
    try { await openProject(e.target.value); vid().dataset.url = ""; renderSourceSelect(); loadSource(); fitZoom(); refresh(); } catch (err) { toast(err.message, "err"); }
  };
  $("#zoom").oninput = (e) => setZoom(ZOOM_MIN * Math.pow(ZOOM_MAX / ZOOM_MIN, e.target.value / 100));
  const view = $("#tlScroll");
  view.addEventListener("scroll", () => requestAnimationFrame(drawWaves));
  view.addEventListener("wheel", (e) => {
    if (!e.altKey && !e.ctrlKey) return;
    e.preventDefault();
    setZoom(S.pps * (e.deltaY < 0 ? 1.15 : 1 / 1.15), e.clientX - view.getBoundingClientRect().left - LABEL_W);
  }, { passive: false });
  $("#tlContent").addEventListener("pointerdown", (e) => {
    if (e.button !== 0) return;
    const node = e.target.closest(".item");
    if (node) return startItemDrag(e, node);
    if (e.target.closest(".tl-label")) return;
    if (e.target.closest(".tl-lane")) { S.sel = null; refresh(); }
    if (e.target.closest(".tl-ruler, .tl-lane")) startScrub(e);
  });
  window.addEventListener("resize", () => { for (const cv of Object.values(S.waveEls)) cv.dataset.key = ""; drawWaves(); });
  window.addEventListener("beforeunload", (e) => { if (isDirty()) { e.preventDefault(); e.returnValue = ""; } });
  const v = vid();
  v.addEventListener("ended", () => { if (usingRender()) setPlaying(false); });
  v.addEventListener("click", () => setPlaying(!S.playing));

  document.addEventListener("keydown", (e) => {
    const mod = e.ctrlKey || e.metaKey, key = e.key.toLowerCase(), tag = e.target.tagName;
    if (mod && key === "s") { e.preventDefault(); save(); return; }
    if (["INPUT", "TEXTAREA", "SELECT"].includes(tag) || e.target.isContentEditable) return; // text fields keep their own shortcuts
    if (mod && key === "z") { e.preventDefault(); e.shiftKey ? redo() : undo(); return; }
    if (mod && key === "y") { e.preventDefault(); redo(); return; }
    if (mod && key === "d") { e.preventDefault(); duplicateSelected(); return; }
    if (mod || e.altKey || $("#dlgHistory").open || $("#dlgRender").open) return;
    if (e.key === " ") { e.preventDefault(); if (tag === "BUTTON") e.target.blur(); setPlaying(!S.playing); }
    else if (e.key === "ArrowLeft" || e.key === "ArrowRight") { e.preventDefault(); setPlaying(false); seek(S.t + (e.key === "ArrowLeft" ? -1 : 1) * (e.shiftKey ? 1 : 1 / fps())); }
    else if (e.key === "Delete" || e.key === "Backspace") { e.preventDefault(); deleteSelected(); }
    else if (key === "s") splitScene();
    else if (e.key === "Home") { e.preventDefault(); seek(0); }
    else if (e.key === "End") { e.preventDefault(); seek(dur()); }
    else if (e.key === "Escape") { S.sel = null; refresh(); }
  });
}

async function start() {
  document.documentElement.style.setProperty("--label-w", `${LABEL_W}px`);
  const theme = pref.get("theme");
  if (theme === "light" || theme === "dark") document.documentElement.dataset.theme = theme;
  try {
    S.info = await api("/api/info");
    const [schema, assets] = await Promise.all([api("/api/schema").catch(() => S.schema), api("/api/assets").catch(() => S.assets)]);
    S.schema = schema; S.assets = assets;
    const want = pref.get("project");
    await openProject(S.info.projects.some((p) => p.name === want) ? want : S.info.default);
  } catch (e) {
    $("#badge").textContent = "Không mở được project";
    return toast(`Không mở được project: ${e.message}`, "err");
  }
  $("#dirName").textContent = S.info.dir;
  $("#projectSelect").replaceChildren(...S.info.projects.map((p) => h("option", { value: p.name, selected: p.name === S.name }, p.name)));
  $("#projectSelect").hidden = S.info.projects.length < 2;
  bind();
  renderSourceSelect();
  loadSource();
  fitZoom();
  refresh();
  seek(0);
  pollRender().then(() => { if (S.rs && S.rs.state === "running") openRenderDialog(); });
}
start();
})();
