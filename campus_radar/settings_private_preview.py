"""SSH-only loopback preview, not a public deployment configuration."""

from .settings_public import *  # noqa: F403

if os.environ.get("RADAR_SSH_PREVIEW") != "1":
    raise ImproperlyConfigured("Private preview requires explicit RADAR_SSH_PREVIEW=1")
if set(ALLOWED_HOSTS) - {"127.0.0.1", "localhost", "[::1]"}:
    raise ImproperlyConfigured("Private preview permits loopback hosts only")
# Browser -> local loopback HTTP; across the network traffic is encrypted by SSH.
# The dedicated launcher also forces a loopback listener; public settings stay HTTPS-only.
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_PROXY_SSL_HEADER = None
RADAR_DISPLAY_SNAPSHOT = os.environ["RADAR_DATABASE_PATH"]
