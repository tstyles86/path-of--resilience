#!/usr/bin/env python3
"""palmier_cut.py — turn a judged keepers list into a CLEAN, waveform-verified
removal plan for a Palmier (palmier-pro MCP) cut. The exact pipeline + constants
that produced the 2026-06-25 screenFish1 cut Luuk signed off on ("cuts are perfect,
gaps good, transitions smooth, no duplicate sentences"). Reproduce it on every video.

WHAT IT DOES (operates on SOURCE seconds; Palmier ripples at these exact seconds):
  1. snap every clip START back to the nearest real silence gap  -> clean onsets
  2. snap every clip END to the gap after the last word           -> clean offsets
  3. trim a dangling FUNCTION word glued onto a kept phrase end    -> kills "it"/"what"/"but" leaks
  4. fix offsets that still land in speech (glued)                 -> extend to release, clamp before next word
  5. excise an internal stutter ONLY if >=0.12s silence between the two copies (clean); else LEAVE it
  6. emit the COMPLEMENT as removal ranges + VERIFY every cut point is silence (rms<THRESH)

WHAT IT DOESN'T (these are Claude judgment steps, done BEFORE this):
  - take selection (default LAST take; for an opener use a take that ENDS on silence)
  - the glued double-say escape hatch: if a line only exists as a glued stutter, pick a
    FLUENT ALTERNATE take instead (e.g. "two different modes"[glued] -> "two different moods"[fluent]).
    Keep both copies (clean seam) only when no alternate take exists. NEVER force a glued cut.
  - keeping intentional A/B demo playbacks / voice-clone samples.

Usage:
  python3 palmier_cut.py SRC_16k.wav judged_keepers.json out_removal.json [src_aligned.json]
  (judged_keepers.json + src_aligned.json come from build_judged.py / make_aligned.py+tighten_gaps.py;
   if aligned not given, looks for screen_aligned.json next to the wav.)
Prints: kept duration, #ranges, any HARSH cut points (should be NONE bar a couple of
truly-glued offsets), and stutters LEFT (glued, gap shown).
"""
import json, sys, os, wave, re
import numpy as np

# ---- the locked constants ----
PHRASE_GAP = 0.30   # a gap this big = a clean phrase boundary to land a cut in
GAPMIN     = 0.15   # smallest gap we'll still cut in (fallback)
BACK       = 4.0    # how far (s) to search back for a silent onset (glued takes need a big window)
LEAD_CAP   = 0.12   # max silence kept before first word
TRAIL_CAP  = 0.16   # max silence kept after last word
TRIM_FUNC  = {'it','what','but','and','so','the','a','i','we','you','that','is','this',
              'now','then','or','my','to','of','in'}   # dangling words safe to trim (never content words)
DANGLE_GAP, DANGLE_DUR, DANGLE_NEXT = 0.30, 0.40, 0.60
STUTTER_BETWEEN = 0.12   # only excise an internal repeat if the copies are >= this apart
RMS_WIN, RMS_SILENT = 0.025, 0.012   # a cut point with rms below this (25ms window) is clean

wav, kj, outp = sys.argv[1], sys.argv[2], sys.argv[3]
aj = sys.argv[4] if len(sys.argv) > 4 else os.path.join(os.path.dirname(wav), "screen_aligned.json")
W = json.load(open(aj)); K = json.load(open(kj))
SRC = W[-1]['end'] + 0.5
wf = wave.open(wav, 'rb'); sr = wf.getframerate()
sig = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32) / 32768.0
def rms_at(t, win=RMS_WIN):
    a = int((t-win)*sr); b = int((t+win)*sr)
    return float(np.sqrt(np.mean(sig[max(0,a):b]**2) + 1e-9))
def nm(w): return re.sub(r'[^a-z0-9]', '', w['word'].lower())
def lwd(w): return w['word'].strip().lower().strip('.,?!;:')

def widx_start(cs):
    for i, w in enumerate(W):
        if w['start'] >= cs-0.06: return i
    return len(W)-1
def widx_end(ce):
    for i in range(len(W)-1, -1, -1):
        if W[i]['end'] <= ce+0.06: return i
    return 0
def snap_cs(cs):
    fw = widx_start(cs); best = None; j = fw
    while j > 0:
        if W[fw]['start']-W[j]['start'] > BACK: break
        gap = W[j]['start']-W[j-1]['end']
        if gap >= PHRASE_GAP: return round(W[j]['start']-min(LEAD_CAP, gap*0.5), 3)
        if gap >= GAPMIN and best is None: best = round(W[j]['start']-min(0.10, gap*0.5), 3)
        j -= 1
    return best if best is not None else round(W[fw]['start']-0.02, 3)
