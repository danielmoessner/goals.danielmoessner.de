# Deployment evaluation categories

This document lists common categories for evaluating an application’s deployment approach.

These are **dimensions** you can score (e.g. 1–5) and weight based on what matters most. For this project, **Ease of deployment** is the primary category.

## 1) Ease of deployment (primary)

How hard is it to ship a change safely?

Signals / things to measure:

- Number of manual steps and “tribal knowledge”
- Time-to-deploy (including waiting time)
- How many prerequisites must be present on the deployer machine and on the server
- How understandable the process is for a new contributor
- Quality of preflight checks and error messages
- How easy it is to set up a fresh server (“from zero to serving traffic”)

## 2) Repeatability & determinism

How consistent is the result across runs and environments?

- Immutable artifacts (tags/digests)
- Pinned dependencies / lockfiles
- Idempotent deploy scripts
- Minimal drift between environments (dev/staging/prod)

## 3) Reliability & availability

How likely is a deploy to fail or cause downtime?

- Health checks and readiness gates
- Failure isolation (one service failing doesn’t take everything down)
- Restart behavior
- Deploy-time downtime (stop-the-world vs rolling)

## 4) Rollback & recovery

How quickly can you recover from a bad deploy or data issue?

- Fast rollback path (previous image, previous config)
- Migration safety (especially DB schema changes)
- Backups (frequency, restore drills)
- Disaster recovery story

## 5) Security

How safe is the process and runtime?

- Least privilege (SSH user, container user, host access)
- Secrets management (where secrets live, rotation)
- Supply-chain controls (trusted images, provenance/signing)
- Network exposure (open ports, internal-only services)

## 6) Observability

How easy is it to understand what is happening after deploy?

- Centralized logs / structured logs
- Metrics (request rates, latency, errors)
- Alerts and dashboards
- Post-deploy verification / smoke tests

## 7) Portability

How hard is it to move the deployment to a different machine/cloud?

- Avoiding hard-coded host paths
- Avoiding host-specific assumptions
- Standardized config (`.env`, env vars, compose overrides)
- Infrastructure-as-code

## 8) Maintainability & operational overhead

How much ongoing effort does the deployment require?

- Update cadence (OS + Docker + deps)
- Clear ownership and runbooks
- Automated routine tasks (rotations, renewals, log rotation)
- Cost in time (not only money)
