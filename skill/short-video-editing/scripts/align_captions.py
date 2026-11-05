#!/usr/bin/env python3
"""Turn a voiceover into burned-in caption groups with accurate text and accurate timing.

Why this is not just "run Whisper and use its output": Whisper mishears. Transcribing a
Vietnamese voiceover of this project's own script produced "mua tui sach" for "mua tui xach"
and "kieu gian" for "kieu dang". Those errors are invisible in a transcript and glaring when
burned onto a video.

But we already know the exact words — we wrote them and sent them to the TTS. So Whisper is
used only for *when*, and the script supplies *what*. Whisper's word sequence is aligned to the
script's word sequence, and the script's spelling wins every time.

Usage:
    python align_captions.py voice_full.mp3 --script script.txt --out captions.srt
    python align_captions.py voice.mp3 --script script.txt --json      # inspect the alignment
    python align_captions.py voice.mp3                                 # no script: raw Whisper

Options worth knowing:
    --model     tiny|base|small|medium|large-v3   (default small; medium for speech over music)
    --words     words per caption group (default 4; use 2-3 for high energy)
    --lang      language code (default vi)

Requires: faster-whisper, ffmpeg on PATH.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

MIN_DISPLAY = 0.5      # a group must stay up at least this long
PER_WORD = 0.3         # plus this per word, so longer groups hold longer


@dataclass
class Word:
    text: str
    start: float
    end: float


KIT_PYTHON = Path.home() / ".local" / "share" / "short-video-kit" / "venv" / "bin" / "python"


def ensure_deps() -> None:
    """Re-run under the kit's virtualenv when faster-whisper is not importable here.

    Skill docs say `python scripts/align_captions.py`, which on a fresh machine means the system
    Python, which has no faster-whisper. Rather than make every caller remember a venv path, the
    script finds the one setup.sh created (or $SVK_PYTHON) and hands over to it.
    """
    try:
        import faster_whisper  # noqa: F401
        return
    except ImportError:
        pass
    # A venv's python is a symlink to the system python, so comparing resolved paths cannot tell
    # them apart. Guard against an exec loop with a marker instead of a path comparison.
    if not os.environ.get("SVK_REEXEC"):
        for candidate in (os.environ.get("SVK_PYTHON"), str(KIT_PYTHON)):
            if candidate and Path(candidate).exists():
                os.environ["SVK_REEXEC"] = "1"
                os.execv(candidate, [candidate] + sys.argv)
    sys.exit(
        "faster-whisper is not installed for this Python. Run the kit's setup.sh, or "
        "`pip install faster-whisper==1.2.1 numpy`."
    )


def decode(path: Path, sr: int = 16000):
    """Decode to mono float32 via ffmpeg.

    faster-whisper can read files itself, but that path goes through PyAV, whose API has
    drifted out of step with faster-whisper releases (metadata_errors was removed and breaks
    decoding outright). ffmpeg is already a hard dependency here and does not move under us.
    """
    import numpy as np
    out = subprocess.run(
        ["ffmpeg", "-nostdin", "-threads", "0", "-i", str(path),
         "-f", "s16le", "-ac", "1", "-acodec", "pcm_s16le", "-ar", str(sr), "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(out, np.int16).astype(np.float32) / 32768.0


def resolve_model(size: str) -> str:
    """Prefer a model already on disk over a download.

    Looked up in order: $WHISPER_MODEL_DIR, then ~/.cache/short-video-kit/models. Each is
    expected to hold a flat folder named faster-whisper-<size>/ containing model.bin. This lets
    a machine with no internet (or a slow one) run from a copied model, while a machine with
    neither falls through to faster-whisper's normal Hugging Face download.
    """
    candidates = []
    env = os.environ.get("WHISPER_MODEL_DIR")
    if env:
        candidates.append(Path(env) / f"faster-whisper-{size}")
    candidates.append(Path.home() / ".cache" / "short-video-kit" / "models" / f"faster-whisper-{size}")
    for c in candidates:
        if (c / "model.bin").exists():
            print(f"Using local model: {c}", file=sys.stderr)
            return str(c)
    return size


def transcribe(audio, model_size: str, lang: str) -> list[Word]:
    from faster_whisper import WhisperModel
    model = WhisperModel(resolve_model(model_size), device="cpu", compute_type="int8")
    segments, _ = model.transcribe(
        audio, language=lang, word_timestamps=True, vad_filter=True,
    )
    words: list[Word] = []
    for seg in segments:
        for w in seg.words or []:
            t = w.word.strip()
            if t:
                words.append(Word(t, round(w.start, 3), round(w.end, 3)))
    return words


def norm(s: str) -> str:
    """Fold to a comparable form: lowercase, no diacritics, letters and digits only.

    Diacritics are stripped because that is exactly where Whisper's Vietnamese errors cluster
    (dang/gian, xach/sach). Matching on the skeleton lets a misheard word still align to its
    true position, which is all we need — the script supplies the spelling.
    """
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", s)


def align(script_words: list[str], heard: list[Word]) -> list[Word]:
    """Give each script word a time, borrowed from the Whisper word it lines up with."""
    a = [norm(w) for w in script_words]
    b = [norm(w.text) for w in heard]
    out: list[Word | None] = [None] * len(script_words)

    for tag, i1, i2, j1, j2 in SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                h = heard[j1 + k]
                out[i1 + k] = Word(script_words[i1 + k], h.start, h.end)
        elif tag in ("replace", "delete"):
            # Script words with no confident match: spread them across whatever span the
            # heard side occupied, so they still land in roughly the right place.
            span = heard[j1:j2]
            if span:
                t0, t1 = span[0].start, span[-1].end
            elif j1 > 0:
                t0 = t1 = heard[j1 - 1].end
            elif heard:
                t0 = t1 = heard[0].start
            else:
                t0 = t1 = 0.0
            n = i2 - i1
            step = (t1 - t0) / n if n and t1 > t0 else 0.0
            for k in range(n):
                out[i1 + k] = Word(script_words[i1 + k], t0 + step * k,
                                   t0 + step * (k + 1) if step else t1)

    # Any still-unplaced word inherits from its neighbour rather than being dropped.
    last = 0.0
    for i, w in enumerate(out):
        if w is None:
            out[i] = Word(script_words[i], last, last)
        else:
            last = w.end
    return [w for w in out if w is not None]


def group(words: list[Word], per_group: int) -> list[tuple[float, float, str]]:
    """Chunk words into caption groups, breaking at sentence ends as well as the word limit."""
    groups: list[tuple[float, float, str]] = []
    buf: list[Word] = []

    def flush():
        if not buf:
            return
        text = " ".join(w.text for w in buf).strip()
        start, end = buf[0].start, buf[-1].end
        floor = MIN_DISPLAY + PER_WORD * len(buf)
        if end - start < floor:
            end = start + floor
        groups.append((start, end, text))
        buf.clear()

    for w in words:
        buf.append(w)
        ends_sentence = w.text.rstrip()[-1:] in ".!?…"
        if len(buf) >= per_group or ends_sentence:
            flush()
    flush()

    # Stop a group overrunning the next one's start.
    for i in range(len(groups) - 1):
        s, e, t = groups[i]
        nxt = groups[i + 1][0]
        if e > nxt:
            groups[i] = (s, max(s + 0.3, nxt - 0.02), t)
    return groups


def ts(sec: float) -> str:
    sec = max(0.0, sec)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Word-accurate captions from a voiceover.")
    ap.add_argument("audio", type=Path)
    ap.add_argument("--script", type=Path, help="The exact text that was synthesized")
    ap.add_argument("--out", type=Path, default=Path("captions.srt"))
    ap.add_argument("--model", default="small")
    ap.add_argument("--lang", default="vi")
    ap.add_argument("--words", type=int, default=4, help="Words per caption group")
    ap.add_argument("--json", action="store_true", help="Print groups as JSON instead of SRT")
    args = ap.parse_args()
    ensure_deps()

    if not args.audio.exists():
        sys.exit(f"Audio not found: {args.audio}")

    heard = transcribe(decode(args.audio), args.model, args.lang)
    if not heard:
        sys.exit("Whisper returned no words. Check the audio is not silent.")
    print(f"Whisper heard {len(heard)} word(s)", file=sys.stderr)

    if args.script:
        if not args.script.exists():
            sys.exit(f"Script not found: {args.script}")
        # Emotion/audio tags such as [excited] or [laughs softly] direct the TTS but are never
        # spoken, so they must not become caption words — or worse, throw the alignment off.
        script_text = re.sub(r"\[[^\]]*\]", " ", args.script.read_text(encoding="utf-8"))
        script_words = script_text.split()
        words = align(script_words, heard)
        matched = sum(1 for s, w in zip(script_words, words) if norm(s) == norm(w.text))
        print(f"Script has {len(script_words)} word(s); "
              f"{len(heard)} heard; alignment anchored on exact matches.", file=sys.stderr)
        rate = 100 * sum(1 for h in heard if norm(h.text) in {norm(s) for s in script_words}) / len(heard)
        if rate < 60:
            print(f"! Only {rate:.0f}% of heard words appear in the script. Either the script "
                  "does not match this audio, or recognition is poor — check before shipping.",
                  file=sys.stderr)
    else:
        words = heard
        print("! No --script given, so captions use Whisper's raw text, which contains "
              "recognition errors. Pass --script to use your own wording.", file=sys.stderr)

    groups = group(words, args.words)

    if args.json:
        print(json.dumps(
            [{"index": i + 1, "start": round(s, 3), "end": round(e, 3), "text": t}
             for i, (s, e, t) in enumerate(groups)],
            ensure_ascii=False, indent=2))
        return 0

    srt = "\n".join(
        f"{i+1}\n{ts(s)} --> {ts(e)}\n{t}\n"
        for i, (s, e, t) in enumerate(groups)
    )
    args.out.write_text(srt + "\n", encoding="utf-8")
    print(f"{args.out}  —  {len(groups)} caption group(s), "
          f"last ends at {groups[-1][1]:.1f}s", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
