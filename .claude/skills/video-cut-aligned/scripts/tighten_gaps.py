#!/usr/bin/env python3
"""tighten_gaps.py — recover real silence GAPS in a whisper word alignment.

Whisper gives correct word ORDER but packs words edge-to-edge (it fills each word's
duration, leaving ~no silence between words), which destroys the gap info the cutter
needs to split clauses and place clean cuts. This re-derives gaps from the audio:
for each word, shrink its [start,end] to where speech ACTUALLY is (RMS above a silence
floor), so genuine pauses reappear as gaps between words. Order is whisper's (so no
repeat-scrambling like MMS_FA); the boundaries get snapped to real silence.

Usage: python3 tighten_gaps.py WAV ALIGNED.json   (edits ALIGNED.json in place)
"""
import json, sys, wave
import numpy as np

wav, aj = sys.argv[1], sys.argv[2]
words = json.load(open(aj))
wf = wave.open(wav, 'rb'); sr = wf.getframerate()
sig = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
HOP = 0.02; hop = int(HOP * sr)
n = max(1, (len(sig) - 1) // hop)
rms = np.sqrt(np.array([np.mean(sig[i*hop:(i+1)*hop] ** 2) for i in range(n)]) + 1e-9)
thr = max(rms.max() * 0.02, float(np.percentile(rms, 12)) * 1.5)   # silence floor — kept LOW so a
# word's quiet RELEASE (decaying consonant/vowel) stays above it and isn't trimmed as silence.
# (A high floor chopped word tails: "speech"->"spee-". unclip_ends.py is the backstop downstream.)


def first_speech(ts, te):
    f0, f1 = int(ts / HOP), min(int(te / HOP), len(rms) - 1)
    for f in range(f0, f1 + 1):
        if rms[f] > thr: return f * HOP
    return ts


def last_speech(ts, te):
    f0, f1 = int(ts / HOP), min(int(te / HOP), len(rms) - 1)
    for f in range(f1, f0 - 1, -1):
        if rms[f] > thr: return (f + 1) * HOP
    return te


for w in words:
    ss = first_speech(w['start'], w['end'])
    se = last_speech(w['start'], w['end'])
    w['start'] = round(min(w['end'] - 0.04, max(w['start'], ss)), 3)
    w['end'] = round(max(w['start'] + 0.04, min(w['end'], se)), 3)
json.dump(words, open(aj, 'w'))
gaps = [words[i]['start'] - words[i - 1]['end'] for i in range(1, len(words))]
print(f"tightened {len(words)} words | gaps >0.3s: {sum(g>0.3 for g in gaps)} (was near 0)")
