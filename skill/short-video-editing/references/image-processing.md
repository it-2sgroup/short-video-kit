# Image processing — tone-mapping, white balance, exposure, grade, stabilisation, noise, lens, level

What happens to the picture before it reaches Remotion, and how the kit decides. Two tools:
`inspect_footage.py --measure` measures and recommends; `prepare_footage.py` applies the corrections and
the playbook's grade while making the proxies. **[M]** measured on ffmpeg 7.0 with test clips and a real
iPhone clip (4K HEVC 60 fps) during the 2026-11 work, **[D]** ffmpeg / vid.stab documentation,
**[C]** craft convention. The thresholds are heuristics: look at the contact sheet before trusting them.

---

## Order of operations (why this order)

| # | Step | Filter | Why here |
|---|---|---|---|
| 1 | Tone-map HDR | `zscale` → `tonemap=hable` → bt709 | everything after assumes SDR bt709; HLG/PQ graded as SDR looks grey and washed out |
| 2 | Frame | `scale … force_original_aspect_ratio=increase, crop` to 9:16 | every later filter works on the proxy's pixels, not 4K: 5–10× cheaper |
| 3 | Denoise | `hqdn3d` | before stabilisation and sharpening, which would otherwise move and sharpen the grain |
| 4 | Stabilise | `vidstabdetect` (pass 1) → `vidstabtransform` (pass 2) | on the framed picture so the transforms match; optimal zoom hides the borders |
| 5 | Lens | `lenscorrection=k1:k2` | geometry before levelling |
| 6 | Level | `rotate` + the zoom that hides the corners | straight horizons and verticals |
| 7 | Frame rate | `fps=30` or `60` | 60 kept from 50+ fps sources so 0.5x slow motion stays smooth |
| 8 | White balance | `colorchannelmixer` gains | corrections before the look |
| 9 | Exposure | `eq=gamma` | |
| 10 | Grade | the playbook's chain in `assets/grades.json` | one look over corrected material; steps 8–10 are baked into **one 3D LUT** (Hald CLUT 64³) and applied in a single RGB pass |
| 11 | Sharpen | `unsharp` (luma only, light) | last, after the downscale |

## 1. HDR footage

iPhones record HDR (HLG, `color_transfer=arib-std-b67`, `bt2020`) by default in many modes.
`inspect_footage.py` reports `hdr: true`; the proxy is tone-mapped with
`zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p`
[D: ffmpeg zscale/tonemap]. Measured on an HLG/BT.2020 10-bit HEVC copy of a real daylight clip [M]:

| Path | Mean luma | Saturation | Look |
|---|---|---|---|
| SDR original | 128 | 11.6 | reference |
| `mobius` (the kit) | 125 | 11.6 | matches |
| `reinhard` | 119 | 11.1 | slightly dark |
| `hable` (the common recipe online) | 90 | 7.7 | dark and dull |
| no tone-mapping (what Remotion shows from the original) | — | — | washed out, grey greens |

A tone-mapped HDR clip that still measures under 0.42 gets an exposure correction. Never render from
the HDR originals. The test clip was converted, not shot in HDR: check the first real HDR batch on the
contact sheet.

## 2. White balance [M]

- **Measured on neutral pixels only.** Plain grey-world averages every pixel, so a green plastic bowl
  read as a +0.10 green cast on a real clip. The kit averages only near-neutral pixels (low
  saturation, neither black nor clipped: walls, concrete, white cloth) of up to 8 keyframes. When they
  cover less than 5% of the frame (a colourful scene), it does not guess: no correction.
- **Decision**: a cast above 6% of grey (warm = (R−B)/grey, green = (G−(R+B)/2)/grey) is corrected.
- **Correction**: per-channel gains `(grey/channel)^k`, clamped to 0.85–1.18 and normalised to keep
  the brightness; `k` is the grade's `wbStrength` (0.35 for `warm-food`, where warm light is the
  look; 0.6–0.8 elsewhere). Never neutralise a sunset or a candle-lit room fully.
