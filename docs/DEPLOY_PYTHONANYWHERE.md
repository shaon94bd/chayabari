# Deploying Chayabari on PythonAnywhere

## Quick deploy (browser only, no desktop needed)

The built frontend (`frontend/dist`) is committed to the repo, so you need no Node.js. Everything can be done in a browser, including on a phone.

1. Create a PythonAnywhere account and open a **Bash console** (Consoles tab).
2. Run:
   ```bash
   git clone -b claude/fine-art-exhibition-saas-4cv01t https://github.com/shaon94bd/chayabari.git
   bash chayabari/scripts/pythonanywhere_setup.sh
   ```
   This creates the virtualenv, generates `backend/.env` with a secret key, sets up the SQLite database and static files, and asks you to create an admin account.
3. **Web** tab → *Add a new web app* → **Manual configuration** → **Python 3.11**. Then fill in the paths the script printed (virtualenv, source code, and the `/static/` and `/media/` static file mappings) and turn on **Force HTTPS**.
4. Run `bash chayabari/scripts/pythonanywhere_setup.sh` once more. It installs the WSGI file and reloads the site.
5. Open `https://yourname.pythonanywhere.com`.

To update later: `cd ~/chayabari && git pull && bash scripts/pythonanywhere_setup.sh`.

The rest of this guide covers the manual route and MySQL.

---

Django serves both the API and the built Vue app from one web app (`https://yourname.pythonanywhere.com`).

> **Plan note.** The free tier works for a pilot, but it has limits: 512 MB disk (images are downscaled to 1600 px JPEG on upload, roughly 200–400 KB each), outbound internet restricted to a whitelist, no custom domain, and only one daily scheduled task. For a real paying customer, the $5 "Hacker" plan is the practical minimum because it adds a custom domain and more disk.

## 1. Build the frontend (only if you changed frontend code)

`frontend/dist` is committed to the repo. Rebuild it on any machine with Node.js after changing the frontend, then commit the result:

```bash
cd frontend
npm install
npm run build        # creates frontend/dist (assets are referenced under /static/)
```

## 2. Get the code onto PythonAnywhere

In a **Bash console**:

```bash
git clone https://github.com/<you>/chayabari.git
cd chayabari/backend
mkvirtualenv --python=/usr/bin/python3.11 chayabari
pip install -r requirements.txt
```

## 3. Database

**MySQL (recommended).** Open the **Databases** tab, set a password, and create the database `chayabari` (it becomes `yourname$chayabari`). `mysqlclient` is already installed on PythonAnywhere.

SQLite also works for a small pilot. Just leave `DB_ENGINE` unset.

## 4. Environment file

```bash
cp .env.example .env
nano .env
```

Set at least `DJANGO_SECRET_KEY` (generate one with `python -c "import secrets; print(secrets.token_urlsafe(50))"`), `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, the `DB_*` values and your bKash/Nagad numbers.

Then:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

## 5. Web app

**Web** tab → *Add a new web app* → **Manual configuration** → Python 3.11.

- **Virtualenv:** `/home/yourname/.virtualenvs/chayabari`
- **Source code:** `/home/yourname/chayabari/backend`
- **WSGI file:** replace its contents with:

```python
import os, sys
path = '/home/yourname/chayabari/backend'
if path not in sys.path:
    sys.path.insert(0, path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

- **Static files** (served directly by PythonAnywhere, fast):

| URL | Directory |
|---|---|
| `/static/` | `/home/yourname/chayabari/backend/staticfiles` |
| `/media/` | `/home/yourname/chayabari/backend/media` |

- Turn on **Force HTTPS**.

Click **Reload**. Visit the site. `/admin/` is the platform admin.

## 6. Scheduled task

**Tasks** tab → daily (free tier) or hourly (paid):

```
/home/yourname/.virtualenvs/chayabari/bin/python /home/yourname/chayabari/backend/manage.py settle_auctions
```

Auctions also settle the moment anyone opens them after they end, so this task is only a safety net.

## 7. Day-to-day operations

- **Verify payments:** `/admin/batches/payment/` → check the TrxID against your bKash/Nagad statement → select it → action *Verify selected payments*. The batch's plan activates immediately, and any remaining paid time is stacked, not lost.
- **Plans and prices:** `/admin/batches/plan/`.
- **Extend a trial or give free time:** edit the batch's subscription inline in `/admin/batches/batch/`.

## Updating

```bash
cd ~/chayabari && git pull
workon chayabari && cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Reload the web app from the Web tab.
