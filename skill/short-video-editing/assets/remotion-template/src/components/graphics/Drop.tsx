// Things that land: an object cut out of the NEXT shot falls in from the top edge and the picture cuts to that shot as it touches the
// ground (`objectDrop`), and the touchdown burst (`impact`, also usable alone on any point).
// Both are pure functions of the frame, drawn from geometry only (no sprite, no footage, no licence), seeded by `seed` so a still and a render agree.
// One landing per beat. The burst is built the way a compositor stacks a ground hit, every layer keyed to the same frame:
//   1. an exposure pop (a faint white plate for one frame) 2. a small white-hot core 3. spark STREAKS that fly out of it fast and drag to a stop
//   (each a line from where it was to where it is: the motion blur is in the shape) 4. embers thrown up that fall back under gravity 5. dust that
//   spreads along the ground with ragged noisy edges and thins out 6. a contact shadow under it 7. a faint flat shockwave ring.
// Sparks, core and ring are screen-blended (they add light); dust and shadow are not (they take it). Squashed by `flat`, a burst reads as lying on the ground.
import React from "react";
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from "remotion";
import type { Overlay } from "../../project";
import { frame as size, motion } from "../../theme";

type Base = { ov: Overlay; dur: number; instant: boolean };
type Point = [number, number];

const unit = (v: number) => Math.min(1, Math.max(0, v));

// mulberry32: a small seeded generator, so the same overlay draws the same sparks in every render.
const rng = (seed: number) => {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
};

// ------------------------------------------------------------------------------------------------ the burst
export type ImpactProps = {
  at?: Point;
  size?: number; // radius of the spark spread in px
  heat?: string; // colour of the sparks' glow
  dust?: string; // colour of the dust
  sparks?: number; // streaks (embers are a third of that again)
  flat?: number; // vertical squash: 1 = a ball, 0.3 = lying on the ground
  ring?: number; // opacity of the shockwave ring (0 = none)
  flash?: number; // opacity of the one-frame exposure pop (0 = none)
  seed?: number;
};

type FxOpts = { k: number; x: number; y: number; s: number; heat: string; dust: string; sparks: number; flat: number; ring: number; flash: number; seed: number };

const FX_FRAMES = 18;

