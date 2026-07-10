#!/usr/bin/env python3
"""Disfluency-faithful transcription: condition_on_previous_text=False stops the model
from 'cleaning up' stutters/retakes using context, so it transcribes what was ACTUALLY said.
Usage: python3 transcribe_literal.py IN.wav OUT_PREFIX [offset_seconds]"""
import sys, json
from faster_whisper import WhisperModel
wav = sys.argv[1]
prefix = sys.argv[2] if len(sys.argv) > 2 else "lit"
off = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
m = WhisperModel("large-v3", device="cpu", compute_type="int8")
segs_it, info = m.transcribe(
    wav, word_timestamps=True, vad_filter=False, beam_size=5, language="en",
    condition_on_previous_text=False, temperature=0.0,
)
words, segs = [], []
for s in segs_it:
    segs.append({"start": round(s.start+off,3), "end": round(s.end+off,3), "text": s.text.strip()})
    for w in (s.words or []):
        words.append({"start": round(w.start+off,3), "end": round(w.end+off,3), "word": w.word})
    print(f"[{s.start+off:7.2f}] {s.text.strip()}", flush=True)
json.dump(words, open(f"{prefix}_words.json","w"))
json.dump(segs, open(f"{prefix}_segments.json","w"))
print(f"\nDONE {len(words)} words -> {prefix}_words.json")
