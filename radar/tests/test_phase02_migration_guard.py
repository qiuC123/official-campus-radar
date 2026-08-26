import importlib
import hashlib

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import SimpleTestCase, TransactionTestCase


migration = importlib.import_module(
    "radar.migrations.0011_recruitment_batches_and_position_progress"
)


class _Progress:
    notice_id = 41
    position_id = None
    position = None

    def __init__(self):
        self.saved_fields = None

    def save(self, *, update_fields):
        self.saved_fields = update_fields


class _ProgressManager:
    def __init__(self, progress):
        self.progress = progress

    def select_related(self, _name):
        return [self.progress]


class _PositionQuery:
    def __init__(self, ids):
        self.ids = ids

    def values_list(self, _field, *, flat):
        assert flat
        return self.ids


class _PositionManager:
    def __init__(self, ids):
        self.ids = ids

    def filter(self, **_kwargs):
        return _PositionQuery(self.ids)


class _Apps:
    def __init__(self, ids):
        self.progress = _Progress()
        self.Progress = type("Progress", (), {"objects": _ProgressManager(self.progress)})
        self.Position = type("Position", (), {"objects": _PositionManager(ids)})

    def get_model(self, _app, name):
        return self.Progress if name == "ApplicationProgress" else self.Position


class Phase02MigrationGuardTests(SimpleTestCase):
    def test_single_position_is_mapped_without_guessing(self):
        apps = _Apps([7])
        migration.move_progress_to_position(apps, None)
        self.assertEqual(apps.progress.position_id, 7)
        self.assertEqual(apps.progress.saved_fields, ["position"])

    def test_zero_or_multiple_positions_abort(self):
        for ids in ([], [7, 8]):
            with self.subTest(ids=ids), self.assertRaisesRegex(RuntimeError, "exactly one position"):
                migration.move_progress_to_position(_Apps(ids), None)

    def test_reverse_mapping_restores_batch_from_position(self):
        apps = _Apps([7])
        apps.progress.position = type("Position", (), {"batch_id": 41})()
        migration.move_progress_to_batch(apps, None)
        self.assertEqual(apps.progress.notice_id, 41)
        self.assertEqual(apps.progress.saved_fields, ["notice"])

    def test_reverse_mapping_rejects_two_progress_rows_for_one_batch_before_writing(self):
        apps = _Apps([7])
        first = apps.progress
        second = _Progress()
        first.position = type("Position", (), {"batch_id": 41})()
        second.position = type("Position", (), {"batch_id": 41})()
        apps.Progress.objects = type(
            "Manager", (), {"select_related": lambda self, _name: [first, second]}
        )()
        with self.assertRaisesRegex(RuntimeError, "multiple position progress"):
            migration.move_progress_to_batch(apps, None)
        self.assertIsNone(first.saved_fields)
        self.assertIsNone(second.saved_fields)


