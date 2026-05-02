# goals.danielmoessner.de

Django app powering `goals.danielmoessner.de`.

- Framework: Django
- App server: Gunicorn
- Build: Docker image (built via GitHub Actions, pushed to GHCR)
- Production runtime: Docker Compose on a single host + Apache reverse proxy

See deployment evaluation categories in [deployment-evaluation.md](deployment-evaluation.md) and a concrete improvement roadmap in [deployment-improvement-plan.md](deployment-improvement-plan.md).

## Local development

### Prerequisites

- Python 3.14
- `uv` (dependency management)

### Setup

1. Create `tmp/secrets.json` (this folder is gitignored)
2. Install dependencies: `uv sync`
3. Run Django: `./run.sh`

Optional (CSS):

- Install the Tailwind standalone CLI (macOS arm64): `./install-tailwind.sh`
- Run Tailwind in watch mode: `./css.sh`

### `tmp/secrets.json` (local)

Local settings still read secrets from `tmp/secrets.json`.

Minimal keys for local dev:

```json
{
  "SECRET_KEY": "replace-me",
  "TELEGRAM_BOT_TOKEN": "dummy-token-for-local"
}
```

Generate a Django `SECRET_KEY` with:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Deployment (production)

### Architecture (current)

- A Docker image is built and pushed to GitHub Container Registry (GHCR) by GitHub Actions.
- The server runs the app using `docker compose` (see `docker-compose.yml`).
- The container runs Gunicorn on port `8080` and Docker publishes it to `127.0.0.1:${GOALS_PORT}` on the host.
- Apache terminates TLS and reverse-proxies to `http://127.0.0.1:${GOALS_PORT}/`.
- Static + media files are stored on the host and served directly by Apache.

State on the server lives under:

- `/home/goals.danielmoessner.de/tmp/db.sqlite3` (SQLite DB)
- `/home/goals.danielmoessner.de/tmp/media/` (uploads)
- `/home/goals.danielmoessner.de/tmp/static/` (collected static)
- `/home/goals.danielmoessner.de/tmp/secrets.json` (Django + integration secrets)

### Build & publish (CI)

GitHub Actions builds and pushes the Docker image to GHCR on pushes to the default branch.

Tags include:

- `latest` (default branch only)
- `sha-<longsha>`
- `sha-<shortsha>`

The production deploy uses an immutable `sha-...` tag.

### One-time server setup

The deploy scripts assume:

- Docker is installed
- Docker Compose V2 plugin is installed (the server must support `docker compose`)
- Apache2 is installed and running
- Apache is configured as reverse proxy + static/media server (see `apache.conf`)
- TLS certs exist (Let’s Encrypt paths referenced in `apache.conf`)

Suggested Apache modules to enable (Debian/Ubuntu style):

- `proxy`, `proxy_http`
- `rewrite`
- `ssl`

Place the vhost config:

- Copy or symlink `apache.conf` to `/etc/apache2/sites-available/goals.danielmoessner.de.conf`
- Enable it and reload Apache (e.g. `a2ensite goals.danielmoessner.de && systemctl reload apache2`)

Create the state directory and the production secrets file:

- Create `/home/goals.danielmoessner.de/tmp/`
- Create `/home/goals.danielmoessner.de/tmp/secrets.json`

Production `secrets.json` must contain at least:

```json
{
  "SECRET_KEY": "...",
  "TELEGRAM_BOT_TOKEN": "...",
  "ALLOWED_HOSTS": ["goals.danielmoessner.de"],
  "EMAIL_ADDRESS": "...",
  "EMAIL_HOST": "...",
  "EMAIL_PORT": 587,
  "EMAIL_USER": "...",
  "EMAIL_PASSWORD": "..."
}
```

### Deploy a new version

The deployment entrypoint is `./call-deploy.sh` (run from your machine).

Prerequisites:

- The commit you want to deploy is pushed to the default branch
- The GitHub Actions “Build & Push Docker Image” workflow has completed for that commit (so the `sha-...` image exists)
- Your machine can SSH/SCP to the server

Run:

```bash
./call-deploy.sh
```

`call-deploy.sh` will:

- compute the current git SHA (`git rev-parse HEAD`)
- use `GOALS_IMAGE=ghcr.io/<owner>/<repo>:sha-<longsha>`
- copy `docker-compose.yml`, `apache.conf`, and `deploy-on-server.sh` to the server
- run `deploy-on-server.sh` on the server (as root)

Useful overrides:

- `HOST` (SSH target, e.g. `root@your-server`)
- `REMOTE_DIR` (defaults to `/home/goals.danielmoessner.de`)
- `IMAGE_REPO` (defaults to `ghcr.io/danielmoessner/goals.danielmoessner.de`)

Compose/runtime parameters (used by `docker-compose.yml` on the server):

- `GOALS_DATA_DIR` (defaults to `/home/goals.danielmoessner.de/tmp`)
- `GOALS_BIND_IP` (defaults to `127.0.0.1`)
- `GOALS_PORT` (defaults to `8080`)

Example:

```bash
HOST=root@your-server REMOTE_DIR=/home/goals.danielmoessner.de ./call-deploy.sh
```

### CI push-to-deploy

The workflow `.github/workflows/docker-image.yml` contains a `deploy` job that can deploy automatically after a successful image build/push on the default branch.

To enable it, add these GitHub Actions secrets:

- `DEPLOY_HOST` (e.g. `46.101.136.214`)
- `DEPLOY_USER` (e.g. `root`)
- `DEPLOY_REMOTE_DIR` (e.g. `/home/goals.danielmoessner.de`)
- `DEPLOY_SSH_PRIVATE_KEY` (an SSH private key with access to the server)

Optional but recommended:

- `DEPLOY_KNOWN_HOSTS` (pinned host key entry for `~/.ssh/known_hosts`)

Once set, a push to `main`/`master` will:

1. build + push `ghcr.io/<owner>/<repo>:sha-<gitsha>`
2. run `./call-deploy.sh` from CI against the server

### Rollback

Rollback is “deploy an older immutable image tag”. Options:

- locally: checkout an older commit and run `./call-deploy.sh`
- on the server: run `GOALS_IMAGE=... ./deploy-on-server.sh` from the directory that contains `docker-compose.yml`

### Troubleshooting

On the server:

- `docker compose ps`
- `docker compose logs -f web`
- Apache logs (see `apache.conf`):
  - `${APACHE_LOG_DIR}/goals.danielmoessner.de.error.log`
  - `${APACHE_LOG_DIR}/goals.danielmoessner.de.access.log`

### Backups

This deployment uses SQLite + filesystem state on the host. At minimum, back up:

- `/home/goals.danielmoessner.de/tmp/db.sqlite3`
- `/home/goals.danielmoessner.de/tmp/media/`

For local debugging, `pull-db.sh` copies the production SQLite DB into `./tmp/db.sqlite3`.

### Restore (runbook)

This deployment stores state in the server’s data dir (default: `/home/goals.danielmoessner.de/tmp`). To restore after a bad migration or data loss:

1. SSH to the server
2. Stop the app: `cd /home/goals.danielmoessner.de && docker compose down`
3. Restore state:
   - replace `tmp/db.sqlite3` from backup
   - restore `tmp/media/` from backup if needed
4. Start/deploy the desired version (recommended: immutable `sha-...`):
   - `GOALS_IMAGE=ghcr.io/<owner>/<repo>:sha-<gitsha> ./deploy-on-server.sh`

Tip: because this uses SQLite, always keep a known-good copy of `db.sqlite3` before running migrations.
