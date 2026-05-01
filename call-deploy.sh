#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-root@46.101.136.214}"
REMOTE_DIR="${REMOTE_DIR:-/home/goals.danielmoessner.de}"

IMAGE_REPO="${IMAGE_REPO:-ghcr.io/danielmoessner/goals.danielmoessner.de}"

# Immutable deploy default: deploy the image built from the current git commit.
if [ -n "${GOALS_IMAGE:-}" ]; then
	IMAGE="$GOALS_IMAGE"
elif [ -n "${1:-}" ]; then
	# Argument can be either a full image ref (ghcr.io/..:tag) or just a tag.
	if [[ "$1" == ghcr.io/*:* ]]; then
		IMAGE="$1"
	else
		IMAGE="$IMAGE_REPO:$1"
	fi
else
	if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
		echo "ERROR: not a git repo; set GOALS_IMAGE or pass a tag/image as arg." >&2
		exit 1
	fi
	SHA="$(git rev-parse HEAD)"
	IMAGE="$IMAGE_REPO:sha-$SHA"
fi

ssh "$HOST" "mkdir -p '$REMOTE_DIR'"
scp ./docker-compose.yml ./apache.conf ./deploy-on-server.sh "$HOST:$REMOTE_DIR/"
ssh "$HOST" "chmod +x '$REMOTE_DIR/deploy-on-server.sh' && cd '$REMOTE_DIR' && GOALS_IMAGE=$(printf %q "$IMAGE") ./deploy-on-server.sh"
