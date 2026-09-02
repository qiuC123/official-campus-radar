import os

from django.core.asgi import get_asgi_application

from campus_radar.environment import load_project_exa_key

load_project_exa_key()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "campus_radar.settings")
application = get_asgi_application()
