#!/usr/bin/env bash
# One-command setup/update for PythonAnywhere. From a PythonAnywhere Bash console:
#
#   git clone -b backend https://github.com/shaon94bd/chayabari.git ~/chayabari
#   bash ~/chayabari/pythonanywhere_setup.sh
#
# Safe to re-run after `git pull` to apply updates.
set -euo pipefail

USER_NAME="$(whoami)"
BACKEND="$(cd "$(dirname "$0")" && pwd)"     # folder containing manage.py
VENV="${VENV:-$HOME/.virtualenvs/chayabari}"
DOMAIN="${USER_NAME}.pythonanywhere.com"

echo "==> Python virtualenv ($VENV)"
if [ ! -x "$VENV/bin/python" ]; then
  python3.11 -m venv "$VENV"
fi
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r "$BACKEND/requirements.txt"

echo "==> Settings file ($BACKEND/.env)"
if [ ! -f "$BACKEND/.env" ]; then
  SECRET="$("$VENV/bin/python" -c 'import secrets; print(secrets.token_urlsafe(50))')"
  cat > "$BACKEND/.env" <<ENV
DJANGO_SECRET_KEY=$SECRET
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=$DOMAIN
DJANGO_CSRF_TRUSTED_ORIGINS=https://$DOMAIN
# SQLite by default. For MySQL set DB_ENGINE=mysql and DB_NAME/DB_USER/DB_PASSWORD/DB_HOST.
SQLITE_PATH=$BACKEND/db.sqlite3
TRIAL_DAYS=14
TRIAL_MAX_MEMBERS=40
PAY_BKASH_NUMBER=01XXXXXXXXX
PAY_NAGAD_NUMBER=01XXXXXXXXX
ENV
  echo "    created (edit payment numbers later with: nano $BACKEND/.env)"
else
  echo "    exists, leaving it alone"
fi

echo "==> Database & static files"
cd "$BACKEND"
"$VENV/bin/python" manage.py migrate --noinput
"$VENV/bin/python" manage.py collectstatic --noinput -v0
mkdir -p "$BACKEND/media"

echo "==> WSGI file"
WSGI="/var/www/${USER_NAME}_pythonanywhere_com_wsgi.py"
WSGI_CONTENT="import os, sys
path = '$BACKEND'
if path not in sys.path:
    sys.path.insert(0, path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
"
if [ -f "$WSGI" ]; then
  printf '%s' "$WSGI_CONTENT" > "$WSGI"   # writing it also reloads the web app
  echo "    installed into $WSGI and reloaded the web app"
else
  echo "    no web app found yet: create it in the Web tab (see below), then re-run this script"
fi

if ! "$VENV/bin/python" manage.py shell -c "from apps.accounts.models import User; import sys; sys.exit(0 if User.objects.filter(is_superuser=True).exists() else 1)"; then
  echo
  echo "==> Create your admin account (used to verify bKash/Nagad payments at /admin/)"
  "$VENV/bin/python" manage.py createsuperuser || true
fi

cat <<TXT

Done. Web tab settings for ${DOMAIN}:
  Source code:  $BACKEND
  Working dir:  $BACKEND
  Virtualenv:   $VENV
  Static files: /static/ -> $BACKEND/staticfiles
                /media/  -> $BACKEND/media
  Force HTTPS:  on
After changing anything in the Web tab, press the green Reload button.

Site:  https://$DOMAIN
Admin: https://$DOMAIN/admin/
TXT
