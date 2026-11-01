"""
WSGI entry point.

On every start (i.e. every "Reload" on PythonAnywhere) this applies database
migrations and collects static files, so deploying an update is just:
`git pull` + Reload. Set CHAYABARI_AUTO_SETUP=0 to turn this off.
"""

import fcntl
import logging
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()


def _auto_setup():
    from django.conf import settings
    from django.core.management import call_command

    lock_path = settings.BASE_DIR / ".setup.lock"
    with open(lock_path, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)  # only one worker at a time
        call_command("migrate", interactive=False, verbosity=0)
        call_command("collectstatic", interactive=False, verbosity=0)
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)


if os.environ.get("CHAYABARI_AUTO_SETUP", "1") == "1":
    try:
        _auto_setup()
    except Exception:  # never stop the site from starting; details go to the error log
        logging.getLogger(__name__).exception("Chayabari auto-setup failed")
