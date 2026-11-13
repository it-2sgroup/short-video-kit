// glDirectionalWarp: a soft wipe whose edge waves, with the old shot stretching along the edge and the new one settling in behind it.
// `direction` is the side the new shot comes from, y up (vec2(1.0, 0.0) = from the right).
// Author: short-video-kit
// License: MIT
const float PI = 3.14159265;
uniform vec2 direction; // = vec2(1.0, 0.0)
uniform float warp; // = 0.07
uniform float soft; // = 0.10

vec4 transition(vec2 uv) {
  vec2 d = normalize(direction + vec2(1e-5));
  vec2 side = vec2(-d.y, d.x);
  float s = dot(uv - 0.5, d) / (abs(d.x) + abs(d.y)) + 0.5;      // 1 at the entry side, 0 at the far side
  float w = dot((uv - 0.5) * vec2(ratio, 1.0), side);
  float edge = mix(1.0 + 2.0 * warp + soft, -2.0 * warp - soft, progress) + warp * sin(w * 13.0 + progress * 8.0);
  float m = smoothstep(edge - soft, edge + soft, s);               // 1 where the new shot already shows
  float bend = warp * 0.5 * (1.0 - m) * m * 4.0;
  vec2 shift = d * bend;
  return mix(getFromColor(uv + shift), getToColor(uv - shift * 0.6), m);
}
