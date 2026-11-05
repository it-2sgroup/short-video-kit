#!/usr/bin/env python3
"""Synthesize a voiceover with ElevenLabs, one audio file per script line.

Keeping lines as separate files is deliberate: a plan changes line by line, and re-synthesizing
one line is cheap while re-synthesizing a whole take is not. The concatenation step inserts the
inter-line pauses, so pacing can be tuned without spending API calls.

Requires ELEVENLABS_API_KEY. It is looked up in the environment, then --env-file, then
~/.config/short-video-kit/env. Never pass the key on the command line: it lands in shell
history and in process listings.

Usage:
    python make_voiceover.py --quota                     # plan, credits left, reset date
    python make_voiceover.py --list-voices               # voice_id, category, language
    python make_voiceover.py script.txt --voice <id> --dry-run   # cost check, spends nothing
    python make_voiceover.py script.txt --voice <id> --out audio/
"""

from __future__ import annotations

import argparse
import datetime
import json
import math
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.elevenlabs.io/v1"

# Chosen by asking the API, not by assumption. GET /v1/models reports a `languages` list per
# model, and eleven_multilingual_v2 -- the obvious default, and the one these docs originally
# named -- has 29 languages and NO Vietnamese. Models that do list `vi`: eleven_v4,
# eleven_v4_turbo, eleven_v3, eleven_turbo_v2_5, eleven_flash_v2_5. eleven_turbo_v2_5 was also
# confirmed to accept stability/similarity/speed settings and to work on the free plan.
DEFAULT_MODEL = "eleven_turbo_v2_5"

# Audio tags such as [excited] or [laughs softly] are interpreted by the v3 family. Every other
# model reads them aloud as words, so they must be stripped before synthesis for those.
# v4 tag support is not confirmed here; pass --keep-tags to send them to a v4 model.
TAG_MODELS = {"eleven_v3", "eleven_v3_conversational"}

# Observed: v3/v4 charged 1 credit per character; turbo/flash are documented at half that.
# This is an estimate used only for the pre-flight check.
CREDITS_PER_CHAR = {"eleven_turbo_v2_5": 0.5, "eleven_flash_v2_5": 0.5}

GAP = 0.22          # seconds of silence between lines
INTRO_PAD = 0.6     # lead-in before the first word
KEY_HOME = Path.home() / ".config" / "short-video-kit" / "env"
TAG_RE = re.compile(r"\[[^\]]*\]\s*")


class ApiError(RuntimeError):
    def __init__(self, code: int, path: str, detail: str):
        super().__init__(f"HTTP {code} on {path}: {detail}")
        self.code, self.path, self.detail = code, path, detail


def _read_key(path: Path) -> str:
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("ELEVENLABS_API_KEY"):
            return line.split("=", 1)[1].strip().strip("'\"")
    return ""


def load_key(env_file: Path | None) -> str:
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not key and env_file:
        key = _read_key(env_file)
    if not key:
        key = _read_key(KEY_HOME)
    if not key:
        sys.exit(
            "ELEVENLABS_API_KEY not found. Export it, put it in ~/.config/short-video-kit/env, "
            "or pass --env-file. Do not pass the key as a command-line argument."
        )
    return key


