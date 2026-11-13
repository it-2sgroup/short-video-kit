// The registry of GL Transitions shaders: one line per .glsl file under shaders/. A plain .mjs on purpose: webpack reads the
// `with { type: "text" }` attribute itself and gives the file's text, while Remotion's esbuild step (target es2015) strips it from .ts files.
// Keep the names in step with TransitionType (project.ts) and DEFAULT_FRAMES (timeline.ts).
import directionalWarp from "../../shaders/directionalWarp.glsl" with { type: "text" };
import mosaic from "../../shaders/mosaic.glsl" with { type: "text" };
import pixelate from "../../shaders/pixelate.glsl" with { type: "text" };
import radialShutter from "../../shaders/radialShutter.glsl" with { type: "text" };
import rgbSplit from "../../shaders/rgbSplit.glsl" with { type: "text" };
import ripplePixel from "../../shaders/ripplePixel.glsl" with { type: "text" };
import swirl from "../../shaders/swirl.glsl" with { type: "text" };

export const GL_SHADERS = {
  glPixelate: pixelate,
  glDirectionalWarp: directionalWarp,
  glSwirl: swirl,
  glMosaic: mosaic,
  glRgbSplit: rgbSplit,
  glRadialShutter: radialShutter,
  glRipplePixel: ripplePixel,
};
