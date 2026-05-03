#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${APP_DATA_DIR:-${GOALS_DATA_DIR:-/home/goals.danielmoessner.de/tmp}}"

if [[ -z "${APP_IMAGE:-}" && -n "${GOALS_IMAGE:-}" ]]; then
	APP_IMAGE="$GOALS_IMAGE"
fi

: "${APP_IMAGE:?ERROR: APP_IMAGE is required}"

export APP_IMAGE
export APP_DATA_DIR="$DATA_DIR"
export APP_BIND_IP="${APP_BIND_IP:-${GOALS_BIND_IP:-127.0.0.1}}"
export APP_PORT="${APP_PORT:-${GOALS_PORT:-8080}}"

mkdir -p "$DATA_DIR/static" "$DATA_DIR/media"

docker compose pull
docker compose run --rm --no-deps web python manage.py migrate --noinput
docker compose run --rm --no-deps web python manage.py collectstatic --noinput
docker compose up -d --remove-orphans

echo "OK: deployed $APP_IMAGE"