def api(path: str, key: str, body: dict | None = None, raw: bool = False):
    req = urllib.request.Request(
        f"{API}{path}",
        data=json.dumps(body).encode() if body else None,
        headers={"xi-api-key": key, "Content-Type": "application/json"},
        method="POST" if body else "GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.read() if raw else json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise ApiError(e.code, path, e.read().decode(errors="replace")[:300]) from None


def subscription(key: str) -> dict | None:
    """Plan and credit balance, or None if the key cannot read it (restricted keys)."""
    try:
        return api("/user/subscription", key)
    except ApiError as e:
        if "invalid_api_key" in e.detail:
            raise            # a rejected key is an error, not "could not read the plan"
        return None          # e.g. the key lacks user_read: cannot tell, so say nothing
    except urllib.error.URLError:
        return None


def show_quota(key: str) -> bool:
    """Print plan and credits. Returns False when the plan could not be read, so the caller
    does not report an unverified key as a working one."""
    sub = subscription(key)
    if not sub:
        print("Could not read the subscription (offline, or the key lacks user_read). "
              "The key is NOT verified.")
        return False
    used, limit = sub.get("character_count", 0), sub.get("character_limit", 0)
    print(f"plan      : {sub.get('tier')}")
    print(f"credits   : {limit - used} left of {limit}")
    ts = sub.get("next_character_count_reset_unix")
    if ts:
        print(f"resets    : {datetime.datetime.fromtimestamp(ts):%Y-%m-%d %H:%M}")
    if sub.get("tier") == "free":
        print("\nFree plan: ElevenLabs states it 'does not include a commercial license and "
              "cannot be used for any commercial purpose'. Audio made outside a paid "
              "subscription stays non-commercial even after upgrading.")
    return True


def list_voices(key: str) -> None:
    voices = api("/voices", key).get("voices", [])
    print(f"{'voice_id':<24}{'category':<14}{'lang':<6}name")
    print("-" * 84)
    for v in voices:
        lab = v.get("labels") or {}
        print(f"{v['voice_id']:<24}{v.get('category','?'):<14}{lab.get('language','?'):<6}"
              f"{v.get('name','?')[:40]}")
    print("\nFree plans can only use 'premade' voices through the API; 'professional' and "
          "other library voices return HTTP 402.")


def spoken_text(line: str, model: str, keep_tags: bool) -> str:
    if keep_tags or model in TAG_MODELS:
        return line.strip()
    return re.sub(r"\s{2,}", " ", TAG_RE.sub("", line)).strip()


def synth(text: str, voice: str, key: str, model: str, out: Path,
          stability: float, similarity: float, speed: float) -> None:
    body = {
        "text": text,
        "model_id": model,
        "voice_settings": {"stability": stability, "similarity_boost": similarity, "speed": speed},
    }
    audio = api(f"/text-to-speech/{voice}?output_format=mp3_44100_128", key, body, raw=True)
    out.write_bytes(audio)


def concat(files: list[Path], out: Path, gap: float, intro: float) -> float:
    tmp = out.parent / "_silence.mp3"
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                    "-t", str(gap), str(tmp)], check=True, capture_output=True)
    intro_f = out.parent / "_intro.mp3"
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                    "-t", str(intro), str(intro_f)], check=True, capture_output=True)
    parts = [intro_f]
    for i, f in enumerate(files):
        parts.append(f)
        if i < len(files) - 1:
            parts.append(tmp)
    listing = out.parent / "_concat.txt"
    listing.write_text("\n".join(f"file '{p.resolve()}'" for p in parts), encoding="utf-8")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-ar", "44100", "-ac", "1", str(out)], check=True, capture_output=True)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=noprint_wrappers=1:nokey=1", str(out)],
                         capture_output=True, text=True, check=True).stdout.strip()
    for f in (tmp, intro_f, listing):
        f.unlink(missing_ok=True)
    return float(dur)


def explain(e: ApiError) -> str:
    d = e.detail
    if e.code == 402 and "library voices" in d:
        return ("This voice is a library voice, and free plans cannot use those through the API. "
                "Pick a 'premade' voice (see --list-voices) or upgrade the plan.")
    if "quota_exceeded" in d:
        return "Out of credits. Run --quota to see the balance and reset date."
    if "invalid_api_key" in d:
        return "ElevenLabs says this API key is invalid. Re-enter it with ./setup.sh --set-key."
    if e.code == 401:
        return "The key was rejected. Check it is current and has text-to-speech permission."
    return str(e)


