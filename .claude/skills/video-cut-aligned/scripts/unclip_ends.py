#!/usr/bin/env python3
"""unclip_ends.py — extend keeper cut-points so word TAILS aren't chopped.

The whisper gap-tightener trims a word's quiet RELEASE (the fade-out of "-ch",
"-tch", a trailing vowel) as if it were silence, so a cut placed at word.end + a
small trail lands mid-release: you hear "spee-" instead of "speech", and the
abrupt chop into silence is what makes the gaps sound harsh.

Fix, on the FINAL keepers (no re-judge): for each segment, look at the audio just
past ce. If speech is still going (the word's release / a clipped word), extend ce
through that CONTIGUOUS speech burst until real silence. We STOP at any gap >=
GAP_STOP — a removed retake always has a breath/gap before it, so we never pull
removed content back in. Bias: keep a hair too much (easy to drag-trim) over
clipping (invisible until you hear it).

Usage: python3 unclip_ends.py WAV KEEPERS.json [--pad 0.06] [--max 0.5]
       (edits KEEPERS.json in place; prints what it extended)
"""
import json, wave, argparse
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("wav"); ap.add_argument("keepers")
ap.add_argument("--pad", type=float, default=0.05)     # silence room left after the recovered word
ap.add_argument("--max", type=float, default=0.30)     # never extend more than this — a word RELEASE is
# < 0.3s; anything longer is a fresh WORD (often a gapless retake) we must NOT re-add. Capping here is
# the real safety against pulling a "let me show you / let me show you" restart back into the cut.
ap.add_argument("--gap-stop", type=float, default=0.08)  # a silence run this long = real boundary, stop
a = ap.parse_args()

ks = json.load(open(a.keepers))
wf = wave.open(a.wav, 'rb'); sr = wf.getframerate()
sig = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32) / 32768.0
HOP = 0.01; hop = int(HOP * sr); n = len(sig) // hop
rms = np.sqrt(np.array([np.mean(sig[i*hop:(i+1)*hop] ** 2) for i in range(n)]) + 1e-9)
peak = float(rms.max()); floor = float(np.percentile(rms, 15))
REL = max(floor * 2.5, peak * 0.02)          # above room tone = speech
gap_frames = int(a.gap_stop / HOP)


def fidx(t): return max(0, min(n - 1, int(t / HOP)))


def speech_end_after(ce):
    """From ce, walk forward through a contiguous speech burst; return the last
    speech frame-time before a real silence gap, or None if ce is already silent."""
    c = fidx(ce); last = None; f = c
    limit = fidx(ce + a.max)
    while f <= limit:
        if rms[f] > REL:
            last = f
            f += 1
            continue
        # silence frame — is it a real gap (>= gap_stop continuous)?
        run = 0; g = f
        while g < n and rms[g] <= REL and run < gap_frames:
            run += 1; g += 1
        if run >= gap_frames:
            break            # real boundary reached
        f = g                # short dip inside the burst, keep going
    return last * HOP if last is not None else None


changed = []
for i, k in enumerate(ks):
    se = speech_end_after(k['ce'])
    if se is None:
        continue
    new_ce = min(se + a.pad, k['ce'] + a.max)
    # don't run past the NEXT keeper's start (would overlap / re-add removed audio
    # only if the next seg is contiguous in source — clamp to be safe)
    if i + 1 < len(ks):
        nxt = ks[i + 1]['cs']
        if nxt > k['ce']:                 # next seg is later in the source
            new_ce = min(new_ce, nxt - 0.02)
    if new_ce - k['ce'] > 0.03:
        changed.append((round(k['ce'], 2), round(new_ce, 2), round(new_ce - k['ce'], 2)))
        k['ce'] = round(new_ce, 3)

json.dump(ks, open(a.keepers, 'w'), indent=1)
print(f"unclipped {len(changed)}/{len(ks)} cut tails:")
for c, nc, d in changed:
    print(f"  {c} -> {nc}  (+{d}s)")
