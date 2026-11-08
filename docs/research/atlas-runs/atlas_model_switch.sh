#!/usr/bin/env bash
# Switch the model served by Atlas Daily (GCP L4 Spot VM, llama.cpp 'llama-server' systemd unit)
# between the original Qwen3.6 setup, the fine-tuned Gemma 4 12B and the fine-tuned Qwen3.6-35B-A3B.
#
#   docs/research/atlas-runs/atlas_model_switch.sh qwen        # restore the stock Qwen3.6-35B-A3B profile
#   docs/research/atlas-runs/atlas_model_switch.sh gemma-ft    # serve gemma-4-12b-orca-ft.Q4_K_M.gguf
#   docs/research/atlas-runs/atlas_model_switch.sh qwen-ft     # serve Qwen3.6-35B-A3B-orca-ft.IQ4_XS.gguf (19.2 GB, from bucket qwen-ft/)
#   docs/research/atlas-runs/atlas_model_switch.sh status
#   QWEN_FT_CTX=12288 ... qwen-ft    # override the context if 16384 does not fit on the L4
#
# Assumes: `atlas daily` is up (VM atlas-daily + IAP tunnel on localhost:8000), the GGUF is in the
# private bucket, and your gcloud account is charanaklavya12@gmail.com on project cs-project-fvrzibw1.
# The VM has no service account, so the copy from the bucket uses a short-lived access token that is
# piped over SSH stdin (never written to disk, never printed).
# The original Qwen env file is kept as /etc/qwen/llama-server.env.qwen; nothing is deleted.
set -euo pipefail

PROJECT=cs-project-fvrzibw1
VM=atlas-daily
BUCKET=gs://orca-ft-cs-project-fvrzibw1
GGUF=gemma-4-12b-orca-ft.Q4_K_M.gguf
GGUF_BYTES=7381383296
GGUF_SHA256=bf1d3afe419358e4e28b77a6d5c55a85a34722423851884b3ab2322b5f0d7af2
QWEN_FT_OBJ=qwen-ft/Qwen3.6-35B-A3B-orca-ft.IQ4_XS.gguf
QWEN_FT_GGUF=Qwen3.6-35B-A3B-orca-ft.IQ4_XS.gguf
QWEN_FT_BYTES=19179521888
QWEN_FT_SHA256=011d7797836571495e8faf545101bee1e71d75a39292e06f946e8a3646b54e16
QWEN_FT_CTX=${QWEN_FT_CTX:-16384}
LOCAL_PORT=${LOCAL_PORT:-8000}
TARGET=${1:-status}

ZONE=$(gcloud compute instances list --project "$PROJECT" --filter="name=$VM" --format='value(zone.basename())' | head -n1)
[ -n "$ZONE" ] || { echo "VM $VM is not running; run 'atlas daily' first." >&2; exit 1; }

vm() { gcloud compute ssh "$VM" --zone "$ZONE" --tunnel-through-iap --project "$PROJECT" \
         --strict-host-key-checking=no --quiet --command "$1" 2> >(grep -v -e NumPy -e 'please see' -e '^WARNING' -e '^$' >&2); }

wait_models() {
  for _ in $(seq 1 90); do
    if curl -fsS -m 5 "http://localhost:$LOCAL_PORT/v1/models" >/tmp/atlas_models.json 2>/dev/null; then
      python3 -c 'import json;print("serving:",json.load(open("/tmp/atlas_models.json"))["data"][0]["id"])'; return 0
    fi
    sleep 4
  done
  echo "server did not answer /v1/models in 6 min; check: atlas logs" >&2; return 1
}

