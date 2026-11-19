# Changelog

Versions follow [Semantic Versioning](https://semver.org/): the number lives in `skill/short-video-editing/VERSION`
(it is installed and packaged with the skill, so `doctor.py` and `./setup.sh --check` can show which version a machine has).
MAJOR: a plan, `project.json` or script interface changes in a way that breaks existing plans. MINOR: a new playbook,
technique, script or option. PATCH: a fix or a documentation change. Releasing: see "Releasing a version" in `README.md`.

## [1.3.0] - 2026-11-20

### Added
- The creative layer (`references/creative-direction.md`): `concept.py` (the idea of a video: feeling, tension, a returning motif, ONE signature move, the restraint of the vocabulary, the energy curve; `check` against a plan, `lock` a chosen direction's
  vocabulary), `directions.py` (three different directions from one plan and one concept, from the axes of `assets/style-axes.json` built only from catalogue ids, with `compare.md`, `--keep`, `--retime`, `--stills`; the same `--seed` gives the same plans)
  and `style_ledger.py` (a memory of the style of finished videos; a repeat of the last eight is flagged and `directions.py` steers away from it). Selftest group 14f. `SKILL.md` step 1a, `docs/WORKFLOW.md` and `CLAUDE.md` put the idea before the plan.

## [1.2.0] - 2026-11-19

### Added
- `textbox` overlay: text in a box you give (`box=x,y,w[,h]`), measured with the real font by `@remotion/layout-utils` (pinned 4.0.540, lockfile regenerated; `fontReady.ts` makes the measurement wait for the font), wrapped at word
  boundaries, shrunk to fit, never drawn outside the box sideways; colour, outline, background plate, alignment, case and any text effect are keys. `reference_to_plan.py` now writes a sample's text slots as `textbox` rows in the sample's own box,
  size, ink and entry effect (`--text-component phrase` keeps the older blocks).
- `layout_check.py`, run by `plan_to_project.py` after every build: text against text, the captions (and their hide bands), the speaker's head, TikTok's right rail and the frame edge.
- `analyze_reference.py --compare` pairs the text events of the recreation with the sample's by time (when, where, how big, how it enters).
- Plan tables: `\;`, `\|` and `\/` write a literal semicolon, pipe and slash between spaces; a mistyped key of `textbox`, `phrase` or `pill` is reported instead of ignored.

### Fixed
- `title` no longer drops the lines between the first and the last (they joined the lead line); `End=auto` of a `phrase` counts its `lead` and `emph` text; a textbox is not judged by the zone-overlap rule.

## [1.1.0] - 2026-11-19

### Added
- Reference mode, so a sample video drives the edit instead of a genre's defaults: `reference_to_plan.py` writes a first-draft plan from `analyze_reference.py`'s `report.json` (the sample's shots, transitions, camera moves,
  text slots and caption track; the user's footage cells and words), the neutral playbook `reference` (no genre numbers), `pacing_checker.py --reference report.json` (the sample's own shot lengths and runtime; rhythm rules are
  warnings, gaps and overlaps stay errors) and `playbook.py suggest --reference` (a request that names a sample picks `reference`). `SKILL.md` step 1b says the sample wins over the genre. Selftest group 14e.

### Changed
- `pacing_checker.check()` reports rhythm rules through one helper so a plan can be judged softly; genre playbooks behave exactly as before.

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
