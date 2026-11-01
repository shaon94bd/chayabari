"""
Chayabari — Django settings.

All deployment-specific values come from environment variables (or a
`.env` file next to manage.py). See `.env.example`.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BASE_DIR.parent

load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def env_list(name, default=""):
    return [v.strip() for v in os.environ.get(name, default).split(",") if v.strip()]


def _secret_key():
    """Use DJANGO_SECRET_KEY if set; otherwise create one once and keep it in .secret_key (git-ignored)."""
    if os.environ.get("DJANGO_SECRET_KEY"):
        return os.environ["DJANGO_SECRET_KEY"]
    path = BASE_DIR / ".secret_key"
    if not path.exists():
        import secrets

        path.write_text(secrets.token_urlsafe(50))
    return path.read_text().strip()


SECRET_KEY = _secret_key()
# Debug is on only for local development commands (runserver / test) unless set explicitly.
_DEV_COMMANDS = {"runserver", "test", "seed_demo"}
DEBUG = env_bool("DJANGO_DEBUG", bool(_DEV_COMMANDS.intersection(sys.argv[1:2])))
# Works out of the box on PythonAnywhere (yourname.pythonanywhere.com) and locally.
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,.pythonanywhere.com")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", "https://*.pythonanywhere.com")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third party
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    # local
    "apps.accounts",
    "apps.batches",
    "apps.gallery",
    "apps.auctions",
    "apps.market",
    "apps.messaging",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- Database -----------------------------------------------------------
# SQLite by default. On PythonAnywhere set DB_ENGINE=mysql and the DB_* vars.
if os.environ.get("DB_ENGINE", "sqlite") == "mysql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ["DB_NAME"],
            "USER": os.environ["DB_USER"],
            "PASSWORD": os.environ["DB_PASSWORD"],
            "HOST": os.environ["DB_HOST"],
            "PORT": os.environ.get("DB_PORT", "3306"),
            "OPTIONS": {"charset": "utf8mb4", "init_command": "SET sql_mode='STRICT_TRANS_TABLES'"},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.environ.get("SQLITE_PATH", BASE_DIR / "db.sqlite3"),
        }
    }

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.environ.get("TIME_ZONE", "Asia/Dhaka")
USE_I18N = True
USE_TZ = True

# --- Static & media -----------------------------------------------------
# The built Vue app (backend/spa, written by `npm run build`) is collected as static files and the
# SPA's index.html is served by Django for every non-API route.
SPA_DIST_DIR = Path(os.environ.get("SPA_DIST_DIR", BASE_DIR / "spa"))
STATIC_URL = "/static/"
STATIC_ROOT = Path(os.environ.get("STATIC_ROOT", BASE_DIR / "staticfiles"))
STATICFILES_DIRS = [SPA_DIST_DIR] if SPA_DIST_DIR.exists() else []
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", BASE_DIR / "media"))
DATA_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- REST framework ------------------------------------------------------
# Uses only packages preinstalled on PythonAnywhere (Python 3.11, "innit" image):
# DRF's built-in TokenAuthentication instead of JWT (simplejwt/PyJWT aren't preinstalled).
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticatedOrReadOnly"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 24,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "120/min", "user": "600/min", "login": "10/min"},
}

CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")

# --- Chayabari business settings ----------------------------------------
TRIAL_DAYS = int(os.environ.get("TRIAL_DAYS", "14"))
TRIAL_MAX_MEMBERS = int(os.environ.get("TRIAL_MAX_MEMBERS", "40"))
# Where batch owners send their subscription fee (shown on the billing page).
PAYMENT_INSTRUCTIONS = {
    "bkash": os.environ.get("PAY_BKASH_NUMBER", "01XXXXXXXXX"),
    "nagad": os.environ.get("PAY_NAGAD_NUMBER", "01XXXXXXXXX"),
}
# When true, submitted payments are auto-verified (handy for local demos).
PAYMENT_AUTO_VERIFY = env_bool("PAYMENT_AUTO_VERIFY", False)
# Anti-sniping: a bid placed in the last N minutes extends the auction by N minutes.
AUCTION_EXTENSION_MINUTES = int(os.environ.get("AUCTION_EXTENSION_MINUTES", "2"))
IMAGE_MAX_DIMENSION = int(os.environ.get("IMAGE_MAX_DIMENSION", "1600"))

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
