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
// Viewer-first layout: text hugs the top and bottom edges and leaves the middle ~45% of the frame
// (y 420-1330) to the footage. The top strip starts just under TikTok's status/tabs (y 220).
export const zones: Record<Zone, number> = {
  top: 236, // title / hook / steps / thumbs strip: the only text above the action
  upper: 470, // secondary text when the top strip is taken (checklist)
  center: 860, // only over hands/products, never over a face
  lower: 1230, // a bar just above the captions (progress)
};
export const captionTop = 1340; // spoken captions: lower third, above TikTok's product bar (y 1644)
export const captions = { size: 58, left: 90, right: 190, lift: 120 }; // right 190 keeps clear of the action rail; lift = shift while the cart arrow shows
// Centre of the yellow shopping-bag tile in TikTok Shop's product bar, in frame pixels. Measured on a
// 1284x2778 iPhone screenshot of the feed (tile x 48-107, y 2180-2239; tab bar starts at y 2530, so the
// video fills 1284x2530 and a 1080x1920 frame is scaled 1.3177 and cropped 69.5 px each side). The bar
// runs x 80-607, y 1644-1709 and the account name starts near y 1750. Other phones differ by ~40 px.
export const cartPoint = { x: 112, y: 1677 };

// Before/after card (components/graphics/Media.tsx). It sits in the `top` zone, inside the safe
// width; frames are in 30 fps frames. `settle` is where the divider stops: 0.5 shows both halves.
// `scrim` dims the footage behind the card so the comparison does not blend into it.
export const compare = { height: 620, radius: 28, border: 6, divider: 6, handle: 76, holdFrames: 8, sweepFrames: 20, settle: 0.5, scrim: 0.5 };
export const thumb = { width: 250, height: 232 }; // the three-photo strip: small, so the footage stays visible

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

// A move must be big enough to be SEEN: at least ~12% scale change over a scene, ~7% pan. Keep the
// total scale under source_px / output_px: 1920-tall proxies soften past ~1.15, 2880-tall proxies stay
// sharp to 1.5, 3840-tall to 2.0 (new_remotion_project.py --proxy-height).
export const camera = {
  defaultPush: [1.0, 1.16] as [number, number],
  defaultPull: [1.24, 1.0] as [number, number],
  defaultPan: 0.08, // share of the frame travelled by a pan
  punchScale: 1.15,
  punchFrames: 6,
  maxScale: 1.7,
};

export const textShadow = `drop-shadow(0 6px 18px ${palette.shadow}) drop-shadow(0 2px 4px rgba(0,0,0,0.35))`;