def snap_ce(ce):
    lw = widx_end(ce)
    if lw+1 < len(W):
        gap = W[lw+1]['start']-W[lw]['end']
        if gap >= 0.06: return round(W[lw]['end']+min(TRAIL_CAP, gap*0.45), 3)
    return round(W[lw]['end']+0.03, 3)
def inside(cs, ce): return [w for w in W if w['start'] >= cs-0.02 and w['end'] <= ce+0.02]

# 1+2 snap, 3 dangling-trim
for k in K:
    k['cs'] = snap_cs(k['cs']); k['ce'] = max(snap_ce(k['ce']), k['cs']+0.08)
    ins = inside(k['cs'], k['ce'])
    if len(ins) >= 2:
        last, prev = ins[-1], ins[-2]
        gb = last['start']-prev['end']; dur = last['end']-last['start']
        nxt = [w for w in W if w['start'] > last['end'] and w['start'] < last['end']+DANGLE_NEXT]
        if gb > DANGLE_GAP and dur < DANGLE_DUR and nxt and lwd(last) in TRIM_FUNC:
            k['ce'] = round(prev['end']+min(TRAIL_CAP, gb*0.45), 3)
# 4 fix offsets still in speech
def fix_ce(ce):
    cur = None
    for w in W:
        if w['start']-0.02 <= ce <= w['end']+0.15: cur = w
    if cur is None: return ce
    nxts = [w for w in W if w['start'] > cur['end']-0.001]; nxt = nxts[0] if nxts else None
    end = cur['end']
    if nxt:
        gap = nxt['start']-end
        new = end+min(0.12, max(0.0, gap*0.45)) if gap >= 0.06 else end+min(0.03, gap*0.5 if gap > 0 else 0)
        new = min(new, nxt['start']-0.02)
    else: new = end+0.10
    return round(max(new, end), 3)
for k in K:
    if rms_at(k['ce']) >= RMS_SILENT: k['ce'] = fix_ce(k['ce'])
# merge keepers
m = sorted([[k['cs'], k['ce']] for k in K]); kp = []
for cs, ce in m:
    if kp and cs <= kp[-1][1]+0.02: kp[-1][1] = max(kp[-1][1], ce)
    else: kp.append([cs, ce])
# 5 stutter excision (only where copies have a real gap between them)
excis = []; left = []
for cs, ce in kp:
    ws = inside(cs, ce); n = len(ws); i = 0
    while i < n:
        hit = False
        for L in range(6, 1, -1):
            if i+2*L > n: continue
            if [nm(x) for x in ws[i:i+L]] == [nm(x) for x in ws[i+L:i+2*L]] and sum(1 for x in ws[i:i+L] if nm(x)) >= 2:
                gb = ws[i+L]['start']-ws[i+L-1]['end']
                gbefore = ws[i]['start']-ws[i-1]['end'] if i > 0 else ws[i]['start']-cs
                txt = ' '.join(x['word'] for x in ws[i:i+L])
                if gb >= STUTTER_BETWEEN and gbefore >= 0.10:
                    a = round((ws[i-1]['end']+ws[i]['start'])/2, 3) if i > 0 else round(cs+0.02, 3)
                    b = round((ws[i+L-1]['end']+ws[i+L]['start'])/2, 3)
                    excis.append([a, b]); i += 2*L; hit = True
                else:
                    left.append((txt, round(gb, 2)))
                break
        if not hit: i += 1
# 6 complement -> removal, + excisions, verify
rem = []; prev = 0.0
for s, e in kp:
    if s > prev+0.001: rem.append([round(prev, 3), round(s, 3)])
    prev = e
if prev < SRC-0.5: rem.append([round(prev, 3), round(W[-1]['end']+0.05, 3)])
allr = sorted(rem+excis); merged = []
for s, e in allr:
    if e <= s: continue
    if merged and s <= merged[-1][1]+0.001: merged[-1][1] = max(merged[-1][1], e)
    else: merged.append([s, e])
json.dump(merged, open(outp, 'w'))
pts = sorted(set(p for r in merged for p in r))
harsh = [round(p, 2) for p in pts if 0 < p < W[-1]['end'] and rms_at(p) >= RMS_SILENT+0.001]
kept = sum(e-s for s, e in kp) - sum(e-s for s, e in excis)
print(f"kept ~{kept:.1f}s ({kept/60:.2f}min) | removal ranges: {len(merged)}")
print(f"HARSH cut points (rms>={RMS_SILENT}): {harsh if harsh else 'NONE'}")
print(f"stutters EXCISED (clean gap): {len(excis)} | LEFT glued (need an alternate take or keep): {len(left)}")
for t, g in left: print(f"   glued: '{t}' (copies {g}s apart)")
