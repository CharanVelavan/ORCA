#!/bin/bash
# usage: serve.sh <port> <model.gguf> [extra args]
export PATH=/usr/local/cuda/bin:$PATH
port=$1; m=$2; shift 2
pkill -f "llama-server" ; sleep 2
nohup ~/ft/llama.cpp/build/bin/llama-server -m $m --jinja -c 16384 -ngl 99 -np 1 --host 127.0.0.1 --port $port "$@" > ~/ft/server.log 2>&1 &
for i in $(seq 1 120); do curl -fs localhost:$port/health >/dev/null 2>&1 && { echo up; exit 0; }; sleep 3; done; echo timeout; tail -20 ~/ft/server.log
