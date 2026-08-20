from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from radar.models import FetchRun, OfficialSource, Organization, UpdateRun
from radar.services.admission import transition_source
from radar.services.update_runner import run_update
from radar.tests.helpers import create_enabled_source


class DemoOwnershipTests(TestCase):
    def test_load_update_cleanup_uses_exact_demo_ownership_and_preserves_sentinels(self) -> None:
        same_domain_sentinel = Organization.objects.create(
            name="Same Domain Sentinel",
            company_type="other",
            industry="test",
            official_domain="demo.invalid",
        )
        run_sentinel = UpdateRun.objects.create(
            trigger=UpdateRun.Trigger.MANUAL,
            status=UpdateRun.Status.SUCCESS,
            error_message="keep-me",
        )

        call_command("load_local_demo")
        demo_source = OfficialSource.objects.get(adapter_name="local_demo_disabled")
        response = self.client.post("/update-now/", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            FetchRun.objects.filter(source=demo_source, status="not_modified").exists()
        )
        demo_update_ids = set(
            FetchRun.objects.filter(source=demo_source).values_list(
                "update_run_id", flat=True
            )
        )
        self.assertTrue(demo_update_ids)

        call_command("load_local_demo", "--remove")

        self.assertTrue(Organization.objects.filter(pk=same_domain_sentinel.pk).exists())
        self.assertTrue(UpdateRun.objects.filter(pk=run_sentinel.pk).exists())
        self.assertFalse(FetchRun.objects.filter(source_id=demo_source.pk).exists())
        self.assertFalse(UpdateRun.objects.filter(pk__in=demo_update_ids).exists())
        self.assertFalse(OfficialSource.objects.filter(adapter_name="local_demo_disabled").exists())


class OfflineUpdateBoundaryTests(TestCase):
    def test_suspended_source_never_resolves_or_calls_an_adapter(self) -> None:
        source = create_enabled_source(name="Suspended Offline Source")
        transition_source(
            source,
            to_state=OfficialSource.AdmissionState.SUSPENDED,
            actor_label="owner",
            reason="offline test suspension",
            evidence="saved test decision",
        )

        with patch("radar.services.update_runner.AdapterRegistry.get") as get_adapter:
            summary = run_update(trigger="manual", source_ids=[source.pk])

        get_adapter.assert_not_called()
        self.assertEqual(summary.sources_checked, 0)

    def test_test_configuration_blocks_unmocked_requests(self) -> None:
        from radar.tests.network_guard import assert_outbound_http_is_blocked

        with self.assertRaisesRegex(RuntimeError, "outbound HTTP is blocked"):
            assert_outbound_http_is_blocked()
