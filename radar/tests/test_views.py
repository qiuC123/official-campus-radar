from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from radar.models import (
    ApplicationProgress,
    RecruitmentPosition,
    Organization,
    RecruitmentBatch,
    RecruitmentPolicy,
)
from radar.tests.helpers import create_enabled_source, publish_formal_notice


class DashboardViewTests(TestCase):
    def setUp(self) -> None:
        source = create_enabled_source(name="北京公司", host="example.test")
        self.beijing = publish_formal_notice(source, identity_key="beijing", title="北京校招", location="北京", hash_character="a")
        self.hangzhou = publish_formal_notice(source, identity_key="shanghai", title="上海校招", location="上海", hash_character="b")
        self.expired = publish_formal_notice(source, identity_key="expired", title="已截止校招", location="深圳", status="expired", hash_character="c")

    def test_city_filter_only_shows_matching_notice(self) -> None:
        response = self.client.get("/?city=北京")
        self.assertContains(response, self.beijing.official_page_url)
        self.assertNotContains(response, self.hangzhou.official_page_url)

    def test_dashboard_displays_human_readable_recruitment_type(self) -> None:
        response = self.client.get("/")
        self.assertContains(response, "校园招聘")
        self.assertContains(response, f'value="{self.beijing.recruitment_type}"')
        self.assertContains(response, '<span class="badge recruit-badge">校园招聘</span>', html=True)

    def test_progress_endpoint_accepts_only_known_choice(self) -> None:
        response = self.client.post(f"/batches/{self.beijing.pk}/progress/", {"status": "interviewed"})
        self.assertEqual(response.status_code, 200)
        self.beijing.application_progress.refresh_from_db()
        self.assertEqual(self.beijing.application_progress.status, "interviewed")
        self.assertEqual(self.client.post(f"/batches/{self.beijing.pk}/progress/", {"status": "bad"}).status_code, 400)

    def test_existing_progress_remains_editable_after_batch_is_hidden(self) -> None:
        progress, _ = ApplicationProgress.objects.update_or_create(
            batch=self.beijing,
            defaults={"status": ApplicationProgress.Status.APPLIED},
        )
        policy, _ = RecruitmentPolicy.objects.get_or_create(key="default")
        policy.announcement_gate_enforced = True
        policy.save(update_fields=["announcement_gate_enforced"])
        self.beijing.announcement_admission = (
            RecruitmentBatch.AnnouncementAdmission.SUPERSEDED
        )
        self.beijing.save(update_fields=["announcement_admission"])

        response = self.client.get("/applications/")
        self.assertContains(response, self.beijing.title)
        self.assertContains(response, "已被精确批次取代")
        update = self.client.post(
            f"/batches/{self.beijing.pk}/progress/",
            {"status": ApplicationProgress.Status.INTERVIEWED},
        )
        self.assertEqual(update.status_code, 200)
        progress.refresh_from_db()
        self.assertEqual(progress.status, ApplicationProgress.Status.INTERVIEWED)

    def test_default_listing_hides_expired_but_status_filter_shows_it(self) -> None:
        self.assertNotContains(self.client.get("/"), self.expired.official_page_url)
        self.assertContains(self.client.get("/history/"), self.expired.official_page_url)

    def test_immediate_update_endpoint_remains_deferred(self) -> None:
        administrator = get_user_model().objects.create_superuser("owner", "owner@example.test", "test")
        self.client.force_login(administrator)
        self.assertEqual(self.client.post("/update-now/").status_code, 404)

    @patch("radar.views.scheduled_run_is_missing", return_value=True)
    def test_missing_schedule_displays_a_factual_update_banner(self, _missing) -> None:
        administrator = get_user_model().objects.create_superuser("owner", "owner@example.test", "test")
        self.client.force_login(administrator)
        response = self.client.get("/")
        self.assertContains(response, 'class="health-panel" data-health="missing"')
        self.assertNotContains(response, 'action="/update-now/"')

    @patch("radar.views.scheduled_run_is_missing", return_value=True)
    def test_operations_are_hidden_from_non_admin_visitors(self, _missing) -> None:
        response = self.client.get("/")
        self.assertNotContains(response, 'action="/update-now/"')
        self.assertNotContains(response, 'class="health warning scheduled-alert"')
        self.assertEqual(self.client.post("/update-now/").status_code, 404)
