from dataclasses import replace
from unittest.mock import patch

from django.test import TestCase

from radar.collectors.base import FetchedPage
from radar.collectors.registry import AdapterRegistry
from radar.models import Evidence, FetchRun, OfficialSource, PublicationEvent, RecruitmentBatch
from radar.services.announcement_discovery import RenderedOfficialPage
from radar.services.availability import (
    AvailabilityObservation,
    AvailabilityProbeError,
    apply_partition_availability,
    closed_availability_candidate,
    closed_availability_page,
    probe_partition_availability,
    probe_source_availability,
)
from radar.services.update_runner import run_update
from radar.tests.helpers import complete_candidate, create_enabled_source, publish_formal_notice


PROBE_CONFIG = {
    "mode": "browser_text",
    "url": "https://official.test/careers",
    "timeout_seconds": 20,
    "ready_text_any": ["在招岗位", "投递已结束"],
    "closed_text_any": ["投递已结束"],
    "open_text_any": [],
    "position_count_pattern": r"在招岗位\s*[（(]\s*(\d+)\s*[）)]",
}
PARTITION_IDENTITY = "official-project:example:internship"
PARTITION_PROBE_CONFIG = {
    **PROBE_CONFIG,
    "identity_key": PARTITION_IDENTITY,
}


class NeverFetchAdapter:
    def fetch(self, source):
        raise AssertionError("job inventory must not be fetched after a closed signal")


class OpenInventoryAdapter:
    def __init__(self, candidate):
        self.candidate = candidate
        self.fetch_calls = 0

    def fetch(self, source):
        self.fetch_calls += 1
        return FetchedPage(source.source_url, "open", "b" * 64, 200, None)

    def extract(self, source, page):
        return [self.candidate]


class PartitionInventoryAdapter:
    def __init__(self, candidates):
        self.candidates = candidates

    def fetch(self, source):
        return FetchedPage(source.source_url, "inventory", "b" * 64, 200, None)

    def extract(self, source, page):
        return self.candidates


def _enable_probe(source: OfficialSource, *, config: dict | None = None) -> None:
    parser_config = dict(source.parser_config)
    parser_config["availability_probe"] = config or PROBE_CONFIG
    parser_config["batch"] = {
        "identity_key": "batch-2027",
        "title": "2027 Campus",
        "official_page_url": source.source_url.rstrip("/") + "/batches/batch-2027",
        "recruitment_type": "autumn_recruitment",
        "target_audience": "2027届",
    }
    source.parser_config = parser_config
    source.save(update_fields=["parser_config"])


def _enable_partition_probe(source: OfficialSource) -> None:
    parser_config = dict(source.parser_config)
    parser_config["batch_partitions"] = [
        {
            "batch": {
                "identity_key": PARTITION_IDENTITY,
                "title": "2027 Campus",
                "official_page_url": (
                    source.source_url.rstrip("/")
                    + f"/batches/{PARTITION_IDENTITY}"
                ),
                "recruitment_type": "internship",
                "target_audience": "在校生",
            },
            "row_filters": [{"path": "projectId", "equals_any": [9]}],
        }
    ]
    parser_config["partition_availability_probes"] = [PARTITION_PROBE_CONFIG]
    source.parser_config = parser_config
    source.save(update_fields=["parser_config"])


