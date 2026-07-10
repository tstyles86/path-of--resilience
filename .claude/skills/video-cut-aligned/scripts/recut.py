#!/usr/bin/env python3
"""recut.py — re-render ONE short from a keepers file: cut_xf -> master -> verify,
writing the final atomically. Encapsulates SKILL.md steps 5-6 so both the skill
and the media agent's /recut endpoint share one code path.

Usage:
  python3 recut.py --input RAW.mp4 --keepers k.json --out 3_SHORTS/X.mp4 [--xf 0.05] [--no-verify]

Prints ONE json line to stdout: {"ok":true,"duration":12.3,"verify_ok":true,"verify_msg":"..."}
Exits non-zero (with a json {"ok":false,"error":...}) on failure.
"""
import argparse, json, os, re, subprocess, sys, tempfile

SK = os.path.dirname(os.path.abspath(__file__))
# BuildLoop cinematic grade — the same Rec709 LUT the b-roll pipeline uses.
GRADE_LUT = os.path.expanduser("~/.claude/skills/broll-ingest/luts/buildloop-FINAL.cube")
# Auto-exposure target (mean luma 0-255) for the GRADED frame. Talking-head
# footage is often shot dark/low-key; the grade should EXPOSE it to a consistent
# level, not just tint it. We lift dark sources toward this and leave well-lit
# footage alone. ~102 lands a well-exposed face that survives video-edit's
# finishing grade (vignette + contrast) without going murky.
EXPOSE_TARGET = 102.0


def _probe_yavg(frame_png, vf):
    """Mean luma (0-255) of one frame after applying `vf`. None if it fails."""
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", frame_png, "-vf",
         f"{vf},signalstats,metadata=print:file=-", "-f", "null", "/dev/null"],
        capture_output=True, text=True)
    vals = [float(m) for m in re.findall(r"YAVG=([0-9.]+)", r.stdout)]
    return sum(vals) / len(vals) if vals else None


def auto_expose_gamma(src, crop_expr, lut_expr, target=EXPOSE_TARGET):
    """Pick a gamma lift that brings the GRADED frame to `target` mean luma.

    Measured through the REAL chain ([crop,] eq=gamma, lut) on a few representative
    frames, so the LUT's own response is accounted for. Only ever brightens
    (gamma >= 1.0) and is clamped to the candidate range — a well-exposed clip
    lands on gamma 1.0 (no-op) and is left untouched.
    """
    try:
        with tempfile.TemporaryDirectory() as td:
            dur = probe_dur(src)
            frames = []
            for i, frac in enumerate((0.25, 0.5, 0.75)):
                fr = os.path.join(td, f"ae{i}.png")
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss",
                                str(round(dur * frac, 2)), "-i", src,
                                "-frames:v", "1", fr], check=True)
                if os.path.isfile(fr):
                    frames.append(fr)
            if not frames:
                return 1.0
            best_g, best_d = 1.0, 1e9
            for g in (1.0, 1.15, 1.3, 1.45, 1.6, 1.75):
                chain = [c for c in (crop_expr, f"eq=gamma={g}" if g > 1.0 else "", lut_expr) if c]
                ys = [y for y in (_probe_yavg(f, ",".join(chain)) for f in frames) if y is not None]
                if not ys:
                    continue
                d = abs(sum(ys) / len(ys) - target)
                if d < best_d:
                    best_d, best_g = d, g
            return best_g
    except Exception:  # noqa: BLE001 — exposure is best-effort; never block the render
        return 1.0


