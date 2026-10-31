#!/usr/bin/env bash
# One-command setup/update for PythonAnywhere. Run from a PythonAnywhere Bash console:
#
#   git clone -b claude/fine-art-exhibition-saas-4cv01t https://github.com/shaon94bd/chayabari.git
#   bash chayabari/scripts/pythonanywhere_setup.sh
#
# Safe to re-run after `git pull` to apply updates.
set -euo pipefail

USER_NAME="$(whoami)"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$REPO/backend"
VENV="$HOME/.virtualenvs/chayabari"
DOMAIN="${USER_NAME}.pythonanywhere.com"

echo "==> Python virtualenv ($VENV)"
if [ ! -x "$VENV/bin/python" ]; then
  python3.11 -m venv "$VENV"
fi
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r "$BACKEND/requirements.txt"

echo "==> Settings file (backend/.env)"
if [ ! -f "$BACKEND/.env" ]; then
  SECRET="$("$VENV/bin/python" -c 'import secrets; print(secrets.token_urlsafe(50))')"
  cat > "$BACKEND/.env" <<ENV
DJANGO_SECRET_KEY=$SECRET
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=$DOMAIN
DJANGO_CSRF_TRUSTED_ORIGINS=https://$DOMAIN
# SQLite by default. For MySQL, see docs/DEPLOY_PYTHONANYWHERE.md
SQLITE_PATH=$BACKEND/db.sqlite3
TRIAL_DAYS=14
TRIAL_MAX_MEMBERS=40
PAY_BKASH_NUMBER=01XXXXXXXXX
PAY_NAGAD_NUMBER=01XXXXXXXXX
ENV
  echo "    created (edit PAY_BKASH_NUMBER / PAY_NAGAD_NUMBER later with: nano $BACKEND/.env)"
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
cat > "$BACKEND/pythonanywhere_wsgi.py" <<PY
import os, sys
path = '$BACKEND'
if path not in sys.path:
    sys.path.insert(0, path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
PY
if [ -f "$WSGI" ]; then
  cp "$BACKEND/pythonanywhere_wsgi.py" "$WSGI"
  touch "$WSGI"   # reloads the web app
  echo "    installed into $WSGI and reloaded the web app"
else
  echo "    web app not created yet — see step below, then re-run this script"
fi

if ! "$VENV/bin/python" manage.py shell -c "from apps.accounts.models import User; import sys; sys.exit(0 if User.objects.filter(is_superuser=True).exists() else 1)"; then
  echo
  echo "==> Create your admin account (used to verify bKash/Nagad payments at /admin/)"
  "$VENV/bin/python" manage.py createsuperuser
fi

cat <<TXT

Done. If you have not set up the Web tab yet:
  Web tab -> Add a new web app -> Manual configuration -> Python 3.11
  Virtualenv:   $VENV
  Source code:  $BACKEND
  Static files: /static/ -> $BACKEND/staticfiles
                /media/  -> $BACKEND/media
  Force HTTPS:  on
Then run this script again (it installs the WSGI file and reloads).

Site:  https://$DOMAIN
Admin: https://$DOMAIN/admin/
TXT
