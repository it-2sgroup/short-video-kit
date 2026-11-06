// Checklist (ticks draw on, rows staggered) and a single numbered step chip.
import React from "react";
import { AbsoluteFill, interpolate, useVideoConfig } from "remotion";
import { evolvePath } from "@remotion/paths";
import type { Overlay } from "../../project";
import { captionTop, fonts, palette, toneColor, zones } from "../../theme";
import { clamp, pop, useEnterExit } from "../anim";
import { OutlineText } from "../text/primitives";

type Base = { ov: Overlay; dur: number; instant: boolean };
const TICK = "M 8 26 L 22 40 L 48 12";

export type CheckListProps = { title?: string; items: string[] };

export const CheckList: React.FC<Base> = ({ ov, dur, instant }) => {
  const p = (ov.props ?? {}) as CheckListProps;
  const { frame, exit } = useEnterExit(dur, { instant });
  const stagger = 9;
  // Never run into the caption band: lift the list if its rows would reach it.
  // ~26 characters fit on one 42px row; longer items wrap to a second line.
  const rows = (p.items ?? []).reduce((n, it) => n + Math.ceil(it.length / 26), 0);
  const height = rows * 52 + (p.items?.length ?? 0) * 14 + (p.title ? 64 : 0);
  const top = Math.min(zones[ov.zone ?? "lower"], captionTop - 30 - height);
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <div style={{ position: "absolute", top, left: 90, right: 200, display: "flex", flexDirection: "column", gap: 14 }}>
        {p.title ? <OutlineText size={44} weight={800}>{p.title}</OutlineText> : null}
        {(p.items ?? []).map((item, i) => {
          const t = instant ? 1 : interpolate(frame, [i * stagger, i * stagger + 8], [0, 1], clamp);
          const tick = evolvePath(instant ? 1 : interpolate(frame, [i * stagger + 3, i * stagger + 11], [0, 1], clamp), TICK);
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 22, opacity: t, translate: `${(1 - t) * -24}px 0` }}>
              <svg width={52} height={46} viewBox="0 0 56 52" style={{ flexShrink: 0, filter: "drop-shadow(0 3px 8px rgba(0,0,0,0.5))" }}>
                <path d={TICK} stroke={toneColor.after} strokeWidth={9} fill="none" strokeLinecap="round" strokeLinejoin="round" strokeDasharray={tick.strokeDasharray} strokeDashoffset={tick.strokeDashoffset} />
              </svg>
              <OutlineText size={42} weight={800} align="left">{item}</OutlineText>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

export type StepProps = { n: number | string; text: string };

export const Step: React.FC<Base> = ({ ov, dur, instant }) => {
  const { fps } = useVideoConfig();
  const p = (ov.props ?? {}) as StepProps;
  const { frame, enter, exit } = useEnterExit(dur, { instant, delay: 3 });
  const chip = instant ? 1 : pop(frame, fps, 0);
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <div style={{ position: "absolute", top: zones[ov.zone ?? "top"], left: 60, right: 60, display: "flex", alignItems: "center", justifyContent: "center", gap: 24 }}>
        <div style={{ width: 80, height: 80, borderRadius: 40, background: `linear-gradient(180deg, ${palette.royal}, ${palette.navy})`, display: "flex", alignItems: "center", justifyContent: "center", scale: String(chip), boxShadow: "0 8px 22px rgba(10,25,60,0.45)", flexShrink: 0 }}>
          <span style={{ fontFamily: fonts.number, fontSize: 52, color: palette.white, lineHeight: 1 }}>{p.n}</span>
        </div>
        <div style={{ opacity: enter, translate: `${(1 - enter) * 20}px 0`, textAlign: "left" }}>
          <OutlineText size={46} weight={800}>{p.text}</OutlineText>
        </div>
      </div>
    </AbsoluteFill>
  );
};
