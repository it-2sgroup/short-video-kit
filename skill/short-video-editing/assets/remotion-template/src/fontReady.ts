// A registry of the font loads in flight, so anything that MEASURES text (components/text/TextBox.tsx) can wait until every font it will draw
// with has really arrived. `loadFont()` of @remotion/google-fonts returns at once and finishes in the background (it holds the frame itself, but
// only for drawing: a measurement taken before the file arrives uses the fallback font and is cached wrong). theme.ts registers the five role
// fonts, fonts.ts every library font it loads.
const pending: Promise<unknown>[] = [];

export const trackFont = (loaded: unknown): void => {
  const wait = (loaded as { waitUntilDone?: () => Promise<unknown> } | undefined)?.waitUntilDone;
  if (typeof wait === "function") pending.push(wait().catch(() => undefined)); // a font that fails to load must not stop the render: the fallback draws
};

export const fontsLoaded = (): Promise<unknown> => Promise.all(pending);
