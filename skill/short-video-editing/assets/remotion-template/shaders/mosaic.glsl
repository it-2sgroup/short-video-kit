// glMosaic: the frame is a grid; a square opens from the middle of every cell and grows until the new shot fills it. The cells
// start in a diagonal order from the side the new shot comes from (`direction`, y up), shaken by a hash.
// Author: short-video-kit
// License: MIT
uniform vec2 cells; // = vec2(7.0, 12.0)
uniform vec2 direction; // = vec2(1.0, 0.0)

float hash(vec2 v) {
  return fract(sin(dot(v, vec2(12.9898, 78.233))) * 43758.5453);
}

vec4 transition(vec2 uv) {
  vec2 g = uv * cells;
  vec2 id = floor(g);
  vec2 c = fract(g) - 0.5;
  vec2 d = normalize(direction + vec2(1e-5));
  float lead = 0.5 - dot(uv - 0.5, d) / (abs(d.x) + abs(d.y)); // 0 at the entry side, 1 at the far side
  float order = 0.55 * lead + 0.45 * hash(id);
  float t = clamp(progress * 1.6 - order * 0.6, 0.0, 1.0);      // each cell has its own start
  float size = t * 0.62;                                          // half-width of the square; 0.5 reaches the edge, 0.62 covers the corners
  float edge = max(abs(c.x), abs(c.y));
  float m = 1.0 - smoothstep(size - 0.03, size + 0.03, edge);
  return mix(getFromColor(uv), getToColor(uv), m);
}
