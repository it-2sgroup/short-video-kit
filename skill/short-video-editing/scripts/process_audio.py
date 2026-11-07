#!/usr/bin/env python3
"""Clean a voice, level a music track, and master the finished video's sound. ffmpeg only.

    python scripts/process_audio.py voice raw_voice.mp3 --out public/audio/v1.wav     # clean + level a voice
    python scripts/process_audio.py music track.mp3 --out public/audio/music.wav      # level a music bed
    python scripts/process_audio.py master out/v1.mp4 --out out/v1_final.mp4 [--phone] # loudness of the mix
    python scripts/process_audio.py measure anything.mp4                              # just the numbers

voice   Measures the noise floor (5th percentile of 100 ms RMS windows) and the speech level (90th
        percentile) and decides from their distance (speech-to-noise):
          >= 35 dB  no noise reduction (it would only cost clarity)
          20-35 dB  afftdn with a noise print taken from the quietest pause (silencedetect)
          <  20 dB  the same, stronger, and a warning: re-record, or use an RNNoise model (arnndn) the
                    user installs; the kit ships none
        then high-pass 80 Hz, a little less 250 Hz mud and more 3.5 kHz presence, de-esser, gentle
        compression (3:1), and the level: -16 LUFS integrated, true peak <= -1.5 dBTP. afftdn delays the
        sound by 25 ms; the chain removes that delay so captions and cuts stay in sync. --no-clean keeps
        only the level; --denoise on|off overrides the decision.
music   Levels a track to -14 LUFS (true peak -1.5 dBTP) so the bed level written into project.json
        (plan_to_project.py: -10 dB in pauses, -18 dB under speech) means the same for every track.
master  Levels the rendered mix to -14 LUFS integrated, true peak <= -1 dBTP (common practice: neither
        TikTok nor Instagram publishes a target; references/audio-processing.md), copies the picture,
        writes AAC 192 kb/s 48 kHz with +faststart. --phone also writes <out>_phone.mp4 (CRF 24) for
        sending to a phone (< ~30 MB).

Every mode prints the measurements before and after. A tool cannot hear: listen before delivering.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

VOICE_I, VOICE_TP = -16.0, -1.5
MUSIC_I, MUSIC_TP = -14.0, -1.5
MASTER_I, MASTER_TP = -14.0, -1.0
AFFTDN_DELAY = 0.025  # seconds afftdn shifts the audio (measured at 44.1 and 48 kHz)


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def loudness(path: Path, af: str = "") -> dict:
    """Integrated loudness (LUFS), true peak (dBTP) and loudness range (LU), via loudnorm's analysis."""
    chain = (af + "," if af else "") + "loudnorm=print_format=json"
    err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af", chain, "-f", "null", "-"]).stderr
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", err, re.S)
    if not m:
        sys.exit(f"could not measure {path}:\n{err[-600:]}")
    d = json.loads(m.group(0))
    return {"I": float(d["input_i"]), "TP": float(d["input_tp"]), "LRA": float(d["input_lra"])}


def windows(path: Path) -> list[float]:
    """RMS level (dBFS) of every 100 ms window."""
    af = ("aresample=48000,asetnsamples=n=4800,astats=metadata=1:reset=1,"
          "ametadata=mode=print:key=lavfi.astats.Overall.RMS_level:file=-")
    out = run(["ffmpeg", "-hide_banner", "-nostats", "-v", "error", "-i", str(path), "-vn", "-af", af, "-f", "null", "-"]).stdout
    vals = [float(v) for v in re.findall(r"RMS_level=(-?[\d.]+|-inf)", out) if v != "-inf"]
    return [v for v in vals if v > -120] or [-120.0]


def pct(vals: list[float], q: float) -> float:
    s = sorted(vals)
    return s[min(len(s) - 1, int(q * len(s)))]


