#!/usr/bin/env python3
"""recover_tails.py — MANDATORY FINAL step (after dedup, before apply). Stop cuts from
chopping the last word. Luuk 2026-06-25: "almost all cuts are made too soon, the last
words get cut in half." Priority #1 = NO cut-up words.

THE CONFLICT this resolves: `tighten_gaps` trims each word's quiet RELEASE (decaying
consonant/vowel) as if it were silence, so word.end lands early; cutting at word.end+trail
chops the word. We HAD `unclip_ends.py` for this, but its clamp was the next CLIP (≈3s
away) so on fish1 it over-extended into the next DELETED word → a leak, and we dropped it.
The right clamp is the next WORD's onset: recover the full release up to (but never into)
the next source word — so no clipped word AND no leaked/duplicated next word.

For every cut END (ce of a kept span): walk forward from the cut through above-floor audio
with a LOW floor (peak*0.01) that follows the quiet release, until a real >=0.08s silence,
capped +0.6s; set ce = min(release_end+0.05, next_word.start-0.02). Never shrink ce; never
let it reach the next span's cs. On a GLUED boundary (next word ~0s away) the word is kept
whole up to the glue and the cut is as tight as physically possible — that's the floor.

Two floors on purpose: LOW to TRACK the release when recovering; a HIGHER one (peak*0.03)
only if you re-measure 'is this still a real clip' (a glued next word reads as speech-past
but isn't a clip of THIS word — check the gap to next word: ~0 = boundary, not a clip).

Usage: python3 recover_tails.py SRC_16k.wav screen_aligned.json removal_in.json removal_out.json
"""
import json, sys, wave
import numpy as np

wav, aj, rin, rout = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
W = json.load(open(aj)); rem = [list(x) for x in json.load(open(rin))]
wf = wave.open(wav, 'rb'); sr = wf.getframerate()
sig = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32)/32768.0
HOP = 0.01; hop = int(HOP*sr); n = len(sig)//hop
rms = np.sqrt(np.array([np.mean(sig[i*hop:(i+1)*hop]**2) for i in range(n)])+1e-9)
REL_FLOOR = rms.max()*0.01
def release_end(t, limit=0.6):
    f = int(t/HOP); last = f; run = 0
    while f < min(int((t+limit)/HOP), n):
        if rms[f] > REL_FLOOR: last = f; run = 0
        else:
            run += 1
            if run >= 8: break
        f += 1
    return (last+1)*HOP
def next_word_start(ce):
    for w in W:
        if w['start'] > ce-0.02: return w['start']
    return 1e9
# kept spans = complement
kp = []; prev = 0.0
for s, e in rem:
    if s > prev: kp.append([prev, s])
    prev = e
if prev < W[-1]['end']: kp.append([prev, W[-1]['end']+0.05])
ext = 0
for sp in kp:
    ce = sp[1]; re_end = release_end(ce-0.06); nxt = next_word_start(ce)
    new = round(min(re_end+0.05, nxt-0.02), 3)
    if new > ce+0.005: ext += 1
    sp[1] = max(new, ce)
kp.sort()
for i in range(len(kp)-1):
    if kp[i][1] > kp[i+1][0]-0.02: kp[i][1] = round(kp[i+1][0]-0.02, 3)
fr = []; prev = 0.0
for cs, ce in kp:
    if cs > prev+0.001: fr.append([round(prev, 3), round(cs, 3)])
    prev = ce
if prev < W[-1]['end']-0.5: fr.append([round(prev, 3), round(W[-1]['end']+0.05, 3)])
json.dump(fr, open(rout, "w"))
print(f"recovered tails on {ext}/{len(kp)} cut ends -> {rout} ({len(fr)} removal ranges)")