const ImpactFx: React.FC<FxOpts> = ({ k, x, y, s, heat, dust, sparks, flat, ring, flash, seed }) => {
  if (k < 0 || k > FX_FRAMES) return null;
  const rnd = rng(seed);
  const id = `fx${seed}`;
  const px = s / 220; // stroke widths are tuned for s = 220
  const drag = 0.72;
  const travel = (v: number, t: number) => (t <= 0 ? 0 : (v * (1 - Math.pow(drag, t))) / (1 - drag)); // distance after t frames of a speed that decays by `drag` each frame

  // spark streaks: head at where the spark is now, tail 1.8 frames behind: a line, so the blur is in the shape
  const streaks = Array.from({ length: sparks }, () => {
    const a = rnd() * Math.PI * 2;
    const v = s * (0.09 + 0.22 * rnd());
    const life = 3 + 3 * rnd();
    const w = (1.2 + 2.6 * rnd()) * px;
    const head = travel(v, k + 2); // already well out on the touchdown frame: a hit does not grow, it starts big
    const tail = travel(v, k + 0.2);
    const fade = 1 - Math.pow(unit(k / life), 1.5);
    return { x1: Math.cos(a) * tail, y1: Math.sin(a) * tail * flat, x2: Math.cos(a) * head, y2: Math.sin(a) * head * flat, w, fade };
  }).filter((p) => p.fade > 0.02);

  // embers: thrown up and out, fall back under gravity, cool from white-yellow through orange to red
  const embers = Array.from({ length: Math.round(sparks / 3) }, () => {
    const a = -Math.PI * (0.1 + 0.8 * rnd());
    const v = s * (0.045 + 0.1 * rnd());
    const g = s * 0.0085;
    const life = 9 + 7 * rnd();
    const w = (1.5 + 1.8 * rnd()) * px;
    const at = (t: number) => ({ x: Math.cos(a) * v * t, y: Math.sin(a) * v * t * 0.9 + 0.5 * g * t * t });
    const p = at(k + 0.5);
    const q = at(Math.max(0, k - 0.8));
    const col = k < 4 ? "#FFE9A0" : k < 8 ? "#FFB347" : "#FF6A2B";
    return { x1: q.x, y1: q.y, x2: p.x, y2: p.y, w, col, fade: 1 - Math.pow(unit(k / life), 2) };
  }).filter((p) => p.fade > 0.02);

  // dust: puffs that spread along the ground (wider than tall), rise a little, thin out; the group gets ragged edges from one noise filter
  const puffs = Array.from({ length: 9 }, () => {
    const ox = (rnd() - 0.5) * s * 0.5;
    const dir = ox >= 0 ? 1 : -1;
    const r0 = s * (0.14 + 0.16 * rnd());
    const wait = Math.floor(rnd() * 2);
    const speed = s * (0.1 + 0.08 * rnd());
    const ry = 0.5 + 0.2 * rnd();
    const kk = k - wait;
    if (kk < 0) return null;
    const r = r0 * (1 + 0.16 * Math.pow(kk, 0.85));
    const a = 0.8 * Math.min(1, (kk + 1) / 2) * Math.pow(Math.max(0, 1 - kk / 15), 1.4);
    return { cx: ox + dir * speed * Math.pow(kk, 0.75), cy: -r * ry * 0.4 - s * 0.01 * kk, rx: r, ry: r * ry, a };
  }).filter((p): p is NonNullable<typeof p> => !!p && p.a > 0.01);

  const box = s * 3.2;
  const core = Math.pow(unit(1 - k / 3), 1.2);
  const cr = s * 0.42 * (0.7 + 0.3 * motion.easeOut(unit((k + 1) / 2)));
  const ringT = unit(k / 8);
  const ringR = s * (0.2 + 1.05 * motion.easeOut(ringT));
  const pop = k === 0 ? flash : k === 1 ? flash * 0.5 : 0;
  return (
    <>
      {pop > 0 ? <AbsoluteFill style={{ background: "#FFFFFF", opacity: pop, mixBlendMode: "screen" }} /> : null}
      <svg width={box * 2} height={box * 2} viewBox={`${-box} ${-box} ${box * 2} ${box * 2}`} style={{ position: "absolute", left: x - box, top: y - box, overflow: "visible" }}>
        <defs>
          <radialGradient id={`${id}c`}>
            <stop offset="0" stopColor="#FFFFFF" />
            <stop offset="0.4" stopColor="#FFF0B8" />
            <stop offset="0.72" stopColor={heat} stopOpacity="0.6" />
            <stop offset="1" stopColor={heat} stopOpacity="0" />
          </radialGradient>
          <radialGradient id={`${id}d`}>
            <stop offset="0" stopColor={dust} stopOpacity="0.95" />
            <stop offset="0.6" stopColor={dust} stopOpacity="0.5" />
            <stop offset="1" stopColor={dust} stopOpacity="0" />
          </radialGradient>
          <radialGradient id={`${id}s`}>
            <stop offset="0" stopColor="#000000" stopOpacity="0.45" />
            <stop offset="1" stopColor="#000000" stopOpacity="0" />
          </radialGradient>
          <filter id={`${id}n`} filterUnits="userSpaceOnUse" x={-s * 2} y={-s * 1.4} width={s * 4} height={s * 2}>
            <feTurbulence type="fractalNoise" baseFrequency="0.011 0.022" numOctaves={3} seed={seed} result="n" />
            <feDisplacementMap in="SourceGraphic" in2="n" scale={s * 0.55} xChannelSelector="R" yChannelSelector="G" result="d" />
            <feGaussianBlur in="d" stdDeviation={Math.max(1, s * 0.025)} />
          </filter>
          <filter id={`${id}b`} x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation={Math.max(1, s * 0.035)} />
          </filter>
        </defs>
        <ellipse cx={0} cy={s * 0.02} rx={s * 0.55} ry={s * 0.55 * flat * 0.9} fill={`url(#${id}s)`} opacity={Math.max(0, 1 - k / 9)} />
        <g filter={`url(#${id}n)`}>
          {puffs.map((p, i) => (
            <ellipse key={`p${i}`} cx={p.cx} cy={p.cy} rx={p.rx} ry={p.ry} fill={`url(#${id}d)`} opacity={p.a} />
          ))}
        </g>
        <g style={{ mixBlendMode: "screen" }}>
          {ring > 0 ? <ellipse cx={0} cy={0} rx={ringR} ry={ringR * flat} fill="none" stroke="#FFFFFF" strokeWidth={Math.max(1, 3 * px * (1 - ringT))} opacity={ring * (1 - ringT)} /> : null}
          <g filter={`url(#${id}b)`} opacity={core}>
            <ellipse cx={0} cy={0} rx={cr} ry={cr * flat * 1.3} fill={`url(#${id}c)`} />
          </g>
          {streaks.map((p, i) => (
            <g key={`s${i}`} opacity={p.fade} strokeLinecap="round">
              <line x1={p.x1} y1={p.y1} x2={p.x2} y2={p.y2} stroke={heat} strokeWidth={p.w * 1.6} opacity={0.8} />
              <line x1={p.x1} y1={p.y1} x2={p.x2} y2={p.y2} stroke="#FFF4C8" strokeWidth={p.w * 0.6} />
            </g>
          ))}
          {embers.map((p, i) => (
            <line key={`e${i}`} x1={p.x1} y1={p.y1} x2={p.x2} y2={p.y2} stroke={p.col} strokeWidth={p.w} strokeLinecap="round" opacity={p.fade} />
          ))}
        </g>
      </svg>
    </>
  );
};

