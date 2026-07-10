#!/usr/bin/env python3
"""dedup_repeats.py — MANDATORY step. Scan the KEPT transcript of a cut for ANY
repeated phrase (NOT just adjacent) and excise the duplicates. Catches the failure
Luuk hit 2026-06-25: a take that stutters mid-phrase ("…go through the whole AND WE
CAN ACTUALLY AND WE CAN ACTUALLY go through the whole library") leaves a duplicate
the engine's adjacent-only collapse never sees. He: "that just cannot happen, I don't
want that ever again." So: ALWAYS run this on the final removal plan before applying,
and again on the rendered transcript (get_transcript) to verify zero.

How it works: walk the kept word sequence; find an n-gram (n=9..3) that repeats again
within the next ~14 words; that's a restarted/duplicated phrase. Keep the LATER/fuller
copy, excise [first_copy.start, second_copy.start] with LOCAL snapping (snap each cut
edge only into the gap right there — NEVER pull back across the excision, or you re-add
the dup). Iterate until zero. On glued restarts the second-copy onset has no silence, so
that seam is necessarily tight — duplicate-removal is the hard requirement (clean seam
loses to it here); flag the tight ones.

JUDGMENT (the one thing it can't decide alone): PARALLEL STRUCTURE is not a duplicate —
"I need to do research. I need to get a script." shares "I need to" but the completions
differ. Same for a term referenced twice in different sentences ("…using the super base
MCP" / "this super base MCP is connected…"). Pass those start-times in --keep so they're
NOT excised. Short matches (n<5) are the usual false positives — eyeball them.

Usage:
  python3 dedup_repeats.py SRC_16k.wav screen_aligned.json section_removal.json out_removal.json [--keep 154.7,179.2,...]
Prints every repeat as CUT/KEEP, the final kept duration, tight seams, and a 0-dup assertion.
"""
import json, re, wave, argparse
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("wav"); ap.add_argument("aligned"); ap.add_argument("section_removal"); ap.add_argument("out")
ap.add_argument("--keep", default="")          # comma-sep start-times (s) of FALSE positives to keep
ap.add_argument("--minlen", type=int, default=3)
ap.add_argument("--window", type=int, default=14)
a = ap.parse_args()
W = json.load(open(a.aligned)); rem = [list(x) for x in json.load(open(a.section_removal))]
KEEP_OK = [float(x) for x in a.keep.split(",") if x.strip()]
def isok(t): return any(abs(t-k) < 1.2 for k in KEEP_OK)
def nm(w): return re.sub(r'[^a-z0-9]', '', w['word'].lower())
def gap_before(idx): return W[idx]['start']-W[idx-1]['end'] if idx > 0 else 1.0
def kept_idx():
    def rm(t): return any(s-0.001 <= t <= e+0.001 for s, e in rem)
    return [k for k, w in enumerate(W) if not rm((w['start']+w['end'])/2)]

report = []
for _ in range(12):
    ki = kept_idx(); kept = [W[k] for k in ki]; tk = [nm(w) for w in kept]; N = len(kept); newex = []; i = 0
    while i < N:
        best = None
        for n in range(9, a.minlen-1, -1):
            if i+n > N or sum(1 for x in tk[i:i+n] if x) < 3: continue
            for j in range(i+1, min(i+n+a.window, N-n+1)):
                if tk[j:j+n] == tk[i:i+n]: best = (n, j); break
            if best: break
        if best and not isok(round(kept[i]['start'], 1)):
            n, j = best; wi, wj = ki[i], ki[j]; gi, gj = gap_before(wi), gap_before(wj)
            aa = W[wi]['start']-min(0.10, gi*0.5)
            bb = W[wj]['start']-(min(0.10, gj*0.5) if gj >= 0.12 else 0.02)
            newex.append([round(aa, 3), round(bb, 3)])
            report.append(("CUT ", round(kept[i]['start'], 1), ' '.join(x['word'] for x in kept[i:i+n]), n)); i = j
        elif best:
            report.append(("KEEP", round(kept[i]['start'], 1), ' '.join(x['word'] for x in kept[i:i+best[0]]), best[0])); i += 1
        else: i += 1
    if not newex: break
    rem = sorted(rem+newex); m = []
    for s, e in rem:
        if e <= s: continue
        if m and s <= m[-1][1]+0.001: m[-1][1] = max(m[-1][1], e)
        else: m.append([s, e])
    rem = m
json.dump(rem, open(a.out, "w"))
# verify zero + tight seams
wf = wave.open(a.wav, 'rb'); sr = wf.getframerate()
sig = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32)/32768.0
def rms_at(t): x=int((t-0.025)*sr); y=int((t+0.025)*sr); return float(np.sqrt(np.mean(sig[max(0,x):y]**2)+1e-9))
def rm(t): return any(s-0.001 <= t <= e+0.001 for s, e in rem)
kept = [w for w in W if not rm((w['start']+w['end'])/2)]; tk = [nm(w) for w in kept]; N = len(kept); d = 0; i = 0
while i < N:
    h = None
    for n in range(9, a.minlen-1, -1):
        if i+n > N or sum(1 for x in tk[i:i+n] if x) < 3: continue
        for j in range(i+1, min(i+n+a.window, N-n+1)):
            if tk[j:j+n] == tk[i:i+n] and not isok(round(kept[i]['start'], 1)): h = (n, j); break
        if h: break
    if h: d += 1; i = h[1]
    else: i += 1
tight = [round(p, 2) for r in rem for p in r if 0 < p < W[-1]['end'] and rms_at(p) >= 0.014]
seen = set()
for k, t, ph, n in report:
    key = (t, ph)
    if key in seen: continue
    seen.add(key)
    if k == "CUT " or n < 5: print(f"  {k} {t}s  ({n}w) '{ph}'")
print(f"\nremoval ranges: {len(rem)} | tight seams(rms>=.014): {len(tight)}")
print(f"DUPLICATES remaining: {d}   {'OK' if d == 0 else '*** STILL HAS DUPES ***'}")
