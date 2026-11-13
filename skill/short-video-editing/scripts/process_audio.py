#!/usr/bin/env python3
"""Clean a voice, level a music track, and master the finished video's sound. ffmpeg only.

    python scripts/process_audio.py voice raw_voice.mp3 --out public/audio/v1.wav     # clean + level a voice
    python scripts/process_audio.py music track.mp3 --out public/audio/music.wav      # level a music bed
    python scripts/process_audio.py master out/v1.mp4 --out out/v1_final.mp4 [--phone] # loudness of the mix
    python scripts/process_audio.py measure anything.mp4                              # just the numbers
    python scripts/process_audio.py duck voice.wav music.wav --out mix.wav [--stem bed.wav]   # music under a voice (sidechain)
    python scripts/process_audio.py gap music.wav --at 12.40 --out music_gap.wav [--ms 120]   # silence before the drop

voice   Measures the noise floor (5th percentile of 100 ms RMS windows) and the speech level (90th
        percentile) and decides from their distance (speech-to-noise):
          >= 35 dB  no noise reduction (it would only cost clarity)
          20-35 dB  afftdn with a noise print taken from the quietest pause (silencedetect)
          <  20 dB  the same, stronger, and a warning: re-record, or use an RNNoise model (arnndn) the
                    user installs; the kit ships none
        then high-pass 80 Hz, a little less 250 Hz mud and more 3.5 kHz presence, de-esser, gentle
        compression (3:1), and the level: -16 LUFS integrated, true peak <= -1.5 dBTP. afftdn delays the
        sound by 25 ms; the chain removes that delay so captions and cuts stay in sync. --no-clean keeps
        only the level; --denoise on|off overrides the decision. --deess off|default|strong and --presence DB
        (gain at 3.5 kHz, with -2 dB at 250 Hz; 0 = none) tune those two steps; the defaults are the chain above.
music   Levels a track to -14 LUFS (true peak -1.5 dBTP) so the bed level written into project.json
        (plan_to_project.py: -10 dB in pauses, -18 dB under speech) means the same for every track.
duck    Mixes a music bed under a voice: the voice drives ffmpeg sidechaincompress on the music (ratio 8, attack 8 ms,
        release 350 ms), the threshold is LINEAR amplitude set from the MEASURED voice (its loud parts - 13 dB), the bed
        sits at --music-db (-10) in the pauses and drops by 8-12 dB while the voice speaks; amix normalize=0, so nothing is
        halved. --stem also writes the ducked bed alone (to measure the drop). The voice sets the length.
gap     Cuts a silence of --ms (default 120, range 80-150) out of a music track, ending ON --at seconds (the drop or hit),
        with --ramp ms (default 8, 5-10) fades inside the span so nothing clicks: the music is back at full level on --at.
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


DEESS = {"off": None, "default": "deesser=i=0.3:m=0.6", "strong": "deesser=i=0.6:m=0.8"}


def voice_chain(path: Path, m: dict, denoise: str, deess: str = "default", presence: float = 3.0) -> tuple[str, list[str]]:
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
    if presence > 0:
        parts += ["equalizer=f=250:t=q:w=1:g=-2", f"equalizer=f=3500:t=q:w=1.2:g={presence:g}"]
        notes.append(f"EQ: -2 dB at 250 Hz, +{presence:g} dB at 3.5 kHz")
    else:
        notes.append("EQ: none (--presence 0)")
    if DEESS[deess]:
        parts.append(DEESS[deess])
        notes.append(f"de-esser: {DEESS[deess]} ({deess})")
    else:
        notes.append("de-esser: off")
    parts.append(f"acompressor=threshold={thr:.1f}dB:ratio=3:attack=10:release=150:knee=6")
    # Compression narrows the gap between speech and room noise (the level step then lifts both): a
    # gentle expander, at most -10 dB, only below 15 dB over the measured floor, gives the pauses back.
    gate = 10 ** ((m["floor"] - (12 if want else 0) + 15) / 20)
    parts.append(f"agate=threshold={min(0.5, gate):.5f}:ratio=2:range=0.316:attack=5:release=250:knee=4")
    notes.append("pauses: gentle expander (max -10 dB) after compression")
    return ",".join(parts), notes


def stereo(path: Path) -> str:
    """To stereo without the default mono upmix, which lays a mono voice on both sides at -3 dB (measured): copy the channel instead."""
    n = run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=channels", "-of", "csv=p=0", str(path)]).stdout.strip()
    return "pan=stereo|c0=c0|c1=c0" if n == "1" else "aformat=channel_layouts=stereo"


DUCK_OVER_DB = 13.0   # threshold = loud parts of the voice minus this: ratio 8 then takes 11 dB off the bed at the loudest words


def duck_graph(thr_lin: float, ratio: float, attack: float, release: float, music_db: float, stem: bool = False,
               to_stereo: tuple[str, str] = ("aformat=channel_layouts=stereo", "aformat=channel_layouts=stereo")) -> str:
    """Voice [0] and music [1] to one mix. The voice is split: one copy is the trigger of sidechaincompress, which compresses the
    music; amix normalize=0 keeps every level as set (the 7.0 default halves them). `stem` also exposes the ducked bed alone as [m2]."""
    return (f"[0:a]{to_stereo[0]},aresample=48000,asplit=2[vo][sc];"
            f"[1:a]{to_stereo[1]},aresample=48000,volume={music_db:g}dB[bed];"
            f"[bed][sc]sidechaincompress=threshold={thr_lin:.5f}:ratio={ratio:g}:attack={attack:g}:release={release:g}[m];"
            + ("[m]asplit=2[m1][m2];" if stem else "[m]anull[m1];") + "[vo][m1]amix=inputs=2:duration=first:normalize=0[mix]")


def duck(voice: Path, music: Path, out: Path, stem: Path | None, ratio: float, attack: float, release: float, music_db: float,
         thr_db: float | None) -> None:
    v = describe("voice", voice)
    thr_db = thr_db if thr_db is not None else v["speech"] - DUCK_OVER_DB
    thr_lin = min(1.0, max(0.00098, 10 ** (thr_db / 20)))     # sidechaincompress accepts 0.00098-1 (linear)
    print(f"  - threshold {thr_db:.1f} dB = {thr_lin:.4f} linear (voice loud parts {v['speech']:.1f} dBFS - {DUCK_OVER_DB:g}), "
          f"ratio {ratio:g}, attack {attack:g} ms, release {release:g} ms, bed {music_db:g} dB in the pauses")
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(voice), "-i", str(music), "-filter_complex", duck_graph(thr_lin, ratio, attack, release, music_db, bool(stem), (stereo(voice), stereo(music))),
           "-map", "[mix]", "-ar", "48000", "-c:a", "pcm_s16le", str(out)]
    if stem:
        cmd += ["-map", "[m2]", "-ar", "48000", "-c:a", "pcm_s16le", str(stem)]
    r = run(cmd)
    if r.returncode:
        sys.exit(r.stderr[-600:])
    describe("mix", out)


def gap_expr(at: float, ms: float, ramp: float) -> str:
    """Gain over time: 1, a linear fall over `ramp` ms, silence, a linear rise that ends exactly on `at`, 1. All inside the span
    [at - ms, at], so the music is back at full level on the frame of the drop."""
    t0, r = at - ms / 1000, ramp / 1000
    return (f"if(lt(t,{t0:.4f}),1,if(lt(t,{t0 + r:.4f}),1-(t-{t0:.4f})/{r:.4f},if(lt(t,{at - r:.4f}),0,"
            f"if(lt(t,{at:.4f}),(t-{at - r:.4f})/{r:.4f},1))))")


def gap(src: Path, out: Path, at: float, ms: float, ramp: float) -> None:
    if not 80 <= ms <= 150:
        print(f"  ! a gap of {ms:g} ms is outside the 80-150 ms range editors use: shorter is not heard, longer reads as a dropout")
    if ramp * 2 >= ms or ramp < 1:
        sys.exit("--ramp must be at least 1 ms and less than half of --ms")
    if at * 1000 < ms:
        sys.exit("--at is earlier than the gap is long")
    e = gap_expr(at, ms, ramp)
    af = f"{stereo(src)},aresample=48000,aeval='val(0)*({e})|val(1)*({e})':c=stereo"
    r = run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vn", "-af", af, "-ar", "48000", "-c:a", "pcm_s16le", str(out)])
    if r.returncode:
        sys.exit(r.stderr[-600:])
    print(f"  - silence {at - ms / 1000:.3f}-{at:.3f} s ({ms:g} ms, {ramp:g} ms ramps inside it); the music is at full level on {at:.3f} s")


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
    v.add_argument("--deess", choices=list(DEESS), default="default", help="de-esser strength (default: the chain's own, i=0.3 m=0.6)")
    v.add_argument("--presence", type=float, default=3.0, help="dB at 3.5 kHz, with -2 dB at 250 Hz; 0 = no EQ (default 3; 2.5 is the usual starting point for a bright voice)")
    du = sub.add_parser("duck"); du.add_argument("src", type=Path, help="the voice"); du.add_argument("music", type=Path)
    du.add_argument("--out", type=Path, required=True); du.add_argument("--stem", type=Path, help="also write the ducked music alone")
    du.add_argument("--ratio", type=float, default=8.0); du.add_argument("--attack", type=float, default=8.0, help="ms")
    du.add_argument("--release", type=float, default=350.0, help="ms"); du.add_argument("--music-db", type=float, default=-10.0, help="bed level in the pauses")
    du.add_argument("--threshold-db", type=float, help="override: dBFS of the voice level at which the bed starts to drop (default: voice loud parts - 13)")
    ga = sub.add_parser("gap"); ga.add_argument("src", type=Path); ga.add_argument("--out", type=Path, required=True)
    ga.add_argument("--at", type=float, required=True, help="seconds: the drop / hit the silence ends on")
    ga.add_argument("--ms", type=float, default=120.0); ga.add_argument("--ramp", type=float, default=8.0, help="ms (default 8)")
    mu = sub.add_parser("music"); mu.add_argument("src", type=Path); mu.add_argument("--out", type=Path, required=True)
    ma = sub.add_parser("master"); ma.add_argument("src", type=Path); ma.add_argument("--out", type=Path, required=True)
    ma.add_argument("--phone", action="store_true", help="also write a CRF 24 copy for sending to a phone")
    me = sub.add_parser("measure"); me.add_argument("src", type=Path)
    a = ap.parse_args()
    if not a.src.is_file():
        sys.exit(f"not found: {a.src}")

    if a.mode == "gap":
        a.out.parent.mkdir(parents=True, exist_ok=True)
        gap(a.src, a.out, a.at, a.ms, a.ramp)
        return 0
    if a.mode == "duck":
        if not a.music.is_file():
            sys.exit(f"not found: {a.music}")
        a.out.parent.mkdir(parents=True, exist_ok=True)
        duck(a.src, a.music, a.out, a.stem, a.ratio, a.attack, a.release, a.music_db, a.threshold_db)
        print("Not listened to: play it before delivering.")
        return 0
    before = describe("before", a.src)
    if a.mode == "measure":
        return 0
    if a.out.resolve() == a.src.resolve():
        sys.exit("--out must be a new file")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    if a.mode == "voice":
        chain, notes = ("", ["level only (--no-clean)"]) if a.no_clean else voice_chain(a.src, before, a.denoise, a.deess, a.presence)
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