def main() -> int:
    ap = argparse.ArgumentParser(description="ElevenLabs voiceover, one file per script line.")
    ap.add_argument("script", nargs="?", type=Path, help="Text file, one line per VO line")
    ap.add_argument("--voice", help="ElevenLabs voice_id")
    ap.add_argument("--out", type=Path, default=Path("audio"))
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--env-file", type=Path, default=Path(".env.local"))
    ap.add_argument("--quota", action="store_true", help="Show plan and credits, then exit")
    ap.add_argument("--list-voices", action="store_true")
    ap.add_argument("--dry-run", action="store_true",
                    help="Check text and cost against your balance; synthesize nothing")
    ap.add_argument("--keep-tags", action="store_true",
                    help="Send [emotion] tags to a model not known to support them")
    ap.add_argument("--force", action="store_true", help="Proceed even if credits look short")
    ap.add_argument("--stability", type=float, default=0.45)
    ap.add_argument("--similarity", type=float, default=0.75)
    ap.add_argument("--speed", type=float, default=1.06)
    ap.add_argument("--gap", type=float, default=GAP)
    ap.add_argument("--intro", type=float, default=INTRO_PAD)
    args = ap.parse_args()

    key = load_key(args.env_file)

    try:
        if args.quota:
            return 0 if show_quota(key) else 3
        if args.list_voices:
            list_voices(key)
            return 0
    except ApiError as e:
        sys.exit(explain(e))

    if not args.script or not args.voice:
        sys.exit("Need a script file and --voice. Run --list-voices to find a voice_id.")
    if not args.script.exists():
        sys.exit(f"Script not found: {args.script}")

    raw_lines = [l.strip() for l in args.script.read_text(encoding="utf-8").splitlines() if l.strip()]
    texts = [spoken_text(l, args.model, args.keep_tags) for l in raw_lines]
    texts = [t for t in texts if t]
    if not texts:
        sys.exit("Script is empty after removing tags.")
    if any(a != b for a, b in zip(raw_lines, texts)):
        print(f"Note: [tags] stripped, because {args.model} would read them aloud. "
              "Use eleven_v3 for emotion tags.", file=sys.stderr)

    chars = sum(len(t) for t in texts)
    est = math.ceil(chars * CREDITS_PER_CHAR.get(args.model, 1.0))
    print(f"{len(texts)} line(s), {chars} characters, ~{est} credits on {args.model}", file=sys.stderr)

    try:
        sub = subscription(key)
    except ApiError as e:
        sys.exit(explain(e))
    tier = sub.get("tier") if sub else None
    if sub:
        left = sub.get("character_limit", 0) - sub.get("character_count", 0)
        print(f"Plan '{tier}', {left} credits left", file=sys.stderr)
        if tier == "free":
            print("! Free plan: ElevenLabs does not license this audio for commercial use. "
                  "Fine for drafts; not for a monetised or client video.", file=sys.stderr)
        if est > left and not args.force:
            sys.exit(f"Not enough credits: need ~{est}, have {left}. Nothing was synthesized, so "
                     "nothing was spent. Run --quota for the reset date, or use --force.")
    else:
        print("! Could not read the balance, so credits are unchecked.", file=sys.stderr)

    if args.dry_run:
        print("Dry run: nothing synthesized.", file=sys.stderr)
        return 0

    args.out.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    for i, text in enumerate(texts):
        dest = args.out / f"line_{i:02d}.mp3"
        for attempt in range(4):
            try:
                synth(text, args.voice, key, args.model, dest,
                      args.stability, args.similarity, args.speed)
                break
            except ApiError as e:
                # Only rate limits and server faults are worth retrying; anything else repeats.
                if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                    time.sleep(2 * (attempt + 1))
                    continue
                sys.exit(f"Line {i} failed: {explain(e)}")
        print(f"[{i:02d}] {text[:52]}... -> {dest.name}", file=sys.stderr)
        files.append(dest)

    full = args.out / "voice_full.mp3"
    total = concat(files, full, args.gap, args.intro)
    (args.out / "voice_manifest.json").write_text(json.dumps({
        "voice_id": args.voice, "model": args.model, "speed": args.speed, "plan": tier,
        "gap_s": args.gap, "intro_pad_s": args.intro, "total_duration_s": round(total, 2),
        "lines": [{"index": i, "sent": t, "file": f.name} for i, (t, f) in enumerate(zip(texts, files))],
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{full}  —  {total:.1f}s across {len(files)} line(s)", file=sys.stderr)
    if total > 45:
        print(f"! {total:.0f}s exceeds the 45s ceiling. Cut script lines or raise --speed.",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