class AvailabilityProbeTests(TestCase):
    def setUp(self) -> None:
        self.source = create_enabled_source()
        _enable_probe(self.source)

    def render(self, body_text: str, *, url: str = "https://official.test/careers"):
        return lambda *args, **kwargs: RenderedOfficialPage(
            url=url,
            title="Official careers",
            body_text=body_text,
            html=f"<body>{body_text}</body>",
        )

    def test_closed_text_and_zero_count_are_closed(self) -> None:
        observation = probe_source_availability(
            self.source,
            renderer=self.render("现阶段投递已结束\n在招岗位（0）"),
        )

        self.assertEqual(observation.state, "closed")
        self.assertIn("closed_text=投递已结束", observation.evidence_excerpt)
        self.assertIn("position_counts=0", observation.evidence_excerpt)
        self.assertEqual(len(observation.content_hash), 64)

    def test_positive_position_count_is_open(self) -> None:
        observation = probe_source_availability(
            self.source,
            renderer=self.render("在招岗位（12）"),
        )

        self.assertEqual(observation.state, "open")
        self.assertIn("position_counts=12", observation.evidence_excerpt)

    def test_conflicting_or_unknown_signals_fail_closed(self) -> None:
        with self.assertRaisesRegex(AvailabilityProbeError, "conflicting"):
            probe_source_availability(
                self.source,
                renderer=self.render("投递已结束\n在招岗位（12）"),
            )
        with self.assertRaisesRegex(AvailabilityProbeError, "no decisive signal"):
            probe_source_availability(
                self.source,
                renderer=self.render("招聘页面正在加载"),
            )

    def test_cross_host_redirect_is_rejected(self) -> None:
        with self.assertRaisesRegex(AvailabilityProbeError, "redirected"):
            probe_source_availability(
                self.source,
                renderer=self.render(
                    "在招岗位（12）",
                    url="https://untrusted.test/careers",
                ),
            )

    def test_registry_rejects_unsafe_or_ambiguous_probe_config(self) -> None:
        unsafe = dict(PROBE_CONFIG, url="https://untrusted.test/careers")
        _enable_probe(self.source, config=unsafe)
        with self.assertRaisesRegex(ValueError, "exact source host"):
            AdapterRegistry.validate_source_config(self.source)

        invalid_regex = dict(PROBE_CONFIG, position_count_pattern=r"在招岗位\s*\d+")
        _enable_probe(self.source, config=invalid_regex)
        with self.assertRaisesRegex(ValueError, "one capture group"):
            AdapterRegistry.validate_source_config(self.source)

        source_config = dict(self.source.parser_config)
        source_config["availability_probe"] = dict(PROBE_CONFIG)
        source_config["batch_partitions"] = [{"identity_key": "a"}]
        self.source.parser_config = source_config
        with self.assertRaisesRegex(ValueError, "batch_partitions"):
            AdapterRegistry.validate_source_config(self.source)

    def test_partition_probe_requires_unique_configured_partition_identity(self) -> None:
        source_config = dict(self.source.parser_config)
        source_config.pop("availability_probe")
        source_config["batch_partitions"] = [
            {
                "batch": {"identity_key": PARTITION_IDENTITY},
                "row_filters": [],
            }
        ]
        source_config["partition_availability_probes"] = [
            PARTITION_PROBE_CONFIG,
            PARTITION_PROBE_CONFIG,
        ]
        self.source.parser_config = source_config

        with self.assertRaisesRegex(ValueError, "must be unique"):
            AdapterRegistry.validate_source_config(self.source)

        source_config["partition_availability_probes"] = [
            dict(PARTITION_PROBE_CONFIG, identity_key="unknown")
        ]
        self.source.parser_config = source_config
        with self.assertRaisesRegex(ValueError, "configured batch partition"):
            AdapterRegistry.validate_source_config(self.source)

    def test_partition_probe_returns_observation_by_identity(self) -> None:
        parser_config = dict(self.source.parser_config)
        parser_config.pop("availability_probe")
        self.source.parser_config = parser_config
        _enable_partition_probe(self.source)

        observations = probe_partition_availability(
            self.source,
            renderer=self.render("投递已结束\n在招岗位（0）"),
        )

        self.assertEqual(set(observations), {PARTITION_IDENTITY})
        self.assertEqual(observations[PARTITION_IDENTITY].state, "closed")

    def test_closed_observation_builds_minimal_auditable_payload(self) -> None:
        observation = AvailabilityObservation(
            state="closed",
            url="https://official.test/careers",
            content_hash="a" * 64,
            evidence_excerpt="state=closed; position_counts=0",
        )

        page = closed_availability_page(observation)
        candidate = closed_availability_candidate(self.source, observation)

        self.assertNotIn("full page", page.body)
        self.assertTrue(candidate.withdrawn)
        self.assertEqual(candidate.positions, ())
        self.assertEqual(
            candidate.field_evidence["availability"].parsed_value,
            RecruitmentBatch.Status.WITHDRAWN,
        )


