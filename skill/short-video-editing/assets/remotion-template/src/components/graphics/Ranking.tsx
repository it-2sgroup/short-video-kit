// Podium of glossy tiles (listicles, "top pick"). Optional logo images live in public/.
import React from "react";
import { AbsoluteFill, Img, interpolate, staticFile, useVideoConfig } from "remotion";
import type { Overlay } from "../../project";
import { fonts, palette, zones } from "../../theme";
import { clamp, pop, smooth, useEnterExit } from "../anim";

export type RankingProps = { items: { label: string; rank?: number | string; image?: string; height?: number }[] };

const tile = "linear-gradient(180deg, #FFFFFF 0%, #DCE3EE 100%)";

export const Ranking: React.FC<{ ov: Overlay; dur: number; instant: boolean }> = ({ ov, dur, instant }) => {
  const { fps } = useVideoConfig();
  const p = (ov.props ?? {}) as RankingProps;
  const { frame, exit } = useEnterExit(dur, { instant });
  const items = (p.items ?? []).slice(0, 3);
  const base = zones[ov.zone ?? "top"] + 330; // podium baseline
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <div style={{ position: "absolute", top: zones[ov.zone ?? "top"], left: 70, right: 70, height: base - zones[ov.zone ?? "top"], display: "flex", gap: 40, justifyContent: "center", alignItems: "flex-end" }}>
        {items.map((it, i) => {
          const rise = instant ? 1 : smooth(frame, fps, i * 4, 12);
          const drop = instant ? 1 : pop(frame, fps, 8 + i * 4);
          const h = it.height ?? (it.rank === 1 || it.rank === "1" ? 170 : 110);
          return (
            <div key={i} style={{ width: 200, display: "flex", flexDirection: "column", alignItems: "center" }}>
              <div style={{ width: 170, height: 170, borderRadius: 34, background: tile, boxShadow: "0 14px 30px rgba(10,25,60,0.35), inset 0 2px 0 #fff", display: "flex", alignItems: "center", justifyContent: "center", translate: `0 ${(1 - drop) * -60}px`, opacity: drop, marginBottom: 10 }}>
                {it.image ? (
                  <Img src={staticFile(it.image)} style={{ width: "62%", height: "62%", objectFit: "contain" }} />
                ) : (
                  <span style={{ fontFamily: fonts.sans, fontWeight: 900, fontSize: 80, color: palette.navy }}>{it.label.slice(0, 1)}</span>
                )}
              </div>
              <div style={{ width: 200, height: h * rise, borderRadius: "22px 22px 6px 6px", background: tile, boxShadow: "0 14px 30px rgba(10,25,60,0.3)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "flex-start", paddingTop: 12, overflow: "hidden" }}>
                <span style={{ fontFamily: fonts.sans, fontWeight: 800, fontSize: 34, color: palette.navy, opacity: interpolate(rise, [0.6, 1], [0, 1], clamp) }}>{it.label}</span>
                {it.rank !== undefined ? (
                  <span style={{ fontFamily: fonts.number, fontSize: 84, lineHeight: 1, color: palette.royal, opacity: interpolate(rise, [0.7, 1], [0, 1], clamp) }}>{it.rank}</span>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
