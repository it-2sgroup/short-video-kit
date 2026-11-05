// Design tokens: the only place fonts, colours, layout zones and motion curves are defined.
// Components read from here, so a new look is a change to this file, not to every component.
import { Easing } from "remotion";
import { loadFont as loadSans } from "@remotion/google-fonts/BeVietnamPro";
import { loadFont as loadSerif } from "@remotion/google-fonts/PlayfairDisplay";
import { loadFont as loadNumber } from "@remotion/google-fonts/Anton";
import type { Tone, Zone } from "./project";

// Vietnamese needs BOTH subsets: the 'vietnamese' subset holds only the extra marks.
const SUBSETS: ("latin" | "latin-ext" | "vietnamese")[] = ["latin", "latin-ext", "vietnamese"];
const sans = loadSans("normal", { weights: ["500", "700", "800", "900"], subsets: SUBSETS });
const serif = loadSerif("italic", { weights: ["700"], subsets: SUBSETS });
const number = loadNumber("normal", { weights: ["400"], subsets: SUBSETS });

export const fonts = {
  sans: sans.fontFamily, // Be Vietnam Pro: titles, labels, captions
  accent: serif.fontFamily, // Playfair Display Italic: one accent word per title
  number: number.fontFamily, // Anton: prices and counters
};

export const palette = {
  white: "#FFFFFF",
  ice: "#DCE7F4",
  sky: "#A8D0FF",
  royal: "#2F64E0",
  navy: "#15224C",
  ink: "#0B1020",
  shadow: "rgba(10,25,60,0.45)",
};

export const toneColor: Record<Tone, string> = {
  neutral: palette.white,
  before: "#FF7A6E",
  after: "#4AE3A4",
  cta: "#FFD23F",
  product: "#FF8FC2",
};

// Layout for a 1080x1920 frame. TikTok publishes no organic UI pixels; these bands are the
// conservative union of third-party measurements (see references/layout-and-motion-graphics.md).
export const frame = { width: 1080, height: 1920 };
export const safe = { left: 60, right: 900, top: 220, bottom: 1400 }; // right rail covers x > 900
export const zones: Record<Zone, number> = {
  top: 270, // head-room band: hook titles, steps, cards
  upper: 560,
  center: 860, // only over hands/products, never over a face
  lower: 1010, // chest band: prices, checklists, lower thirds
};
export const captionTop = 1190; // spoken captions live in their own band
export const cartPoint = { x: 300, y: 1440 }; // where TikTok Shop's yellow basket sits (approx.)

export const motion = {
  easeOut: Easing.bezier(0.16, 1, 0.3, 1), // default entrance
  easeInOut: Easing.bezier(0.65, 0, 0.35, 1), // transitions, sweeps
  exit: Easing.bezier(0.4, 0, 1, 1),
  camera: Easing.bezier(0.33, 0, 0.67, 1), // slow push/pull/pan
  smooth: { damping: 200 }, // no overshoot: cards, panels
  pop: { damping: 12, stiffness: 220, mass: 0.6 }, // stickers, dots, badges
  card: { damping: 16, stiffness: 180 },
  enterFrames: 10,
  exitFrames: 8, // exits are shorter than entrances
};

export const camera = {
  defaultPush: [1.0, 1.06] as [number, number],
  defaultPull: [1.14, 1.0] as [number, number],
  punchScale: 1.12,
  punchFrames: 6,
  // Keep total scale under source_px / output_px: 1080p proxies blur past ~1.15,
  // 2160x3840 sources stay sharp to 2.0.
  maxScale: 1.6,
};

export const textShadow = `drop-shadow(0 6px 18px ${palette.shadow}) drop-shadow(0 2px 4px rgba(0,0,0,0.35))`;