// ------------------------------------------------------------------------------------------------ impact
// The burst alone, on any point: a door slam, a product set down, a stamp. Give it 10-18 frames. `at` is the ground point (fractions of the frame).
export const Impact: React.FC<Base> = ({ ov }) => {
  const p = (ov.props ?? {}) as ImpactProps;
  const frame = useCurrentFrame();
  const [ax, ay] = p.at ?? [0.5, 0.62];
  return (
    <AbsoluteFill>
      <ImpactFx k={frame} x={ax * size.width} y={ay * size.height} s={p.size ?? 230} heat={p.heat ?? "#FFC21A"} dust={p.dust ?? "#CFC2AB"} sparks={p.sparks ?? 56} flat={p.flat ?? 0.32} ring={p.ring ?? 0.3} flash={p.flash ?? 0.14} seed={p.seed ?? 7} />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------------------------------------ objectDrop
export type DropProps = ImpactProps & {
  src: string; // a transparent PNG under public/ (scripts/object_cutout.py writes it and prints the other keys)
  width?: number; // the object's width in px as it lands
  aspect?: number; // height / width of the PNG (the cutout script prints it)
  fall?: number; // frames of falling before touchdown (default 4 = 0.13 s at 30 fps)
  tilt?: number; // degrees of lean at the top that straighten while it falls
  scaleFrom?: number; // size on the first frame as a fraction of the landed size: it grows a little as it comes down (default 0.9)
  drift?: number; // px it starts to the side of the landing spot (default 0)
  enter?: number; // fraction of the object already inside the frame on the first frame (default 0.3)
  shadow?: boolean; // a ground shadow that darkens as it nears
  impact?: number; // frames of burst after touchdown (0 = none)
  burstY?: number; // the burst's centre as a fraction of the frame height (default: the landing y); lift it when the ground is below the frame
};

// Frame `fall` is the touchdown: the plan puts the CUT to the next shot on that frame (start = cut time - fall / fps), and the object is not
// drawn from then on (the next shot already holds the real one in the same place); the burst plays over the new shot for `impact` frames.
// `at` is the object's bottom-centre as fractions of the frame, `width` its width in px; both come from the cutout script, measured on the
// frame the next shot starts with. Fall: constant acceleration (position ~ t squared), a vertical smear that grows with speed, a lean that
// straightens, a size that grows to the landed size, and a shadow that darkens as it nears the ground.
export const ObjectDrop: React.FC<Base> = ({ ov }) => {
  const p = (ov.props ?? {}) as DropProps;
  const frame = useCurrentFrame();
  const fall = Math.max(2, Math.round(p.fall ?? 4));
  const after = Math.round(p.impact ?? FX_FRAMES);
  const [ax, ay] = p.at ?? [0.5, 0.62];
  const X = ax * size.width;
  const Y = ay * size.height;
  const w = p.width ?? 420;
  const t = unit(frame / fall);
  const ease = t * t;
  const grow = (p.scaleFrom ?? 0.9) + (1 - (p.scaleFrom ?? 0.9)) * ease;
  const h = w * (p.aspect ?? 0.8) * grow;
  const bottom0 = (p.enter ?? 0.3) * h;
  const bottom = bottom0 + (Y - bottom0) * ease;
  const speed = (Y - bottom0) * ((2 * t) / fall); // px per frame at this moment
  const smear = Math.min(16, speed * 0.04);
  const lean = (p.tilt ?? 4) * (1 - ease);
  const sideways = (p.drift ?? 0) * (1 - ease);
  const flying = frame < fall;
  const filterId = `dropblur${Math.round(ov.start * 1000)}`; // no dot: a url(#id) with one is not found
  const s = p.size ?? Math.max(240, Math.min(400, w * 0.5));
  return (
    <AbsoluteFill>
      {flying && p.src ? (
        <>
          {p.shadow !== false ? (
            <div
              style={{
                position: "absolute",
                left: X,
                top: Y,
                width: w * 1.15,
                height: w * 0.14,
                translate: "-50% -50%",
                borderRadius: "50%",
                background: "radial-gradient(ellipse, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0) 70%)",
                opacity: ease,
                scale: String(0.5 + 0.5 * ease),
              }}
            />
          ) : null}
          {smear > 0.5 ? (
            <svg width={0} height={0} style={{ position: "absolute" }}>
              <defs>
                <filter id={filterId} x="-10%" y="-30%" width="120%" height="160%">
                  <feGaussianBlur stdDeviation={`0 ${smear.toFixed(2)}`} />
                </filter>
              </defs>
            </svg>
          ) : null}
          <div
            style={{
              position: "absolute",
              left: X + sideways,
              top: bottom,
              width: w * grow,
              translate: "-50% -100%",
              transformOrigin: "50% 100%",
              rotate: `${lean}deg`,
              filter: smear > 0.5 ? `url(#${filterId})` : undefined,
            }}
          >
            <Img src={staticFile(p.src)} style={{ width: "100%", display: "block" }} />
          </div>
        </>
      ) : null}
      {after > 0 ? <ImpactFx k={frame - fall} x={X} y={(p.burstY ?? ay) * size.height} s={s} heat={p.heat ?? "#FFC21A"} dust={p.dust ?? "#CFC2AB"} sparks={p.sparks ?? 56} flat={p.flat ?? 0.32} ring={p.ring ?? 0.3} flash={p.flash ?? 0.14} seed={p.seed ?? 7} /> : null}
    </AbsoluteFill>
  );
};
