"""Private preview only: Django's static handler is not a public static server."""

import os

os.environ["DJANGO_SETTINGS_MODULE"] = "campus_radar.settings_private_preview"

from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.wsgi import get_wsgi_application
from django.conf import settings

django_application = get_wsgi_application()
from radar.services.public_snapshot import read_snapshot
read_snapshot(settings.RADAR_DISPLAY_SNAPSHOT)  # Fail startup for a full or invalid database.
application = StaticFilesHandler(django_application)