class AvailabilityGateUpdateTests(TestCase):
    def setUp(self) -> None:
        self.source = create_enabled_source()
        self.batch = publish_formal_notice(self.source)
        _enable_probe(self.source)

    def test_closed_gate_withdraws_batch_without_fetching_stale_inventory(self) -> None:
        observation = AvailabilityObservation(
            state="closed",
            url="https://official.test/careers",
            content_hash="c" * 64,
            evidence_excerpt="state=closed; position_counts=0",
        )

        with (
            patch(
                "radar.services.update_runner.probe_source_availability",
                return_value=observation,
            ),
            patch(
                "radar.services.update_runner.AdapterRegistry.get",
                return_value=NeverFetchAdapter(),
            ),
        ):
            summary = run_update(trigger="manual", source_ids=[self.source.pk])

        self.batch.refresh_from_db()
        self.source.refresh_from_db()
        event = PublicationEvent.objects.get(
            batch=self.batch,
            event_type=PublicationEvent.EventType.WITHDRAWN,
        )
        self.assertEqual(summary.sources_failed, 0)
        self.assertEqual(self.batch.status, RecruitmentBatch.Status.WITHDRAWN)
        self.assertFalse(self.batch.positions.get().is_current)
        self.assertEqual(
            event.reason_codes,
            ["explicit_source_withdrawal", "availability_probe_closed"],
        )
        self.assertTrue(event.evidence_complete)
        self.assertTrue(
            Evidence.objects.filter(
                batch=self.batch,
                publication_event=event,
                field_name="availability",
                locator="browser:body-text",
            ).exists()
        )
        self.assertEqual(self.source.last_error, "")

    def test_probe_failure_records_failure_and_hides_previous_formal_batch(self) -> None:
        self.assertTrue(
            RecruitmentBatch.objects.formal().filter(pk=self.batch.pk).exists()
        )

        with (
            patch(
                "radar.services.update_runner.probe_source_availability",
                side_effect=AvailabilityProbeError("no decisive signal"),
            ),
            patch(
                "radar.services.update_runner.AdapterRegistry.get",
                return_value=NeverFetchAdapter(),
            ),
        ):
            summary = run_update(trigger="manual", source_ids=[self.source.pk])

        self.source.refresh_from_db()
        self.batch.refresh_from_db()
        self.assertEqual(summary.sources_failed, 1)
        self.assertEqual(self.batch.status, RecruitmentBatch.Status.ACTIVE)
        self.assertIn("no decisive signal", self.source.last_error)
        self.assertTrue(
            FetchRun.objects.filter(
                source=self.source,
                status=FetchRun.Status.FAILED,
            ).exists()
        )
        self.assertFalse(
            RecruitmentBatch.objects.formal().filter(pk=self.batch.pk).exists()
        )

    def test_open_gate_continues_to_normal_inventory_collection(self) -> None:
        candidate = complete_candidate(self.source, location="上海")
        adapter = OpenInventoryAdapter(candidate)
        observation = AvailabilityObservation(
            state="open",
            url="https://official.test/careers",
            content_hash="d" * 64,
            evidence_excerpt="state=open; position_counts=12",
        )

        with (
            patch(
                "radar.services.update_runner.probe_source_availability",
                return_value=observation,
            ),
            patch(
                "radar.services.update_runner.AdapterRegistry.get",
                return_value=adapter,
            ),
        ):
            summary = run_update(trigger="manual", source_ids=[self.source.pk])

        self.source.refresh_from_db()
        self.batch.refresh_from_db()
        self.assertEqual(summary.sources_failed, 0)
        self.assertEqual(adapter.fetch_calls, 1)
        self.assertEqual(self.batch.status, RecruitmentBatch.Status.ACTIVE)
        self.assertEqual(self.batch.positions.get().location_text, "上海")
        self.assertEqual(self.source.last_error, "")


