#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-root@46.101.136.214}"
REMOTE_DIR="${REMOTE_DIR:-/home/goals.danielmoessner.de}"
IMAGE_REPO="${IMAGE_REPO:-ghcr.io/danielmoessner/goals.danielmoessner.de}"

SHA="$(git rev-parse HEAD)"
IMAGE="${IMAGE_REPO}:sha-${SHA}"

ssh "$HOST" "mkdir -p '$REMOTE_DIR'"
scp \
	docker-compose.yml \
	deploy-on-server.sh \
    apache.conf \
	"$HOST:$REMOTE_DIR/"

ssh "$HOST" \
	"cd '$REMOTE_DIR' \
	&& chmod +x deploy-on-server.sh \
	&& GOALS_IMAGE=$(printf %q "$IMAGE") ./deploy-on-server.sh"
