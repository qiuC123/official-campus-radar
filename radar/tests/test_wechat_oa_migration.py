import importlib

from django.test import SimpleTestCase

from radar.models import RecruitmentAnnouncement


migration = importlib.import_module(
    "radar.migrations.0034_rename_wxcli_verification_method"
)


class _Query:
    def __init__(self, manager, filters):
        self.manager = manager
        self.filters = filters

    def update(self, **values):
        self.manager.updates.append((self.filters, values))


class _Manager:
    def __init__(self):
        self.updates = []

    def filter(self, **filters):
        return _Query(self, filters)


class _Apps:
    def __init__(self):
        self.manager = _Manager()
        self.model = type("RecruitmentAnnouncement", (), {"objects": self.manager})

    def get_model(self, app_label, model_name):
        assert (app_label, model_name) == ("radar", "RecruitmentAnnouncement")
        return self.model


class WeChatOAVerificationMigrationTests(SimpleTestCase):
    def test_forward_renames_existing_wxcli_values_without_deleting_rows(self):
        apps = _Apps()
        migration.rename_wxcli_to_wechat_oa(apps, None)
        self.assertEqual(
            apps.manager.updates,
            [
                (
                    {"verification_method": "wxcli"},
                    {"verification_method": "wechat_oa"},
                )
            ],
        )

    def test_reverse_restores_the_previous_persisted_value(self):
        apps = _Apps()
        migration.restore_wxcli_name(apps, None)
        self.assertEqual(
            apps.manager.updates,
            [
                (
                    {"verification_method": "wechat_oa"},
                    {"verification_method": "wxcli"},
                )
            ],
        )

    def test_runtime_model_exposes_only_the_canonical_name(self):
        self.assertEqual(
            RecruitmentAnnouncement.VerificationMethod.WECHAT_OA,
            "wechat_oa",
        )
        self.assertFalse(
            hasattr(RecruitmentAnnouncement.VerificationMethod, "WXCLI")
        )
