#!/bin/zsh
# Wave 1 launcher (lead). Renders prompts from docs/plan/prompts/wave1 and runs Codex + Gemini.
REPO=/Users/CharanVelavan/Charan/SSN/UAE/orca-ntn
P=$REPO/docs/plan/prompts/wave1; T=$REPO/docs/research/targets; L=$REPO/corpus/logs
cd $REPO
render() { python3 - "$@" <<'PY'
import sys, pathlib
tpl, out, *kv = sys.argv[1:]
s = pathlib.Path(tpl).read_text().replace("{{RULES}}", pathlib.Path(sys.argv[1]).parent.joinpath("_rules.md").read_text())
for pair in kv:
    k, v = pair.split("=", 1)
    s = s.replace("{{%s}}" % k, pathlib.Path(v[1:]).read_text() if v.startswith("@") else v)
pathlib.Path(out).write_text(s)
PY
}
targets() {   # $1 = india-A etc. Codex first; Gemini Flash #3 takes over on failure.
  local n=$1 pr=$L/prompt-codex-$1.md
  render $P/codex-targets.md $pr SCOPE=@$P/scope-$n.txt
  codex exec --skip-git-repo-check -m gpt-6-luna -c model_reasoning_effort="medium" -s read-only \
    -C $REPO -o $T/$n.yaml "$(cat $pr)" < /dev/null > $L/codex-$n.log 2>&1
  if [ ! -s $T/$n.yaml ] || [ $(grep -c "url:" $T/$n.yaml) -lt 20 ]; then
    echo "$(date) codex $n failed or short; handing to gemini flash #3" >> $L/wave1-events.log
    mv -f $T/$n.yaml $T/$n.codex-partial.yaml 2>/dev/null
    agy -p "$(cat $pr)

Write the YAML list (only YAML) to $T/$n.yaml. If $T/$n.codex-partial.yaml exists, keep its good items and continue from there." \
      --model gemini-3.8-flash-medium --add-dir $REPO --dangerously-skip-permissions --print-timeout 90m > $L/flash3-$n.log 2>&1
  fi
  echo "$(date) targets $n done: $(grep -c 'url:' $T/$n.yaml 2>/dev/null) items" >> $L/wave1-events.log
}
gemini() {    # $1 = india|global
  local j=$1 pr=$L/prompt-gemini-$1.md name
  [ $j = india ] && name="India" || name="Global"
  mkdir -p corpus/raw/$j kb/staging/$j
  render $P/gemini-download.md $pr AGENT=$j JUR_NAME=$name \
    "LISTS=docs/research/targets/$j-A.yaml, then docs/research/targets/$j-B.yaml"
  agy -p "$(cat $pr)" --model gemini-3.8-flash-medium --add-dir $REPO --dangerously-skip-permissions \
    --print-timeout 6h > $L/gemini-$j.log 2>&1
  echo "$(date) gemini $j exited $?" >> $L/wave1-events.log
}
case $1 in
  targets) targets $2 ;;
  gemini)  gemini $2 ;;
esac
