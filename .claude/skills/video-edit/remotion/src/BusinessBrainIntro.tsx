/**
 * BusinessBrainIntro — moody, filmic cold-open for the "Business Brain" longform.
 * Direction (locked with Luuk): MOODY & FILMIC, faster. Side/profile shot (LUT-graded, letterboxed)
 * as hero; clean Kikkertweg-53 voice (sped 1.15×, lip-locked). Captions are CINEMATIC KEYWORD
 * fragments kinetic-typed into the left negative space (not full sentences). Claude's response
 * (thinking → rising revenue graph) builds as an OVERLAY on the footage WHILE he's still talking,
 * then a clean cut into the hook.
 */
import React from "react";
import {
  AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, interpolate, spring,
  useCurrentFrame, useVideoConfig, staticFile, Easing,
} from "remotion";

const FPS = 30;
const f = (sec: number) => Math.round(sec * FPS);

const RAISIN = "#0F121A";
const LIME = "#CFFF05";
const SILVER = "#B5BFC2";
const CLAY = "#D97757";
const SANS = "'Space Grotesk', 'Helvetica Neue', sans-serif";
const MONO = "'JetBrains Mono', 'SF Mono', Menlo, monospace";
const SERIF = "'Playfair Display', Georgia, serif";
const EASE = Easing.bezier(0.45, 0, 0.18, 1);

const END = 18.7;
const BARH = 0.1278;

// kinetic keyword fragments (sped intro time). Each is placed DIFFERENTLY — varied x/y/size/rot,
// white text with an animated lime marker under the key word. Premium editorial, not stacked.
type Kw = { t: string; key: string; at: number; x: number; y: number; size: number; rot: number };
const KW: Kw[] = [
  { t: "all my revenue", key: "revenue", at: 3.45, x: 4, y: 17, size: 5.0, rot: -3 },
  { t: "my products", key: "products", at: 4.86, x: 19, y: 39, size: 3.9, rot: 2 },
  { t: "support messages", key: "support", at: 6.13, x: 3, y: 30, size: 4.0, rot: -1 },
  { t: "the margins", key: "margins", at: 7.51, x: 22, y: 19, size: 4.4, rot: 3 },
  { t: "competitors", key: "competitors", at: 11.30, x: 5, y: 42, size: 4.6, rot: -2 },
];
// once the real Claude response is on screen, NO caption text overlaps it.
const CLAUDE_IN = 12.9;

const GRAIN_URI = "data:image/svg+xml;utf8," + encodeURIComponent(
  `<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/><feColorMatrix type='saturate' values='0'/></filter><rect width='240' height='240' filter='url(#n)' opacity='0.55'/></svg>`
);

const Flash: React.FC<{ at: number; color?: string; peak?: number; up?: number; down?: number }> = ({ at, color = "#fff", peak = 0.5, up = 1, down = 5 }) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [at, at + up, at + up + down], [0, peak, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  if (o <= 0) return null;
  return <AbsoluteFill style={{ background: color, opacity: o, pointerEvents: "none" }} />;
};

const Sfx: React.FC<{ src: string; at: number; volume?: number; rate?: number }> = ({ src, at, volume = 0.4, rate = 1 }) => (
  <Sequence from={at} durationInFrames={f(1.6)}><Audio src={staticFile(src)} volume={volume} playbackRate={rate} /></Sequence>
);