case "$TARGET" in
  status)
    vm 'grep -E "^(MODEL|CTX|EXTRA_ARGS)=" /etc/qwen/llama-server.env; systemctl is-active llama-server'
    curl -fsS -m 5 "http://localhost:$LOCAL_PORT/v1/models" | python3 -c 'import json,sys;print("serving:",json.load(sys.stdin)["data"][0]["id"])' || true
    ;;
  qwen)
    vm 'set -e; [ -f /etc/qwen/llama-server.env.qwen ] || { echo "no Qwen backup env"; exit 1; }
        sudo cp /etc/qwen/llama-server.env.qwen /etc/qwen/llama-server.env; sudo systemctl restart llama-server'
    wait_models
    ;;
  gemma-ft)
    # 1. original Qwen env backup (once), Gemma env file, and a copy of the GGUF if missing/wrong size
    have=$(vm "stat -c %s /opt/qwen/models/$GGUF 2>/dev/null || echo 0" | tail -n1)
    if [ "$have" != "$GGUF_BYTES" ]; then
      echo "copying $GGUF from $BUCKET to the VM (inside GCP) ..."
      gcloud auth print-access-token | vm "set -e; read -r T; sudo rm -f /opt/qwen/models/$GGUF.part
        sudo curl -fsS --retry 3 -o /opt/qwen/models/$GGUF.part -H \"Authorization: Bearer \$T\" \
          'https://storage.googleapis.com/storage/v1/b/${BUCKET#gs://}/o/$GGUF?alt=media'
        [ \$(stat -c %s /opt/qwen/models/$GGUF.part) = $GGUF_BYTES ]
        sudo mv /opt/qwen/models/$GGUF.part /opt/qwen/models/$GGUF"
      vm "echo '$GGUF_SHA256  /opt/qwen/models/$GGUF' | sha256sum -c -" || { echo "sha256 mismatch on VM copy" >&2; exit 1; }
    fi
    vm "set -e
      [ -f /etc/qwen/llama-server.env.qwen ] || sudo cp /etc/qwen/llama-server.env /etc/qwen/llama-server.env.qwen
      printf '%s\n' '# llama-server profile: fine-tuned Gemma 4 12B (ORCA-NTN)' 'MODEL=/opt/qwen/models/$GGUF' 'HOST=127.0.0.1' 'PORT=8080' 'CTX=16384' 'EXTRA_ARGS=-ngl 99 -fa on -np 1 --jinja' | sudo tee /etc/qwen/llama-server.env.gemma-ft >/dev/null
      sudo cp /etc/qwen/llama-server.env.gemma-ft /etc/qwen/llama-server.env
      sudo systemctl restart llama-server"
    wait_models
    ;;
  qwen-ft)
    have=$(vm "stat -c %s /opt/qwen/models/$QWEN_FT_GGUF 2>/dev/null || echo 0" | tail -n1)
    if [ "$have" != "$QWEN_FT_BYTES" ]; then
      echo "copying $QWEN_FT_GGUF from $BUCKET to the VM (inside GCP) ..."
      # object name contains a slash, so it must be URL-encoded (%2F) in the JSON API path
      gcloud auth print-access-token | vm "set -e; read -r T; sudo rm -f /opt/qwen/models/$QWEN_FT_GGUF.part
        sudo curl -fsS --retry 3 -o /opt/qwen/models/$QWEN_FT_GGUF.part -H \"Authorization: Bearer \$T\" \
          'https://storage.googleapis.com/storage/v1/b/${BUCKET#gs://}/o/${QWEN_FT_OBJ//\//%2F}?alt=media'
        [ \$(stat -c %s /opt/qwen/models/$QWEN_FT_GGUF.part) = $QWEN_FT_BYTES ]
        sudo mv /opt/qwen/models/$QWEN_FT_GGUF.part /opt/qwen/models/$QWEN_FT_GGUF"
    fi
    vm "echo '$QWEN_FT_SHA256  /opt/qwen/models/$QWEN_FT_GGUF' | sha256sum -c -" || { echo "sha256 mismatch on VM copy" >&2; exit 1; }
    # same flags as the stock Qwen profile on this L4 (see /etc/qwen/llama-server.env.qwen): --jinja, -ngl 99, -fa on, -np 1, thinking off
    # EXTRA_ARGS_QWEN_FT is filled from the stock profile's EXTRA_ARGS with the model/ctx replaced (see below)
    vm "set -e
      [ -f /etc/qwen/llama-server.env.qwen ] || sudo cp /etc/qwen/llama-server.env /etc/qwen/llama-server.env.qwen
      sed -e 's|^MODEL=.*|MODEL=/opt/qwen/models/$QWEN_FT_GGUF|' -e 's|^CTX=.*|CTX=$QWEN_FT_CTX|' /etc/qwen/llama-server.env.qwen | sudo tee /etc/qwen/llama-server.env.qwen-ft >/dev/null
      sudo cp /etc/qwen/llama-server.env.qwen-ft /etc/qwen/llama-server.env
      sudo systemctl restart llama-server"
    wait_models
    ;;
  *) echo "usage: $0 qwen|gemma-ft|qwen-ft|status" >&2; exit 2 ;;
esac
