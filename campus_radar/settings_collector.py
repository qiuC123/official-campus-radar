"""Private CLI-only collection worker; never use this module to serve HTTP."""
from .settings import *  # noqa: F403

collector_path = Path(os.environ.get("RADAR_COLLECTOR_DATABASE", ""))
if not collector_path.is_absolute() or not collector_path.is_file():
    raise ImproperlyConfigured("An existing absolute RADAR_COLLECTOR_DATABASE is required")
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": collector_path}}
DEBUG = False
ALLOWED_HOSTS = []
RADAR_PUBLIC_READONLY = True
