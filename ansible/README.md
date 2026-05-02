# Ansible (Debian + Nginx)

This folder provisions a Debian server and deploys the app via Docker Compose.

- Nginx terminates HTTP (port 80) and reverse-proxies to the container on `127.0.0.1:8080`.
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

If the server already runs Apache, Nginx will fail to start because port `:80` is in use.
To let Ansible stop/disable Apache during provisioning:

```bash
ansible-playbook ansible/provision.yml -e goals_disable_apache=true
```

## Manual secrets step

Create the file on the server:

- `{{ goals_data_dir }}/secrets.json` (default: `/home/goals.danielmoessner.de/tmp/secrets.json`)

## Migrate tmp/ (old -> new)

Create an inventory that contains both the old server and the new server by IP.
You can edit `ansible/inventory/migration/hosts.ini`:

```ini
[goals_old]
old ansible_host=<OLD_IP> ansible_user=root

[goals]
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
  -e goals_image=ghcr.io/<owner>/<repo>:sha-<longsha>
```

## HTTPS

Provision installs `certbot`, but enabling HTTPS requires your domain to point to the new server.
Let’s Encrypt does not issue certificates for bare IP addresses.

After DNS cutover, enable HTTPS like this:

```bash
ansible-playbook ansible/provision.yml \
  -e goals_enable_https=true
```

Optional aliases (e.g. `www.`) can be set via `goals_server_aliases`.

## One-shot bootstrap

If your inventory contains both `goals_old` and `goals` (new), you can run:

```bash
ansible-playbook -i ansible/inventory/migration/hosts.ini ansible/bootstrap_new_server.yml
```
