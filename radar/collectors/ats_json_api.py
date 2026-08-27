from types import SimpleNamespace
from urllib.parse import urlparse

from radar.collectors.json_api import JsonApiSourceAdapter
from radar.models import OfficialSource


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


class AtsJsonApiSourceAdapter(JsonApiSourceAdapter):
    """Use the generic JSON adapter for an ATS linked from an official site."""

    @staticmethod
    def _normalized_source(source: OfficialSource):
        endpoint_host = _host(str(source.parser_config.get("endpoint", "")))
        return SimpleNamespace(
            parser_config=source.parser_config,
            source_url=source.source_url,
            organization=SimpleNamespace(official_domain=endpoint_host),
        )

    @classmethod
    def validate_source_config(cls, source: OfficialSource) -> None:
        if source.source_type != OfficialSource.SourceType.ATS:
            raise ValueError("ATS JSON adapter requires source_type=ats")
        entrypoint = str(source.official_entrypoint_url or "").strip()
        official_domain = source.organization.official_domain.strip().lower()
        entrypoint_host = _host(entrypoint)
        if not entrypoint_host or not (
            entrypoint_host == official_domain
            or entrypoint_host.endswith(f".{official_domain}")
        ):
            raise ValueError(
                "ATS JSON adapter requires an official-domain entrypoint"
            )
        endpoint_host = _host(str(source.parser_config.get("endpoint", "")))
        if not endpoint_host:
            raise ValueError("ATS JSON adapter endpoint host is required")
        JsonApiSourceAdapter.validate_source_config(cls._normalized_source(source))

    def fetch(self, source: OfficialSource):
        self.validate_source_config(source)
        return JsonApiSourceAdapter().fetch(self._normalized_source(source))
