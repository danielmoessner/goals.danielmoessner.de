#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${GOALS_DATA_DIR:-/home/goals.danielmoessner.de/tmp}"

: "${GOALS_IMAGE:?ERROR: GOALS_IMAGE is required}"

export GOALS_IMAGE
export GOALS_DATA_DIR="$DATA_DIR"
export GOALS_BIND_IP="${GOALS_BIND_IP:-127.0.0.1}"
export GOALS_PORT="${GOALS_PORT:-8080}"

mkdir -p "$DATA_DIR/static" "$DATA_DIR/media"

docker compose pull
docker compose run --rm --no-deps web python manage.py migrate --noinput
docker compose run --rm --no-deps web python manage.py collectstatic --noinput
docker compose up -d --remove-orphans

systemctl reload apache2

echo "OK: deployed $GOALS_IMAGE"