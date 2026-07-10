#!/usr/bin/env python3
"""build_judged.py — the reusable judged-cut engine (lesson 14).

Two modes:
  --emit    : split screen_aligned.json into gap-phrases, write phrases_full.{txt,json}
              for Claude to READ and judge.
  --build   : apply a decisions file {KEEP:[idx...], TRIM:{idx:[mode,seq]}} -> keepers.json
              (hard-cut windows) + an output-timecoded transcript. Same engine that cut
              Video 1: within-phrase repeat excision, strip hallucinated trailing "you",
              tight margins on trimmed edges, MERGE contiguous keepers into continuous spans
              (cut only where content was removed), then COMPRESS long internal pauses.

Usage:
  python3 build_judged.py --aligned A.json --emit OUTDIR
  python3 build_judged.py --aligned A.json --decisions d.json --out keepers.json --transcript t.txt
"""
import argparse, json, os

GAP = 0.45       # a breath/pause
LONG_WORD = 1.0  # a word this long absorbed a trailing pause (alignment artifact) -> unit boundary
LEAD, TRAIL, TRIM_MARGIN = 0.13, 0.18, 0.04
MERGE_GAP = 2.0
PAUSE_MAX, PAUSE_KEEP = 1.00, 0.15
_OBJ = {'for', 'with', 'to', 'tell', 'told', 'show', 'showing', 'let', 'give', 'help', 'ask', 'get', 'at', 'on', 'of', 'thank'}


def lw(w): return w['word'].strip().lower().strip('.,?!')
def text(ws): return ' '.join(w['word'].strip() for w in ws)


def phrases_of(aligned):
    # CLAUSE units: split on ANY of three signals — clause-ending punctuation, a real pause,
    # or a pause-absorbed long word. Meaning-aligned + breath-aligned + breaks dead-air spans.
    # Finer than sentences, so a comma-continuation can be CUT; when KEPT, the merge pass
    # re-joins contiguous kept clauses into one continuous clip. Over-splitting is safe (merge
    # heals it); under-splitting is what loses flexibility.
    ph, cur = [], []
    for w in aligned:
        if cur:
            prev = cur[-1]; tok = prev['word'].strip()
            clause_end = bool(tok) and tok[-1] in ',.!?;:'
            big_gap = (w['start'] - prev['end']) > GAP
            prev_long = (prev['end'] - prev['start']) > LONG_WORD   # split AFTER a long word
            cur_long = (w['end'] - w['start']) > LONG_WORD          # split BEFORE one -> it stands alone (dead-air word, easy to cut)
            if clause_end or big_gap or prev_long or cur_long:
                ph.append(cur); cur = []
        cur.append(w)
    if cur:
        ph.append(cur)
    return ph


def find_seq(words, seq):
    s = seq.split(); n = len(s); L = [lw(w) for w in words]
    for i in range(len(L) - n + 1):
        if L[i:i + n] == s:
            return i, i + n - 1
    return None


