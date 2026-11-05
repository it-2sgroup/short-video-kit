// Graphics that show footage: a magnifier lens on a detail, and a recap row of frozen thumbnails.
import React from "react";
import { AbsoluteFill, Freeze, OffthreadVideo, interpolate, staticFile, useVideoConfig } from "remotion";
import type { Overlay } from "../../project";
import { frame as size, palette, zones } from "../../theme";
import { clamp, smooth, useEnterExit } from "../anim";
import { OutlineText } from "../text/primitives";

type Base = { ov: Overlay; dur: number; instant: boolean };

export type MagnifierProps = { clip: string; in: number; target: [number, number]; at?: [number, number]; zoom?: number; diameter?: number };

export const Magnifier: React.FC<Base> = ({ ov, dur, instant }) => {
  const { fps } = useVideoConfig();
  const p = (ov.props ?? {}) as MagnifierProps;
  const { frame, exit } = useEnterExit(dur, { instant });
  const k = instant ? 1 : smooth(frame, fps, 0, 10);
  const dia = p.diameter ?? 400;
  const [cx, cy] = p.at ?? [0.32, 0.3];
  const [tx, ty] = p.target;
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <div
        style={{
          position: "absolute",
          left: cx * size.width - dia / 2,
          top: cy * size.height - dia / 2,
          width: dia,
          height: dia,
          borderRadius: "50%",
          overflow: "hidden",
          border: `8px solid ${palette.white}`,
          boxShadow: "0 18px 50px rgba(0,0,0,0.45)",
          scale: String(interpolate(k, [0, 1], [0.6, 1])),
          opacity: k,
        }}
      >
        <div
          style={{
            position: "absolute",
            width: size.width,
            height: size.height,
            left: dia / 2 - tx * size.width,
            top: dia / 2 - ty * size.height,
            transformOrigin: `${tx * 100}% ${ty * 100}%`,
            scale: String(p.zoom ?? 2.2),
          }}
        >
          <OffthreadVideo src={staticFile(`clips/${p.clip}.mp4`)} startFrom={Math.round(p.in * fps)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

export type ThumbsProps = { cards: { clip: string; at: number; caption?: string }[] };

export const Thumbs: React.FC<Base> = ({ ov, dur, instant }) => {
  const { fps } = useVideoConfig();
  const p = (ov.props ?? {}) as ThumbsProps;
  const { frame, exit } = useEnterExit(dur, { instant });
  const cards = (p.cards ?? []).slice(0, 3);
  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <div style={{ position: "absolute", top: zones[ov.zone ?? "top"], left: 70, right: 70, display: "flex", gap: 22, justifyContent: "center" }}>
        {cards.map((c, i) => {
          const k = instant ? 1 : smooth(frame, fps, i * 4, 14);
          const cap = interpolate(frame, [i * 4 + 4, i * 4 + 12], [0, 1], clamp);
          return (
            <div key={i} style={{ width: 286, display: "flex", flexDirection: "column", alignItems: "center", gap: 10, translate: `0 ${(1 - k) * 40}px`, opacity: k }}>
              <div style={{ width: 286, height: 266, borderRadius: 22, overflow: "hidden", border: `5px solid ${palette.white}`, boxShadow: "0 10px 26px rgba(0,0,0,0.38)" }}>
                <Freeze frame={Math.round(c.at * fps)}>
                  <OffthreadVideo src={staticFile(`clips/${c.clip}.mp4`)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                </Freeze>
              </div>
              {c.caption ? (
                <div style={{ opacity: cap }}>
                  <OutlineText size={36} weight={800} lineHeight={1.05}>{c.caption}</OutlineText>
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
