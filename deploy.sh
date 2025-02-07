cd /home/goals.danielmoessner.de/ || exit
curl -LsSf https://astral.sh/uv/install.sh | sh
git reset --hard HEAD
git pull
uv sync
uv run manage.py migrate
uv run manage.py collectstatic --noinput
./permissions.sh
systemctl restart apache2
