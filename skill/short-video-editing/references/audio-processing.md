# Audio processing — noise, voice chain, loudness (`process_audio.py`)

Every number here was measured on ffmpeg 7.0 with synthetic test audio (speech-like tones, pink and
white noise, 50 Hz hum) during the 2026-11 research; nobody listened. They are starting points the
script implements, not laws. **[M]** measured, **[O]** official, **[C]** craft convention.

---

## What the script decides

```bash
python scripts/process_audio.py measure voice.mp3          # loudness, true peak, noise floor, speech level
python scripts/process_audio.py voice voice.mp3 --out public/audio/v1.wav
python scripts/process_audio.py music track.mp3 --out public/audio/music.wav
python scripts/process_audio.py master out/v1.mp4 --out out/v1_final.mp4 --phone
```

**Measuring** [M]. The noise floor is the 5th percentile of 100 ms RMS windows (−41.2 dBFS against a
true −40.8 on steady noise); the speech level is the 90th percentile. The 10th percentile was tried first
and failed on a TTS line with few pauses: it landed on the edge of a word (−47 dB) instead of the
near-digital silence of the pauses (−90 dB), so the script "cleaned" a clean file and raised its floor
to −31 dB. ffmpeg's `astats` "Noise_floor" reads about 6 dB high: do not feed it to `afftdn`. The
distance between floor and speech decides the cleaning:

| Speech above the noise | Action |
|---|---|
| ≥ 35 dB | No noise reduction: it would only cost clarity |
| 20–35 dB | `afftdn` (nr 15) with a **noise print** from the longest stretch of pure room noise |
| < 20 dB | The same at nr 25, and a warning: re-record, or use `arnndn` with a model (below) |

**Voice chain** (order matters): high-pass 80 Hz → noise print + `afftdn` → EQ (250 Hz −2 dB, 3.5 kHz +3 dB)
→ `deesser=i=0.3:m=0.6` → `acompressor` 3:1, threshold 8 dB under the voice's loud parts, attack 10 ms,
release 150 ms, knee 6 → a gentle expander (`agate`, ratio 2, at most −10 dB, threshold 15 dB over the
floor) → level to −16 LUFS → true-peak-safe limiter. A fixed −24 dB threshold took 10 dB off a hot voice
and the level step then lifted its room noise by the same amount; the threshold now follows the voice
(3–5 dB of reduction) and the expander gives the pauses back what compression took [M].

Results of the kit's own runs [M]: steady-noise voice, speech-to-floor 27.9 → 43.5 dB; clean TTS line
untouched (76 → 75 dB, no noise reduction); loud synthetic speech over faint noise 46 → 47 dB.

**Music**: levelled to −14 LUFS so the bed numbers in `project.json` mean the same for every track.

**Master**: the rendered mix to −14 LUFS integrated, true peak ≤ −1 dBTP (common practice; neither TikTok
nor Instagram publishes a target [O]), picture copied, AAC 192 kb/s 48 kHz, `+faststart`; `--phone` adds a
CRF 24 copy for phones (files over ~30 MB fail in phone and web viewers).

---

## Results of the research runs [M]

- Noise print (`asendcmd=c='0.1 afftdn sn start; 0.9 afftdn sn stop',afftdn=nr=15:nf=-41`): noise in
  pauses −40.8 → −55.4 dBFS, speech-to-error 24.7 → 30.5 dB, 50 Hz hum −15 dB. Improvement stopped
  at nr 20–25.
- Blind `afftdn` on pink room noise removed 0.5 dB; `tn=1` made white noise worse; `anlmdn` was 13×
  slower and weaker; `agate` only lowers the pauses.
- `speechnorm` overshot to +1.0 dBTP: not used.

## Traps the script avoids [M]

| Trap | What happens | The fix in `process_audio.py` |
|---|---|---|
| `afftdn` latency | the voice comes out 25 ms late (44.1 and 48 kHz), same length: captions and cuts drift | `atrim=start=0.025,asetpts=PTS-STARTPTS,apad=pad_dur=0.025` after it |
| `anlmdn` latency | ~8 ms late | not used |
| `alimiter` defaults | `level=true` adds make-up gain (−14.7 → −13.2 LUFS, +1.4 dBTP); 5 ms delay | `level=false:latency=true` |
| sample vs true peak | `alimiter` limits samples: a −1.5 dBFS ceiling still gave −0.1 dBTP | limiter at 192 kHz, then back to 48 kHz (gave −1.1 dBTP) |
| `loudnorm` | outputs 192 kHz; `linear=true` silently falls back to dynamic mode when the peak would clip (−14.64 LUFS, −0.6 dBTP) | used only to measure; gain + limiter instead, a second pass corrects the shortfall |
| `deesser` | does nothing at its default `i=0`; `m` is a gain floor (higher m = less de-essing) | `i=0.3:m=0.6` |
| sidechain ducking | a threshold within 10 dB of the voice's noise floor keeps the music ducked in pauses | the kit ducks from word timings in Remotion instead |
| `afftdn` on a clean file | a TTS line with digital-silence pauses came out with a floor of −31 dB | no noise reduction when speech is ≥ 35 dB over the floor measured on the pauses |

## RNNoise (`arnndn`) — only when the user installs a model

For noise that is not steady (traffic, crowd, wind) or speech under 20 dB above the noise, ffmpeg's
`arnndn` filter needs an RNNoise model file. Source: GregorR/rnnoise-models (README: "not subject to
copyright"; no formal licence); ready-made ffmpeg files in richardpl/arnndn-models (archived), e.g.
`sh.rnnn` (speech, 297,646 bytes). The kit ships none: **ask before downloading**, then run
`ffmpeg -i in.wav -af "highpass=f=80,arnndn=m=sh.rnnn" out.wav` and pass the result to
`process_audio.py voice --denoise off`.

## Rules

- Clean the voice **before** aligning captions: alignment then matches what is heard.
- The jump-cut voice of a talking head (`trim_voice.py --jumpcut`) is cleaned after cutting, so the
  noise print comes from the room, not from a removed pause.
- Never re-clean a TTS voice; use `--no-clean` (level only).
- A tool cannot hear: say "not listened to" in the report unless someone listened end to end.
