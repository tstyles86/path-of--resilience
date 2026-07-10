#!/usr/bin/env python3
"""Crossfade-capable cutter (Descript-style). Takes EXPLICIT (cs,ce) source windows and
joins them with short video xfades + audio acrossfades. This bridges GLUED word junctions
(e.g. '...somewhere|because honestly...') that hard cuts can't split, and smooths head-jumps.
Usage: python3 cut_xf.py --input IN.mp4 --keepers k.json --out OUT.mp4 [--xf 0.07]"""
import argparse, json, subprocess
ap = argparse.ArgumentParser()
ap.add_argument("--input", required=True)
ap.add_argument("--keepers", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--xf", type=float, default=0.07, help="crossfade seconds per join")
ap.add_argument("--crf", type=int, default=18)
a = ap.parse_args()
ks = json.load(open(a.keepers))
XF = a.xf

# build per-segment trims
parts, vL, aL = [], [], []
for i, k in enumerate(ks):
    cs, ce = float(k["cs"]), float(k["ce"])
    parts.append(f"[0:v]trim=start={cs:.3f}:end={ce:.3f},setpts=PTS-STARTPTS,fps=50,format=yuv420p,setsar=1,settb=AVTB[v{i}]")
    parts.append(f"[0:a]atrim=start={cs:.3f}:end={ce:.3f},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[a{i}]")
    vL.append(f"[v{i}]"); aL.append(f"[a{i}]")
    print(f'{k.get("label",""):28s} {cs:8.3f}-{ce:8.3f} ({ce-cs:5.2f}s)')

# xfade chain (video) + acrossfade chain (audio)
chain = list(parts)
cur_v, cur_len = f"v{0}", float(ks[0]["ce"])-float(ks[0]["cs"])
cur_a = f"a{0}"
for i in range(1, len(ks)):
    di = float(ks[i]["ce"])-float(ks[i]["cs"])
    off = cur_len - XF
    nv, na = f"vx{i}", f"ax{i}"
    chain.append(f"[{cur_v}][v{i}]xfade=transition=fade:duration={XF}:offset={off:.3f}[{nv}]")
    chain.append(f"[{cur_a}][a{i}]acrossfade=d={XF}:c1=tri:c2=tri[{na}]")
    cur_v, cur_a = nv, na
    cur_len = cur_len + di - XF

fc = ";".join(chain)
open("_filter_xf.txt","w").write(fc)
cmd = ["ffmpeg","-y","-i",a.input,"-filter_complex_script","_filter_xf.txt",
       "-map",f"[{cur_v}]","-map",f"[{cur_a}]",
       "-c:v","libx264","-preset","medium","-crf",str(a.crf),"-pix_fmt","yuv420p",
       "-c:a","aac","-b:a","192k","-movflags","+faststart",a.out]
print(f"\n~{cur_len:.1f}s, {len(ks)} segs, xf={XF}s -> {a.out}")
r = subprocess.run(cmd, capture_output=True, text=True)
print("RC", r.returncode, "OK" if r.returncode==0 else r.stderr[-1500:])
