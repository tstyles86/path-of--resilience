#!/usr/bin/env python3
"""Generate a DaVinci-importable timeline (FCPXML + EDL) from explicit cut windows.
Pairs with cut_xf.py: same keepers → an editable timeline that references the raw,
so the human can re-tweak takes by hand in DaVinci.
Usage: python3 make_timeline.py --input RAW.mp4 --keepers k.json --outdir DIR --name SHORTNAME

NOTE: timeline offsets are accumulated in INTEGER FRAMES (not seconds) so consecutive
clips butt together exactly — no 1-frame gaps (black flashes) or overlaps from rounding."""
import argparse, json, os, subprocess, urllib.parse

ap = argparse.ArgumentParser()
ap.add_argument("--input", required=True)
ap.add_argument("--keepers", required=True)
ap.add_argument("--outdir", required=True)
ap.add_argument("--name", default="short")
a = ap.parse_args()

def probe(*args):
    out = subprocess.run(["ffprobe","-v","error",*args,"-of",
        "default=noprint_wrappers=1:nokey=1",a.input],
        capture_output=True,text=True).stdout.strip().splitlines()
    return out

_d = probe("-show_entries","format=duration")
dur = float(_d[0]) if _d else 0.0
_r = probe("-select_streams","v:0","-show_entries","stream=r_frame_rate")
rfr = _r[0] if _r else "50/1"
num, den = (rfr.split("/") + ["1"])[:2]
FPS = round(float(num) / float(den)) or 50
wxh = probe("-select_streams","v:0","-show_entries","stream=width,height")
W, H = (int(wxh[0]), int(wxh[1])) if len(wxh) >= 2 else (1920, 1080)
ks = json.load(open(a.keepers))

def fr(t): return int(round(t * FPS))
def ratf(f): return f"{f*100}/{FPS*100}s"          # integer-frame -> fcpxml rational
def tcf(f):  return f"{f//(FPS*3600):02d}:{(f//(FPS*60))%60:02d}:{(f//FPS)%60:02d}:{f%FPS:02d}"

src_url = "file://" + urllib.parse.quote(os.path.abspath(a.input))
name = os.path.splitext(os.path.basename(a.input))[0]

# accumulate timeline position in integer frames so clips are gapless/overlap-free
clips, rec_f = [], 0
for k in ks:
    cs, ce = float(k["cs"]), float(k["ce"])
    in_f = fr(cs); df = fr(ce) - in_f                 # source in + duration in frames
    if df <= 0: continue
    clips.append(f'        <asset-clip ref="r2" offset="{ratf(rec_f)}" name="{k.get("label","clip")}" '
                 f'start="{ratf(in_f)}" duration="{ratf(df)}" format="r1" tcFormat="NDF"/>')
    rec_f += df
fcpxml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.9">
  <resources>
    <format id="r1" name="FFVideoFormat{H}p{FPS}" frameDuration="100/{FPS*100}s" width="{W}" height="{H}" colorSpace="1-1-1 (Rec. 709)"/>
    <asset id="r2" name="{name}" start="0s" duration="{ratf(fr(dur))}" hasVideo="1" hasAudio="1" format="r1" videoSources="1" audioSources="1" audioChannels="2" audioRate="48000">
      <media-rep kind="original-media" src="{src_url}"/>
    </asset>
  </resources>
  <library>
    <event name="{a.name}">
      <project name="{a.name}">
        <sequence format="r1" duration="{ratf(rec_f)}" tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="48k">
          <spine>
{chr(10).join(clips)}
          </spine>
        </sequence>
      </project>
    </event>
  </library>
</fcpxml>
'''
os.makedirs(a.outdir, exist_ok=True)
open(os.path.join(a.outdir, a.name + ".fcpxml"), "w").write(fcpxml)
edl = [f"TITLE: {a.name}", "FCM: NON-DROP FRAME"]; rec_f = 0
for i, k in enumerate(ks, 1):
    cs, ce = float(k["cs"]), float(k["ce"])
    in_f = fr(cs); df = fr(ce) - in_f
    if df <= 0: continue
    edl.append(f'{i:03d}  AX       AA/V  C        {tcf(in_f)} {tcf(in_f+df)} {tcf(rec_f)} {tcf(rec_f+df)}')
    edl.append(f'* FROM CLIP NAME: {k.get("label","clip")}'); rec_f += df
open(os.path.join(a.outdir, a.name + ".edl"), "w").write("\n".join(edl) + "\n")
print(f"wrote {a.name}.fcpxml + .edl ({len(clips)} clips, {rec_f} frames / {rec_f/FPS:.1f}s, {W}x{H}@{FPS}) -> {a.outdir}")
