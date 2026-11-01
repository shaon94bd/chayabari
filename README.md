# Chayabari: Django backend

This folder is the deployable Django project. Built from the `backend/` folder of the main branch, it is published as the **`backend`** branch, with `manage.py` at the top level.

It includes the built Vue app in `spa/`, so Django serves the whole site and the server needs no Node.js.

## Deploy on PythonAnywhere

```bash
git clone -b backend https://github.com/shaon94bd/chayabari.git ~/chayabari
bash ~/chayabari/pythonanywhere_setup.sh
```

Then, in the **Web** tab:

| Setting | Value |
|---|---|
| Source code / Working directory | `/home/<you>/chayabari` |
| Virtualenv | `/home/<you>/.virtualenvs/chayabari` |
| Static files `/static/` | `/home/<you>/chayabari/staticfiles` |
| Static files `/media/` | `/home/<you>/chayabari/media` |
| Force HTTPS | on |

Run the script again so it can install the WSGI file and reload the site.

**Update:** `cd ~/chayabari && git pull && bash pythonanywhere_setup.sh`

**Verify payments:** go to `/admin/` → Payments → select a payment → *Verify selected payments*.

**Optional scheduled task** (Tasks tab, daily):
`/home/<you>/.virtualenvs/chayabari/bin/python /home/<you>/chayabari/manage.py settle_auctions`
