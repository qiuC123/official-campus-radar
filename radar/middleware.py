"""Explicit public route allowlist; private/local mode retains the owner's UI."""

from django.conf import settings
from django.http import HttpResponseNotAllowed, HttpResponseNotFound
from django.urls import Resolver404, resolve


class PublicReadOnlyMiddleware:
    public_views = frozenset({"dashboard", "history", "batch_positions"})

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.RADAR_PUBLIC_READONLY:
            try:
                match = resolve(request.path_info)
            except Resolver404:
                return HttpResponseNotFound()
            if match.view_name not in self.public_views:
                return HttpResponseNotFound()
            if request.method not in {"GET", "HEAD"}:
                return HttpResponseNotAllowed(["GET", "HEAD"])
            # Do not load admin sessions or messages in the public process.
            request.COOKIES = {}
        response = self.get_response(request)
        if settings.RADAR_PUBLIC_READONLY:
            response["Cache-Control"] = "no-store"
        return response
