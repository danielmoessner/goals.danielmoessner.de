#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-root@46.101.136.214}"
REMOTE_DIR="${REMOTE_DIR:-/home/goals.danielmoessner.de}"

IMAGE_REPO="${IMAGE_REPO:-ghcr.io/danielmoessner/goals.danielmoessner.de}"

# Optional preflight: verify the image exists before connecting to the server.
# Values:
# - auto (default): check if possible (requires local docker), otherwise warn+skip
# - 1: require the check (fails if docker missing or image not found)
# - 0: disable the check
PREFLIGHT_IMAGE_CHECK="${PREFLIGHT_IMAGE_CHECK:-auto}"
WAIT_FOR_IMAGE_SECONDS="${WAIT_FOR_IMAGE_SECONDS:-0}"

SHA="$(git rev-parse HEAD)"
IMAGE="$IMAGE_REPO:sha-$SHA"

image_exists() {
	local image="$1"
	# Prefer Docker registry probing via the local Docker CLI (works well for GHCR).
	# If this fails due to auth, run: docker login ghcr.io
	command -v docker >/dev/null 2>&1 || return 2
	docker manifest inspect "$image" >/dev/null 2>&1
}


do_preflight_check=0
case "$PREFLIGHT_IMAGE_CHECK" in
	0) do_preflight_check=0 ;;
	1) do_preflight_check=1 ;;
	auto) do_preflight_check=1 ;;
	*)
		echo "ERROR: invalid PREFLIGHT_IMAGE_CHECK='$PREFLIGHT_IMAGE_CHECK' (use: auto|1|0)" >&2
		exit 2
		;;
esac

if [ "$do_preflight_check" = "1" ]; then
	image_exists "$IMAGE"
	rc="$?"

	if [ "$rc" -eq 2 ]; then
		if [ "$PREFLIGHT_IMAGE_CHECK" = "auto" ]; then
			echo "WARN: skipping image preflight check (docker not found)." >&2
			rc=0
		else
			echo "ERROR: docker not found; cannot verify image exists locally." >&2
			echo "- Install Docker, or disable the check: PREFLIGHT_IMAGE_CHECK=0 ./call-deploy.sh" >&2
			exit 2
		fi
	fi

	if [ "$rc" -ne 0 ] && [ "$WAIT_FOR_IMAGE_SECONDS" -gt 0 ]; then
		echo "INFO: image not available yet; waiting up to ${WAIT_FOR_IMAGE_SECONDS}s: $IMAGE" >&2
		end=$((SECONDS + WAIT_FOR_IMAGE_SECONDS))
		while [ "$SECONDS" -lt "$end" ]; do
			sleep 5
			if image_exists "$IMAGE"; then
				rc=0
				break
			fi
		done
	fi

	if [ "$rc" -ne 0 ]; then
		echo "ERROR: image tag not found (or not readable): $IMAGE" >&2
		echo "- If you just pushed, wait for the GitHub Actions build to finish." >&2
		echo "- If the image is private, run: docker login ghcr.io" >&2
		echo "- To disable this check: PREFLIGHT_IMAGE_CHECK=0 ./call-deploy.sh" >&2
		echo "- To require this check (and fail if docker missing): PREFLIGHT_IMAGE_CHECK=1 ./call-deploy.sh" >&2
		echo "- To wait (bounded): WAIT_FOR_IMAGE_SECONDS=120 ./call-deploy.sh" >&2
		exit 1
	fi
fi

ssh "$HOST" "mkdir -p '$REMOTE_DIR'"
scp ./docker-compose.yml ./apache.conf ./deploy-on-server.sh "$HOST:$REMOTE_DIR/"
ssh "$HOST" "chmod +x '$REMOTE_DIR/deploy-on-server.sh' && cd '$REMOTE_DIR' && GOALS_IMAGE=$(printf %q "$IMAGE") ./deploy-on-server.sh"
