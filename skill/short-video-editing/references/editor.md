# Video editor (browser timeline for `project.json`)

A small local web app to look at a render project and fix it by hand: move a title, shorten a scene, fix a typo in a
caption, then render again. Standard library Python on the server, plain JavaScript in the page, no packages, no network.

## Start

```
python skill/short-video-editing/scripts/editor.py RENDER_DIR [--project v1.json] [--port 5174] [--no-open]
```

It prints `http://127.0.0.1:PORT/` (the next free port is used when the one asked for is busy; `--port 0` picks any).
`RENDER_DIR` is the folder made by `new_remotion_project.py` (it holds `src/`, `public/`, `out/` and the project JSON
files). Without `--project` the newest project JSON is opened; the header lists the others. Stop with Ctrl+C.

## What is on screen

| Area | What it does |
|---|---|
| Header | Project name, badge **N changes not rendered** (changes against the project the last render saw), Undo / Redo, History, Save project, Re-render |
| Phone preview | Plays the newest `out/*.mp4`; with no render it plays the proxy clip of the current scene (voice and music follow). **Safe zone** draws the platform zones (TikTok feed, or Meta Reels ads when `layout` is `reels-ad`), **Face zone** the scene's `face` and camera `focus`, **Draft text** draws boxes for the overlays and captions at the playhead (on by default when edits are newer than the render) |
| Properties | Fields for the selected scene, overlay, caption or sound cue; nothing selected shows the project settings, quick checks and shortcuts. An overlay shows one field per `props` key, a box with the plan's `key=value; ...` notation (same rules as `plan_to_project.py`), and "Add property" |
| Timeline | Tracks Scenes, Text · graphics (stacked lanes when they overlap), Captions, Voice, Music (waveforms), Sound effects. Click the ruler to seek; drag to move, drag edges to resize; snaps to cuts, other edges and the playhead (hold Alt to switch it off); zoom slider, Alt+wheel, **Fit** |

Dragging the edge of a scene is a rolling edit: the neighbour follows and the right scene's `in` moves with the cut so the
footage stays in step (hold Shift to keep `in`). Dragging a scene's body reorders the scenes. **Split scene** (S) splits at
the playhead; Delete on a scene gives its time to the previous one. **+ Text** inserts a `title` at the playhead.

## Shortcuts

Space play/pause, ← → one frame (Shift: one second), Home/End, Delete, S split, Ctrl+Z / Ctrl+Y undo/redo, Ctrl+D duplicate,
Ctrl+S save, Esc deselect. Text fields keep their own shortcuts.

## What is saved where

- Edits live in the page (undo and redo are snapshots there) until **Save project**.
- Saving first copies the old file to `RENDER_DIR/.editor-history/<name>-<timestamp>.json` (the last 50 per project are
  kept) and then replaces the project file atomically. **History** lists them; restoring one also snapshots the current file.
  The file is rewritten with the same indentation; unknown keys (`words`, `punches`, ...) are kept untouched.
- A save is refused with a prompt when the file changed on disk since it was opened (for example `plan_to_project.py` ran again).
- **Re-render** saves, then runs `npx remotion render src/index.ts Short out/<name>.mp4 --props=<name>.json --codec=h264 --crf=18
  --concurrency=N` in `RENDER_DIR` (N = 5, or the core count when lower: Remotion refuses more workers than cores), one at a time,
  with a progress bar and log. It needs `node_modules` in `RENDER_DIR`; the editor never runs `npm install`. A copy of the project
  as rendered goes to `.editor-history/<name>.rendered.json` so the badge can count later edits.

## Limits

- The plan (`edit-plan.md`) is not updated: editing here changes `project.json` only. A later `plan_to_project.py` run overwrites
  these edits unless the plan is changed too; keep the footage ledger (the plan tables) in step by hand.
- The preview of overlays is a wireframe, not the real graphics; only a render shows the real look. Proxy playback ignores
  speed ramps (uses the mean speed), transitions and grading.
- Waveforms need `ffmpeg`; clip lengths in the pickers need `ffprobe`. Peaks are cached in the system temp folder.
- Only `public/` and `out/` are served; a symlink inside them that points outside is refused. The server binds `127.0.0.1`,
  accepts only its own Host and Origin, and runs nothing but the render command above.
- Not covered: the caption `words` track, `captionBands`, `punches` and `subject` have no editor UI (they are preserved as they are).
