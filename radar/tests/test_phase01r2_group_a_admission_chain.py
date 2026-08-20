from django.core.exceptions import ValidationError
from django.test import TestCase

from radar.collectors.registry import AdapterRegistry
from radar.models import (
    ApprovedApplicationHost,
    Evidence,
    OfficialSource,
    Organization,
    PublicationEvent,
    RecruitmentNotice,
    SourceAdmissionEvent,
    SourceVersion,
)
from radar.services.admission import (
    approve_application_host,
    source_is_admitted,
    source_permits_application_url,
    transition_source,
)
from radar.tests.helpers import create_enabled_source, publish_formal_notice


class AdmissionChainIntegrityTests(TestCase):
    def make_candidate(self, name: str = "Chain Org") -> OfficialSource:
        organization = Organization.objects.create(
            name=name,
            company_type="internet",
            industry="tech",
            official_domain="official.test",
        )
        return OfficialSource.objects.create(
            organization=organization,
            source_type="website",
            source_url="https://official.test/careers",
            admission_evidence="candidate",
        )

    def test_enabled_projection_requires_a_continuous_latest_event_chain(self) -> None:
        source = create_enabled_source(name="Broken Chain Org")
        latest = source.admission_events.order_by("-pk").first()
        SourceAdmissionEvent.objects.filter(pk=latest.pk).update(
            from_state="candidate",
            actor_label="",
        )

        self.assertFalse(source_is_admitted(source))

    def test_direct_discontinuous_event_append_is_rejected(self) -> None:
        source = self.make_candidate(name="Direct Jump Org")
        with self.assertRaises(ValidationError):
            SourceAdmissionEvent.objects.create(
                source=source,
                from_state="candidate",
                to_state="enabled",
                actor_label="owner",
                reason="skip verification",
                evidence="forged evidence",
            )

    def test_nonempty_admission_event_rewrite_is_detected(self) -> None:
        source = create_enabled_source(name="Event Rewrite Org")
        latest = source.admission_events.order_by("-pk").first()
        SourceAdmissionEvent.objects.filter(pk=latest.pk).update(
            reason="different nonempty reason"
        )

        self.assertFalse(source_is_admitted(source))

    def test_formal_query_rechecks_latest_admission_event(self) -> None:
        source = create_enabled_source(name="Stale Chain Org")
        notice = publish_formal_notice(source)
        latest = source.admission_events.order_by("-pk").first()
        SourceAdmissionEvent.objects.filter(pk=latest.pk).update(
            to_state=OfficialSource.AdmissionState.SUSPENDED
        )

        self.assertFalse(RecruitmentNotice.objects.formal().filter(pk=notice.pk).exists())

    def test_formal_query_rejects_cross_source_and_cross_notice_publication_links(self) -> None:
        source_a = create_enabled_source(name="Projection A", host="a.test")
        source_b = create_enabled_source(name="Projection B", host="b.test")
        notice_a = publish_formal_notice(source_a, identity_key="notice-a")
        notice_b = publish_formal_notice(source_b, identity_key="notice-b")
        original_event = notice_a.latest_publication_event
        foreign_version = notice_b.latest_publication_event.source_version
        forged_event = PublicationEvent.objects.create(
            source_version=foreign_version,
            notice=notice_b,
            event_type=PublicationEvent.EventType.UPDATED,
            identity_key=notice_a.identity_key,
            candidate_title=notice_a.title,
            evidence_complete=True,
        )
        for item in Evidence.objects.filter(publication_event=original_event):
            Evidence.objects.create(
                notice=notice_a,
                source_version=foreign_version,
                publication_event=forged_event,
                position=item.position,
                application_link=item.application_link,
                field_name=item.field_name,
                excerpt=item.excerpt,
                locator=item.locator,
                raw_value=item.raw_value,
                parsed_value=item.parsed_value,
                value_hash=item.value_hash,
            )
        notice_a.latest_publication_event = forged_event
        notice_a.save(update_fields=["latest_publication_event"])

        self.assertFalse(RecruitmentNotice.objects.formal().filter(pk=notice_a.pk).exists())


class ApprovedHostIntegrityTests(TestCase):
    def test_host_record_is_immutable_and_consumers_recheck_its_event_chain(self) -> None:
        source = create_enabled_source(name="Host Integrity")
        verification_event = source.admission_events.get(to_state="verified")
        host = ApprovedApplicationHost.objects.create(
            source=source,
            host="apply.test",
            evidence="official entrypoint link",
            actor_label="owner",
            admission_event=verification_event,
        )
        host.evidence = "rewritten"
        with self.assertRaises(ValidationError):
            host.save()

        ApprovedApplicationHost.objects.filter(pk=host.pk).update(actor_label="")
        self.assertFalse(
            source_permits_application_url(source, "https://apply.test/jobs/1")
        )

    def test_nonempty_host_approval_rewrite_is_detected(self) -> None:
        source = create_enabled_source(name="Host Rewrite")
        host = ApprovedApplicationHost.objects.create(
            source=source,
            host="apply.test",
            evidence="official entrypoint link",
            actor_label="owner",
            admission_event=source.admission_events.get(to_state="verified"),
        )
        ApprovedApplicationHost.objects.filter(pk=host.pk).update(
            evidence="different nonempty evidence"
        )

        self.assertFalse(
            source_permits_application_url(source, "https://apply.test/jobs/1")
        )

    def test_host_record_rejects_an_admission_event_from_another_source(self) -> None:
        source_a = create_enabled_source(name="Host Source A", host="a.test")
        source_b = create_enabled_source(name="Host Source B", host="b.test")
        with self.assertRaises(ValidationError):
            ApprovedApplicationHost.objects.create(
                source=source_a,
                host="apply.test",
                evidence="official entrypoint link",
                actor_label="owner",
                admission_event=source_b.admission_events.get(to_state="verified"),
            )


class AdapterAdmissionContractTests(TestCase):
    def test_html_source_cannot_be_enabled_with_an_incomplete_parser_contract(self) -> None:
        organization = Organization.objects.create(
            name="Incomplete Parser",
            company_type="internet",
            industry="tech",
            official_domain="official.test",
        )
        source = OfficialSource.objects.create(
            organization=organization,
            source_type="website",
            source_url="https://official.test/careers",
            admission_evidence="candidate",
            parser_config={"notice_selector": "article", "title_selector": "h2"},
        )
        transition_source(
            source,
            to_state="verified",
            actor_label="owner",
            reason="official host reviewed",
            evidence="saved review",
        )

        with self.assertRaises(ValidationError):
            transition_source(
                source,
                to_state="enabled",
                actor_label="owner",
                reason="fixture checked",
                evidence="fixture result",
            )

    def test_local_demo_adapter_is_registered_and_never_fetches_network(self) -> None:
        source = self.make_demo_source()
        adapter = AdapterRegistry.get(source)
        page = adapter.fetch(source)

        self.assertTrue(page.not_modified)
        self.assertEqual(adapter.extract(source, page), [])

    @staticmethod
    def make_demo_source() -> OfficialSource:
        organization = Organization.objects.create(
            name="Offline Demo Adapter",
            company_type="other",
            industry="demo",
            official_domain="demo.invalid",
        )
        return OfficialSource.objects.create(
            organization=organization,
            source_type="website",
            source_url="https://demo.invalid/careers",
            admission_evidence="offline demo",
            adapter_name="local_demo_disabled",
        )
