from django.test import TestCase

from radar.models import OfficialSource, Organization
from radar.services.admission import source_is_admitted
from radar.services.admission import transition_source
from radar.tests.helpers import valid_html_parser_config


class SourceAdmissionTests(TestCase):
    def test_requires_verified_active_https_source_with_evidence(self) -> None:
        organization = Organization.objects.create(name="示例公司", company_type="internet", industry="互联网", official_domain="careers.example.test")
        source = OfficialSource.objects.create(
            organization=organization, source_type="website", source_url="https://careers.example.test",
            admission_evidence="官网页脚可证明归属",
            parser_config=valid_html_parser_config(),
        )
        transition_source(source, to_state="verified", actor_label="owner", reason="verified", evidence="review")
        transition_source(source, to_state="enabled", actor_label="owner", reason="enabled", evidence="fixture")
        source.refresh_from_db()
        self.assertTrue(source_is_admitted(source))
        source.admission_state = "suspended"
        self.assertFalse(source_is_admitted(source))