class PartitionAvailabilityGateUpdateTests(TestCase):
    def setUp(self) -> None:
        self.source = create_enabled_source()
        self.closed_batch = publish_formal_notice(
            self.source,
            identity_key=PARTITION_IDENTITY,
            title="2027 Campus",
            hash_character="a",
        )
        self.open_batch = publish_formal_notice(
            self.source,
            identity_key="official-project:example:campus",
            title="2027 Campus",
            hash_character="c",
        )
        _enable_partition_probe(self.source)

    def test_closed_partition_withdraws_only_matching_batch(self) -> None:
        closed_candidate = replace(
            complete_candidate(
                self.source,
                identity_key=PARTITION_IDENTITY,
                title="2027 Campus",
            ),
            positions=(),
        )
        open_candidate = complete_candidate(
            self.source,
            identity_key="official-project:example:campus",
            title="2027 Campus",
        )
        observation = AvailabilityObservation(
            state="closed",
            url=self.source.source_url,
            content_hash="d" * 64,
            evidence_excerpt="state=closed; closed_text=投递已结束",
        )

        with (
            patch(
                "radar.services.update_runner.probe_partition_availability",
                return_value={PARTITION_IDENTITY: observation},
            ),
            patch(
                "radar.services.update_runner.AdapterRegistry.get",
                return_value=PartitionInventoryAdapter(
                    [closed_candidate, open_candidate]
                ),
            ),
        ):
            summary = run_update(trigger="manual", source_ids=[self.source.pk])

        self.closed_batch.refresh_from_db()
        self.open_batch.refresh_from_db()
        self.source.refresh_from_db()
        self.assertEqual(summary.sources_failed, 0)
        self.assertEqual(
            self.closed_batch.status,
            RecruitmentBatch.Status.WITHDRAWN,
        )
        self.assertEqual(self.open_batch.status, RecruitmentBatch.Status.ACTIVE)
        self.assertFalse(self.closed_batch.positions.get().is_current)
        event = PublicationEvent.objects.get(
            batch=self.closed_batch,
            event_type=PublicationEvent.EventType.WITHDRAWN,
        )
        self.assertEqual(
            event.reason_codes,
            ["explicit_source_withdrawal", "availability_probe_closed"],
        )
        self.assertEqual(self.source.last_error, "")

    def test_partition_probe_failure_hides_previous_formal_batches(self) -> None:
        with (
            patch(
                "radar.services.update_runner.probe_partition_availability",
                side_effect=AvailabilityProbeError("no decisive signal"),
            ),
            patch(
                "radar.services.update_runner.AdapterRegistry.get",
                return_value=PartitionInventoryAdapter([]),
            ),
        ):
            summary = run_update(trigger="manual", source_ids=[self.source.pk])

        self.source.refresh_from_db()
        self.assertEqual(summary.sources_failed, 1)
        self.assertIn("no decisive signal", self.source.last_error)
        self.assertFalse(
            RecruitmentBatch.objects.formal()
            .filter(source=self.source)
            .exists()
        )

    def test_open_signal_does_not_turn_an_empty_inventory_into_withdrawal(self) -> None:
        empty_candidate = replace(
            complete_candidate(
                self.source,
                identity_key=PARTITION_IDENTITY,
                title="2027 Campus",
            ),
            positions=(),
        )
        observation = AvailabilityObservation(
            state="open",
            url=self.source.source_url,
            content_hash="e" * 64,
            evidence_excerpt="state=open",
        )

        page, candidates = apply_partition_availability(
            self.source,
            FetchedPage(self.source.source_url, "inventory", "f" * 64, 200, None),
            [empty_candidate],
            {PARTITION_IDENTITY: observation},
        )

        self.assertNotEqual(page.content_hash, "f" * 64)
        self.assertFalse(candidates[0].withdrawn)
        self.assertEqual(candidates[0].positions, ())
