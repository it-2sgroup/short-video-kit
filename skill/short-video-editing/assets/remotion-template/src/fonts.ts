// The font library: Google Fonts families (SIL OFL) that ship a Vietnamese subset, grouped by mood, picked per overlay with
// `font=<id>` in a plan row. The five role fonts of theme.ts (sans, accent, number, condensed, script) stay the defaults and are
// loaded for every project; a library font is loaded only when an overlay asks for it (the first render of that overlay calls
// `loadFont` for ONE weight of ONE family), so a render never fetches 30 families. Unknown ids fall back to the role font.
//   const f = pickFont(props.font, 900, fonts.sans);   // { family, weight, ratio }
// `weight` is the nearest weight the family really has (Anton has only 400); `ratio` is the average letter width / font size,
// for `fitSize`. Every id and weight below was checked against @remotion/google-fonts (see references/typography.md).
import * as BeVietnamPro from "@remotion/google-fonts/BeVietnamPro";
import * as Montserrat from "@remotion/google-fonts/Montserrat";
import * as BricolageGrotesque from "@remotion/google-fonts/BricolageGrotesque";
import * as LeagueSpartan from "@remotion/google-fonts/LeagueSpartan";
import * as Unbounded from "@remotion/google-fonts/Unbounded";
import * as TikTokSans from "@remotion/google-fonts/TikTokSans";
import * as PlusJakartaSans from "@remotion/google-fonts/PlusJakartaSans";
import * as BarlowCondensed from "@remotion/google-fonts/BarlowCondensed";
import * as Anton from "@remotion/google-fonts/Anton";
import * as LeagueGothic from "@remotion/google-fonts/LeagueGothic";
import * as Oswald from "@remotion/google-fonts/Oswald";
import * as BigShoulders from "@remotion/google-fonts/BigShoulders";
import * as SairaExtraCondensed from "@remotion/google-fonts/SairaExtraCondensed";
import * as PlayfairDisplay from "@remotion/google-fonts/PlayfairDisplay";
import * as Fraunces from "@remotion/google-fonts/Fraunces";
import * as CormorantGaramond from "@remotion/google-fonts/CormorantGaramond";
import * as Newsreader from "@remotion/google-fonts/Newsreader";
import * as LibreBodoni from "@remotion/google-fonts/LibreBodoni";
import * as Nunito from "@remotion/google-fonts/Nunito";
import * as Baloo2 from "@remotion/google-fonts/Baloo2";
import * as PaytoneOne from "@remotion/google-fonts/PaytoneOne";
import * as Coiny from "@remotion/google-fonts/Coiny";
import * as Pacifico from "@remotion/google-fonts/Pacifico";
import * as DancingScript from "@remotion/google-fonts/DancingScript";
import * as PatrickHand from "@remotion/google-fonts/PatrickHand";
import * as PlaypenSans from "@remotion/google-fonts/PlaypenSans";
import * as SpaceGrotesk from "@remotion/google-fonts/SpaceGrotesk";
import * as Tektur from "@remotion/google-fonts/Tektur";
import * as Bungee from "@remotion/google-fonts/Bungee";
import * as Sigmar from "@remotion/google-fonts/Sigmar";
import * as Bangers from "@remotion/google-fonts/Bangers";

export type FontMood = "bold" | "condensed" | "serif" | "rounded" | "script" | "tech" | "retro";

type FontModule = {
  loadFont: (style: "normal", options: { weights: string[]; subsets: string[] }) => unknown;
  getInfo: () => { fontFamily: string; subsets: string[]; fonts: { normal?: Record<string, unknown> } };
};

