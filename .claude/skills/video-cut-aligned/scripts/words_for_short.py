#!/usr/bin/env python3
"""words_for_short.py — produce the per-word transcript (source-time) backing the
back-office TEXT editor (Descript-style). Transcribes the short's source region
ONCE, force-aligns it, and tags each word kept/removed by the current keepers.

Usage:
  python3 words_for_short.py --input RAW.mp4 --keepers <stem>_keepers.json --out <stem>_words.json

Output: [{"word","cs","ce","kept"}, ...] in source seconds, in spoken order.
"kept"=true means the word is inside a current keeper window (it's in the cut);
removed retakes come back kept=false so the editor can show them struck-through.
"""
import argparse, json, os, subprocess, sys, tempfile

SK = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--keepers", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--margin", type=float, default=0.3)
    a = ap.parse_args()

    keepers = json.load(open(a.keepers))
    if not keepers:
        print(json.dumps({"ok": False, "error": "empty keepers"})); sys.exit(1)
    region_start = max(0.0, min(k["cs"] for k in keepers) - a.margin)
    region_end = max(k["ce"] for k in keepers) + a.margin

    with tempfile.TemporaryDirectory() as td:
        wav = os.path.join(td, "region.wav")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(region_start), "-to", str(region_end),
                        "-i", a.input, "-vn", "-ac", "1", "-ar", "16000", wav], check=True, cwd=td)
        # 1 transcription for the whole region (retakes included). Offset = region_start
        # so word times are GLOBAL. Use whisper's own word timestamps directly — they
        # KEEP numbers/punctuation (MMS forced-alignment strips non-letters, which drops
        # "10,000", "100", etc.), and are precise enough for labels + edge-snapping.
        subprocess.run([sys.executable, os.path.join(SK, "transcribe_literal.py"), wav, os.path.join(td, "lit"), str(region_start)],
                       check=True, cwd=td)
        words = json.load(open(os.path.join(td, "lit_words.json")))

    def kept(w):
        mid = (w["start"] + w["end"]) / 2.0
        return any(k["cs"] - 0.02 <= mid <= k["ce"] + 0.02 for k in keepers)

    out = [{"word": w["word"], "cs": round(w["start"], 3), "ce": round(w["end"], 3), "kept": kept(w)}
           for w in words]
    json.dump(out, open(a.out, "w"))
    print(json.dumps({"ok": True, "words": len(out), "kept": sum(1 for w in out if w["kept"]), "out": a.out}))


if __name__ == "__main__":
    main()
