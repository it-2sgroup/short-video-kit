// Overlay name -> component. project.json refers to components only by these names.
import React from "react";
import type { Overlay } from "../project";
import { Title } from "./text/Title";
import { Callout } from "./graphics/Callout";
import { CheckList, Step } from "./graphics/Lists";
import { Price } from "./graphics/Price";
import { CartPointer, Highlight, Sticker } from "./graphics/Pointers";
import { Compare, ImageCard, Magnifier, Thumbs } from "./graphics/Media";
import { Chart, Label, Pin, Specs, Stat } from "./graphics/Info";
import { Ranking } from "./graphics/Ranking";
import { LowerThird, Progress } from "./graphics/Bars";
import { Circled, Counter, Icon, Logo, RawFinal } from "./graphics/Brand";
import { Arc, Burst, Phrase, Pill, Script, Tag } from "./text/Phrase";
import { Flare, Streak, Sweep } from "./graphics/Light";
import { Knockout } from "./text/Knockout";

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
  specs: Specs,
  pin: Pin,
  label: Label,
  stat: Stat,
  chart: Chart,
  image: ImageCard,
  phrase: Phrase,
  pill: Pill,
  arc: Arc,
  burst: Burst,
  script: Script,
  tag: Tag,
  logo: Logo,
  counter: Counter,
  icon: Icon,
  circled: Circled,
  rawfinal: RawFinal,
  sweep: Sweep,
  flare: Flare,
  streak: Streak,
  knockout: Knockout,
};

export const resolveOverlay = (name: string): OverlayComponent => {
  const c = registry[name];
  if (!c) throw new Error(`Unknown overlay component "${name}". Known: ${Object.keys(registry).join(", ")}`);
  return c;
};