// ratio: average letter width / font size at heavy weights (0.56 is the template's default for a bold sans)
const defs = [
  { id: "be-vietnam-pro", mod: BeVietnamPro, mood: "bold", ratio: 0.56, use: "the default sans: titles, labels, captions" },
  { id: "montserrat", mod: Montserrat, mood: "bold", ratio: 0.62, use: "800-900 headlines, price tags" },
  { id: "bricolage-grotesque", mod: BricolageGrotesque, mood: "bold", ratio: 0.55, use: "offbeat, quirky hooks" },
  { id: "league-spartan", mod: LeagueSpartan, mood: "bold", ratio: 0.55, use: "short punchy geometric titles" },
  { id: "unbounded", mod: Unbounded, mood: "bold", ratio: 0.72, use: "wide, modern product names (keep lines short)" },
  { id: "tiktok-sans", mod: TikTokSans, mood: "bold", ratio: 0.56, use: "captions and titles that look platform-native" },
  { id: "plus-jakarta-sans", mod: PlusJakartaSans, mood: "bold", ratio: 0.56, use: "clean UI-like labels and calls to action" },
  { id: "barlow-condensed", mod: BarlowCondensed, mood: "condensed", ratio: 0.43, use: "the default emphasis line (phrase, tag)" },
  { id: "anton", mod: Anton, mood: "condensed", ratio: 0.42, use: "prices, counters, loud one-word lines" },
  { id: "league-gothic", mod: LeagueGothic, mood: "condensed", ratio: 0.36, use: "tall, narrow slogans" },
  { id: "oswald", mod: Oswald, mood: "condensed", ratio: 0.45, use: "news-style headlines" },
  { id: "big-shoulders", mod: BigShoulders, mood: "condensed", ratio: 0.42, use: "strong claims, sport and tools" },
  { id: "saira-extra-condensed", mod: SairaExtraCondensed, mood: "condensed", ratio: 0.38, use: "spec lines, techy lists" },
  { id: "playfair-display", mod: PlayfairDisplay, mood: "serif", ratio: 0.55, use: "the default accent serif; luxe titles" },
  { id: "fraunces", mod: Fraunces, mood: "serif", ratio: 0.56, use: "soft elegant serif: food, fashion, beauty" },
  { id: "cormorant-garamond", mod: CormorantGaramond, mood: "serif", ratio: 0.44, use: "light luxe serif for real estate (use 600+)" },
  { id: "newsreader", mod: Newsreader, mood: "serif", ratio: 0.5, use: "editorial serif: quotes, testimonials" },
  { id: "libre-bodoni", mod: LibreBodoni, mood: "serif", ratio: 0.58, use: "high-contrast fashion headlines" },
  { id: "nunito", mod: Nunito, mood: "rounded", ratio: 0.55, use: "friendly rounded: kids, home, food" },
  { id: "baloo-2", mod: Baloo2, mood: "rounded", ratio: 0.55, use: "chunky playful promos" },
  { id: "paytone-one", mod: PaytoneOne, mood: "rounded", ratio: 0.58, use: "sale badges" },
  { id: "coiny", mod: Coiny, mood: "rounded", ratio: 0.6, use: "bubbly fun food and kids" },
  { id: "pacifico", mod: Pacifico, mood: "script", ratio: 0.5, use: "the default script: one handwritten phrase" },
  { id: "dancing-script", mod: DancingScript, mood: "script", ratio: 0.46, use: "signatures, thank-you lines" },
  { id: "patrick-hand", mod: PatrickHand, mood: "script", ratio: 0.42, use: "casual notes and annotations" },
  { id: "playpen-sans", mod: PlaypenSans, mood: "script", ratio: 0.55, use: "kid-like handwriting for tutorials" },
  { id: "space-grotesk", mod: SpaceGrotesk, mood: "tech", ratio: 0.56, use: "gadgets, SaaS" },
  { id: "tektur", mod: Tektur, mood: "tech", ratio: 0.6, use: "gaming, futuristic squared letters" },
  { id: "bungee", mod: Bungee, mood: "retro", ratio: 0.78, use: "retro signage, neon-sign looks (very wide)" },
  { id: "sigmar", mod: Sigmar, mood: "retro", ratio: 0.62, use: "loud heavy sale stickers" },
  { id: "bangers", mod: Bangers, mood: "retro", ratio: 0.42, use: "comic impact words" },
] as const;

export type FontId = (typeof defs)[number]["id"];
export type FontDef = { id: FontId; family: string; mood: FontMood; weights: number[]; ratio: number; use: string; subsets: string[]; load: (weight: number) => void };

// Vietnamese needs BOTH subsets: the 'vietnamese' subset holds only the extra marks (theme.ts).
const WANT = ["latin", "latin-ext", "vietnamese"];

export const FONT_LIBRARY: FontDef[] = defs.map((d) => {
  const mod = d.mod as unknown as FontModule;
  const info = mod.getInfo();
  const subsets = WANT.filter((s) => info.subsets.includes(s));
  const done = new Set<number>();
  return {
    id: d.id,
    family: info.fontFamily,
    mood: d.mood,
    weights: Object.keys(info.fonts.normal ?? {}).map(Number).sort((a, b) => a - b),
    ratio: d.ratio,
    use: d.use,
    subsets,
    load: (weight: number) => {
      if (done.has(weight)) return;
      done.add(weight);
      mod.loadFont("normal", { weights: [String(weight)], subsets });
    },
  };
});

export const FONT_IDS: FontId[] = FONT_LIBRARY.map((f) => f.id);
const byId = new Map<string, FontDef>(FONT_LIBRARY.map((f) => [f.id, f]));
const warned = new Set<string>();

export type FontPick = { family: string; weight: number; ratio?: number };

// The font an overlay draws with: the library font `id` at the nearest weight it has (loading just that weight), or `fallback`
// (a role font family from theme.ts) at the wanted weight when there is no id. `ratio` is set only for a library font.
export const pickFont = (id: unknown, want: number, fallback: string): FontPick => {
  if (typeof id !== "string" || !id) return { family: fallback, weight: want };
  const d = byId.get(id);
  if (!d) {
    if (!warned.has(id)) {
      warned.add(id);
      console.warn(`font=${id}: not in the library (${FONT_IDS.join(", ")}); using the default`);
    }
    return { family: fallback, weight: want };
  }
  const weight = d.weights.reduce((best, w) => (Math.abs(w - want) < Math.abs(best - want) || (Math.abs(w - want) === Math.abs(best - want) && w > best) ? w : best), d.weights[0]);
  d.load(weight);
  return { family: `"${d.family}", ${fallback}`, weight, ratio: d.ratio }; // the role font fills any glyph the family lacks
};

// The width ratio of a library font (no loading), for sizing text before it is drawn.
export const fontRatio = (id: unknown): number | undefined => (typeof id === "string" ? byId.get(id)?.ratio : undefined);

// The library ids a project's overlays ask for (tooling: a plan checker can warn about ids that are not here).
export const fontsInUse = (overlays: { props?: Record<string, unknown> }[]): string[] => {
  const ids = new Set<string>();
  for (const o of overlays) for (const key of ["font", "leadFont"]) if (typeof o.props?.[key] === "string") ids.add(o.props[key] as string);
  return [...ids];
};
