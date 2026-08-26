from django.core.management import call_command
from django.test import TestCase

from radar.models import ApplicationProgress, Organization, RecruitmentBatch, UpdateRun


class LocalDemoCommandTests(TestCase):
    def test_load_and_remove_controlled_local_demo(self) -> None:
        call_command("load_local_demo")
        organization = Organization.objects.get(official_domain="demo.invalid")
        self.assertEqual(RecruitmentBatch.objects.filter(organization=organization).count(), 3)
        self.assertTrue(ApplicationProgress.objects.filter(position__batch__organization=organization, status="interviewed").exists())
        self.assertTrue(UpdateRun.objects.filter(error_message="local_demo").exists())
        source = organization.official_sources.get()
        self.assertTrue(source.is_active)
        self.assertEqual(source.adapter_name, "local_demo_disabled")
        self.assertTrue(RecruitmentBatch.objects.formal().filter(organization=organization, status="active").exists())
        call_command("load_local_demo", "--remove")
        self.assertFalse(Organization.objects.filter(official_domain="demo.invalid").exists())