def noise_print(levels: list[float], floor: float) -> tuple[float, float] | None:
    """The longest run (>= 0.3 s) of 100 ms windows within 6 dB of the floor, trimmed 50 ms each side:
    a stretch of pure room noise to teach afftdn what to remove."""
    best, run_start = None, None
    for i, v in enumerate(levels + [0.0]):
        if v <= floor + 6:
            run_start = i if run_start is None else run_start
            continue
        if run_start is not None and i - run_start >= 3 and (best is None or i - run_start > best[1] - best[0]):
            best = (run_start, i)
        run_start = None
    return (best[0] * 0.1 + 0.05, best[1] * 0.1 - 0.05) if best else None


def describe(tag: str, path: Path) -> dict:
    lv = windows(path)
    ld = loudness(path)
    floor, speech = pct(lv, 0.05), pct(lv, 0.90)  # 5th percentile: the pauses, even when a voice has few
    print(f"{tag:7} {ld['I']:6.1f} LUFS  TP {ld['TP']:5.1f} dBTP  LRA {ld['LRA']:4.1f} LU  "
          f"floor {floor:6.1f} dBFS  loud parts {speech:6.1f} dBFS  (distance {speech - floor:4.1f} dB)")
    return {**ld, "floor": floor, "speech": speech, "snr": speech - floor, "levels": lv}


def level(src: Path, out: Path, target_i: float, target_tp: float, pre: str = "") -> None:
    """Gain to the target, then a true-peak-safe limiter: alimiter limits sample peaks, so it runs at
    192 kHz (inter-sample peaks become samples) with level=false (no make-up gain) and latency=true
    (no delay). A second pass corrects what the limiter took off."""
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp) / "stage.wav"
        if pre:
            r = run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vn", "-af", pre, "-ar", "48000", "-c:a", "pcm_s24le", str(stage)])
            if r.returncode:
                sys.exit(r.stderr)
        else:
            stage = src
        gain = target_i - loudness(stage)["I"]
        limit = 10 ** ((target_tp - 0.5) / 20)  # 0.5 dB of margin for the encoder
        for _ in range(2):
            af = (f"volume={gain:.2f}dB,aresample=192000,alimiter=limit={limit:.4f}:level=false:latency=true:attack=2:release=60,"
                  "aresample=48000")
            codec = ["-c:a", "libmp3lame", "-q:a", "2"] if out.suffix.lower() == ".mp3" else ["-c:a", "pcm_s16le"]
            r = run(["ffmpeg", "-y", "-v", "error", "-i", str(stage), "-vn", "-af", af, "-ar", "48000", *codec, str(out)])
            if r.returncode:
                sys.exit(r.stderr)
            short = target_i - loudness(out)["I"]
            if abs(short) < 0.4:
                break
            gain += short


def voice_chain(path: Path, m: dict, denoise: str) -> tuple[str, list[str]]:
    notes, parts = [], ["highpass=f=80"]
    want = {"auto": m["snr"] < 35, "on": True, "off": False}[denoise]
    if want:
        nr = 15 if m["snr"] >= 20 else 25
        nf = max(-80.0, min(-20.0, m["floor"]))
        pr = noise_print(m["levels"], m["floor"])
        if pr:
            parts.append(f"asendcmd=c='{pr[0]:.2f} afftdn sn start; {pr[1]:.2f} afftdn sn stop'")
            notes.append(f"noise reduction: afftdn nr={nr} with a noise print from {pr[0]:.2f}-{pr[1]:.2f}s")
        else:
            notes.append(f"noise reduction: afftdn nr={nr} nf={nf:.0f} (no pause long enough for a noise print)")
        parts.append(f"afftdn=nr={nr}:nf={nf:.0f}")
        parts.append(f"atrim=start={AFFTDN_DELAY},asetpts=PTS-STARTPTS,apad=pad_dur={AFFTDN_DELAY}")
        if m["snr"] < 20:
            notes.append("speech is less than 20 dB above the noise: expect artefacts. Re-record if possible, or "
                         "install an RNNoise model and use arnndn (references/audio-processing.md)")
    else:
        notes.append("noise reduction: none (speech is far enough above the noise)" if denoise == "auto" else "noise reduction: off")
    # The compressor's threshold follows the voice: 8 dB under its loud parts, so loud words lose about
    # 3-5 dB whatever the recording level (a fixed -24 dB took 10 dB off a hot voice and lifted its noise).
    thr = max(-40.0, min(-10.0, m["speech"] - 8))
    parts += ["equalizer=f=250:t=q:w=1:g=-2", "equalizer=f=3500:t=q:w=1.2:g=3",
              "deesser=i=0.3:m=0.6", f"acompressor=threshold={thr:.1f}dB:ratio=3:attack=10:release=150:knee=6"]
    # Compression narrows the gap between speech and room noise (the level step then lifts both): a
    # gentle expander, at most -10 dB, only below 15 dB over the measured floor, gives the pauses back.
    gate = 10 ** ((m["floor"] - (12 if want else 0) + 15) / 20)
    parts.append(f"agate=threshold={min(0.5, gate):.5f}:ratio=2:range=0.316:attack=5:release=250:knee=4")
    notes.append("pauses: gentle expander (max -10 dB) after compression")
    return ",".join(parts), notes


