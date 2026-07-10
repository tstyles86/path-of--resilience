#!/usr/bin/env bash
# publish_editor.sh REC SHORTNAME SRC
# Builds everything the back-office ClipEditor needs for a recording:
#   - <SHORT>_keepers.json + <SHORT>_words.json (from screen_aligned.json + the judged keepers)
#   - _proxy.mp4 (540p, keyframe forced at every clip start -> smooth seek playback)
#   - _thumbs.jpg + _thumbs.json (filmstrip sprite)
# The 3_SHORTS/<SHORT> render and the content_pieces upsert are done separately.
set -euo pipefail
REC="$1"; SHORT="$2"; SRC="$3"
W="$HOME/Movies/BuildLoop/$REC/2_SOURCE"; P="$W/_pipeline"; STEM="${SHORT%.mp4}"
K="$P/${STEM}_keepers.json"
[ -f "$K" ] || { echo "no keepers at $K"; exit 1; }

# 1. per-word file (kept-flag = word midpoint inside a keeper) — straight from the alignment
python3 - "$W/screen_aligned.json" "$K" "$P/${STEM}_words.json" <<'PY'
import json,sys
a=json.load(open(sys.argv[1])); keepers=json.load(open(sys.argv[2]))
def kept(w):
    m=(w['start']+w['end'])/2
    return any(k['cs']-0.02<=m<=k['ce']+0.02 for k in keepers)
json.dump([{'word':w['word'],'cs':round(w['start'],3),'ce':round(w['end'],3),'kept':kept(w)} for w in a], open(sys.argv[3],'w'))
print('words:',len(a))
PY

# 2. scrub proxy — keyframe at every clip start (smooth clip-to-clip seeks) + 0.5s periodic
CS=$(python3 -c "import json;print(','.join(f'{k[\"cs\"]:.3f}' for k in json.load(open('$K'))))")
ffmpeg -y -v error -i "$SRC" -vf "scale=-2:540,format=yuv420p" -c:v libx264 -preset veryfast -crf 28 \
  -force_key_frames "$CS" -g 15 -keyint_min 1 -sc_threshold 0 -c:a aac -b:a 96k -movflags +faststart "$W/_proxy.mp4"
echo "proxy: $(ls -lh "$W/_proxy.mp4" | awk '{print $5}')"

# 3. filmstrip sprite (1 frame / 2s, 96x54 cells)
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$W/_proxy.mp4" | cut -d. -f1)
COUNT=$(( (DUR + 1) / 2 )); COLS=30; ROWS=$(( (COUNT + COLS - 1) / COLS ))
ffmpeg -y -v error -i "$W/_proxy.mp4" -vf "fps=1/2,scale=96:54,tile=${COLS}x${ROWS}:padding=0:margin=0" -frames:v 1 -q:v 5 "$W/_thumbs.jpg"
python3 -c "import json;json.dump({'interval':2.0,'cols':$COLS,'rows':$ROWS,'cellW':96,'cellH':54,'count':$COUNT},open('$W/_thumbs.json','w'))"
echo "thumbs: $(ls -lh "$W/_thumbs.jpg" | awk '{print $5}'), grid ${COLS}x${ROWS}"
echo "DONE editor assets for $REC / $SHORT"
