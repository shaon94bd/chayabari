# Deploying Chayabari on PythonAnywhere

Chayabari is built for a **default PythonAnywhere web app**: system Python 3.11, no virtualenv and no `pip install`. Every dependency is preinstalled there at the exact version in `requirements.txt` (see `CLAUDE.md`). Deployment uses the **`backend`** branch, which contains only the Django project (`manage.py` at the top level) plus the built Vue app in `spa/`.

On every start or **Reload**, the app sets itself up:
- creates a secret key once (`.secret_key`, git-ignored),
- runs with DEBUG off and accepts `*.pythonanywhere.com`,
- applies database migrations (SQLite `db.sqlite3` by default),
- collects static files into `staticfiles/`.

## First time

1. **Bash console:**
   ```bash
   git clone -b backend https://github.com/shaon94bd/chayabari.git ~/chayabari
   ```
2. **Web tab** (a web app with Python 3.11):
   - **Source code** and **Working directory:** `/home/<you>/chayabari`
   - **Virtualenv:** leave empty
   - **Static files:** `/static/` → `/home/<you>/chayabari/staticfiles`, and `/media/` → `/home/<you>/chayabari/media`. Remove any other static entries.
   - **Force HTTPS:** on
   - **WSGI configuration file:** replace everything with:
     ```python
     import sys
     path = '/home/<you>/chayabari'
     if path not in sys.path:
         sys.path.insert(0, path)
     from config.wsgi import application
     ```
3. Press **Reload** and open `https://<you>.pythonanywhere.com`.

## Updating

```bash
cd ~/chayabari && git pull
```

Then press **Reload**.

## Admin account

Create it whenever you like:

```bash
cd ~/chayabari && python3.11 manage.py createsuperuser
```

`/admin/` is where you verify bKash/Nagad payments (Payments → select → *Verify selected payments*), edit plans and prices, and extend trials.

## Optional

- **Settings** (payment numbers, trial length, MySQL…): copy `.env.example` to `.env` in `~/chayabari`, edit it, then Reload.
- **MySQL:** create the database in the Databases tab and set `DB_ENGINE=mysql`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` and `DB_HOST` in `.env`. `mysqlclient` is preinstalled.
- **Scheduled task** (Tasks tab, daily): `python3.11 /home/<you>/chayabari/manage.py settle_auctions`. This is a safety net; auctions also settle when someone opens them after they end.
- **Errors:** check the *error log* link on the Web tab.

## Free-tier limits

512 MB disk (images are downscaled to 1600 px on upload), no custom domain, and outbound internet only to whitelisted sites. The $5 plan removes the domain and disk limits.

## For maintainers: publishing the `backend` branch

```bash
cd frontend && npm run build && cd ..     # if the frontend changed (writes backend/spa); commit it
git subtree split --prefix=backend -b backend
git push origin backend
```
