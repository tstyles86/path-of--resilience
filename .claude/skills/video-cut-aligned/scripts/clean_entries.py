#!/usr/bin/env python3
"""clean_entries.py — FINAL polish after recover_tails. Kills aggressive ENTRIES.
Palmier word-timestamps can start LATE (the audible onset precedes the stamp), so a cut
that ends at word.start-lead can land INSIDE the word's onset -> aggressive entry (Luuk's
#1 complaint). For every removal END (= next clip's entry), find the next kept word's TRUE
acoustic onset (walk back from its stamp through above-floor audio to the last silence),
then set the cut END = acoustic_onset - 0.10 so the clip enters on real silence. Only moves
a cut EARLIER (more lead), never later; never crosses the previous kept word. Leaves a seam
alone if it's already silent (rms<0.012) or if there is no silence before the word (glued).
Usage: clean_entries.py SRC_16k.wav screen_aligned.json removal_in.json removal_out.json"""
import json, sys, wave
import numpy as np
wav,aj,rin,rout=sys.argv[1:5]
W=json.load(open(aj)); rem=[list(x) for x in json.load(open(rin))]
wf=wave.open(wav,'rb'); sr=wf.getframerate()
sig=np.frombuffer(wf.readframes(wf.getnframes()),np.int16).astype(np.float32)/32768.0
HOP=0.01; hop=int(HOP*sr); n=len(sig)//hop
rms=np.sqrt(np.array([np.mean(sig[i*hop:(i+1)*hop]**2) for i in range(n)])+1e-9)
FLOOR=max(rms.max()*0.02, 0.012)
def rms_at(t):
    x=int((t-0.025)*sr); y=int((t+0.025)*sr); return float(np.sqrt(np.mean(sig[max(0,x):y]**2)+1e-9))
def acoustic_onset(ws):
    f=int(ws/HOP); 
    while f>0 and rms[f-1]>FLOOR: f-=1
    return f*HOP
def prev_word_end(t):
    pe=0.0
    for w in W:
        if w['end']<=t+0.02: pe=max(pe,w['end'])
    return pe
moved=0
for r in rem:
    e=r[1]
    if e>=W[-1]['end']-0.3: continue
    if rms_at(e)<0.014: continue                  # already clean
    nxt=min((w['start'] for w in W if w['start']>e-0.05), default=None)
    if nxt is None: continue
    on=acoustic_onset(nxt)
    if rms_at(on-0.10) > 0.012: continue           # no silence before word (glued) -> leave
    cap=prev_word_end(r[0])                          # don't cross prior kept word
    ne=round(max(on-0.10, cap+0.02), 3)
    if ne < e-0.005:
        r[1]=ne; moved+=1
json.dump(rem, open(rout,'w'))
print(f"cleaned {moved} aggressive entries -> {rout}")
