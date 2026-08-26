from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from radar.models import RecruitmentPosition, Organization, RecruitmentBatch
from radar.services.update_runner import UpdateSummary
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
        self.assertContains(response, '<span data-column-content="recruitment-type">校园招聘</span>')

    def test_progress_endpoint_accepts_only_known_choice(self) -> None:
        response = self.client.post(f"/batches/{self.beijing.pk}/progress/", {"status": "interviewed"})
        self.assertEqual(response.status_code, 200)
        self.beijing.application_progress.refresh_from_db()
        self.assertEqual(self.beijing.application_progress.status, "interviewed")
        self.assertEqual(self.client.post(f"/batches/{self.beijing.pk}/progress/", {"status": "bad"}).status_code, 400)

    def test_default_listing_hides_expired_but_status_filter_shows_it(self) -> None:
        self.assertNotContains(self.client.get("/"), self.expired.official_page_url)
        self.assertContains(self.client.get("/history/"), self.expired.official_page_url)

    @patch("radar.views.run_update")
    def test_manual_update_reports_actual_summary(self, run_update) -> None:
        administrator = get_user_model().objects.create_superuser("owner", "owner@example.test", "test")
        self.client.force_login(administrator)
        run_update.return_value = UpdateSummary(7, 2, 0, 1, 0, 0, status="success")
        response = self.client.post("/update-now/", follow=True)
        self.assertContains(response, 'class="message info"')
        run_update.assert_called_once_with(trigger="manual")

    @patch("radar.views.scheduled_run_is_missing", return_value=True)
    def test_missing_schedule_displays_a_factual_update_banner(self, _missing) -> None:
        administrator = get_user_model().objects.create_superuser("owner", "owner@example.test", "test")
        self.client.force_login(administrator)
        response = self.client.get("/")
        self.assertContains(response, 'class="health warning scheduled-alert"')
        self.assertContains(response, 'action="/update-now/"')

    @patch("radar.views.scheduled_run_is_missing", return_value=True)
    def test_operations_are_hidden_from_non_admin_visitors(self, _missing) -> None:
        response = self.client.get("/")
        self.assertNotContains(response, 'action="/update-now/"')
        self.assertNotContains(response, 'class="health warning scheduled-alert"')
        self.assertEqual(self.client.post("/update-now/").status_code, 302)
