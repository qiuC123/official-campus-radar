from radar.collectors.base import FetchedPage
from radar.collectors.ats_json_api import AtsJsonApiSourceAdapter
from radar.collectors.embedded_jobs import EmbeddedJobsAdapter
from radar.collectors.html import HtmlSourceAdapter
from radar.collectors.isolated_browser_json import IsolatedBrowserJsonSourceAdapter
from radar.collectors.json_api import JsonApiSourceAdapter
from radar.collectors.moka_api import MokaPublicApiAdapter
from radar.models import OfficialSource


class DisabledLocalDemoAdapter:
    """Explicit offline adapter used only by the reserved local demo fixture."""

    @staticmethod
    def validate_source_config(source: OfficialSource) -> None:
        if source.organization.official_domain != "demo.invalid":
            raise ValueError("local demo adapter is restricted to demo.invalid")

    @staticmethod
    def fetch(source: OfficialSource) -> FetchedPage:
        return FetchedPage(source.source_url, "", "", 304, None, True)

    @staticmethod
    def extract(source: OfficialSource, page: FetchedPage):
        return []


class AdapterRegistry:
    adapters = {
        "html_selector": HtmlSourceAdapter,
        "json_api": JsonApiSourceAdapter,
        "ats_json_api": AtsJsonApiSourceAdapter,
        "embedded_jobs": EmbeddedJobsAdapter,
        "moka_public_api": MokaPublicApiAdapter,
        "isolated_browser_json": IsolatedBrowserJsonSourceAdapter,
        "local_demo_disabled": DisabledLocalDemoAdapter,
    }

    @classmethod
    def get(cls, source: OfficialSource):
        try:
            return cls.adapters[source.adapter_name]()
        except KeyError as error:
            raise ValueError(f"unregistered adapter: {source.adapter_name}") from error

    @classmethod
    def validate_source_config(cls, source: OfficialSource) -> None:
        adapter = cls.get(source)
        adapter.validate_source_config(source)
