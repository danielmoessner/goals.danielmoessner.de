# Deployment pruning notes (reduce complexity)

Date: 2026-05-02

Goal: **reduce deployment code/steps significantly**. Approach: delete anything not clearly required for a working deploy, then add back only what we miss.

## Requirements audit (question everything)

All deployment-related requirements in this repo appear (via `git blame`) to have been introduced by **danielmoessner**.

For each requirement: *Who asked for it?* → `git blame` author shown. *Why does it exist?* → question. *Decision* → keep/delete.

### 1) "Deploy must be immutable" (`GOALS_IMAGE` must not be `:latest`)

- Author: danielmoessner
- Question: Do we really need to block `latest`? Would allowing `latest` make deploys easier?
- Decision: **Keep** (still easy, and prevents accidental drifting deploys).

### 2) "call-deploy.sh should verify the image exists before deploying"

- Author: danielmoessner
- Question: Does the deployer machine *need* Docker credentials and registry probing, or can we just try the deploy and let `docker compose pull` fail loudly?
- Decision: **Delete** (removed preflight logic to cut complexity/lines).

### 3) "Wait for healthcheck to be healthy, otherwise fail deploy"

- Author: danielmoessner
- Question: Does deploy really need a blocking health gate, or is it enough to start the container and let operators check `docker compose logs`?
- Decision: **Delete** (removed the health-wait loop). Healthchecks remain in Compose for visibility.

### 4) "Recursively chown/chmod static/media/logs on every deploy"

- Author: danielmoessner
- Question: Is this necessary every time? It can be slow (large media dirs) and adds brittle code paths.
- Decision: **Delete** (now we only ensure directories exist and set permissions on the few critical files).

### 5) "Secrets must be a JSON file on disk"

- Author: danielmoessner
- Question: Should we switch to env vars / secret manager? That may improve security but can reduce simplicity.
- Decision: **Keep (for now)** because it’s simple and already integrated into Django settings.

### 6) "Run deploy as root"

- Author: danielmoessner
- Question: Could we use a non-root user + `sudo` for the few privileged commands?
- Decision: **Keep (for now)** because it reduces moving parts. Revisit later if needed.

## What we deleted (can add back later)

- Image existence preflight / polling in `call-deploy.sh`.
- The healthcheck wait loop in `deploy-on-server.sh`.
- Recursive permission fixing across all state folders.

## What we kept / added back (minimum viable safety)

- A single `secrets.json` existence check (otherwise failures are confusing).

## Round 2 (repeat the cycle)

### 7) "Compose healthcheck must exist"

- Author: danielmoessner
- Question: Do we need healthchecks if they create false failures and block deploy? Can we just use `docker compose ps`/`logs`?
- Decision: **Delete** (removed healthcheck to cut lines and failure modes).

### 8) "Deploy script must fix permissions every time"

- Author: danielmoessner
- Question: Is it worth touching permissions on every deploy (slow, brittle) instead of one-time setup?
- Decision: **Delete** (removed chown/chmod entirely).

### 9) "Deploy should run a settings import check"

- Author: danielmoessner
- Question: Does this provide value beyond `migrate` failing anyway?
- Decision: **Delete** (removed).

### 10) "Deploy script must validate docker/compose availability"

- Author: danielmoessner
- Question: Is the nicer error message worth the extra code? Or do we rely on the command failing naturally?
- Decision: **Delete**, then **added back ~10%**: we kept a minimal `run as root` check + `secrets.json` check because those failures are otherwise confusing.

## Round 2 outcome (what changed)

- `call-deploy.sh`: compressed to a handful of lines; no longer copies `apache.conf` on every deploy.
- `deploy-on-server.sh`: now only does `pull → migrate → collectstatic → up → apache reload`.
- `docker-compose.yml`: healthcheck removed entirely; still supports path/port parameterization.

## If something breaks next

Likely add-backs (in this order):

1. A small post-deploy smoke test (non-blocking) that prints the app homepage status.
2. A bounded health wait (e.g. 30–60s) *only in CI*.
3. Optional preflight image existence check (only in CI).
