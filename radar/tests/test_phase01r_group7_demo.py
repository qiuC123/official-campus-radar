from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from radar.models import OfficialSource, Organization, RecruitmentNotice


class OfflineDemoFixtureTests(TestCase):
    def test_demo_is_not_loaded_by_default_and_loads_only_traceable_local_records(self) -> None:
        self.assertFalse(Organization.objects.filter(official_domain="demo.invalid").exists())
        self.assertTrue((Path(settings.BASE_DIR) / "data" / "local_demo.json").is_file())

        call_command("load_local_demo")
        organization = Organization.objects.get(official_domain="demo.invalid")
        source = organization.official_sources.get()
        self.assertEqual(source.admission_state, "enabled")
        self.assertEqual(source.adapter_name, "local_demo_disabled")
        notices = RecruitmentNotice.objects.filter(organization=organization)
        self.assertEqual(notices.count(), 3)
        self.assertFalse(notices.filter(source__isnull=True).exists())
        self.assertFalse(notices.filter(latest_publication_event__isnull=True).exists())
        active = notices.get(status="active")
        self.assertTrue(RecruitmentNotice.objects.formal().filter(pk=active.pk).exists())
        self.assertGreater(active.latest_publication_event.evidence.count(), 0)

    def test_demo_cleanup_preserves_non_demo_data(self) -> None:
        sentinel = Organization.objects.create(
            name="Keep Me", company_type="other", industry="test"
        )
        call_command("load_local_demo")
        call_command("load_local_demo", "--remove")
        self.assertFalse(Organization.objects.filter(official_domain="demo.invalid").exists())
        self.assertTrue(Organization.objects.filter(pk=sentinel.pk).exists())
        self.assertFalse(OfficialSource.objects.filter(source_url__contains="demo.invalid").exists())
