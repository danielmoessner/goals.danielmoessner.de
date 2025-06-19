cd /home/
git clone https://github.com/danielmoessner/goals.danielmoessner.de.git
cd goals.danielmoessner.de
mkdir tmp
mkdir tmp/logs
mkdir tmp/media
mkdir tmp/static
touch tmp/logs/django.log
ln -sf /home/goals.danielmoessner.de/apache.conf /etc/apache2/sites-available/goals.danielmoessner.de.conf