export const BusinessBrainIntro: React.FC = () => {
  const frame = useCurrentFrame();
  const { width: W, height: H } = useVideoConfig();
  const u = W / 100;

  const push = 1.05 + interpolate(frame, [0, f(END)], [0, 0.06], { extrapolateRight: "clamp", easing: Easing.linear });
  const dx = Math.sin(frame / 120) * 0.1, dy = Math.cos(frame / 150) * 0.08;
  const openFade = interpolate(frame, [0, f(0.7)], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const scrim = interpolate(frame, [f(2.6), f(3.4)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: "#000", fontFamily: SANS }}>
      {/* hero: LUT-graded side shot (muted) + clean sped VO */}
      <AbsoluteFill style={{ transform: `translate(${dx * u}px, ${dy * u}px) scale(${push})` }}>
        <OffthreadVideo src={staticFile("intros/businessbrain/side_lut_fast.mp4")} muted
          style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </AbsoluteFill>
      <Audio src={staticFile("intros/businessbrain/voice_clean_fast.wav")} />

      {/* left scrim for overlay legibility (cinematic) */}
      <AbsoluteFill style={{ pointerEvents: "none", opacity: scrim,
        background: "linear-gradient(90deg, rgba(5,7,12,0.72) 0%, rgba(5,7,12,0.34) 26%, transparent 48%)" }} />

      {/* opening hook: "Hey Claude" + logo + live voice waveform (talking to Claude) */}
      <HeyClaudeHook u={u} W={W} H={H} />

      {/* kinetic keyword captions + Claude response overlay (while he talks) */}
      <KineticKeywords u={u} H={H} />
      <ClaudeResponse u={u} W={W} H={H} />

      {/* vignette + grain */}
      <AbsoluteFill style={{ pointerEvents: "none", background: "radial-gradient(ellipse 82% 74% at 52% 46%, transparent 48%, rgba(0,0,0,0.6) 100%)" }} />
      <AbsoluteFill style={{ pointerEvents: "none", opacity: 0.055, mixBlendMode: "overlay",
        backgroundImage: `url("${GRAIN_URI}")`, backgroundSize: `${u * 12.5}px`,
        transform: `translate(${(frame % 3) * 3}px, ${(frame % 2) * -3}px)` }} />

      {/* 2.39:1 letterbox */}
      <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: `${BARH * 100}%`, background: "#000", pointerEvents: "none" }} />
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: `${BARH * 100}%`, background: "#000", pointerEvents: "none" }} />

      <RecTag u={u} />
      <AbsoluteFill style={{ background: "#000", opacity: openFade, pointerEvents: "none" }} />

      <Flash at={f(END) - 5} color={LIME} peak={0.26} up={2} down={5} />
      <Flash at={f(END) - 1} color="#ffffff" peak={0.9} up={1} down={4} />

      <Audio src={staticFile("music/bg-brand-minimal-genA.mp3")}
        volume={(ff) => interpolate(ff, [0, f(2), f(END) - f(2), f(END)], [0, 0.26, 0.26, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />
      <Sfx src="higgs/sfx/whoosh.wav" at={f(CLAUDE_IN) - 3} volume={0.2} rate={0.95} />
    </AbsoluteFill>
  );
};

/* ---------------- kinetic keyword captions — varied, premium, marker under key word --------- */
const KineticKeywords: React.FC<{ u: number; H: number }> = ({ u, H }) => {
  const frame = useCurrentFrame();
  return (
    <div style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
      {KW.map((k, i) => {
        const at = f(k.at);
        const next = i < KW.length - 1 ? f(KW[i + 1].at) : f(END);
        // all keywords must clear the screen before the real Claude response appears
        const outAt = Math.min(next, at + f(2.6), f(CLAUDE_IN - 0.25));
        if (frame < at - 8 || frame > outAt + 9) return null;
        // reveal: clip-wipe from left + rise, settle
        const rev = interpolate(frame, [at, at + 9], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASE });
        const outP = interpolate(frame, [outAt - 3, outAt + 8], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        const op = Math.min(interpolate(frame, [at - 2, at + 5], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }), outP);
        const marker = interpolate(frame, [at + 5, at + 15], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASE });
        const isLast = k.key === "10×?";
        const lines = k.t.split("\n");
        return (
          <div key={i} style={{
            position: "absolute", left: `${k.x}%`, top: `${k.y}%`,
            opacity: op, transform: `translateY(${(1 - rev) * u * 1.4}px) rotate(${k.rot}deg)`, transformOrigin: "left top",
          }}>
            {/* index kicker */}
            <div style={{ fontFamily: MONO, fontSize: u * 1.0, letterSpacing: "0.3em", color: SILVER, opacity: 0.6 * op, marginBottom: u * 0.5 }}>
              {isLast ? "THE ASK" : String(i + 1).padStart(2, "0")}
            </div>
            <div style={{ position: "relative", display: "inline-block", clipPath: `inset(0 ${(1 - rev) * 100}% 0 0)` }}>
              <div style={{
                fontFamily: SANS, fontWeight: 700, fontSize: u * k.size, lineHeight: 0.96, letterSpacing: "-0.02em",
                color: isLast ? LIME : "#F6F8F9", whiteSpace: "pre-line", textShadow: "0 6px 30px rgba(0,0,0,0.85)",
              }}>
                {lines.map((ln, j) => <div key={j}>{ln}</div>)}
              </div>
              {/* lime marker swipe under the key word (last line) */}
              {!isLast && (
                <div style={{
                  position: "absolute", left: 0, bottom: -u * 0.5, height: u * 0.7,
                  width: `${marker * 100}%`, background: LIME, borderRadius: u * 0.1, opacity: 0.9,
                  boxShadow: `0 0 ${u * 0.8}px rgba(207,255,5,0.5)`,
                }} />
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

/* ---------------- REAL Claude response (screen recording, screen-blend, no box) ------------- */
const ClaudeResponse: React.FC<{ u: number; W: number; H: number }> = ({ u, W, H }) => {
  const frame = useCurrentFrame();
  const inAt = f(CLAUDE_IN);
  if (frame < inAt - 4) return null;
  const op = interpolate(frame, [inAt, inAt + f(0.9)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const outO = interpolate(frame, [f(END) - 5, f(END)], [1, 0.4], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const rise = interpolate(frame, [inAt, inAt + f(1.2)], [1.5, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASE });
  // the screen rec is dark-bg + light text → screen blend drops the bg, only the real text glows.
  const feather = "radial-gradient(ellipse 62% 70% at 42% 45%, #000 40%, rgba(0,0,0,0) 82%)";
  return (
    <div style={{
      position: "absolute", left: "1%", top: "44%", width: "50%", height: "48%",
      opacity: op * outO, transform: `translateY(${rise * u}px)`,
      mixBlendMode: "screen", pointerEvents: "none",
      maskImage: feather, WebkitMaskImage: feather,
    }}>
      <OffthreadVideo src={staticFile("intros/businessbrain/screen.mp4")} muted
        style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "12% 24%", filter: "brightness(1.15) contrast(1.05)" }} />
    </div>
  );
};

/* ---------------- opening hook: "Hey Claude" — monochrome, cinematic ---------------- */
const HeyClaudeHook: React.FC<{ u: number; W: number; H: number }> = ({ u, W, H }) => {
  const frame = useCurrentFrame();
  const inAt = f(0.85);
  const outStart = f(2.9), outEnd = f(3.45);
  if (frame < inAt - 2 || frame > outEnd) return null;
  const op = Math.min(
    interpolate(frame, [inAt, inAt + 9], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }),
    interpolate(frame, [outStart, outEnd], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
  );
  const rise = interpolate(frame, [inAt, inAt + 12], [u * 1.1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASE });
  const INK = "#F1F3F4"; // single tone — everything is this off-white
  const spark = u * 3.4;
  const bars = 30;
  return (
    <div style={{ position: "absolute", left: "6%", top: "36%", opacity: op, transform: `translateY(${rise}px)`, pointerEvents: "none" }}>
      <div style={{ display: "flex", alignItems: "center", gap: u * 1.3 }}>
        {/* Claude spark, drawn as a clean white burst (monochrome) */}
        <svg width={spark} height={spark} viewBox="0 0 100 100" style={{ transform: `rotate(${frame * 0.4}deg)`, opacity: 0.95 }}>
          {Array.from({ length: 11 }).map((_, i) => {
            const ang = (i / 11) * Math.PI * 2 - Math.PI / 2;
            const inner = 7;
            const outer = 34 + 10 * Math.abs(Math.sin(i * 1.7));
            return <line key={i}
              x1={50 + Math.cos(ang) * inner} y1={50 + Math.sin(ang) * inner}
              x2={50 + Math.cos(ang) * outer} y2={50 + Math.sin(ang) * outer}
              stroke={INK} strokeWidth={5.4} strokeLinecap="round" />;
          })}
        </svg>
        <span style={{ fontFamily: SANS, fontWeight: 600, fontSize: u * 5.4, letterSpacing: "-0.01em", color: INK, whiteSpace: "nowrap", textShadow: "0 4px 30px rgba(0,0,0,0.8)" }}>
          Hey Claude
        </span>
      </div>
      {/* thin, single-tone voice waveform */}
      <div style={{ display: "flex", alignItems: "center", gap: u * 0.3, height: u * 2.4, marginTop: u * 1.2, marginLeft: u * 0.3 }}>
        {Array.from({ length: bars }).map((_, i) => {
          const env = interpolate(frame, [f(1.0), f(1.4), outStart - 3, outStart], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const a = Math.abs(Math.sin(frame * 0.38 + i * 0.7));
          const b = Math.abs(Math.sin(frame * 0.16 + i * 1.3));
          const h = (0.14 + 0.86 * a * (0.55 + 0.45 * b)) * env;
          return <div key={i} style={{
            width: u * 0.26, height: `${Math.max(3, h * u * 2.4)}px`, borderRadius: u * 0.2,
            background: INK, opacity: 0.28 + 0.4 * h,
          }} />;
        })}
      </div>
    </div>
  );
};

/* ---------------- filmic REC timecode ---------------- */
const RecTag: React.FC<{ u: number }> = ({ u }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [f(0.5), f(1.2)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const blink = Math.floor(frame / 15) % 2 === 0;
  const ss = Math.floor(frame / FPS), ff = frame % FPS;
  const tc = `00:${String(ss).padStart(2, "0")}:${String(ff).padStart(2, "0")}`;
  return (
    <div style={{ position: "absolute", right: u * 4, top: `${BARH * 100 + 3}%`, display: "flex", alignItems: "center", gap: u * 0.7, opacity: p * 0.8 }}>
      <div style={{ width: u * 0.6, height: u * 0.6, borderRadius: "50%", background: CLAY, opacity: blink ? 1 : 0.25, boxShadow: `0 0 ${u * 0.6}px ${CLAY}` }} />
      <div style={{ fontFamily: MONO, fontSize: u * 1.0, letterSpacing: "0.22em", color: SILVER }}>REC</div>
      <div style={{ fontFamily: MONO, fontSize: u * 1.0, letterSpacing: "0.14em", color: SILVER, opacity: 0.8, marginLeft: u * 0.4 }}>{tc}</div>
    </div>
  );
};

export default BusinessBrainIntro;
