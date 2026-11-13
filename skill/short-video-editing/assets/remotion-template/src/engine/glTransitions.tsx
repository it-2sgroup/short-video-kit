// GL Transitions loader. A transition written in the gl-transitions.com convention (`vec4 transition(vec2 uv)` that reads
// `getFromColor(uv)`, `getToColor(uv)`, `progress` and `ratio`, uv origin bottom-left) becomes a Remotion presentation through
// `makeHtmlInCanvasPresentation`. A new one is ONE .glsl file under shaders/ plus a line in GL_SHADERS (glShaders.mjs), and its
// name in TransitionType (project.ts) with its length in DEFAULT_FRAMES (timeline.ts).
//
// Parameters: a line `uniform float strength; // = 0.5` declares a parameter and its default (float, int, bool, vec2..vec4; the
// default may be a literal or `vecN(...)`). `direction` is filled from the plan's Direction (the side the new shot comes from, y up).
// Needs WebGL in headless Chrome like every shader transition (the template defaults to `swangle`); keep the Author/License header
// of every file, and a third-party file keeps its own.
import { makeHtmlInCanvasPresentation, type HtmlInCanvasShader } from "@remotion/transitions";
import type { TransitionType } from "../project";
import { GL_SHADERS } from "./glShaders.mjs";

export type GlTransitionType = Exclude<Extract<TransitionType, `gl${string}`>, "glitchSlice">; // "glitchSlice" is a CSS transition that happens to start with "gl"
export const isGlTransition = (type: string): type is GlTransitionType => Object.prototype.hasOwnProperty.call(GL_SHADERS, type);

export type GlProps = Record<string, number | boolean | number[]>;
type Param = { name: string; type: "float" | "int" | "bool" | "vec2" | "vec3" | "vec4"; value: number[] };

const PARAM = /^\s*uniform\s+(float|int|bool|vec2|vec3|vec4)\s+(\w+)\s*;\s*\/\/\s*=\s*(.+?)\s*$/gm;
const NUMBER = /-?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?/gi;

export const parseParams = (source: string): Param[] =>
  [...source.matchAll(PARAM)].map((m) => ({
    type: m[1] as Param["type"],
    name: m[2],
    value: m[1] === "bool" ? [/true/.test(m[3]) ? 1 : 0] : (m[3].replace(/^[iub]?vec\d\s*\(/, "").match(NUMBER) ?? []).map(Number),
  }));

const VERTEX = `#version 300 es
in vec2 a_pos;
out vec2 v_uv;
void main() {
  v_uv = a_pos * 0.5 + 0.5;
  gl_Position = vec4(a_pos, 0.0, 1.0);
}`;

// Remotion binds the outgoing scene to `u_next` and the incoming one to `u_prev` and counts u_time from 0 (outgoing) to 1
// (incoming), the way its own crosswarp does; the textures are uploaded top row first, so uv.y is flipped on sampling.
const prelude = `#version 300 es
precision highp float;
uniform sampler2D u_from;
uniform sampler2D u_to;
uniform float progress;
uniform float ratio;
in vec2 v_uv;
out vec4 outColor;
vec4 getFromColor(vec2 uv) { return texture(u_from, vec2(uv.x, 1.0 - uv.y)); }
vec4 getToColor(vec2 uv) { return texture(u_to, vec2(uv.x, 1.0 - uv.y)); }
`;
const epilogue = `
void main() { outColor = transition(v_uv); }
`;

const compile = (gl: WebGL2RenderingContext, type: number, source: string) => {
  const shader = gl.createShader(type);
  if (!shader) throw new Error("Failed to create shader");
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) throw new Error(`Failed to compile transition shader: ${gl.getShaderInfoLog(shader)}`);
  return shader;
};

const texture = (gl: WebGL2RenderingContext) => {
  const tex = gl.createTexture();
  if (!tex) throw new Error("Failed to create texture");
  gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([0, 0, 0, 0]));
  return tex;
};

