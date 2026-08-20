import requests


_ORIGINAL_REQUEST = requests.sessions.Session.request


def _blocked_request(self, method, url, *args, **kwargs):
    raise RuntimeError(
        f"outbound HTTP is blocked in radar tests: {method} {url}"
    )


def install_requests_guard() -> None:
    if requests.sessions.Session.request is not _blocked_request:
        requests.sessions.Session.request = _blocked_request


def assert_outbound_http_is_blocked() -> None:
    requests.Session().get("https://network.invalid/")
