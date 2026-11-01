# Deploying Chayabari on PythonAnywhere

## Quick deploy (browser only, no desktop needed)

Deploy the **`backend`** branch. It contains only the Django project (`manage.py` at the top level) plus the built Vue app in `spa/`.

1. Open a **Bash console** on PythonAnywhere and run:
   ```bash
   git clone -b backend https://github.com/shaon94bd/chayabari.git ~/chayabari
   bash ~/chayabari/pythonanywhere_setup.sh
   ```
2. **Web** tab (web app on Python 3.11). Set Source code and Working directory to `/home/<you>/chayabari` and Virtualenv to `/home/<you>/.virtualenvs/chayabari`. Add static mappings `/static/` → `/home/<you>/chayabari/staticfiles` and `/media/` → `/home/<you>/chayabari/media`, and turn on Force HTTPS.
3. Run `bash ~/chayabari/pythonanywhere_setup.sh` again. It writes the WSGI file and reloads the site.

To update later: `cd ~/chayabari && git pull && bash pythonanywhere_setup.sh`.

**Maintainers:** after changing code on the main branch, rebuild the frontend (`cd frontend && npm run build`, which writes to `backend/spa`), commit, then publish:
`git subtree split --prefix=backend -b backend && git push origin backend`.

---

Django serves both the API and the built Vue app from one web app (`https://yourname.pythonanywhere.com`).

> **Plan note.** The free tier works for a pilot, but it has limits: 512 MB disk (images are downscaled to 1600 px JPEG on upload, roughly 200–400 KB each), outbound internet restricted to a whitelist, no custom domain, and only one daily scheduled task. For a real paying customer, the $5 "Hacker" plan is the practical minimum because it adds a custom domain and more disk.

## 1. Build the frontend (only if you changed frontend code)

The built app lives in `backend/spa` and is committed. Rebuild it on any machine with Node.js after changing the frontend, then commit the result:

```bash
cd frontend
npm install
npm run build        # writes backend/spa (assets are referenced under /static/)
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
