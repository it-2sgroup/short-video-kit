// One composition, "Short". Its length and size come from the project, so the same code renders
// every video:  npx remotion render src/index.ts Short out/video.mp4 --props=project.json
import React from "react";
import { Composition } from "remotion";
import type { Project } from "./project";
import { Short } from "./engine/Short";
import example from "../project.example.json";

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Short"
    component={Short}
    defaultProps={example as Project}
    durationInFrames={300}
    fps={30}
    width={1080}
    height={1920}
    calculateMetadata={({ props }) => {
      const fps = props.fps ?? 30;
      return {
        fps,
        width: props.width ?? 1080,
        height: props.height ?? 1920,
        durationInFrames: Math.max(1, Math.round(props.duration * fps)),
      };
    }}
  />
);