def repeat_clean_runs(words):
    c = [lw(w) for w in words]; n = len(c)
    for i in range(n):
        for Ln in range(min(10, (n - i) // 2), 0, -1):
            if c[i:i + Ln] == c[i + Ln:i + 2 * Ln] and (Ln >= 2 or c[i] not in {'so', 'the', 'a', 'i'}):
                d1 = words[i + Ln - 1]['end'] - words[i]['start']            # earlier copy duration
                d2 = words[i + 2 * Ln - 1]['end'] - words[i + Ln]['start']    # later copy duration
                # Default: drop the EARLIER copy, keep the later take. BUT if the later copy is much
                # longer, the alignment absorbed a PAUSE into it (a stretched word) — keeping it would
                # orphan a word onto its own clip with dead air. Drop the bloated copy, keep the clean
                # earlier one, so the cut lands at the real sentence boundary, not mid-clause.
                if d2 > d1 * 1.6 + 0.3:
                    left, right = words[:i + Ln], words[i + 2 * Ln:]
                else:
                    left, right = words[:i], words[i + Ln:]
                runs = []
                if len(left) >= 1:
                    runs += repeat_clean_runs(left)
                runs += repeat_clean_runs(right)
                return [r for r in runs if r]
    return [words]


def strip_you(words):
    while len(words) >= 2 and lw(words[-1]) == 'you' and lw(words[-2]) not in _OBJ:
        words = words[:-1]
    return words


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aligned", required=True)
    ap.add_argument("--emit")
    ap.add_argument("--decisions")
    ap.add_argument("--out")
    ap.add_argument("--transcript")
    a = ap.parse_args()
    aligned = json.load(open(a.aligned))
    ph = phrases_of(aligned)

    if a.emit:
        os.makedirs(a.emit, exist_ok=True)
        out = [{'i': i, 'cs': round(p[0]['start'], 2), 'ce': round(p[-1]['end'], 2), 't': text(p)} for i, p in enumerate(ph)]
        json.dump(out, open(os.path.join(a.emit, "phrases_full.json"), "w"), indent=0)
        with open(os.path.join(a.emit, "phrases_full.txt"), "w") as f:
            for p in out:
                f.write(f"[{p['i']:3d}] {p['cs']:7.2f}-{p['ce']:7.2f}  {p['t']}\n")
        print(f"emitted {len(out)} phrases -> {a.emit}/phrases_full.txt")
        return

    dec = json.load(open(a.decisions))
    KEEP = dec["KEEP"]
    TRIM = {int(k): tuple(v) for k, v in dec.get("TRIM", {}).items()}

    raw = []
    for idx in KEEP:
        words = ph[idx]; head_trim = tail_trim = False
        if idx in TRIM:
            mode, seq = TRIM[idx]; pos = find_seq(words, seq)
            if pos is None:
                print(f"!! TRIM miss on [{idx}] '{seq}'")
            else:
                i, j = pos
                if mode == 'tail':
                    words = words[:j + 1]; tail_trim = True
                else:
                    words = words[i:]; head_trim = True
        runs = [strip_you(r) for r in repeat_clean_runs(words)]; runs = [r for r in runs if r]
        for ri, run in enumerate(runs):
            first_sub, last_sub = ri == 0, ri == len(runs) - 1
            lead = LEAD if (first_sub and not head_trim) else TRIM_MARGIN
            trail = TRAIL if (last_sub and not tail_trim) else TRIM_MARGIN
            raw.append({'idx': idx, 'sub': ri, 'last_sub': last_sub,
                        'cs': round(run[0]['start'] - lead, 3), 'ce': round(run[-1]['end'] + trail, 3),
                        'ht': head_trim and first_sub, 'tt': tail_trim and last_sub})

    merged = []
    for r in raw:
        if merged:
            p = merged[-1]
            if r['sub'] == 0 and r['idx'] == p['last'] + 1 and p['last_sub'] and not p['ttlast'] and not r['ht'] and (r['cs'] - p['ce']) < MERGE_GAP:
                p['ce'] = r['ce']; p['last'] = r['idx']; p['ttlast'] = r['tt']; p['last_sub'] = r['last_sub']; continue
        merged.append({'cs': r['cs'], 'ce': r['ce'], 'first': r['idx'], 'last': r['idx'], 'ttlast': r['tt'], 'last_sub': r['last_sub']})

    def span_words(cs, ce): return [w for w in aligned if w['start'] >= cs - 0.03 and w['end'] <= ce + 0.03]
    keepers, saved = [], 0.0
    for m in merged:
        ws = span_words(m['cs'], m['ce'])
        if not ws:
            keepers.append({'cs': m['cs'], 'ce': m['ce']}); continue
        seg_cs = m['cs']
        for i in range(len(ws) - 1):
            g = ws[i + 1]['start'] - ws[i]['end']
            if g > PAUSE_MAX:
                keepers.append({'cs': round(seg_cs, 3), 'ce': round(ws[i]['end'] + PAUSE_KEEP, 3)})
                saved += g - 2 * PAUSE_KEEP; seg_cs = ws[i + 1]['start'] - PAUSE_KEEP
        keepers.append({'cs': round(seg_cs, 3), 'ce': round(m['ce'], 3)})
    json.dump(keepers, open(a.out, "w"), indent=1)

    if a.transcript:
        def stext(cs, ce): return ' '.join(w['word'].strip() for w in span_words(cs, ce))
        lines, t, buf, ls, prev = [], 0.0, '', 0.0, None
        for k in keepers:
            tx = stext(k['cs'], k['ce'])
            if prev is not None and abs(k['cs'] - prev) > 0.35 and buf:
                lines.append(f"{int(ls//60)}:{ls%60:05.2f}  {buf.strip()}"); buf = ''; ls = t
            if not buf:
                ls = t
            buf = (buf + ' ' + tx).strip(); t += k['ce'] - k['cs']; prev = k['ce']
        if buf:
            lines.append(f"{int(ls//60)}:{ls%60:05.2f}  {buf.strip()}")
        open(a.transcript, "w").write("\n".join(lines) + f"\n\n[total {int(t//60)}:{t%60:05.2f}]\n")
    print(f"JUDGED: {len(merged)} spans -> {len(keepers)} segs after pause-compress, "
          f"{round(sum(k['ce']-k['cs'] for k in keepers),1)}s (tightened {round(saved,1)}s)")


if __name__ == "__main__":
    main()
