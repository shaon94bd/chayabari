# Chayabari: notes for Claude

## Hosting constraint: PythonAnywhere default setup (do not break)

Production runs on a **PythonAnywhere free account**, as a default web app using the
**system Python 3.11** (system image **"innit"**), with **no virtualenv and no `pip install`**.
The owner deploys **only with `git pull`** (plus the Reload button) from the `backend` branch.

Therefore the backend may only use packages preinstalled there. Verified versions
(from https://www.pythonanywhere.com/batteries_included/, image innit, Python 3.11):

| Package | Version |
|---|---|
| Django | 5.0.9 |
| djangorestframework | 3.15.2 (use `rest_framework.authtoken` for auth) |
| django-cors-headers | 4.6.0 |
| Pillow | 10.4.0 |
| python-dotenv | 1.0.1 |
| mysqlclient | 2.2.6 (optional MySQL) |
| requests | 2.32.3 |

Also available there if ever needed: django-environ 0.11.2, django-allauth 65.2.0,
dj-rest-auth 7.0.0, django-extensions 3.2.3, cryptography 43.0.3, itsdangerous 2.2.0.
**Not available:** djangorestframework-simplejwt, PyJWT, whitenoise, channels, celery,
django-filter. Never add a dependency without checking that list first; prefer
the standard library or Django/DRF built-ins.

Other platform limits to respect:
- No websockets or background workers. Use polling; long jobs run as a daily
  scheduled task (`manage.py settle_auctions`).
- There is no Node.js on the server. The Vue app is built here (`cd frontend && npm run build`,
  which writes `backend/spa/`) and committed.
- The site must start with zero manual steps: `config/wsgi.py` runs `migrate` and
  `collectstatic` on start, the secret key is auto-generated in `.secret_key`, and
  the defaults allow `*.pythonanywhere.com` with DEBUG off.
- Disk is 512 MB, so uploaded images are downscaled (`apps/core/images.py`).

## Branches & publishing

- Main development: `claude/fine-art-exhibition-saas-4cv01t` (repo root: `backend/`, `frontend/`, `docs/`).
- Deploy branch: **`backend`**, the contents of `backend/` only (`manage.py` at the top level).
  After committing on the dev branch, publish it with:
  ```bash
  cd frontend && npm run build && cd ..        # if the frontend changed; commit backend/spa
  git subtree split --prefix=backend -b backend && git push origin backend
  ```

## Checks before pushing

```bash
cd backend && python manage.py test          # backend tests (use a Python 3.11 venv with requirements.txt)
cd frontend && npm run build
```
