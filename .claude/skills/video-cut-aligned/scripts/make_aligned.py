#!/usr/bin/env python3
"""make_aligned.py — source video -> screen_aligned.json (word-level timestamps the
judged cutter reads).

Uses faster-whisper's OWN word timestamps (large-v3, literal). We deliberately do
NOT use MMS_FA forced alignment: MMS_FA force-fits a fixed word list onto the audio
and, when the speaker REPEATS a phrase (stutters/retakes — which is constant in this
footage), it takes the wrong DTW branch and SCRAMBLES the timestamps — it'll stretch
the clean take across the whole window (swallowing the stutter) and shove later words
seconds away. The result: the transcript text is right but the timestamp points at the
wrong audio, so a clip reads clean while playing the stutter. Whisper places words
sequentially as it hears them, so it doesn't scramble on repeats. Slightly coarser at
word edges (~50-100ms) but CORRECT — and the cut margins absorb the coarseness.
Correct-but-coarse beats precise-but-wrong.

Usage: python3 make_aligned.py SRC.mp4 OUTDIR
Writes OUTDIR/screen_aligned.json  (+ OUTDIR/_full16k.wav, OUTDIR/_transcript.txt)
"""
import json, sys, subprocess, os
from faster_whisper import WhisperModel

SRC = sys.argv[1]
OUTDIR = sys.argv[2]
os.makedirs(OUTDIR, exist_ok=True)
wav = os.path.join(OUTDIR, "_full16k.wav")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", SRC, "-vn", "-ac", "1", "-ar", "16000", wav], check=True)

print("transcribing (large-v3, literal, word-timestamps)…", flush=True)
m = WhisperModel("large-v3", device="cpu", compute_type="int8")
segs_it, _ = m.transcribe(wav, word_timestamps=True, vad_filter=False, beam_size=5,
                          language="en", condition_on_previous_text=False, temperature=0.0)
words, tlines = [], []
for s in segs_it:
    for w in (s.words or []):
        words.append({"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3),
                      "score": round(getattr(w, "probability", 1.0), 3)})
    line = f"[{s.start:7.2f}] {s.text.strip()}"
    tlines.append(line); print(line, flush=True)
open(os.path.join(OUTDIR, "_transcript.txt"), "w").write("\n".join(tlines) + "\n")
json.dump(words, open(os.path.join(OUTDIR, "screen_aligned.json"), "w"))
subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tighten_gaps.py"), wav, os.path.join(OUTDIR, "screen_aligned.json")], check=True)
print(f"DONE: {len(words)} words (whisper word-timestamps) -> screen_aligned.json", flush=True)
