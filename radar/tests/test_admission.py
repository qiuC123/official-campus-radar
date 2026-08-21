from django.core.exceptions import ValidationError
from django.test import TestCase

from radar.models import OfficialSource, Organization
from radar.services.admission import source_is_admitted
from radar.services.admission import transition_source
from radar.tests.helpers import valid_html_parser_config


class SourceAdmissionTests(TestCase):
    def test_api_source_type_is_available(self) -> None:
        self.assertIn("api", OfficialSource.SourceType.values)

    def test_api_source_uses_the_official_domain_admission_rule(self) -> None:
        organization = Organization.objects.create(
            name="API Source Org",
            company_type="internet",
            industry="tech",
            official_domain="careers.example.test",
        )
        source = OfficialSource.objects.create(
            organization=organization,
            source_type=OfficialSource.SourceType.WEBSITE,
            source_url="https://careers.example.test/api/jobs",
            admission_evidence="official API fixture",
            parser_config=valid_html_parser_config(),
        )
        transition_source(
            source,
            to_state="verified",
            actor_label="owner",
            reason="official API domain checked",
            evidence="saved local verification",
        )
        transition_source(
            source,
            to_state="enabled",
            actor_label="owner",
            reason="offline API fixture accepted",
            evidence="fixture passed",
        )
        source.refresh_from_db()
        source.source_type = "api"
        source.parser_config = {
            "endpoint": "https://careers.example.test/api/jobs"
        }
        source.save(update_fields=["source_type", "parser_config"])

        self.assertTrue(source_is_admitted(source))
        source.parser_config["endpoint"] = "https://untrusted.example/api/jobs"
        source.save(update_fields=["parser_config"])
        self.assertFalse(source_is_admitted(source))

    def test_api_source_rejects_an_endpoint_outside_the_official_domain(self) -> None:
        organization = Organization.objects.create(
            name="Untrusted API Endpoint Org",
            company_type="internet",
            industry="tech",
            official_domain="careers.example.test",
        )
        source = OfficialSource.objects.create(
            organization=organization,
            source_type=OfficialSource.SourceType.API,
            source_url="https://careers.example.test/jobs",
            admission_evidence="official API fixture",
            adapter_name="json_api",
            parser_config={"endpoint": "https://untrusted.example/api/jobs"},
        )

        with self.assertRaisesRegex(ValidationError, "API endpoint"):
            transition_source(
                source,
                to_state="verified",
                actor_label="owner",
                reason="API domain review",
                evidence="saved local verification",
            )

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
