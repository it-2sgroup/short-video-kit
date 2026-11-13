// glPixelate: both shots break into square blocks that grow to a peak in the middle and shrink away again; the swap happens at the peak.
// Author: short-video-kit
// License: MIT
const float PI = 3.14159265;
uniform float squares; // = 22.0

vec4 transition(vec2 uv) {
  float k = sin(PI * progress);
  float width = mix(0.0006, 1.0 / squares, pow(k, 1.3)); // block width as a fraction of the frame width
  vec2 cell = vec2(width, width * ratio);                  // square in pixels
  vec2 q = (floor(uv / cell) + 0.5) * cell;
  return mix(getFromColor(q), getToColor(q), smoothstep(0.44, 0.56, progress));
}
