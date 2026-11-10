#!/bin/bash
# usage: run_eval.sh <name> <gguf> [extra llama-server args]
name=$1; m=$2; shift 2
source ~/ft/venv/bin/activate
~/ft/serve.sh 8090 $m "$@" || exit 1
python ~/ft/probe.py 8090 > ~/ft/evals/$name.probe.txt 2>&1
cd ~/orca-ntn
python ~/ft/eval_wrap.py $name http://localhost:8090/v1 ~/ft/cases_subset300_tools.jsonl ~/ft/evals/$name.raw.json ~/ft/evals/$name.json > ~/ft/evals/$name.log 2>&1
cp ~/ft/server.log ~/ft/evals/$name.server.log
pkill -f llama-server
