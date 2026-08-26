from importlib import import_module

from django.test import SimpleTestCase


migration = import_module("radar.migrations.0012_progress_per_recruitment_batch")


class _Progress:
    def __init__(self, *, batch_id=None, position_batch_id=None):
        self.batch_id = batch_id
        self.position_id = None
        self.position = (
            type("PositionRef", (), {"batch_id": position_batch_id})()
            if position_batch_id is not None
            else None
        )
        self.saved_fields = []

    def save(self, *, update_fields):
        self.saved_fields.append(list(update_fields))


class _ProgressManager:
    def __init__(self, progresses):
        self.progresses = progresses

    def select_related(self, *args):
        return self.progresses

    def all(self):
        return self.progresses


class _PositionValues:
    def __init__(self, ids):
        self.ids = ids

    def values_list(self, *args, **kwargs):
        return self.ids


class _PositionManager:
    def __init__(self, ids_by_batch):
        self.ids_by_batch = ids_by_batch

    def filter(self, *, batch_id):
        return _PositionValues(self.ids_by_batch.get(batch_id, []))


class _Apps:
    def __init__(self, progresses, ids_by_batch=None):
        self.Progress = type(
            "Progress", (), {"objects": _ProgressManager(progresses)}
        )
        self.Position = type(
            "Position", (), {"objects": _PositionManager(ids_by_batch or {})}
        )

    def get_model(self, app_label, model_name):
        return self.Progress if model_name == "ApplicationProgress" else self.Position


class BatchProgressMigrationTests(SimpleTestCase):
    def test_forward_maps_one_position_progress_to_its_batch(self):
        progress = _Progress(position_batch_id=41)
        migration.move_progress_to_batch(_Apps([progress]), None)
        self.assertEqual(progress.batch_id, 41)
        self.assertEqual(progress.saved_fields, [["batch"]])

    def test_forward_rejects_multiple_position_progress_rows_for_one_batch(self):
        first = _Progress(position_batch_id=41)
        second = _Progress(position_batch_id=41)
        with self.assertRaisesRegex(RuntimeError, "multiple progress rows"):
            migration.move_progress_to_batch(_Apps([first, second]), None)
        self.assertEqual(first.saved_fields, [])
        self.assertEqual(second.saved_fields, [])

    def test_reverse_maps_batch_progress_only_when_one_position_exists(self):
        progress = _Progress(batch_id=41)
        migration.move_progress_to_position(_Apps([progress], {41: [7]}), None)
        self.assertEqual(progress.position_id, 7)
        self.assertEqual(progress.saved_fields, [["position"]])

    def test_reverse_rejects_zero_or_multiple_positions_before_writing(self):
        first = _Progress(batch_id=41)
        second = _Progress(batch_id=42)
        with self.assertRaisesRegex(RuntimeError, "exactly one position"):
            migration.move_progress_to_position(
                _Apps([first, second], {41: [7], 42: [8, 9]}), None
            )
        self.assertEqual(first.saved_fields, [])
        self.assertEqual(second.saved_fields, [])
