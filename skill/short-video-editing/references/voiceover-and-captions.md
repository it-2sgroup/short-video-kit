# Voiceover and Captions

The pipeline is: **script → ElevenLabs → audio → Whisper → timings → SRT**, with one rule that
makes the whole thing work — **Whisper supplies the timing, the script supplies the words.**

---

## Why not just use Whisper's transcript

Running Whisper over this project's own Vietnamese voiceover produced:

| Spoken | Whisper heard |
|---|---|
| mua **túi xách** | mua *tui sách* |
| thấy **kiểu dáng** | thấy *kiểu gián* |

Both are plausible-looking Vietnamese. Neither is what was said. In a transcript that is a minor
annoyance; burned onto a video at 44px it is the first thing a viewer notices, and it makes the
brand look careless.

The fix is structural rather than a better model: **we already know the exact words**, because we
wrote them and sent them to the TTS. So the script is the source of truth for text, and Whisper is
used only to find out *when* each word was spoken. `scripts/align_captions.py` does this — it
matches Whisper's word sequence against the script's word sequence and keeps the script's
spelling.

Matching is done on diacritic-stripped, lowercased skeletons, because that is exactly where
Vietnamese recognition errors cluster (`dang`/`gian`, `xach`/`sach`). A misheard word still aligns
to the right position; only its spelling is replaced.

---

## 1. Write the script to a word budget

Commerce pace runs about 4.5–5 words per second. A 35-second video supports roughly **150–170
words** including pauses. Write to the budget rather than trimming after synthesis — re-cutting
audio to fit is slower and sounds worse than writing shorter in the first place.

One line per VO line, one line per file:

```
Ủa, mọi người ơi! Có ai giống mình không?
Nhưng mà lần này... mình phải nói thật là chiếc túi này khiến mình bất ngờ luôn!
```

Check every line against the rewrite table in `claims-and-compliance.md` §2 before synthesizing. Fixing
a prohibited claim after the voiceover exists means paying for the synthesis twice.

---

## 2. Synthesize with ElevenLabs

```bash
python scripts/make_voiceover.py --quota                          # plan, credits, reset date
python scripts/make_voiceover.py --list-voices                    # id, category, language
python scripts/make_voiceover.py script.txt --voice <id> --dry-run   # cost check, spends nothing
python scripts/make_voiceover.py script.txt --voice <id> --out audio/
```

Key lookup order: environment variable, `--env-file`, then `~/.config/short-video-kit/env`
(`setup.sh` installs the last one so it works from any folder). **Never put the key on the command
line** — it lands in shell history and in process listings.

### Two things that will bite if ignored

**1. Pick a model that actually speaks Vietnamese.** `eleven_multilingual_v2` — the obvious
default, and what an earlier draft of this file recommended — lists 29 languages and **not
Vietnamese**. Checked against `GET /v1/models`:

| Model | Vietnamese | Notes |
|---|---|---|
| `eleven_turbo_v2_5` | yes | **Default.** Verified: accepts stability/similarity/speed, works on the free plan. ~0.5 credit/char |
| `eleven_flash_v2_5` | yes | Faster/cheaper; quality not compared |
| `eleven_v3` | yes | Interprets `[emotion]` audio tags. 1 credit/char. Stability is coarse on this family — not verified here |
| `eleven_v4`, `eleven_v4_turbo` | yes | Newest; not tested here (no credits left at the time) |
| `eleven_multilingual_v2`, `eleven_turbo_v2`, `eleven_flash_v2` | **no** | Do not use for Vietnamese |

Re-check with `GET /v1/models` when this matters — the list changes. Look for `vi` in each model's
`languages`.

**2. The free plan cannot be used commercially.** ElevenLabs' own help article states: *"The free
plan does not include a commercial license and cannot be used for any commercial purpose."* Audio
made outside a paid subscription *"(before or after) cannot be used commercially"* — upgrading later
does not retroactively license it. Free-plan audio is fine for drafts and timing tests; an
affiliate or client video needs audio generated **during a paid subscription**. `make_voiceover.py`
prints this warning whenever it sees a free-tier key.

Also on the free plan: **only `premade` voices work through the API.** Library voices (including
the professional Vietnamese voice in this account) return HTTP 402. `--list-voices` shows each
voice's category.

### Emotion tags

Scripts written for the Adam workflow carry tags like `[gasp][excited]` and `[laughs softly]`.
Only the **v3 family interprets them**; every other model reads them out loud as words. So
`make_voiceover.py` strips them for non-v3 models and says so, and `align_captions.py` always
strips them from caption text, since a tag directs the voice but is never spoken. Use
`--keep-tags` only for a model known to support them.