class Phase02MigrationDataTests(TransactionTestCase):
    migrate_from = ("radar", "0010_officialsource_api_source_type")
    migrate_to = ("radar", "0011_recruitment_batches_and_position_progress")

    def _migrate(self, target):
        executor = MigrationExecutor(connection)
        executor.migrate([target])
        return executor.loader.project_state([target]).apps

    def setUp(self):
        super().setUp()
        old_apps = self._migrate(self.migrate_from)
        Organization = old_apps.get_model("radar", "Organization")
        Source = old_apps.get_model("radar", "OfficialSource")
        Version = old_apps.get_model("radar", "SourceVersion")
        Notice = old_apps.get_model("radar", "RecruitmentNotice")
        Position = old_apps.get_model("radar", "NoticePosition")
        Event = old_apps.get_model("radar", "PublicationEvent")
        Evidence = old_apps.get_model("radar", "Evidence")

        organization = Organization.objects.create(
            name="Migration Org", company_type="internet", industry="tech"
        )
        self.source_id = Source.objects.create(
            organization=organization,
            source_type="api",
            source_url="https://migration.test/jobs",
            admission_evidence="fixture",
            adapter_name="json_api",
            parser_config={
                "endpoint": "https://migration.test/api/jobs",
                "notice": {
                    "identity_key": "2027-campus",
                    "title": "2027 校园招聘",
                    "official_notice_url": "https://migration.test/campus",
                },
            },
        ).pk
        source = Source.objects.get(pk=self.source_id)
        version = Version.objects.create(
            source=source,
            canonical_url=source.source_url,
            content_hash="a" * 64,
            is_applied=True,
        )
        notice = Notice.objects.create(
            organization=organization,
            source=source,
            identity_key="2027-campus",
            title="2027 校园招聘",
            official_notice_url="https://migration.test/campus",
            recruitment_type="campus_recruitment",
            target_audience="2027届",
            published_on="2026-08-01",
            deadline="2026-12-31",
        )
        self.batch_first_seen_at = notice.first_seen_at
        position = Position.objects.create(
            notice=notice,
            position_key="engineer",
            title="工程师",
            location_text="北京市",
            normalized_locations=["北京"],
            raw_text="工程师 北京市",
        )
        event = Event.objects.create(
            source_version=version,
            notice=notice,
            event_type="published",
            identity_key=notice.identity_key,
            candidate_title=notice.title,
            evidence_complete=True,
        )
        notice.latest_publication_event = event
        notice.save(update_fields=["latest_publication_event"])

        values = {
            "title": notice.title,
            "recruitment_type": notice.recruitment_type,
            "target_audience": notice.target_audience,
            "published_on": "2026-08-01",
            "deadline": "2026-12-31",
            "notice_url": notice.official_notice_url,
        }
        for name, value in values.items():
            Evidence.objects.create(
                notice=notice,
                source_version=version,
                publication_event=event,
                field_name=name,
                excerpt="fixture",
                locator=f"#{name}",
                raw_value=value,
                parsed_value=value,
                value_hash=hashlib.sha256(value.encode("utf-8")).hexdigest(),
            )
        for name, value in (
            ("position_title", position.title),
            ("location", position.location_text),
            ("raw_text", position.raw_text),
        ):
            Evidence.objects.create(
                notice=notice,
                source_version=version,
                publication_event=event,
                position=position,
                field_name=name,
                excerpt="fixture",
                locator=f"#{name}",
                raw_value=value,
                parsed_value=value,
                value_hash=hashlib.sha256(value.encode("utf-8")).hexdigest(),
            )

    def tearDown(self):
        self._migrate(self.migrate_to)
        super().tearDown()

    def test_forward_and_reverse_keep_json_config_and_evidence_usable(self):
        new_apps = self._migrate(self.migrate_to)
        Source = new_apps.get_model("radar", "OfficialSource")
        Evidence = new_apps.get_model("radar", "Evidence")
        config = Source.objects.get(pk=self.source_id).parser_config
        self.assertIn("batch", config)
        self.assertNotIn("notice", config)
        self.assertEqual(
            config["batch"]["official_page_url"], "https://migration.test/campus"
        )
        self.assertTrue(Evidence.objects.filter(field_name="official_page_url").exists())
        migrated_position = new_apps.get_model("radar", "RecruitmentPosition").objects.get()
        self.assertEqual(migrated_position.first_seen_at, self.batch_first_seen_at)
        self.assertEqual(migrated_position.content_changed_at, self.batch_first_seen_at)

        from radar.models import RecruitmentBatch
        from radar.services.evidence import batch_projection_has_valid_evidence

        self.assertTrue(
            batch_projection_has_valid_evidence(RecruitmentBatch.objects.get())
        )

        old_apps = self._migrate(self.migrate_from)
        old_config = old_apps.get_model("radar", "OfficialSource").objects.get(
            pk=self.source_id
        ).parser_config
        self.assertIn("notice", old_config)
        self.assertNotIn("batch", old_config)
        self.assertEqual(
            old_config["notice"]["official_notice_url"],
            "https://migration.test/campus",
        )
        self.assertTrue(
            old_apps.get_model("radar", "Evidence").objects.filter(
                field_name="notice_url"
            ).exists()
        )