def probe_dur(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True)
    return float(r.stdout.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--keepers", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--xf", type=float, default=0.05)
    ap.add_argument("--no-verify", action="store_true")
    ap.add_argument("--no-grade", action="store_true", help="skip the BuildLoop cinematic color grade")
    ap.add_argument("--vertical", action="store_true", help="reframe to 9:16 (center crop) for Shorts/Reels")
    a = ap.parse_args()

    lift_gamma = 1.0
    try:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with tempfile.TemporaryDirectory() as td:
            cut_raw = os.path.join(td, "cut_raw.mp4")
            # 1. HARD-CUT concat (NO crossfade). The export now plays the EXACT same
            #    [cs,ce] windows the editor preview does — same boundaries, same length —
            #    so "what you review = what you export". The old 0.05s xfade drifted the
            #    export ~0.05s/join SHORTER than the preview (the audible mismatch) and its
            #    nested chain collapsed past ~40 clips; concat fixes both and is robust at
            #    any count. (--xf kept for API compat; ignored.)
            ks = json.load(open(a.keepers))
            if not ks:
                raise RuntimeError("empty keepers")
            fl = []
            for i, k in enumerate(ks):
                fl.append(f"[0:v]trim=start={k['cs']}:end={k['ce']},setpts=PTS-STARTPTS[v{i}];")
                fl.append(f"[0:a]atrim=start={k['cs']}:end={k['ce']},asetpts=PTS-STARTPTS[a{i}];")
            fl.append("".join(f"[v{i}][a{i}]" for i in range(len(ks))) + f"concat=n={len(ks)}:v=1:a=1[outv][outa]")
            fcs = os.path.join(td, "concat.txt")
            with open(fcs, "w") as f:
                f.write("".join(fl))
            subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-i", a.input,
                 "-filter_complex_script", fcs, "-map", "[outv]", "-map", "[outa]",
                 "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
                 "-c:a", "aac", "-b:a", "192k", cut_raw],
                check=True, cwd=td)

            # 2. master the audio + apply the BuildLoop cinematic grade (same LUT
            #    the b-roll pipeline uses). The grade needs a video re-encode; without
            #    it the video is copied through. format=yuv420p is mandatory after lut3d.
            dur = probe_dur(cut_raw)
            out_fade = max(0.0, round(dur - 0.12, 3))
            af = (f"afade=t=in:st=0:d=0.05,highpass=f=90,afftdn=nr=10,"
                  f"acompressor=threshold=-20dB:ratio=2.5:attack=5:release=150,"
                  f"loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=out:st={out_fade}:d=0.12")
            mastered = os.path.join(td, "mastered.mp4")
            cmd = ["ffmpeg", "-y", "-v", "error", "-i", cut_raw, "-af", af]
            crop_expr = "crop=trunc(ih*9/16/2)*2:ih,scale=1080:1920" if a.vertical else ""  # 9:16 center crop
            do_grade = (not a.no_grade) and os.path.isfile(GRADE_LUT)
            lut_expr = f"lut3d=file='{GRADE_LUT.replace(':', chr(92) + ':')}'" if do_grade else ""

            vchain = []
            if crop_expr:
                vchain.append(crop_expr)
            # Auto-exposure: lift dark sources to a consistent level so the grade
            # EXPOSES the face, not just tints it. Probed through the real crop+lut
            # chain; only brightens, clamped — well-lit footage is left as-is.
            if do_grade:
                lift_gamma = auto_expose_gamma(cut_raw, crop_expr, lut_expr)
                if lift_gamma > 1.0:
                    vchain.append(f"eq=gamma={lift_gamma}")
            if lut_expr:
                vchain.append(lut_expr)
            if vchain:
                vchain.append("format=yuv420p")   # mandatory after lut3d / crop for QuickTime
                cmd += ["-vf", ",".join(vchain), "-c:v", "libx264", "-crf", "18", "-preset", "medium"]
            else:
                cmd += ["-c:v", "copy"]
            cmd += ["-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", mastered]
            subprocess.run(cmd, check=True, cwd=td)

            # 3. verify (re-transcribe, fail on dupes) on the mastered temp
            verify_ok, verify_msg = True, "skipped"
            if not a.no_verify:
                r = subprocess.run(
                    [sys.executable, os.path.join(SK, "verify.py"), mastered],
                    capture_output=True, text=True, cwd=td)
                verify_ok = (r.returncode == 0)
                verify_msg = ((r.stdout or "") + (r.stderr or "")).strip()[-600:]

            # 4. swap into place atomically — the live preview file is never half-written
            final_dur = probe_dur(mastered)
            os.replace(mastered, a.out)

        print(json.dumps({"ok": True, "duration": round(final_dur, 2),
                          "verify_ok": verify_ok, "verify_msg": verify_msg,
                          "exposure_gamma": round(lift_gamma, 2)}))
    except subprocess.CalledProcessError as e:
        print(json.dumps({"ok": False, "error": f"{os.path.basename(e.cmd[0])} failed (exit {e.returncode})"}))
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
