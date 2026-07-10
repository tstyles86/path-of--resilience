---
name: video-cut-aligned
description: >-
  Cut a raw talking-head recording into clean, fast-paced shorts using FORCED
  ALIGNMENT — the high-quality method (Descript-grade, $0, fully local). Use this
  whenever Luuk wants shorts/clips cut from a raw talking-head take: "cut my
  shorts", "cut this recording", "make shorts from this", "remove the retakes",
  "tighten this", or when he drops a file in ~/Movies/BuildLoop/_INBOX/. This is
  the CURRENT standard cutter and SUPERSEDES the older "video-cut" skill — prefer
  this one for any talking-head cut; the old energy-detection method clips words
  and leaks false-starts on glued footage. Handles multi-take "yapping" where each
  line is re-said several times. Produces a rendered MP4 + an editable DaVinci
  timeline (FCPXML/EDL). NOT for cutting screen recordings or already-finished
  videos, and NOT for adding captions/music (that's the finishing/edit step).
---

# Video Cut — Forced-Alignment (the good cutter)

Turns a **raw, multi-take talking-head recording** (Luuk re-says each line several times, with filler, false-starts, and dead air) into a **tight, clean short** — and does it well on his *exceptionally glued* footage (almost no silence between words/sentences), which is exactly where naive cutters fail.

## Why this method (read first — it's the whole point)

The old `video-cut` skill found cut points from **audio energy**. That works only when there's silence between words. On glued/disfluent speech it can't find a boundary, so it **clips word-tails and leaks false-starts** ("...but I recently", "...leaked because"). It also runs blind — you can't hear the result.

This skill fixes that with **forced alignment**: it computes the *sample-accurate start/end of every word*, then places each cut **inside the tiny silence gap between two words** — never mid-syllable. That single change is what closes the gap to Descript-quality, for free, locally. (Validated 2026-06-20 on the "$2,500 Google bill" short.)

Two more hard-won pieces:
- **Literal transcription** (`condition_on_previous_text=False`) — the default whisper *smooths away* disfluencies (it hid an "I am I'm" stutter and a "very shit" flub). Literal mode exposes them so you don't pick a flawed take.
- **Crossfade joins** — short video `xfade` + audio `acrossfade` smooth the head-position jumps between takes and avoid clicks.

## Luuk's hard rule

**He NEVER re-records.** Cut the short from the content exactly as recorded. If a line has no clean take anywhere (flub/stutter/pause in all of them — like the "I'm very ashamed" hook here), **drop or replace that beat** with the cleanest alternative. Never ask him to re-record.

## Prerequisites (already set up on this machine)

- `ffmpeg` / `ffprobe`, Python 3 with `faster_whisper`, `torch`+`torchaudio` (2.1.x).
- First run downloads the MMS_FA alignment model (~1.18GB) to torch hub — one time.
- `torchaudio.load` has no audio backend here → the scripts load WAVs via the `wave` module (already handled).

## Folder structure

Recordings live under `~/Movies/BuildLoop/` (see `~/Movies/BuildLoop/_GUIDES/FOLDER_STRUCTURE.md`). New raw files arrive in `_INBOX/`. For each recording, work inside its dated folder:
`1_RAW/` (source) · `2_SOURCE/` (your working files) · `3_SHORTS/` (rendered shorts) · `4_TIMELINES/` (FCPXML/EDL) · `5_DAVINCI/` · `6_EXPORTS/`.

If the raw is still in `_INBOX/`, first create `~/Movies/BuildLoop/<YYYY-MM-DD>_<slug>/` with those subfolders and move the raw into `1_RAW/`.

## Workflow

Let `RAW` = the raw file in `1_RAW/`, `W` = the recording's `2_SOURCE/` working dir. Run python from `W`. `SK` = this skill's `scripts/` dir.

### 1. Extract a 16k mono WAV
```bash
ffmpeg -y -v error -i "$RAW" -vn -ac 1 -ar 16000 "$W/audio16k.wav"
```

### 2. Literal transcription (exposes the disfluencies)
```bash
python3 "$SK/transcribe_literal.py" "$W/audio16k.wav" "$W/lit" 0
```
Writes `lit_words.json` + `lit_segments.json`. Read `lit_segments.json` to map the recording: each distinct line is re-said several times (those repeats are the takes). A ~12-min file has several topic blocks separated by long gaps — **each block is usually one short.**

### 3. Forced alignment (sample-accurate word boundaries)
For each region you're cutting, align its word sequence to the audio. Align a slice to keep it fast and memory-light:
```bash
# slice the region's audio (example: a short living 515–630s), offset = slice start
ffmpeg -y -v error -ss 515 -to 630 -i "$RAW" -vn -ac 1 -ar 16000 "$W/region.wav"
python3 "$SK/transcribe_literal.py" "$W/region.wav" "$W/region_lit" 515
python3 "$SK/align.py" "$W/region.wav" "$W/region_lit_words.json" "$W/region_aligned.json" 515
```
`region_aligned.json` has `{word, start, end, score}` per word, in global seconds.

### 4. Pick takes + place cuts IN THE GAPS (the judgment step)
Dump the aligned words with the gaps between them and choose:
```bash
python3 - <<'PY'
import json
w=json.load(open("region_aligned.json")); prev=None
for x in w:
    g=x['start']-prev if prev is not None else 0
    print(f"{x['start']:7.3f}-{x['end']:7.3f} {x['word']!r}{'   <<GAP %.2f>>'%g if g>0.18 else ''}")
    prev=x['end']
PY
```
Rules that make it clean:
- **For each line, keep the cleanest take.** The literal transcript shows repeats and flubs — avoid takes with internal repeats/false-starts.
- **Set each segment's `cs`/`ce` to land INSIDE a silence gap** (a `<<GAP>>` ≥ ~0.2s), not at a word edge. Cutting in the gap is what prevents leaks/clips. E.g. if "but" ends 522.74 and "I" starts 522.96, start the hook at ~522.86.
- Prefer one continuous take over stitching when a clean multi-sentence run exists (fewer joins = better flow).
- **If a line has no clean take, drop it.** Don't force a flubbed/glued one. The short reads fine without it.

Write the **canonical per-short keepers file** `$W/_pipeline/<SHORTNAME>_keepers.json` (this exact name + location is what the media agent's `/keepers` and the back-office "Edit cut" timeline read & write — always keep it current so Luuk's self-serve edits and your cuts share one source of truth):
```json
[{"cs": 522.86, "ce": 525.85, "label": "hook"}, {"cs": 537.20, "ce": 539.25, "label": "not-using"}]
```

### 5. Cut (crossfade) + master the audio

**Shortcut (does cut + master + verify in one, atomic):**
```bash
python3 "$SK/recut.py" --input "$RAW" --keepers "$W/_pipeline/<SHORTNAME>_keepers.json" --out "<REC>/3_SHORTS/<SHORTNAME>.mp4" --xf 0.05
```
`recut.py` is the SAME code the media agent's `/recut` runs, so your cuts and Luuk's self-serve edits are byte-identical. It prints `{"ok":..,"duration":..,"verify_ok":..}`. Use this for re-cuts; use the explicit steps below when you want to inspect the intermediate `cut_raw.mp4`. **It also applies the BuildLoop cinematic grade by default** — the same b-roll Rec709 LUT (`~/.claude/skills/broll-ingest/luts/buildloop-FINAL.cube`); pass `--no-grade` to skip. So every exported short is graded (one-time backfill of existing shorts: `ffmpeg -i SHORT.mp4 -vf "lut3d=file='<LUT>',format=yuv420p" -c:v libx264 -crf 18 -preset medium -c:a copy -movflags +faststart OUT.mp4`).

```bash
python3 "$SK/cut_xf.py" --input "$RAW" --keepers "$W/_pipeline/<SHORTNAME>_keepers.json" --out "$W/cut_raw.mp4" --xf 0.05
DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$W/cut_raw.mp4")
OUT=$(python3 -c "print(round(float('$DUR')-0.12,3))")
ffmpeg -y -v error -i "$W/cut_raw.mp4" \
  -af "afade=t=in:st=0:d=0.05,highpass=f=90,afftdn=nr=10,acompressor=threshold=-20dB:ratio=2.5:attack=5:release=150,loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=out:st=${OUT}:d=0.12" \
  -c:v copy -c:a aac -b:a 192k -movflags +faststart "<REC>/3_SHORTS/<SHORTNAME>.mp4"
```
`--xf` is the crossfade length. Keep it short (~0.05). If a join eats a boundary word, shorten `--xf` or nudge that window's `cs`/`ce` deeper into the gap.

### 6. Verify — MANDATORY gate
```bash
cd /tmp && python3 "$SK/verify.py" "<REC>/3_SHORTS/<SHORTNAME>.mp4"
```
`verify.py` re-transcribes the output and **fails on any repeated phrase**; also reports leading dead air + gaps. A cut is NOT done until it reports `CONTENT: clean`. If it fails, re-pick the take / move the cut deeper into the gap, re-cut, re-verify. (Note: the re-transcription is itself imperfect — it may print a phantom leading word or mis-hear one word; trust it for *duplicates/clips*, and do a final listen for nuance.)

### 7. Editable DaVinci timeline
```bash
python3 "$SK/make_timeline.py" --input "$RAW" --keepers "$W/keepers.json" --outdir "<REC>/4_TIMELINES" --name "<SHORTNAME>"
```
Writes `<SHORTNAME>.fcpxml` + `.edl` referencing the raw, so Luuk can re-tweak takes by hand (see `~/Movies/BuildLoop/_GUIDES/DAVINCI_RESOLVE_GUIDE.md`).

### 8. Publish + SHARE the editor link — MANDATORY, automatically, the FIRST time you cut

**The moment you have a first watchable cut (`verify.py` reports clean), publish it to the back office and SHARE THE EDITOR URL with Luuk — without being asked.** This is non-negotiable and it is the point of the whole flow: Luuk reviews the cut in the editor to confirm the workflow/story is laid out well BEFORE you keep going. Don't sit on a cut you only have as a local file — a cut he can't watch is a cut he can't approve. So: cut → verify → **publish + paste the link** → pause for his review.

"Publish" means make the editor FULLY functional, not just drop a URL. Do all four (they're detailed below): (1) the **`content_pieces` upsert** with `metadata.preview_url` → gives you `https://backoffice.build-loop.ai/content/<id>`; (2) the **dense-keyframe proxy** (so playback is smooth, lesson in "the self-serve editor"); (3) the **per-word file** — generate it straight from the alignment you already have (`[{word,cs,ce,kept}]`, kept = word midpoint inside a keeper), NOT a slow re-transcribe; (4) the **thumbnail sprite** (filmstrip). Match `platform`/`content_type`/`production_format` to the real aspect ratio (see the ⚠ below). Then post the link plainly: **"Review the cut here → https://backoffice.build-loop.ai/content/<id>"** and stop for feedback. The bytes stream live from his Mac, so confirm the Mac is on if the player 404s.

The bytes stream from the local media agent (the same one the Content Hub uses — bytes stay local, $0 storage; **Luuk's Mac must be on** to play). Build the URL and **read the key from the file — never hardcode it** (it can rotate):
```bash
KEY=$(cat ~/Movies/BuildLoop/_TOOLS/.agent_key)
echo "https://media.build-loop.ai/video?f=<SHORTNAME>.mp4&key=$KEY"
```

Then register it in Supabase through the **Supabase MCP** (`execute_sql`, project `xchadavewdhgirwpkkzk` — Luuk's back office). This single statement is **idempotent**: it refreshes the existing piece for this short if one exists (matched on `metadata->>'source_short'`), otherwise creates one in `editing`. Re-cutting just updates the URL — it never duplicates:
```sql
with upd as (
  update content_pieces
     set metadata = jsonb_set(coalesce(metadata,'{}'::jsonb), '{preview_url}', to_jsonb('<URL>'::text), true),
         updated_at = now()
   where metadata->>'source_short' = '<SHORTNAME>.mp4'
  returning id
)
insert into content_pieces
  (user_id, title, status, platform, content_type, production_format, created_by, notes, metadata)
select 'b9402fae-a601-4491-837d-504c8f1712ac'::uuid,
       '<TITLE>', 'editing', 'youtube_shorts', 'short_form', 'short', 'video-cut-aligned',
       'Cut by video-cut-aligned from <REC>. Inline preview streams from media.build-loop.ai (Mac must be on).',
       jsonb_build_object('preview_url','<URL>','source_recording','<REC>','source_short','<SHORTNAME>.mp4','cut_by','video-cut-aligned')
where not exists (select 1 from upd);
```
Fill `<URL>` (from the `echo` above, key included), `<SHORTNAME>.mp4`, `<REC>` (recording folder, e.g. `2026-06-20_prompt-machine-monologue`), and `<TITLE>` (a short working title — Luuk renames in the editor). **⚠ Match `platform`/`content_type`/`production_format` to the ACTUAL video — the values above (`youtube_shorts`/`short_form`/`short`) are for a 9:16 vertical short. If the cut is a 16:9 HORIZONTAL video (a screencast / long-form / sit-down — check the rendered file's dimensions, `ffprobe ... width,height`), use `platform='youtube'`, `content_type='long_form'`, and `production_format='screenshare-tutorial'` (screen demo) or `'sit-down'` (talking head). Getting this wrong makes the editor frame a landscape video in the vertical shorts player. If you cut this short FROM an already-planned content piece, set that piece's `metadata.source_short` to the filename *first* so the upsert targets it instead of creating a new row. (`b9402fae-…` is Luuk's user_id; the key lives in `_TOOLS/.agent_key`.)

### 9. Acting on review feedback ("feedback is in")

Luuk reviews cuts in the back office and leaves **timecoded notes** on the inline player (Frame.io-style). When he says **"feedback is in"**, drain the queue:

1. **Read the queued notes** via the Supabase MCP (project `xchadavewdhgirwpkkzk`):
   ```sql
   select f.id, f.content_piece_id, cp.title, f.t_seconds, f.t_end_seconds, f.kind, f.body
   from cut_feedback f join content_pieces cp on cp.id = f.content_piece_id
   where f.status = 'ready' order by cp.title, f.t_seconds;
   ```
   (`ready` = he hit "Send to Claude". If nothing's `ready`, also check `status='open'` — he may have skipped that button.)

2. **Map each timecode CUT-time → SOURCE-time.** `t_seconds` is in the *short's* timeline (what he watched); `keepers.json` is in *source* seconds. Walk the keepers in order accumulating each window's duration (`ce-cs`); the note at cut-time `T` lands in the window whose running total brackets `T`, at `source = cs + (T - running_total_before_that_window)`. (Crossfades trim ~`xf` per join, so the map drifts a few hundred ms over many cuts — confirm the exact beat against `region_aligned.json` words.)

3. **Apply, then re-cut.** Edit `keepers.json`:
   - `kind='edit'` "trim/cut/delete <range>" → move that window's `cs`/`ce` deeper into a gap, or drop the window entirely.
   - "abrupt jump / soften" → widen `--xf` for that join or nudge the boundary into a cleaner gap.
   - `kind='note'` → judgment; re-pick the take or adjust as described.
   Re-run **steps 5–6** (cut + master + verify) and **step 8** (the preview upsert — keep the SAME `<SHORTNAME>.mp4`, so `preview_url` is unchanged and the player just re-fetches the new bytes).

4. **Close the loop** — mark what you applied:
   ```sql
   update cut_feedback set status='addressed', addressed_at=now() where id in (<applied ids>);
   ```
   Use `status='wontfix'` for any you deliberately skip, and tell Luuk which and why.

### The self-serve editor (how it ties in)

The back office has a **Descript-style transcript editor** ("Edit by transcript"): Luuk deletes words/sentences from the cut's transcript and re-renders without you (deleting a word notches exactly its source span out of the keepers). It reads the canonical `<REC>/2_SOURCE/_pipeline/<SHORTNAME>_keepers.json` + the per-word `<SHORTNAME>_words.json` through the media agent and re-renders via `/recut` → `scripts/recut.py` (~30s). So the keepers file is the **shared source of truth** — when you cut (step 5) or apply feedback (step 9), write the adjusted windows back to it AND regenerate the words file so his editor matches: `python3 "$SK/words_for_short.py" --input "$RAW" --keepers "$W/_pipeline/<SHORTNAME>_keepers.json" --out "$W/_pipeline/<SHORTNAME>_words.json"` (transcribe region once + force-align + tag kept; `/recut` also re-tags it automatically after a render). The editor plays a lightweight **proxy** of the raw for smooth in-browser scrubbing (the raw is huge / not faststart). Generate it once per recording (≈23MB for 12min). **⚠ The proxy MUST have a keyframe at every clip start, or the editor's playback stutters.** `ClipEditor.tsx` plays clips by SEEKING the proxy (`v.currentTime = clip.cs`) at each boundary; with a default ~10s GOP, that seek decodes from a far-back keyframe and the audio stalls — the user hears "too big a gap between clips," and the preview sounds gappier than the seamless final render even though the cut is identical. Fix: force a keyframe at every keeper `cs` (plus a dense periodic one for mid-clip scrubbing). Drop the cinematic LUT for a SCREEN recording (it's a UI capture, not graded footage):
```bash
CS=$(python3 -c "import json;print(','.join(f'{k[\"cs\"]:.3f}' for k in json.load(open('$W/_pipeline/<SHORTNAME>_keepers.json'))))")
ffmpeg -y -v error -i "$RAW" -vf "scale=-2:540,format=yuv420p" -c:v libx264 -preset veryfast -crf 28 \
  -force_key_frames "$CS" -g 15 -keyint_min 1 -sc_threshold 0 -c:a aac -b:a 96k -movflags +faststart "$W/_proxy.mp4"
# (talking-head footage: keep the LUT — add lut3d=file='$HOME/.claude/skills/broll-ingest/luts/buildloop-FINAL.cube' before format=yuv420p)
# Re-run this whenever the keepers change (the cs list moves), so the forced keyframes stay aligned to the clip starts.
```
The final export still renders from the full-res `$RAW`. Agent endpoints (key-gated via `_TOOLS/.agent_key`): `GET /keepers?rec=&short=` (returns `{keepers, xf, thumbs}`), `GET /proxy?rec=` (the 540p source proxy), `GET /words?rec=&short=`, `GET /thumbs?rec=` (the filmstrip sprite), `POST /recut {rec,short,keepers,xf?}`.

**Filmstrip thumbnails (the editor's Descript-style timeline).** The ClipEditor renders the timeline as a strip of real frames sampled from a sprite. Generate it once per recording (alongside the proxy), and the `_thumbs.json` meta is what `/keepers` returns as `thumbs`:
```bash
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$W/_proxy.mp4" | cut -d. -f1)
COUNT=$(( (DUR + 1) / 2 )); COLS=30; ROWS=$(( (COUNT + COLS - 1) / COLS ))   # 1 frame / 2s, 96x54 cells
ffmpeg -y -v error -i "$W/_proxy.mp4" -vf "fps=1/2,scale=96:54,tile=${COLS}x${ROWS}:padding=0:margin=0" -frames:v 1 -q:v 5 "$W/_thumbs.jpg"
python3 -c "import json;json.dump({'interval':2.0,'cols':$COLS,'rows':$ROWS,'cellW':96,'cellH':54,'count':$COUNT},open('$W/_thumbs.json','w'))"
```
The agent (`~/Movies/BuildLoop/_TOOLS/hub.py`, launchd `ai.buildloop.mediaagent`) serves `/thumbs` (the jpg) and embeds `_thumbs.json` in the `/keepers` response. It is LOCAL + unversioned — if hub.py is ever reset, re-add the `/thumbs` GET handler (mirror `/proxy`) + the `thumbs` field in `/keepers`, then `launchctl kickstart -k gui/$(id -u)/ai.buildloop.mediaagent`. The editor falls back to plain solid clips when no sprite exists, so this step is optional-but-nice.

## Output

Per short: a clean mastered MP4 in `3_SHORTS/`, an editable timeline in `4_TIMELINES/`, and a `content_pieces` row in the back office carrying `metadata.preview_url` so the cut plays inline in the Content editor. The source is 16:9; the 9:16 reframe + captions + music happen in the finishing step (DaVinci or the edit skill), not here.

## The lessons, condensed (don't relearn these)

1. **Cut in the gaps, not at energy edges** — forced alignment gives the gaps; that's the whole method.
2. **Literal transcription** (`condition_on_previous_text=False`) or you'll pick takes with hidden flubs.
3. **`torchaudio.load` has no backend** — load WAVs via `wave` (scripts already do).
4. **Crossfade short** (~0.05s); too long eats boundary words.
5. **`verify.py` is mandatory** — re-transcribes and fails on dupes; run it on every short.
6. **Never re-record** — drop an un-cuttable beat instead.
7. Align in **slices** (per region) — faster and lighter than the whole 12-min file at once.
8. **Publish + SHARE the editor link on the FIRST cut, automatically** (step 8) — the instant a cut verifies clean, set up the full editor (preview_url upsert + dense-keyframe proxy + per-word file + thumbnail sprite) and paste `https://backoffice.build-loop.ai/content/<id>` to Luuk, then pause for review. Don't wait to be asked; a cut he can't watch is a cut he can't approve. The upsert is idempotent (keyed on `source_short`), so re-cuts refresh the same review URL rather than duplicate.
9. **"Feedback is in"** (step 9) — drain `cut_feedback` rows; the timecodes are in CUT time, so map them back to SOURCE via the keepers before editing. Mark rows `addressed` when done.
10. **Boundary-overlap retakes — dedup MUST check across phrase boundaries, not just whole-phrase restarts** (codified 2026-06-24). The common retake isn't a sentence re-started from its beginning; it's a clause that TRAILS OFF the end of one phrase and gets re-said at the START of the next ("…but also for example make scripts" | "but also for example make scripts in Claude…"). Whole-phrase / same-first-words dedup never sees it — the duplicate straddles the gap. Fix: after the restart-collapse pass, run a boundary-overlap pass — if the last K words of keeper A equal the first K words of keeper B (**K≥2**), trim A's trailing K words (the false-start) and keep B's completed take. **Use K≥2, not K≥3** — a 2-word trail-off is common ("…let Claude **interact with**" | "**interact with** fish"); K≥3 misses it. The false-positive risk (a legit 2-word anadiplosis) is negligible in demo speech. **Sibling case: WITHIN-phrase repeats.** When the duplicate is glued inside ONE phrase (no gap, so it never splits — "and it now sounds like this **and it now sounds like this**", "you did it **you did it**"), a separate within-phrase pass must scan each phrase for a repeated consecutive n-gram (L≥3) and keep the LATER occurrence (drop the first block). (Both implemented in `build_keepers_final.py`: pass 2 = boundary-overlap K≥2, pass 3 = within-phrase repeat.)
11. **`verify.py` is mandatory on EVERY render path — the xfade chain silently collapses past ~30-40 segments** (codified 2026-06-24). `cut_xf.py`'s nested xfade filter breaks on long cuts: a 130-segment cut REPORTED 473s but output only 62s, dropping everything after the first ~11 joins. For many-segment cuts (screen demos, full videos), render with the **concat filter** in one pass (`[0:v]trim=start:end,setpts=PTS-STARTPTS[vN]; … concat=n=N:v=1:a=1[cv][ca]`) — robust at any count; hard cuts are fine for screen demos. Use `-filter_complex_script` to dodge command-length limits. **Whatever path you use, run `verify.py` on the ACTUAL output file** — bypassing `recut.py` (as the raw concat path does) also bypasses verify, which is exactly how a duplicate shipped uncaught. (Verify will FALSE-POSITIVE on legitimately-repeated playbacks — same words, different voices, like an A/B comparison — confirm those are the intended progression, not real dupes.)
12. **Semantic review pass — after the mechanical clean, Claude judges what's NEEDED, not just what's clean** (codified 2026-06-24). Forced alignment removes pauses + stutters but CANNOT know the same demo line / voice-playback was repeated 8× and we only need it 2-3× where it matters. After the mechanical pass, emit the keeper transcript (`build_keepers.py` writes `*_transcript.txt`) and do an LLM judgment pass: (a) cut redundant repeats of the same line/playback, keeping the meaningful PROGRESSION (e.g. ElevenLabs → Fish → Fish+emotion, one of each); (b) KEEP short filler lines where the SCREEN ACTION behind them carries the moment ("so we can run this", "you continue"); (c) cut rambling/redundant narration. Output a drop-list of segment indices, apply, re-render, verify. This is the intelligence layer the mechanical cutter lacks — always run it on long screencasts.
13. **The FULL retake-dedup stack for messy screencasts — exact-match alone is not enough** (codified 2026-06-24, after a 31-min screencast surfaced retake after retake). Prefix/first-word collapse misses variant retakes. Layer ALL of these in `build_keepers_final.py`, in order: (1) **normalize brand mishearings BEFORE comparing** — Whisper hears "Claude" as *clot / clod / cloud* in the same recording, so "...done with **clot** as well" vs "...done with **cloud** as well" never matches until you map them all → `claude` in the word-normalizer. Do this FIRST or every downstream pass leaks. (2) **fuzzy same-line collapse** — when adjacent phrases vary ("you **add** the following" vs "you **need to add** the following command"), exact prefix fails; collapse if word-set overlap ≥0.75 and the shorter has ≥4 words and they're <~12s apart, keeping the later/fullest take. (3) **trailing-restart trim** — A trails off with a fragment that restarts B with a *different ending* ("...and it will now **read**" | "and it will now **regenerate**…"): if A's trailing m-word suffix shares ≥3 leading words with B's start, trim that suffix off A. (4) Don't over-rely on manual source-time drop windows for adjacent retake clusters — a too-narrow window can SPLIT a cluster and leave two survivors past the merge gap; prefer letting the fuzzy/restart passes collapse the whole cluster, and reserve manual drops for NON-adjacent redundancy (repeated playbacks separated by narration). After all passes, run the repeated-4-gram scan (with a false-positive allowlist for fillers like "as you can see" and intended progressions like the A/B "hi there") — zero real repeats before you render. (5) **tail-echo guard — "keep the later take" can DELETE a whole sentence.** When you collapse a fuzzy cluster you normally keep the *last* member (the later take is usually the cleaner retake). But if someone finishes a complete sentence and then tacks on a short restatement of its ending ("...you can have a conversation with Claude and Claude will explain it, **or it can run it for you.** [pause] **Or it can run it for you.**"), the short echo is the LAST member, so keep-last throws away the complete sentence and keeps the 6-word fragment — leaving a broken cut ("but this is not something … or it can run it for you", middle gone). Guard: before appending the cluster representative, if the last member's words are a strict subset of a longer earlier member, keep the longer (complete) one instead. Apply this ONLY to the subset case — a blanket "keep longest" loosens every other cluster and re-bloats the cut. This failure reads to a viewer as "a sentence got cut in half," NOT as a duplicate, so the 4-gram scan can't catch it — only watching (or a content-gap check) will. (6) **don't let `strip_ty` clip a real trailing "you"** — stripping end-"you" to kill Whisper "thank you" hallucinations also eats legit objects ("run it for **you**", "show **you**"); guard with a preposition/verb allowlist (for/with/to/show/let/give/help/get…) before stripping.
14. **⭐ PREFERRED METHOD for messy multi-take screencasts: Claude judges the SELECTION; mechanics only align + apply** (codified 2026-06-24, after lessons 10–13 turned into endless whack-a-mole). The hard lesson from stacking six mechanical dedup passes: **"which take stays" is a comprehension task, not a string-matching task** — and every heuristic you add to approximate comprehension leaks a new edge case the user then catches by watching. Stop approximating. Split the job by what each side is actually good at:
    - **Mechanical, required:** forced-align the whole recording → word-level timestamps. (Claude can't hear word boundaries; this part stays.)
    - **Mechanical, cheap:** gap-split into phrases and emit a numbered transcript `[idx] cs-ce  text` for the FULL video (`phrases_full.txt`).
    - **Claude (the judgment):** READ the entire phrase transcript and decide, per phrase, KEEP / CUT / TRIM — choosing the best/most-complete take of each retake cluster, **deleting Whisper hallucinations** (random off-topic lines over music/silence — "setting goals is like a puzzle", "it handles the scheduling" — which a STRAY denylist can never fully enumerate but a reader spots instantly), keeping the **meaningful playback progression** (ElevenLabs→Fish→Fish+emotion, one each), dropping **orphan/stray re-recorded takes** that don't connect, and guaranteeing **every kept sentence is whole**. Encode as `KEEP=[indices]` + `TRIM={idx:('tail'|'head','word seq to end-at/start-from')}`.
    - **Mechanical, apply:** resolve each kept phrase to a `cs/ce` (whole, or trimmed at the substring boundary), run a light within-phrase repeat-collapse for glued stutters, strip the hallucinated trailing "you", render via the concat filter, then `verify.py`.
    This is `build_keepers_judged.py`. It produced a *more coherent* cut than the full heuristic stack (no broken sentences, no hallucinations, correct A/B progression) in ONE judged pass — and it's far less fragile because there's no growing pile of pattern-matchers to leak. The heuristic passes (lessons 10–13) are still fine for LIGHT cases or as the within-phrase cleanup layer, but for any long, messy, multi-take screencast: **align mechanically, then let Claude read and decide.** Cost is trivial (a 31-min recording is ~200 phrases / ~5k words — one read). The only thing the LLM must NOT invent is timestamps: it selects phrases/words by index or exact substring; the cut points always come from the alignment.
    Two apply-step gotchas that produce audible seams even when the SELECTION is perfect (both caught by the user watching, both now fixed in `build_keepers_judged.py`):
    - **(a) A mid-speech trim leaks the adjacent glued word — use a TIGHT margin on any trimmed edge.** The normal lead/trail (~0.13/0.18s) exists to avoid clipping word-tails at a *natural* phrase boundary (real silence). But when you tail- or head-TRIM a phrase mid-sentence, the next/previous word sits right against the cut (glued footage), so a 0.18s trail leaks it — e.g. trimming "...made sure | to cut it up" left the "to" audible, then the next kept segment started "to cut it up" → a doubled "**to to**". Fix: full margin only on UNTRIMMED edges (natural pauses); a tight ~0.04s margin on any trimmed edge. This is a general class — it would equally produce "we we", "the the" at any trimmed seam.
    - **(c) ⭐ CUT ONLY WHERE CONTENT WAS REMOVED — merge contiguous keepers into continuous spans.** This is the single biggest "feel" lesson. Gap-splitting the recording into phrases is a tool for SELECTION, not the cut granularity: if you keep every phrase as its own segment and hard-join them, a single flowing sentence said with a 0.5s mid-breath becomes two hard cuts and the whole video feels like a stutter ("cut up way too often"). The viewer should hear complete, naturally-paced sentences; a hard cut should only ever land where you actually deleted something. Implement as a MERGE pass after selection: walk the kept segments in source order and fuse each into the previous span when ALL hold — (i) consecutive source phrase (nothing was cut between them), (ii) neither side of the seam is a trim edge (no false-start removed there), (iii) no within-phrase dup was excised at the seam, (iv) the natural gap is a breath, not dead air (`< ~2.0s`). The result: ~80 continuous spans instead of ~110 fragments; every surviving hard cut's preceding gap maps to a real removal (a cut phrase, a trimmed false-start, or a >2s dead pause) — print that gap per span to audit it. Keep the natural sub-2s pauses; they ARE the rhythm, and on a screencast they line up with the on-screen clicks.
    - **(e) After merging for flow, COMPRESS long internal pauses — "cut only when needed" still includes cutting dead air.** Merging keeps the full natural gap between phrases (up to ~2s), which preserves the speaker's "thinking about the next thing to say" silence — the user feels that as "too much whitespace between words." The fix is NOT to un-merge (that brings back choppiness); it's to tighten. Within each continuous span, walk the word-level gaps and cap any silence longer than ~0.6s down to a ~0.3s beat, cutting in the MIDDLE of the silence (no word is ever clipped, so the sentence stays whole and the cut is inaudible — it's just less dead air). This only ever fires on inter-phrase gaps (intra-phrase gaps are ≤ the 0.45s split threshold by construction), so it tightens exactly the thinking-pauses and never disturbs in-clause rhythm. On this 31-min screencast it removed ~19s of dead air and made the pacing consistent without adding a single audible cut. Net model: hard cuts at real removals (sentence level) + pause-compression of long internal silences (dead-air level) + short breaths kept (rhythm). That's the full "cut only when needed" picture.
    - **(d) The merge re-derives audio from a continuous source span, so within-phrase dedup MUST be a real excision, not an endpoint trim.** Taking `words[0].start … words[-1].end` after dropping interior duplicate words does NOTHING to the audio — the cut still plays the whole span including the stutter ("it's their newest **it's their newest** model"). To actually remove an internal repeat, split the phrase into the contiguous RUNS on either side of the dup and emit them as separate segments (the dup's audio falls into the gap between them), and forbid the merge pass from bridging that internal seam. Otherwise the stutter silently survives every continuous-span render.
    - **(f) When deleting a restart cluster, the LAST restart is usually the real lead-in — keep it.** A stutter like "so now we have / files / so now we have / files / so now we have / **files and enough so if I play this**" tempts you to cut every "so now we have" as a restart and keep only the completed phrase — but then the kept take starts mid-sentence ("files and enough, so if I play this") and the viewer says "I have no idea what I'm saying, it got cut off." The completed take's grammatical subject lives in the immediately-preceding restart; keep that last one so it joins into a whole sentence ("so now we have files and enough, so if I play this"). General rule: after selecting the final take of a cluster, check it's a COMPLETE clause on its own; if it starts with a dangling object/verb, pull in the preceding fragment that supplies the subject.
    - **(h) ⭐ COHERENCE GATE — a kept take must be a sentence that actually works; if the best available take is still garbled, CUT it.** Completeness (lesson (f)) is not enough — a take can have its subject and still be nonsense. After a multi-take stumble, the "most complete" survivor is sometimes itself broken ("so now we have files and enough" — grammatically incoherent, the viewer says "I have no idea what I'm saying"). Patching such a fragment in is WORSE than removing it: a confusing sentence costs the viewer more than a missing one. So read every kept span as plain English and ask "does this parse as a real statement?" If not: (i) trim it to the coherent sub-clause that does work (here, drop "so now we have files and enough" and keep only "so if I play this →" leading into the sample), or (ii) cut it entirely and let the neighbours carry the meaning. Short broken fragments ("and you need minutes minimum") that add no clear info: just cut them. The story should be made of clean sentences only.
    - **(i) For an OPENER (or any take that must end cleanly), pick a take that ENDS on a natural pause — don't tail-trim a take whose next word is glued on.** Tail-trimming forces a tight 0.04s margin (to avoid leaking the glued next word), which makes the line sound clipped/cut-off — fatal for the first line of the video. If take A says "okay so fish audio **and today…**" (continues immediately) but take B earlier said "okay so fish audio**.**" followed by real silence, use take B's version: it ends on a true pause and gets a full natural trail. General rule: a clean ending requires real silence after the last word in THAT take; if the chosen take doesn't have it, find one that does rather than fabricating it with a trim.
    - **(g) Show the output-timecoded transcript on every change.** The user reviews by watching, but a written transcript at OUTPUT timecodes (not source) lets him read exactly what each second says and catch mid-sentence cutoffs, dangling takes, and bad seams far faster than scrubbing. After every recut, print `M:SS  <text>` per sentence-line (group segments, break the line only on a real source-jump hard cut). Flag that auto-transcription mishearings (Claude→"clot/club/cloth", ElevenLabs→"-lapse") are TEXT-only — the audio is correct — so they aren't mistaken for errors.
    - **(b) Don't assemble a sentence by splicing across two takes at a shared word — keep it within ONE take.** When the complete line only exists spread across takes, resist stitching take-A's head to take-B's tail at a word both contain ("...their newest **s2**" from take A + "**model** which is insanely good" from take B). The prosody/pitch differ across takes, so the seam at "s2/model" sounds wrong. Look for a single CONTINUOUS take that carries the whole clause (here take B said "newest S2.1 model which is insanely good" across two gap-split phrases `[2]+[3]` — adjacent in the source, same take) and use that; reserve the other take only for a part that ends on a real sentence boundary ("okay so fish audio."). Rule of thumb: cross-take joins are clean ONLY at full-stop boundaries, never mid-clause.

15. **⭐ GLOBAL semantic-dedup pass — a SEPARATE, REQUIRED step from local retake removal** (codified 2026-06-25, after the user kept finding "I'm basically saying the same thing twice" in shipped cuts). There are two kinds of duplicate and they need two different passes:
    - **Local / mechanical** (handled by the engine + the lesson-13 stack): adjacent restarts, stutters, exact n-gram repeats. String-matchable.
    - **Global / semantic** (ONLY a read-for-meaning pass catches it): the SAME POINT made twice in DIFFERENT words, often several phrases apart — "this is an ad that I have been running myself" … [4 phrases later] … "this is an ad and a short that I've been running." Share almost no exact words, not adjacent → **no heuristic can ever flag them.** Only judgment can.
    The failure mode that forced this lesson: judging phrase-by-phrase with a LOCAL lens ("is this a restart of the sentence right before it?") catches adjacent retakes but is BLIND to "have I already made this point earlier in the video?" Concretely: two phrases both said "this is an ad I've been running"; they were deduped against EACH OTHER (cut one) while a THIRD, earlier expression of the same beat survived untouched — because it was never cross-checked against the rest of the script. The "keep when unsure" bias (right for unverifiable playbacks) compounds it by letting redundant lines live.
    **The required process:** after the local cleanup and BEFORE rendering, do an explicit global pass — read the whole judged transcript, build a list of the distinct CONTENT BEATS in order, and for every beat expressed more than once anywhere in the script, keep the single strongest expression and cut/trim ALL the others, regardless of distance or wording. The output is extra CUT indices or TRIMs (often a tail/head trim that drops just the redundant clause, e.g. trim "…tools more. **So this is an ad I've been running**" down to "…tools more" because a later phrase carries that beat better). This is NOT optional and NOT something the engine can do for you — it is the editorial half of the job. The litmus the user gave: "even if they aren't direct retakes, it's basically me saying the same thing" — if two kept spans would make a viewer think *he just said that*, one of them goes. (Distinguish from intentional repetition: an A/B progression, a deliberate callback, or the same audio demonstrating two DIFFERENT methods are NOT semantic dups — flag those structural choices to the user instead of auto-cutting.)

16. **When excising a repeated word/phrase, DROP THE PAUSE-ABSORBED copy — keep the clean one, so the cut lands at a sentence boundary, not mid-clause** (codified 2026-06-25, from the "itself" orphan). Forced alignment sometimes gives a word a huge duration because it absorbed the SILENCE after it (e.g. "...fish audio itself**[0.4s] itself[3.4s]** Also…" — the second "itself" is 0.4s of speech + 3s of pause baked into one word). The default within-phrase dedup "keep the later copy" then keeps the BLOATED copy: the cut boundary lands at "audio | itself", orphaning "itself" onto its own clip with 3s of dead air — the viewer sees a sentence chopped 90%/10% with a dangling fragment. Fix: compare the two copies' durations; if the later one is much longer (`d2 > d1*1.6 + 0.3`), it's pause-absorbed — drop IT and keep the earlier clean copy, which puts the cut at the real sentence break ("…fish audio itself." | "Also if you need help…"). General principle behind it (the user's rule): **a sentence that exists whole in one take should play as ONE continuous clip; only split when content was actually removed, and when you must split, split at a sentence/clause boundary — never leave 90% of a sentence on one clip and a 10% fragment ("itself", "you can", "the rest") dangling on the next.** A clip that STARTS with a lowercase continuation word is the red flag.

17. **⭐ THE UNIT IS A CLAUSE, NOT A SILENCE-GAP (the architectural fix, codified 2026-06-25)** — grounded in how pro transcript editors actually work (radio edit / paper edit at the sentence-and-clause level; word-level cuts, sentence-level *decisions*). The old `phrases_of` split purely on silence (`gap > 0.45`), an ACOUSTIC unit that doesn't track meaning — and that single mismatch caused most of the recurring bugs: phrases spanning 100s+ of dead air, sentences split mid-clause, two takes lumped together, orphaned fragments. **Replace it with a clause split that fires on ANY of three signals:** (a) the previous word ends in clause punctuation `,.!?;:` (whisper's punctuation, used as a hint), (b) a real pause (`gap > GAP`), (c) a pause-absorbed long word on either side (`dur > LONG_WORD≈1.0s`) — the alignment frequently bakes a long silence into a single word's duration (a 199-second "you" during a generation wait), so split BEFORE and AFTER it to isolate it as its own throwaway unit you simply CUT. Why three signals: punctuation alone is too sparse (whisper under-punctuates whole stretches like intros); silence alone smears sentences and misses pause-absorbed dead air. Together they give meaning-aligned, breath-aware units that also break dead-air spans. **Over-splitting is safe — the MERGE pass re-joins contiguous kept clauses into one continuous clip**, so a comma-continuation you keep ("…have a conversation with Claude, *[pause]* and Claude will explain it") plays as one clip, while a comma-clause you want gone (a redundant tail, a new beat) can be cut precisely without substring hacks. This is the Descript model: fine granularity to cut anywhere, semantic grouping to keep thoughts whole. It removed a whole class of bugs at the source (the 111s/199s dead spans, the "itself" orphan, mid-sentence splits) and made both multi-part Fish videos visibly cleaner (V2 5:11→4:43, V3 6:16→6:05) in one pass. The decision unit Claude reasons in is still the sentence/thought (and the global beat-map, lesson 15); the clause is just what gives word-level freedom underneath it.

18. **⭐ USE WHISPER'S WORD-TIMESTAMPS, NOT MMS_FA — forced alignment SCRAMBLES repeated phrases (codified 2026-06-25; this REVERSES the earlier "forced alignment is the whole point" guidance).** This was the deepest bug, and it presents as the scariest kind: the transcript reads CLEAN but the clip PLAYS a stutter. Root cause: MMS_FA (torchaudio forced alignment) force-fits a fixed word sequence onto the audio via a DTW path. When the speaker REPEATS a phrase — which is constant in this footage ("click on auto tag … and I can then … click on auto tag") — the DTW takes the wrong branch and SCRAMBLES the timestamps: it stretched the clean take across the whole window (so the window silently CONTAINED the stutter that was actually at 548–551s) and shoved "generate speech" 9 seconds away to where the stutter's words nominally were. Net: every word's TEXT is right and in order (so the transcript/row looks clean and you trust it), but the TIMESTAMP points at the wrong audio — so cutting by those windows plays audio that doesn't match the text. You cannot catch this by reading the transcript; only re-transcribing the rendered file's audio (or the raw at the exact window times) exposes it. **The fix:** `make_aligned.py` now takes faster-whisper's OWN `word_timestamps=True` output directly and skips MMS_FA entirely. Whisper places words sequentially as it decodes the audio, so it does NOT scramble on repeats — verified it nailed the clean/stutter boundary (548.2s) that MMS_FA got backwards. Whisper word edges are slightly coarser (~50–100ms vs MMS_FA's ~10ms) but the cut margins (LEAD/TRAIL 0.13–0.18, TRIM 0.04) absorb that. **Correct-but-coarse beats precise-but-wrong.** Diagnostic to keep in the loop: after any cut of repeat-heavy footage, spot-check by re-transcribing a slice of the RENDERED output and confirming it matches the intended transcript — a mismatch means the alignment lied.

19. **⭐ RUN `unclip_ends.py` ON EVERY KEEPERS FILE BEFORE RENDER — the gap-tightener chops word TAILS, which reads to the user as "sections cut off too quick, I don't hear the last part of the sentence" AND makes the gaps "sound harsh" (codified 2026-06-25).** `tighten_gaps.py` shrinks each word to where RMS is above a silence floor — but a word's quiet RELEASE (the decaying "-ch" in "speech", "-tch" in "Dutch") falls below the floor, so it gets trimmed as silence. The cut then lands mid-release (`ce = word.end + TRAIL`), you hear "spee-" instead of "speech", and the abrupt chop into silence (no natural decay) is the "harsh gap." Measured on a real cut: **16–30 of ~60 keeper ends had speech continuing PAST the cut**, some by ~0.5s (a whole word eaten). Two fixes, both shipped: (a) `tighten_gaps.py` floor lowered (`max(peak*0.02, p12*1.5)`) so releases survive; (b) **`unclip_ends.py` is a mandatory post-build step** — it reads the wav + final keepers and extends each `ce` forward through CONTIGUOUS speech until real silence, **stopping at any gap ≥0.12s** (a removed retake always has a breath/gap before it, so it can't pull removed content back in), capped at +0.55s. Run it right after `build_judged.py --build` and before `recut.py`: `python3 "$SK/unclip_ends.py" "$W/_full16k.wav" "$W/_pipeline/<SHORT>_keepers.json"`. Philosophy: **bias the auto-cut toward keeping a hair too much** — an extra 0.1s is invisible / drag-trimmable in the editor; a clipped word is invisible until you HEAR it and unrecoverable without a re-cut. Verified safe by re-transcribing the rendered output (no new doubled phrases) — the contiguous-only + gap-stop rule means it recovers tails without re-adding takes.

20. **AUTO-SAVE vs EXPORT are two different things in the editor (codified 2026-06-25).** The media agent's `POST /recut` now takes `save_only:true` → it writes the keepers file and returns instantly WITHOUT re-rendering the mp4. `ClipEditor.tsx` fires this debounced (700ms) on every edit, so the user's work is never lost (the badge shows "saving…/saved"); the explicit **Export** button (formerly "Save") is the only thing that re-renders the full mp4. Keepers are the shared source of truth, so an auto-saved edit is already reflected next time the editor loads — only the downstream mp4 needs a deliberate Export.
