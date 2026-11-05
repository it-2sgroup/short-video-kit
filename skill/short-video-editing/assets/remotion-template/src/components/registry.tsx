// Overlay name -> component. project.json refers to components only by these names.
import React from "react";
import type { Overlay } from "../project";
import { Title } from "./text/Title";
import { Callout } from "./graphics/Callout";
import { CheckList, Step } from "./graphics/Lists";
import { Price } from "./graphics/Price";
import { CartPointer, Highlight, Sticker } from "./graphics/Pointers";
import { Compare, Magnifier, Thumbs } from "./graphics/Media";
import { Ranking } from "./graphics/Ranking";
import { LowerThird, Progress } from "./graphics/Bars";

export type OverlayComponent = React.FC<{ ov: Overlay; dur: number; instant: boolean }>;

export const registry: Record<string, OverlayComponent> = {
  title: Title,
  callout: Callout,
  checklist: CheckList,
  step: Step,
  price: Price,
  cart: CartPointer,
  highlight: Highlight,
  sticker: Sticker,
  magnifier: Magnifier,
  thumbs: Thumbs,
  compare: Compare,
  ranking: Ranking,
  progress: Progress,
  lowerThird: LowerThird,
};

export const resolveOverlay = (name: string): OverlayComponent => {
  const c = registry[name];
  if (!c) throw new Error(`Unknown overlay component "${name}". Known: ${Object.keys(registry).join(", ")}`);
  return c;
};