def master(src: Path, out: Path, phone: bool) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "mix.wav"
        r = run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vn", "-ar", "48000", "-c:a", "pcm_s24le", str(wav)])
        if r.returncode:
            sys.exit(f"no audio track in {src}?\n{r.stderr}")
        leveled = Path(tmp) / "leveled.wav"
        level(wav, leveled, MASTER_I, MASTER_TP)
        r = run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-i", str(leveled), "-map", "0:v:0", "-map", "1:a:0",
                 "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", str(out)])
        if r.returncode:
            sys.exit(r.stderr)
    describe("after", out)
    if phone:
        small = out.with_name(out.stem + "_phone.mp4")
        run(["ffmpeg", "-y", "-v", "error", "-i", str(out), "-c:v", "libx264", "-crf", "24", "-preset", "medium",
             "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(small)])
        print(f"phone copy: {small} ({small.stat().st_size / 1e6:.1f} MB)")
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")


def main() -> int:
    ap = argparse.ArgumentParser(description="Clean a voice, level music, master a video's sound (ffmpeg).")
    sub = ap.add_subparsers(dest="mode", required=True)
    v = sub.add_parser("voice"); v.add_argument("src", type=Path); v.add_argument("--out", type=Path, required=True)
    v.add_argument("--denoise", choices=["auto", "on", "off"], default="auto")
    v.add_argument("--no-clean", action="store_true", help="only level it (TTS, studio recordings)")
    mu = sub.add_parser("music"); mu.add_argument("src", type=Path); mu.add_argument("--out", type=Path, required=True)
    ma = sub.add_parser("master"); ma.add_argument("src", type=Path); ma.add_argument("--out", type=Path, required=True)
    ma.add_argument("--phone", action="store_true", help="also write a CRF 24 copy for sending to a phone")
    me = sub.add_parser("measure"); me.add_argument("src", type=Path)
    a = ap.parse_args()
    if not a.src.is_file():
        sys.exit(f"not found: {a.src}")

    before = describe("before", a.src)
    if a.mode == "measure":
        return 0
    if a.out.resolve() == a.src.resolve():
        sys.exit("--out must be a new file")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    if a.mode == "voice":
        chain, notes = ("", ["level only (--no-clean)"]) if a.no_clean else voice_chain(a.src, before, a.denoise)
        for n in notes:
            print(f"  - {n}")
        level(a.src, a.out, VOICE_I, VOICE_TP, chain)
        describe("after", a.out)
    elif a.mode == "music":
        level(a.src, a.out, MUSIC_I, MUSIC_TP)
        describe("after", a.out)
    else:
        master(a.src, a.out, a.phone)
    print("Not listened to: play it before delivering.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
