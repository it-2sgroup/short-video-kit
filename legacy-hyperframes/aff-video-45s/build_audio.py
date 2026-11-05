import json
import subprocess
from pathlib import Path

BASE = Path(__file__).parent
AUDIO_DIR = BASE / "audio"
ASSETS_AUDIO = BASE / "assets" / "audio"
GAP = 0.22
INTRO_PAD = 0.6
END_PAD = 2.0

manifest = json.loads((BASE / "tts_manifest.json").read_text(encoding="utf-8"))

# Build concat list with silence between lines, and compute absolute offsets.
concat_lines = []
captions = []
cursor = INTRO_PAD

silence_path = ASSETS_AUDIO / "silence_gap.mp3"
subprocess.run(
    ["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono", "-t", str(GAP), str(silence_path)],
    check=True, capture_output=True,
)
intro_silence_path = ASSETS_AUDIO / "silence_intro.mp3"
subprocess.run(
    ["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono", "-t", str(INTRO_PAD), str(intro_silence_path)],
    check=True, capture_output=True,
)

concat_lines.append(f"file '{intro_silence_path.resolve()}'")

for entry in manifest:
    line_path = (AUDIO_DIR / entry["file"]).resolve()
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(line_path)],
        capture_output=True, text=True, check=True,
    )
    dur = float(out.stdout.strip())

    words = entry["words"]
    # group words into caption chunks of ~4-5 words for readable burned captions
    chunk_size = 4
    for i in range(0, len(words), chunk_size):
        chunk = words[i : i + chunk_size]
        start = cursor + chunk[0]["offset"]
        end = cursor + chunk[-1]["offset"] + chunk[-1]["duration"]
        text = " ".join(w["text"] for w in chunk)
        captions.append({"start": round(start, 3), "end": round(end, 3), "text": text})

    concat_lines.append(f"file '{line_path}'")
    cursor += dur
    if entry is not manifest[-1]:
        concat_lines.append(f"file '{silence_path.resolve()}'")
        cursor += GAP

voice_end = cursor
total_duration = voice_end + END_PAD

concat_file = ASSETS_AUDIO / "concat_list.txt"
concat_file.write_text("\n".join(concat_lines), encoding="utf-8")

voice_track = ASSETS_AUDIO / "voice_full.mp3"
subprocess.run(
    ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-ar", "44100", "-ac", "1", str(voice_track)],
    check=True, capture_output=True,
)

(BASE / "captions.json").write_text(
    json.dumps({"captions": captions, "voice_end": round(voice_end, 3), "total_duration": round(total_duration, 3)}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print("voice_end:", round(voice_end, 3))
print("total_duration:", round(total_duration, 3))
print("captions:", len(captions))
