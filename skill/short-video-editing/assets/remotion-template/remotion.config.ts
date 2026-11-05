// CLI config. Node.js render APIs ignore this file; pass the same options to them directly.
import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
Config.setDefaultPremountInSeconds(2);
// Shader transitions (crossZoom) and @remotion/light-leaks need WebGL in headless Chrome.
Config.setChromiumOpenGlRenderer("angle");
