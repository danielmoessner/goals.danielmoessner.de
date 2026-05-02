# Deployment improvement plan (goals.danielmoessner.de)

Date: 2026-05-01

This plan improves the current deployment across the categories in `deployment-evaluation.md`, with **Ease of deployment** as the top priority.

## Current baseline (what exists today)

- Build: GitHub Actions builds and pushes `ghcr.io/<owner>/<repo>` Docker images (tags include `sha-<longsha>`)
- Deploy trigger: manual `./call-deploy.sh` from a developer machine
- Server runtime: `docker compose` using `docker-compose.yml`
- Web serving: Apache TLS termination + reverse proxy to Gunicorn on `127.0.0.1:8080`
- State: SQLite + secrets + static/media on host under `/home/goals.danielmoessner.de/tmp`

## Improvements by category

### 1) Ease of deployment (highest priority)

Current strengths:

- Immutable deploy target (`sha-...` tag)
- Single command deploy entrypoint (`./call-deploy.sh`)

Current friction:

- Deploy requires a configured developer machine (SSH access, correct repo SHA, etc.)
- No “wait until image exists” gating (deploy can fail if CI hasn’t pushed the image yet)
- First-time server provisioning is partly manual (Apache config, directories, secrets file)
- `deploy-on-server.sh` applies permissions but doesn’t create missing directories/files, so a truly fresh server can fail in non-obvious ways

Planned improvements (in priority order):

1. **Make deploy self-verifying**
   - Add a preflight in `call-deploy.sh` that verifies the image tag exists in GHCR before connecting to the server.
   - Optionally: poll until the image appears (bounded wait), then continue.

2. **Make server script self-contained**
   - In `deploy-on-server.sh`, `mkdir -p` for required paths (`$DATA_DIR`, `$DATA_DIR/static`, `$DATA_DIR/media`, `$DATA_DIR/logs`) and `touch` for expected files (`django.log`).
   - Add an explicit, friendly check for `$DATA_DIR/secrets.json` with clear “missing keys” guidance.

3. **Parameterize host-specific paths**
   - Update `docker-compose.yml` to use a variable for the data dir, e.g. `${GOALS_DATA_DIR:-/home/goals.danielmoessner.de/tmp}:/django/tmp`.
   - Keep defaults so existing servers continue to work.

4. **Reduce “root SSH” dependency**
   - Introduce a `deploy` user on the server.
   - Use `sudo` for the small set of privileged operations (Apache reload, ownership changes) instead of requiring root login.

5. **Make deployment happen from CI (push-to-deploy)**
   - Add a GitHub Actions “deploy” job that runs after a successful image push.
   - The deploy job SSHes to the server and runs `deploy-on-server.sh` with `GOALS_IMAGE=sha-<longsha>`.
   - Optional: protect the environment (manual approval) if you want a human gate.

Outcome target:

- Deploy becomes “push to main → CI builds → CI deploys”, with no need to run scripts manually.

### 2) Repeatability & determinism

Current:

- Good: deploy uses immutable tags; dependencies are locked via `uv.lock`.
- Gap: server config/state is partly out-of-band (Apache config, secrets file format).

Improvements:

- Encode server config as code (templated Apache config or a managed symlink install step).
- Pin images by digest (optional) for maximum determinism.

### 3) Reliability & availability

Current:

- `docker compose up -d` restarts the service; there’s no explicit readiness gate.

Improvements:

- Add a Compose `healthcheck` for the web container.
- Add post-deploy smoke test in `deploy-on-server.sh` (e.g. `curl --fail http://127.0.0.1:8080/`).
- Consider a graceful Gunicorn config (`--graceful-timeout`, structured access logs) to reduce deploy impact.

### 4) Rollback & recovery

Current:

- Rollback is possible by redeploying an older immutable image.
- Risk: SQLite migrations without backups can be dangerous if schema/data changes.

Improvements:

- Add automatic pre-migrate backup of `db.sqlite3` (copy with timestamp) in `deploy-on-server.sh`.
- Add documented “restore” runbook.
- Add scheduled backups (cron/systemd timer) for DB + media.

### 5) Security

Current:

- Container runs as non-root.
- SSH defaults to root login in `call-deploy.sh`.
- Secrets live in a JSON file on disk.

Improvements:

- Use non-root SSH + least privilege via `sudo`.
- Ensure GHCR auth on server is handled safely if the image is private.
- Move secrets to environment variables or a secrets manager (optional; balance against ease).

### 6) Observability

Current:

- Django warnings go to a file (`tmp/django.log`).
- Container logs are not explicitly configured.

Improvements:

- Configure Gunicorn to log to stdout/stderr so `docker logs` shows useful information.
- Add basic metrics/monitoring (optional) and a simple uptime check.

### 7) Portability

Current:

- Hard-coded host paths and `network_mode: host` reduce portability.

Improvements:

- Parameterize paths and ports.
- Consider switching from host networking to explicit `ports:` mapping for more standard compose setups.

### 8) Maintainability & operational overhead

Improvements:

- Add a short runbook section for routine tasks: renew certs, rotate secrets, backups.
- Add a consistent command surface (Makefile/Justfile) for `dev`, `build`, `deploy`, `rollback`.

## Proposed roadmap

Phase 0 (done): Documentation

- README deployment instructions

Phase 1 (quick wins, 1–2 hours)

- Preflight checks in `call-deploy.sh` (image exists, SSH connectivity)
- Make `deploy-on-server.sh` create missing directories/files
- Parameterize the compose bind mount path

Phase 2 (automation, 0.5–1 day)

- CI deploy job (push-to-deploy)
- Post-deploy smoke test + optional healthcheck gating
- Deploy user + sudo-based privileges

Phase 3 (bigger / optional)

- Automated backups + restore drill
- Staging environment
- Replace SQLite with Postgres (only if reliability requirements justify the added complexity)
