#!/usr/bin/env python3
"""Turn a Remotion render into the files you hand over: limited-range H.264, mastered sound, a copy without music, a phone copy, a cover.

    python scripts/finish_video.py render/out/video.mp4 --name SISMO_KB1 --out-dir render/out/final \
        [--audio-nomusic render/out/audio_nomusic.wav] [--cover-at 3.9] [--preview720]

What it does, in order:
  1. Remotion's JPEG frames come out as full-range `yuvj420p`; players and platforms expect limited range: re-encode the picture once
     (x264 crf 15, slow, BT.709 tags, +faststart). One generation of loss, invisible at crf 15.
  2. Mux the render's own soundtrack (voice + music + effects) -> NAME_music.mp4, and master it (`process_audio.py master`: -14 LUFS,
     true peak <= -1 dBTP, `--phone` copy: CRF 24, usually small enough for a chat; viewers cap at ~30 MB, so check the size it prints).
  3. With --audio-nomusic (a WAV rendered from the same project with `"music": null`, `npx remotion render ... out/x.wav --codec=wav`):
     the same picture with that sound -> NAME_nomusic.mp4, mastered the same way. A business account must take its music from the
     platform's own library, so the version without music is the one to upload.
  4. A cover frame (--cover-at seconds) and, with --preview720, a 720p copy under 30 MB that fits in a chat.
Nobody listens here: the report says what it measured, not what it sounds like.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(cmd: list[str], what: str) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"{what} failed:\n{r.stderr[-1200:]}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Turn a Remotion render into the delivery files.")
    ap.add_argument("render", type=Path, help="the Remotion mp4 (picture + the project's soundtrack)")
    ap.add_argument("--name", required=True, help="file name prefix, e.g. SISMO_KB1")
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--audio-nomusic", type=Path, help="WAV of the same project rendered without music")
    ap.add_argument("--cover-at", type=float, default=0.0, help="seconds of the cover frame (default: none)")
    ap.add_argument("--preview720", action="store_true", help="also write a 720p copy for chat (CRF 27)")
    ap.add_argument("--crf", type=int, default=15)
    a = ap.parse_args()

    a.out_dir.mkdir(parents=True, exist_ok=True)
    pic = a.out_dir / f"_{a.name}_picture.mp4"
    print("1/4 picture: full range -> limited range, BT.709 (a few minutes)")
    run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", str(a.render), "-an",
         "-vf", "scale=in_range=full:out_range=limited:flags=lanczos+accurate_rnd,format=yuv420p",
         "-c:v", "libx264", "-preset", "slow", "-crf", str(a.crf), "-color_range", "tv", "-colorspace", "bt709",
         "-color_primaries", "bt709", "-color_trc", "bt709", "-movflags", "+faststart", str(pic)], "picture re-encode")

    def make(tag: str, audio: list[str]) -> Path:
        pre = a.out_dir / f"_{a.name}_{tag}_pre.mp4"
        run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", str(pic), *audio, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
             "-c:a", "aac", "-b:a", "256k", "-shortest", str(pre)], f"mux {tag}")
        out = a.out_dir / f"{a.name}_{tag}.mp4"
        r = subprocess.run([sys.executable, str(HERE / "process_audio.py"), "master", str(pre), "--out", str(out), "--phone"], capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"mastering {tag} failed:\n{r.stderr[-800:]}")
        print("   " + "\n   ".join(l for l in r.stdout.splitlines() if l.startswith(("before", "after", "phone", "wrote"))))
        pre.unlink(missing_ok=True)
        return out

    print("2/4 with music (the render's own soundtrack)")
    main_mp4 = make("music", ["-i", str(a.render)])
    if a.audio_nomusic:
        print("3/4 without music")
        make("nomusic", ["-i", str(a.audio_nomusic)])
    else:
        print("3/4 without music: skipped (give --audio-nomusic)")
    print("4/4 cover and preview")
    if a.cover_at:
        run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-ss", str(a.cover_at), "-i", str(main_mp4), "-frames:v", "1", "-q:v", "2",
             str(a.out_dir / f"{a.name}_cover.jpg")], "cover")
    if a.preview720:
        run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", str(main_mp4), "-vf", "scale=720:1280:flags=lanczos", "-c:v", "libx264", "-preset", "slow",
             "-crf", "27", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(a.out_dir / f"{a.name}_music_preview720.mp4")], "preview")
    pic.unlink(missing_ok=True)
    print(f"done: {a.out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
