"""Public read-only process. Management/collection must use a separate process."""

from urllib.parse import quote

from .settings import *  # noqa: F403

DEBUG = False
RADAR_PUBLIC_READONLY = True
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if len(SECRET_KEY) < 50 or len(set(SECRET_KEY)) < 5 or SECRET_KEY.startswith("django-insecure-"):
    raise ImproperlyConfigured("Public service requires a strong DJANGO_SECRET_KEY (at least 50 characters).")

ALLOWED_HOSTS = [item.strip() for item in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if item.strip()]
if not ALLOWED_HOSTS or any("*" in item or item.startswith(".") for item in ALLOWED_HOSTS):
    raise ImproperlyConfigured("Public service requires explicit DJANGO_ALLOWED_HOSTS; wildcards are forbidden.")

_database_path = Path(os.environ.get("RADAR_DATABASE_PATH", ""))
if not _database_path.is_absolute() or not _database_path.is_file():
    raise ImproperlyConfigured("RADAR_DATABASE_PATH must name an existing absolute SQLite file.")
DATABASES = {"default": {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": "file:" + quote(_database_path.as_posix(), safe="/:") + "?mode=ro",
    "OPTIONS": {"uri": True, "timeout": 20},
}}
STATIC_ROOT = Path(os.environ.get("RADAR_STATIC_ROOT", str(BASE_DIR / "staticfiles")))
if not STATIC_ROOT.is_absolute() or _database_path.resolve().is_relative_to(STATIC_ROOT.resolve()):
    raise ImproperlyConfigured("Static files require an absolute directory that does not contain the database.")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
# Only enable behind a loopback-only proxy that overwrites this header.
if os.environ.get("RADAR_TRUST_PROXY_HTTPS") == "1":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
