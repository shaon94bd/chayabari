# Chayabari: Django backend

This folder is the deployable Django project. Built from the `backend/` folder of the main branch, it is published as the **`backend`** branch, with `manage.py` at the top level. It includes the built Vue app in `spa/`, so Django serves the whole site.

## Deploy on PythonAnywhere (git pull only)

There is nothing to configure. On first start the app:
- creates its own secret key (saved in `.secret_key`, which is git-ignored),
- runs with `DEBUG` off and accepts `*.pythonanywhere.com`,
- applies database migrations (SQLite `db.sqlite3`) and collects static files.

This happens on every **Reload**, so an update is just `git pull` followed by Reload.

It needs **no `pip install`**: every dependency in `requirements.txt` is preinstalled on PythonAnywhere for Python 3.11 at the same version. Use a default web app with Python 3.11 and **no virtualenv**.

**First time only:**
1. `git clone -b backend https://github.com/shaon94bd/chayabari.git ~/chayabari`
2. Web tab: set Source code and Working directory to `/home/<you>/chayabari`, and leave Virtualenv empty. Add static files `/static/` → `/home/<you>/chayabari/staticfiles` and `/media/` → `/home/<you>/chayabari/media`. Replace the WSGI file with:
   ```python
   import sys
   path = '/home/<you>/chayabari'
   if path not in sys.path:
       sys.path.insert(0, path)
   from config.wsgi import application
   ```
3. Reload.

**Admin account (whenever you like):** `cd ~/chayabari && python3.11 manage.py createsuperuser`, then go to `/admin/`.

**Optional settings:** copy `.env.example` to `.env` (for example for your bKash/Nagad numbers or MySQL), then Reload.
