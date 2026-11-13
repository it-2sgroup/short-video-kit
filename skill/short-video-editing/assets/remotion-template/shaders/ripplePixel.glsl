// glRipplePixel: a ring spreads from the centre; inside it the new shot, outside the old one, and along the ring the picture is
// pixelated and pushed outward in a wave.
// Author: short-video-kit
// License: MIT
uniform float cell; // = 0.03
uniform float width; // = 0.2

vec4 transition(vec2 uv) {
  vec2 p = (uv - 0.5) * vec2(ratio, 1.0);
  float r = length(p);
  float reach = 0.5 * length(vec2(ratio, 1.0)) + width * 1.5;
  float x = (r - progress * reach) / width;                  // < 0 inside the ring (new shot), > 0 outside (old shot)
  float ring = exp(-x * x * 2.0);
  vec2 radial = normalize(p + vec2(1e-5)) / vec2(ratio, 1.0);
  vec2 moved = uv - radial * ring * sin(x * 9.0) * 0.035;
  vec2 size = vec2(cell, cell * ratio);
  vec2 snapped = (floor(moved / size) + 0.5) * size;
  vec2 q = mix(moved, snapped, smoothstep(0.08, 0.5, ring));
  return mix(getToColor(q), getFromColor(q), smoothstep(-0.2, 0.2, x));
}
