#!/bin/zsh
# India target top-up (ranks 131-330) with Gemini Flash; Codex under-delivers on volume.
REPO=/Users/CharanVelavan/Charan/SSN/UAE/orca-ntn; P=$REPO/docs/plan/prompts/wave1; T=$REPO/docs/research/targets; L=$REPO/corpus/logs
cd $REPO
python3 - <<PY
from pathlib import Path
s=Path("$P/codex-targets.md").read_text().replace("{{RULES}}",Path("$P/_rules.md").read_text()).replace("{{SCOPE}}",Path("$P/scope-india-C.txt").read_text())
Path("$L/prompt-india-C.md").write_text(s+"\n\nWrite the YAML list (only YAML, values with colons quoted) to $T/india-C.yaml. Write it in batches of ~40 items as you go, so downloaders can start early.\n")
PY
agy -p "$(cat $L/prompt-india-C.md)" --model gemini-3.8-flash-medium --add-dir $REPO --dangerously-skip-permissions --print-timeout 2h > $L/flash-india-C.log 2>&1
echo "$(date) targets india-C done: $(grep -c 'url:' $T/india-C.yaml 2>/dev/null) items" >> $L/wave1-events.log