### Spending credits safely

`--dry-run` prices the script against your balance and refuses to start if it cannot finish —
otherwise a run that dies on line 7 of 9 has spent credits on a take you cannot use. A 35-second
script is about 750 characters: roughly 380 credits on turbo, 750 on v3.

One file per line is deliberate: re-synthesizing one line is cheap, a whole take is not. The
concatenation step inserts the pauses, so pacing is tuned without another API call.

Settings worth understanding rather than copying:
- `--stability` (0.45) — lower is more expressive and varies between runs; higher is flatter and
  more consistent.
- `--speed` (1.06) — 1.0 often sounds flat for commerce. Past about 1.15 it sounds rushed, which
  undercuts the honest-neighbour register these videos rely on.
- `--gap` (0.22s) and `--intro` (0.6s) shape pacing.

`voice_manifest.json` records the voice, model, speed, plan and the exact text sent per line.

## 3. Align captions

```bash
python scripts/align_captions.py audio/voice_full.mp3 --script script.txt --out captions.srt
```

Options:
- `--model` — `small` is the default and handles clean TTS audio well (about 16s to process 50s of
  audio on CPU). Use `medium` for speech over music or noisy room tone.
- `--words` — words per caption group. Default 4; use 2–3 for high-energy cuts, 4–6 for calm ones.
- `--json` — print the groups instead of writing SRT, for checking the alignment.

The script reports how many words it heard against how many the script contains, and warns when
fewer than 60% of heard words appear in the script — which means either the wrong script was
passed, or recognition failed badly enough to distrust the timings.

Without `--script` it falls back to Whisper's raw text and says so. Only do that when transcribing
audio you did not generate, such as a creator's own recording — see "A supplied voice" below.

Caption groups get a minimum display of **0.5s + 0.3s per word**, so a four-word group holds at
least 1.7s. Groups are trimmed if they would overrun the next one.

Whisper sometimes stretches a word across a pause (it timed "Vừa" 0.5 s before the voice said it, and the
caption showed early). After aligning, `align_captions.py` measures the real silences (≥ 0.2 s at −35 dB) and
pulls any word that overlaps one back to the sound; it prints "Snapped N word edge(s)". The cuts the sync report
still flags inside a word are then usually a pause that Whisper's timing hides: check it with
`trim_voice.py --silences` before moving the cut.

---

## A supplied voice (a recording instead of synthesis)

When the client or creator hands over a recording, skip step 2 and work like this:

1. **Too long?** The ceiling is the playbook's `runtime.max` (`playbook.py show <id>`; 45 s for
   product demos). `python scripts/trim_voice.py voice.mp3 --silences` lists every pause with a
   midpoint to cut at; `--keep 0-3.8,8.3-16.1,... --out short.mp3` joins the ranges you keep. Cut
   between sentences only, drop whole sentences, and tell the user exactly which ones. A talking head
   recorded on camera is cut with `--jumpcut` instead (`playbooks/talking-head.md`).
2. **Clean and level it**: `python scripts/process_audio.py voice short.mp3 --out
   RENDER/public/audio/v1.wav` (noise print, presence, de-esser, compression, −16 LUFS;
   `audio-processing.md`). Align on the cleaned file: its timing is what the video plays.
3. **Draft transcript.** `align_captions.py short.mp3 --out draft.srt` (no `--script`) gives Whisper's
   text. It mishears Vietnamese and recordings rarely match the written script, so read the draft
   while listening to the sentences that look odd, and correct it by hand.
4. **Save the corrected text as `script.txt`** (one sentence per line, UTF-8) and align again with
   `--script script.txt --words-out words.json`. Now the spelling is yours and the timing is Whisper's.
5. **Scan the voice for claims** the on-screen text must not repeat (`claims-and-compliance.md` §2) and list
   them for the user; a recorded line cannot be silently changed.

Supplied voices are often fast (≈5 words/s): the aligner merges caption groups shorter than 0.45 s, and
the plan compiler still reports a few that remain — that is the voice, not an error.

---

## 4. Mix

There is no separate mixing step: the render mixes the voice, the ducked music bed and the sound
effects (`project.json`), and `process_audio.py master` levels the result to −14 LUFS, ≤ −1 dBTP.
Levels and licensing: `audio-and-music.md`. A synthesized voice is levelled with `process_audio.py
voice --no-clean` (no noise reduction on TTS).

ElevenLabs can also return character-level timestamps with the audio; Whisper alignment stays the
default because it keeps working after the audio is trimmed, re-paced or spliced with a recording.
