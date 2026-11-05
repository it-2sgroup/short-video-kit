// Audio lives at the root, outside <TransitionSeries>, so scene overlaps never shift it.
// Music ducks under speech (computed from word timings) with a 2-frame attack and 12-frame release.
import React from "react";
import { Audio, Sequence, interpolate, staticFile, useCurrentFrame } from "remotion";
import type { AudioCue, Music, Word } from "../project";
import { dbToGain, toFrames } from "./timeline";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// Merge word timings into speech spans; gaps under 0.4 s stay ducked so the music doesn't pump.
const speechSpans = (words: Word[]) => {
  const spans: { s: number; e: number }[] = [];
  for (const w of words) {
    const last = spans[spans.length - 1];
    if (last && w.start - last.e < 0.4) last.e = Math.max(last.e, w.end);
    else spans.push({ s: w.start, e: w.end });
  }
  return spans;
};

const MusicBed: React.FC<{ music: Music; words: Word[]; fps: number }> = ({ music, words, fps }) => {
  const frame = useCurrentFrame();
  const bed = dbToGain(music.volumeDb ?? -18);
  const duck = dbToGain((music.volumeDb ?? -18) + (music.duckDb ?? -12));
  const gain = speechSpans(words).reduce((g, { s, e }) => {
    const a = toFrames(s, fps);
    const b = toFrames(e, fps);
    return Math.min(g, interpolate(frame, [a - 2, a, b, b + 12], [bed, duck, duck, bed], clamp));
  }, bed);
  return <Audio src={staticFile(music.src)} volume={gain} />;
};

export const Soundtrack: React.FC<{
  voice?: string | null;
  music?: Music | null;
  sfx?: AudioCue[];
  words?: Word[];
  fps: number;
}> = ({ voice, music, sfx = [], words = [], fps }) => (
  <>
    {voice ? <Audio src={staticFile(voice)} /> : null}
    {music ? <MusicBed music={music} words={words} fps={fps} /> : null}
    {sfx.map((c, i) => (
      <Sequence key={i} from={Math.max(0, toFrames(c.at, fps))} layout="none">
        <Audio src={staticFile(c.src)} volume={dbToGain(c.volumeDb ?? -16)} />
      </Sequence>
    ))}
  </>
);
