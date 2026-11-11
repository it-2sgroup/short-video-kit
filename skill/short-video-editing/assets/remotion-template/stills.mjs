// Render many stills of one project from ONE bundle (a `remotion still` call per frame re-bundles every time).
//
//   node stills.mjs project.json out/d1 1.0 2.5 12.2        -> out/d1_0001.00.jpg, out/d1_0002.50.jpg, out/d1_0012.20.jpg
//   node stills.mjs project.json out/d1 --every 0.5 --from 0 --to 8        every half second between 0 and 8 s
//   node stills.mjs project.json out/d1 --cuts                              the middle of every scene and 0.1 s after every cut
//
// Times are seconds of the video. Look at them (`python scripts/montage.py "out/d1_*.jpg" --out sheet.jpg`): every transition,
// every text effect and every card must be seen before the render. Run it from the render project's folder.
import fs from "node:fs";
import path from "node:path";
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";

const args = process.argv.slice(2);
const [project, prefix] = args;
if (!project || !prefix) {
  console.error("usage: node stills.mjs project.json out/prefix [seconds ...] [--every S --from A --to B] [--cuts]");
  process.exit(2);
}
const flag = (name, dflt) => {
  const i = args.indexOf(name);
  return i >= 0 ? parseFloat(args[i + 1]) : dflt;
};
const props = JSON.parse(fs.readFileSync(project, "utf8"));

// bare numbers are seconds; the number after --every/--from/--to belongs to that flag, not to the list
const valued = new Set(["--every", "--from", "--to"]);
let times = args.slice(2).filter((a, i, all) => /^\d+(\.\d+)?$/.test(a) && !valued.has(all[i - 1])).map(Number);
const every = flag("--every", 0);
if (every > 0) {
  for (let t = flag("--from", 0); t <= flag("--to", props.duration ?? 60) + 1e-6; t += every) times.push(+t.toFixed(3));
}
if (args.includes("--cuts")) {
  // from the project's own scene table: just after each cut and the middle of each scene
  for (const s of props.scenes ?? []) {
    times.push(+(s.start + 0.1).toFixed(3), +(s.start + Math.max(0.2, (s.end - s.start) / 2)).toFixed(3));
  }
}
times = [...new Set(times)].sort((a, b) => a - b);
if (!times.length) {
  console.error("no times: give seconds, --every, or --cuts");
  process.exit(2);
}

const serveUrl = await bundle({ entryPoint: path.resolve("src/index.ts") });
const composition = await selectComposition({ serveUrl, id: "Short", inputProps: props });
fs.mkdirSync(path.dirname(prefix), { recursive: true });
for (const t of times) {
  const frame = Math.min(composition.durationInFrames - 1, Math.round(t * composition.fps));
  await renderStill({
    composition,
    serveUrl,
    output: `${prefix}_${t.toFixed(2).padStart(7, "0")}.jpg`,
    frame,
    inputProps: props,
    imageFormat: "jpeg",
    jpegQuality: 88,
    chromiumOptions: { gl: "angle" },   // shader transitions and light leaks render on Windows with angle
    logLevel: "error",
  });
}
console.log(`stills: ${times.length} in ${path.dirname(prefix)}`);
