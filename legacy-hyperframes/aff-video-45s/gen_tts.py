import asyncio
import json
import sys
from pathlib import Path

import edge_tts

VOICE = "vi-VN-HoaiMyNeural"
BASE = Path(__file__).parent
SCRIPT = BASE / "script.txt"
AUDIO_DIR = BASE / "audio"
AUDIO_DIR.mkdir(exist_ok=True)


async def synth_line(i: int, text: str) -> dict:
    out_path = AUDIO_DIR / f"line_{i:02d}.mp3"
    communicate = edge_tts.Communicate(text, VOICE, rate="+12%", boundary="WordBoundary")
    words = []
    with open(out_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append(
                    {
                        "text": chunk["text"],
                        "offset": chunk["offset"] / 10_000_000,
                        "duration": chunk["duration"] / 10_000_000,
                    }
                )
    return {"index": i, "text": text, "file": out_path.name, "words": words}


async def main():
    lines = [l.strip() for l in SCRIPT.read_text(encoding="utf-8").splitlines() if l.strip()]
    results = []
    for i, text in enumerate(lines):
        for attempt in range(8):
            try:
                result = await synth_line(i, text)
                break
            except Exception as e:
                print(f"  retry {i} attempt {attempt}: {e}", file=sys.stderr)
                await asyncio.sleep(3 * (attempt + 1))
        else:
            raise RuntimeError(f"failed to synth line {i}")
        results.append(result)
        print(f"[{i}] {text[:40]}... -> {result['file']} ({len(result['words'])} words)", file=sys.stderr)
        await asyncio.sleep(2.5)
    (BASE / "tts_manifest.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Done. Manifest written to tts_manifest.json", file=sys.stderr)


asyncio.run(main())
