// glSwirl: the picture twists around the centre, strongest in the middle of the move, and the new shot untwists out of it.
// Author: short-video-kit
// License: MIT
const float PI = 3.14159265;
uniform float twist; // = 5.0
uniform float radius; // = 0.95

vec4 transition(vec2 uv) {
  vec2 p = (uv - 0.5) * vec2(ratio, 1.0);
  float r = length(p);
  float k = sin(PI * progress);
  float falloff = 1.0 - clamp(r / radius, 0.0, 1.0);
  float a = twist * k * falloff * falloff;
  float c = cos(a), s = sin(a);
  vec2 q = vec2(c * p.x - s * p.y, s * p.x + c * p.y) / vec2(ratio, 1.0) + 0.5;
  return mix(getFromColor(q), getToColor(q), smoothstep(0.36, 0.64, progress));
}