- `grayworld` (ffmpeg's LAB filter) was 23× slower than real time on a 2880-tall proxy and outputs
  float frames: not used.
- `colortemperature` lowers luma by ~8% unless `pl=1` (preserve lightness) [M]; the grades use `pl=1`.

## 3. Exposure [M]

Mean keyframe luma, as a share of the video range (16–235): below 0.33 too dark, above 0.72 too
bright. The gamma that moves it toward 0.45 (dark) or 0.62 (bright), clamped 0.75–1.5
(`eq=gamma>1` brightens: a 0.23 clip went from YAVG 66 to 88 at gamma 1.4). Highlights are not
clipped by a gamma; a clip that is already clipped cannot be rescued, say so.

## 4. Grades (`assets/grades.json`)

| Grade | Playbooks | Look |
|---|---|---|
| `natural` | product-demo, talking-head, tutorial | contrast 1.04, saturation 1.05, a little vibrance: nothing that could exaggerate a result |
| `bright-interior` | real-estate | lifted shadows and mids (curves), slightly warm (6000 K at 25%), clean whites |
| `warm-food` | food-fnb | warm (5400 K at 30%), contrast 1.06, saturation 1.1, highlights kept |
| `soft-skin` | fashion-beauty | gentle contrast, warm skin, protected highlights, fabric colours not pushed |
| `vivid` | montage-recap, promo-sale | firm S-curve, saturation 1.12, vibrance |

On a real daylight clip the grades moved mean luma by −3 to +12 and saturation by +1 to +7 (of 255):
visible but not loud [M]. A `.cube` LUT can become a grade (`"chain": "lut3d=file=…"`) when the user
owns it; most free LUT packs forbid redistribution, so none ships with the kit.

**Before/after is special**: with `correction: shared` (product-demo, tutorial, promo) one white balance
and one exposure are computed from all clips together and applied to every clip, so a BEFORE and an
AFTER are never corrected differently (`claims-and-compliance.md` §3).

## 5. Stabilisation [M, D]

- **Measured** with `vidstabdetect` on the first 12 s at 480 px wide: the median local-motion vector
  per frame gives `move` (the camera travels) and `jitter` (shake around a 9-frame average). Test clips:
  locked 0.4 px, slow pan 3.4/2.0, violently shaken 22.9/27.2; a real handheld-still iPhone clip 0.5/0.2.
- **Decision**: jitter above 4 px/frame → stabilise; move above 2.5 → `motion: high` (a walk, a pan):
  `plan_to_project.py --analysis` then holds the virtual camera still on that clip, because a virtual
  move on top of a real one reads as a wobble.
- **Correction**: two passes, `shakiness=6:accuracy=12`, then `smoothing=15:optzoom=1:zoomspeed=0.25:
  interpol=bicubic` (keeps intentional moves, zooms just enough to hide borders).
- **Trap**: an RGB filter (curves, colortemperature, vibrance) directly after `vidstabtransform`
  segfaults ffmpeg 7.0; a `scale=iw:ih` in between fixes it, and the script adds it.
- Not every build has libvidstab (Homebrew's ffmpeg may not): the scripts say so and skip.
  `deshake` is the fallback by hand. Rolling-shutter wobble is not fixed by either.

## 6. Noise [M]

- **Measured**: PSNR between frames (at 25/50/75% of the clip, 1080 px wide) and a lightly denoised
  copy (`hqdn3d=6:4:0:0`); the first frame `hqdn3d` sees is barely filtered, so it is skipped. A dark
  noisy test clip read 40.9 dB, clean ones 52–54. Fine texture lowers it too: a clean daylight clip of
  concrete read 43.6.
- **Decision**: denoise below 40 dB anywhere, or below 44 dB when the clip is dark (light < 0.38):
  grain shows in shadows, texture in daylight.
- **Correction**: `hqdn3d=2:1.5:3:2.25` (light) or `4:3:6:4.5` (very noisy). `nlmeans` and `bm3d` are
  higher quality and many times slower; use by hand for a hero shot.

## 7. Lens and level (by hand: `--fix`)

- Phones correct their lens distortion in camera, so there is no automatic lens step. For a GoPro or a
  0.5× clip that bows, `--fix "CLIP:lens=-0.12:0.03"` (k1, k2; negative k1 straightens barrel distortion).
- A tilted horizon or leaning door frames: `--fix "CLIP:rotate=-1.5"` (degrees, positive = clockwise
  in ffmpeg's `rotate`); the zoom `cos a + sin a × 16/9` hides the corners. Judge the angle on the
  contact sheet; property footage is worth it (verticals are what make rooms look straight).
- Strong converging verticals (camera tilted up at a building) need `perspective`, which the kit does
  not automate: reshoot level or accept them.

## 8. Commands

```bash
python scripts/inspect_footage.py CLIPS --measure --json analysis.json        # what each clip needs
python scripts/prepare_footage.py CLIPS render/public/clips --playbook real-estate --analysis analysis.json \
    --fix "IMG_0402:rotate=-1.2" --fix "IMG_0410:stabilize=off"
python scripts/contact_sheet.py render/public/clips --out proxies.png        # look at the result
```

`corrections.json` beside the proxies records what was applied to each clip (and the proxy fps that
`plan_to_project.py` checks slow motion against); quote it in the report.

**Speed** [M, 4-core laptop, 14 GB]: decoding 4K60 HEVC alone runs at ~4 s per second of footage.
A 2880-tall 30 fps proxy with white balance + grade took 45 s for 6 s of footage (1.1 GB RAM); applying
the same colour filters one by one took 113 s, which is why they are baked into one LUT (the pictures
differ by 46 dB PSNR: invisible). Stabilisation adds a detection pass; `--slowmo` (60 fps) roughly
doubles the encode. For drafts use `--proxy-height 1920`; run one heavy ffmpeg job at a time on small
machines (two 4K jobs together exhausted 14 GB and were killed).
