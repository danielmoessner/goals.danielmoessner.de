#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-root@46.101.136.214}"
REMOTE_DIR="${REMOTE_DIR:-/home/goals.danielmoessner.de}"

ssh "$HOST" "mkdir -p '$REMOTE_DIR'"
scp ./docker-compose.yml ./apache.conf ./deploy-on-server.sh "$HOST:$REMOTE_DIR/"
ssh "$HOST" "chmod +x '$REMOTE_DIR/deploy-on-server.sh' && cd '$REMOTE_DIR' && ./deploy-on-server.sh"
