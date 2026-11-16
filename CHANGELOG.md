# Changelog

Versions follow [Semantic Versioning](https://semver.org/): the number lives in `skill/short-video-editing/VERSION`
(it is installed and packaged with the skill, so `doctor.py` and `./setup.sh --check` can show which version a machine has).
MAJOR: a plan, `project.json` or script interface changes in a way that breaks existing plans. MINOR: a new playbook,
technique, script or option. PATCH: a fix or a documentation change. Releasing: see "Releasing a version" in `README.md`.

## [1.0.0] - 2026-11-16

First packaged release.

### Added
- Packaging: `VERSION`, this changelog, `LICENSE`, a lockfile for the Remotion template (`package-lock.json`, every platform's optional
  binaries), compatible-range pins for `numpy` and `onnxruntime`, the version shown by `doctor.py` and `./setup.sh --check` (and a warning when the
  installed skill is another version than the repository), and a selftest group that guards all of it (group 15).
- Showreel transition pack (experimental, Remotion only): `gridFlash`, `cropPop`, `cropNegative`, `flashWipe`, `blackFlicker`, `zoomFade`;
  the `timelinePanel` overlay; `find_occluders.py` and `reverse_clip.py`; recipes in `references/transition-pack.md`.
- `skin_check.py` is documented and tested (it measured skin tones under a grade but was in no document and no test).

### Changed
- Documentation counts (techniques, transitions, selftest groups, sound files) now match the code; the README states what was verified on Windows.

## Before 1.0.0

Kept as a summary of the git history (`git log` has the detail).

- 2026-11-15: object drop technique (`objectDrop`, `impact`, `+jolt`, `object_cutout.py`); five more CC0 sounds; the selftest runs on Windows;
  `SKILL.md` frontmatter parses in YAML loaders; the repository converted to English.
- 2026-11-13: setup covers the optional extras (OCR, person model, static ffmpeg) and checks dependency drift; the technique catalogue
  (`techniques.json`, `technique.py`), the browser timeline editor (`editor.py`) and reference-video analysis (`analyze_reference.py`).
- 2026-11-11 to 11-12: the agency-pitch flow (cards over an animated grid, lip-synced takes, `finish_video.py`, `check_lipsync.py`);
  prompt templates for any genre and for a batch; the content-rights policy file renamed to `policy.md`.
- 2026-11-09: HyperFrames as a second renderer; CapCut-style hits and a CapCut technique catalogue; keyframed camera in both renderers.
- 2026-11-07: genre playbooks, footage and audio processing, beat cuts and speed ramps; `doctor.py` (a fresh machine or chat can install and use the whole skill).
- 2026-11-05 to 11-06: the first versions: the skill, the scripts, `setup.sh`, the data-driven Remotion template, motion graphics, camera and
  sync tooling, sound design with licence-safe sounds, the before/after card, the viewer-first layout, batch planners and the content-rights policy.
