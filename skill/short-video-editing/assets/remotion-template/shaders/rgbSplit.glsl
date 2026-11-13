// glRgbSplit: a dissolve in which the red, green and blue channels cross-fade at different times and slide apart sideways
// (`direction`, y up), so the colours fringe and snap back together. Reads as an RGB glitch without hard edges.
// Author: short-video-kit
// License: MIT
const float PI = 3.14159265;
uniform float shift; // = 0.05
uniform vec2 direction; // = vec2(1.0, 0.0)

vec4 transition(vec2 uv) {
  float k = sin(PI * progress);
  vec2 d = normalize(direction + vec2(1e-5)) * vec2(1.0, ratio);
  vec2 o = d * shift * k;
  float mr = smoothstep(0.05, 0.65, progress);
  float mg = smoothstep(0.20, 0.80, progress);
  float mb = smoothstep(0.35, 0.95, progress);
  float r = mix(getFromColor(uv + o).r, getToColor(uv + o).r, mr);
  float g = mix(getFromColor(uv).g, getToColor(uv).g, mg);
  float b = mix(getFromColor(uv - o).b, getToColor(uv - o).b, mb);
  return vec4(r, g, b, 1.0) * (1.0 + 0.12 * k);
}
