// glRadialShutter: the new shot opens through a fan of blades around the centre, like the iris of a camera lens; `twist` bends the
// blades into a spiral.
// Author: short-video-kit
// License: MIT
const float PI = 3.14159265;
uniform float blades; // = 6.0
uniform float twist; // = 1.6
uniform float soft; // = 0.06

vec4 transition(vec2 uv) {
  vec2 p = (uv - 0.5) * vec2(ratio, 1.0);
  float f = fract(atan(p.y, p.x) / (2.0 * PI) * blades + length(p) * twist);
  float u = progress * (1.0 + soft);
  float m = smoothstep(f, f + soft, u);
  return mix(getFromColor(uv), getToColor(uv), m);
}