// The shader factory Remotion calls once per canvas.
export const glShader = (source: string): HtmlInCanvasShader<GlProps> => {
  const params = parseParams(source);
  return (canvas) => {
    const gl = canvas.getContext("webgl2", { premultipliedAlpha: true });
    if (!gl) throw new Error("Failed to create WebGL2 context");
    const program = gl.createProgram();
    if (!program) throw new Error("Failed to create WebGL program");
    gl.attachShader(program, compile(gl, gl.VERTEX_SHADER, VERTEX));
    gl.attachShader(program, compile(gl, gl.FRAGMENT_SHADER, prelude + source + epilogue));
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(`Failed to link transition shader: ${gl.getProgramInfoLog(program)}`);
    const fromTex = texture(gl);
    const toTex = texture(gl);
    const vao = gl.createVertexArray();
    gl.bindVertexArray(vao);
    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    const aPos = gl.getAttribLocation(program, "a_pos");
    gl.enableVertexAttribArray(aPos);
    gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);
    const at = (name: string) => gl.getUniformLocation(program, name);
    const [uFrom, uTo, uProgress, uRatio] = [at("u_from"), at("u_to"), at("progress"), at("ratio")];
    const uParams = params.map((p) => ({ ...p, loc: at(p.name) }));

    const setParam = (p: (typeof uParams)[number], given: GlProps[string] | undefined) => {
      const v = given === undefined ? p.value : typeof given === "number" ? [given] : typeof given === "boolean" ? [given ? 1 : 0] : given;
      if (p.type === "float") gl.uniform1f(p.loc, v[0]);
      else if (p.type === "int" || p.type === "bool") gl.uniform1i(p.loc, Math.round(v[0]));
      else if (p.type === "vec2") gl.uniform2f(p.loc, v[0], v[1]);
      else if (p.type === "vec3") gl.uniform3f(p.loc, v[0], v[1], v[2]);
      else gl.uniform4f(p.loc, v[0], v[1], v[2], v[3]);
    };

    return {
      clear: () => {
        gl.clearColor(0, 0, 0, 0);
        gl.clear(gl.COLOR_BUFFER_BIT);
      },
      cleanup: () => {
        gl.deleteProgram(program);
        gl.deleteTexture(fromTex);
        gl.deleteTexture(toTex);
      },
      draw: ({ prevImage, nextImage, width, height, time, passedProps }) => {
        if (!prevImage && !nextImage) return;
        if ((prevImage && (prevImage.width === 0 || prevImage.height === 0)) || (nextImage && (nextImage.width === 0 || nextImage.height === 0))) return;
        // One side missing: show the other fully (time 0 is the outgoing shot, 1 the incoming one).
        const progress = !prevImage ? 0 : !nextImage ? 1 : time;
        gl.viewport(0, 0, width, height);
        gl.clearColor(0, 0, 0, 0);
        gl.clear(gl.COLOR_BUFFER_BIT);
        gl.useProgram(program);
        gl.activeTexture(gl.TEXTURE0);
        gl.bindTexture(gl.TEXTURE_2D, fromTex);
        if (nextImage) gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, nextImage);
        gl.uniform1i(uFrom, 0);
        gl.activeTexture(gl.TEXTURE1);
        gl.bindTexture(gl.TEXTURE_2D, toTex);
        if (prevImage) gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, prevImage);
        gl.uniform1i(uTo, 1);
        gl.uniform1f(uProgress, progress);
        gl.uniform1f(uRatio, width / height);
        for (const p of uParams) setParam(p, passedProps[p.name]);
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      },
    };
  };
};

// One presentation factory per shader: Remotion keeps the component's identity, so it must not be rebuilt on every render.
const factories = new Map<GlTransitionType, ReturnType<typeof makeHtmlInCanvasPresentation<GlProps>>>();
export const glTransition = (type: GlTransitionType, props: GlProps = {}) => {
  let make = factories.get(type);
  if (!make) {
    make = makeHtmlInCanvasPresentation<GlProps>(glShader(GL_SHADERS[type]));
    factories.set(type, make);
  }
  return make(props);
};
