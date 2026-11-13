// CLI config. Node.js render APIs ignore this file; pass the same options to them directly.
import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
Config.setDefaultPremountInSeconds(2);
// Shader transitions (crossZoom, filmBurn, zoomBlur...) and @remotion/effects (the +leak accent) need WebGL in headless Chrome. "swangle" (software ANGLE)
// works on every machine, with or without a GPU; set SVK_GL=angle on a machine with a GPU for the faster path.
Config.setChromiumOpenGlRenderer((process.env.SVK_GL as "angle" | "swangle" | undefined) ?? "swangle");
