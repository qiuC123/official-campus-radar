import os

from django.core.wsgi import get_wsgi_application

from campus_radar.environment import load_project_exa_key

load_project_exa_key()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "campus_radar.settings")
application = get_wsgi_application()
