#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${DATA_DIR:-/home/goals.danielmoessner.de/tmp}"
APACHE_SITE_PATH="${APACHE_SITE_PATH:-/etc/apache2/sites-available/goals.danielmoessner.de.conf}"

if [ -z "${GOALS_IMAGE:-}" ]; then
	echo "ERROR: GOALS_IMAGE is required (deploy immutable tags)." >&2
	echo "Example: GOALS_IMAGE=ghcr.io/danielmoessner/goals.danielmoessner.de:sha-<gitsha>" >&2
	exit 1
fi

if [ "${ALLOW_MUTABLE_IMAGE:-0}" != "1" ] && [[ "$GOALS_IMAGE" == *:latest ]]; then
	echo "ERROR: refusing to deploy mutable tag ':latest'." >&2
	echo "Set GOALS_IMAGE to an immutable tag (sha-... or a release tag), or set ALLOW_MUTABLE_IMAGE=1." >&2
	exit 1
fi

export GOALS_IMAGE

if [ "$(id -u)" -ne 0 ]; then
	echo "ERROR: must be run as root (needs chown + systemctl + apache reload)." >&2
	exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
	echo "ERROR: docker not found." >&2
	exit 127
fi

if ! docker compose version >/dev/null 2>&1; then
	echo "ERROR: Docker Compose plugin not found (need 'docker compose')." >&2
	exit 127
fi

chown 999:33 "$DATA_DIR" || true
chmod 710 "$DATA_DIR" || true

chown -R 999:33 "$DATA_DIR/static" "$DATA_DIR/media" "$DATA_DIR/logs" || true
chmod 750 "$DATA_DIR/static" "$DATA_DIR/media" "$DATA_DIR/logs" || true

chown 999:33 "$DATA_DIR/django.log" || true
chmod 640 "$DATA_DIR/django.log" || true

chown 999:999 "$DATA_DIR/secrets.json" || true
chmod 600 "$DATA_DIR/secrets.json" || true

chown 999:999 "$DATA_DIR/db.sqlite3" || true
chmod 600 "$DATA_DIR/db.sqlite3" || true

docker compose pull

docker compose run --rm --no-deps web \
	python -c 'import importlib; importlib.import_module("config.settings.production"); open("/django/tmp/secrets.json", "rb").read(1); print("OK: settings import + secrets readable")'

docker compose run --rm --no-deps web python manage.py migrate --noinput
docker compose run --rm --no-deps web python manage.py collectstatic --noinput

docker compose up -d --remove-orphans

systemctl reload apache2

echo "OK: deployed ${GOALS_IMAGE}"