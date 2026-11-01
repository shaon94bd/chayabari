# Chayabari: Django backend

This folder is the deployable Django project. Built from the `backend/` folder of the main branch, it is published as the **`backend`** branch, with `manage.py` at the top level. It includes the built Vue app in `spa/`, so Django serves the whole site.

## Deploy on PythonAnywhere (git pull only)

There is nothing to configure. On first start the app:
- creates its own secret key (saved in `.secret_key`, which is git-ignored),
- runs with `DEBUG` off and accepts `*.pythonanywhere.com`,
- applies database migrations (SQLite `db.sqlite3`) and collects static files.

This happens on every **Reload**, so an update is just `git pull` followed by Reload.

**First time only:**
1. `git clone -b backend https://github.com/shaon94bd/chayabari.git ~/chayabari`
2. Install the packages into the web app's virtualenv: `pip install -r ~/chayabari/requirements.txt`
3. Web tab: set Source code and Working directory to `/home/<you>/chayabari`. Add static files `/static/` → `/home/<you>/chayabari/staticfiles` and `/media/` → `/home/<you>/chayabari/media`. Replace the WSGI file with:
   ```python
   import sys
   path = '/home/<you>/chayabari'
   if path not in sys.path:
       sys.path.insert(0, path)
   from config.wsgi import application
   ```
4. Reload.

**Admin account (whenever you like):** `cd ~/chayabari && python manage.py createsuperuser`, then go to `/admin/`.

**Optional settings:** copy `.env.example` to `.env` (for example for your bKash/Nagad numbers or MySQL), then Reload.
