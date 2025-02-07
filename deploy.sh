cd /home/goals.danielmoessner.de/ || exit
curl -LsSf https://astral.sh/uv/install.sh | sh
git reset --hard HEAD
git pull
tmp/venv/bin/pip install -r requirements.txt
tmp/venv/bin/python manage.py migrate
tmp/venv/bin/python manage.py collectstatic --noinput
./permissions.sh
systemctl restart apache2
