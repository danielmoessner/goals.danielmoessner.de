# Ansible (Debian + Nginx)

This folder provisions a Debian server and deploys the app via Docker Compose.

- Nginx serves the domain over HTTPS and reverse-proxies to the container on `127.0.0.1:8080`.
- The server IP shows the Debian default Nginx page on both HTTP and HTTPS (HTTPS uses Debian's snakeoil cert).
- `secrets.json` is **manual** (not managed by Ansible).

## Prereqs

On your machine:
- `ansible` installed
- SSH access to the server (root or sudo-capable user)

On the server:
- Debian
- Python 3 installed (needed for Ansible modules)

## Configure inventory

Edit `ansible/inventory/production/hosts.ini` and add your host.

## Provision

```bash
ansible-playbook ansible/provision.yml
```

## Manual secrets step

Create the file on the server:

- `{{ app_data_dir }}/secrets.json` (default: `/home/goals.danielmoessner.de/tmp/secrets.json`)

## Migrate tmp/ (old -> new)

Create an inventory that contains both the old server and the new server by IP.
You can edit `ansible/inventory/migration/hosts.ini`:

```ini
[app_old]
old ansible_host=<OLD_IP> ansible_user=root

[app]
new ansible_host=<NEW_IP> ansible_user=root
```

Then run:

```bash
ansible-playbook -i ansible/inventory/migration/hosts.ini ansible/migrate.yml
```

Notes:
- Uses a local staging dir and `rsync --ignore-existing` (never overwrites destination files)
- Excludes `secrets.json`

## Deploy

Deploy the image for the current git SHA (or `GITHUB_SHA` if set):

```bash
ansible-playbook ansible/deploy.yml
```

Deploy a specific image tag:

```bash
ansible-playbook ansible/deploy.yml \
  -e app_image=ghcr.io/<owner>/<repo>:sha-<longsha>
```

## HTTPS

Provision always enables HTTPS for the domain via Let's Encrypt (HTTP-01 + webroot).
Ensure DNS for `app_domain` points to this server and port 80 is reachable.

Lets Encrypt does not issue certificates for bare IP addresses; `https://<ip>` is served by the Debian default site using a self-signed (snakeoil) cert.

Optional aliases (e.g. `www.`) can be set via `app_domain_aliases`.

## One-shot bootstrap

If your inventory contains both `app_old` and `app` (new), you can run:

```bash
ansible-playbook -i ansible/inventory/migration/hosts.ini ansible/bootstrap_new_server.yml
```
