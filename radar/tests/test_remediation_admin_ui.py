import csv
import json
import tempfile
from pathlib import Path

from django.contrib import admin
from django.core.management import call_command
from django.test import RequestFactory, TestCase

from radar.models import Evidence, FetchRun, OfficialSource, Organization, SourceVersion


class OrganizationNormalizationTests(TestCase):
    def test_catalog_alias_reuses_actual_recruiting_organization_without_merging_child(self) -> None:
        parent = Organization.objects.create(name="Group", company_type="internet", industry="tech")
        actual = Organization.objects.create(name="Actual Recruiter", aliases=["Recruiter Alias"], company_type="internet", industry="tech", official_domain="official.test", parent=parent)
        file = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", suffix=".csv", delete=False)
        with file:
            fields = ["organization_name", "company_type", "industry", "official_domain", "source_type", "source_url", "admission_evidence", "adapter_name", "parser_config", "is_active"]
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerow({"organization_name": "Recruiter Alias", "company_type": "internet", "industry": "tech", "official_domain": "official.test", "source_type": "website", "source_url": "https://official.test/jobs", "admission_evidence": "candidate", "adapter_name": "html_selector", "parser_config": json.dumps({"notice_selector": "article", "title_selector": "h2"}), "is_active": "false"})
        call_command("import_source_catalog", "--path", file.name)
        self.assertEqual(Organization.objects.count(), 2)
        self.assertEqual(OfficialSource.objects.get().organization_id, actual.pk)


class AuditAdminAndColumnTests(TestCase):
    def test_audit_records_are_immutable_in_admin(self) -> None:
        request = RequestFactory().get("/admin/")
        request.user = type("Superuser", (), {"has_perm": staticmethod(lambda permission: True)})()
        for model in (OfficialSource, SourceVersion, Evidence, FetchRun):
            model_admin = admin.site._registry[model]
            self.assertFalse(model_admin.has_change_permission(request, object()))
            self.assertFalse(model_admin.has_delete_permission(request, object()))

    def test_every_confirmed_column_has_its_own_control(self) -> None:
        response = self.client.get("/")
        columns = (
            "company-type", "industry", "recruitment-type", "target-audience",
            "updated", "deadline", "official-page",
        )
        self.assertEqual(response.content.count(b'type="checkbox" data-column='), 7)
        for column in columns:
            self.assertContains(response, f'<input type="checkbox" data-column="{column}" checked>')

    def test_column_visibility_script_targets_declared_optional_content(self) -> None:
        script = (Path(__file__).resolve().parents[1] / "static" / "radar" / "phase02.js").read_text(encoding="utf-8")
        self.assertIn(
            'document.querySelectorAll(`[data-column-content="${input.dataset.column}"]`)',
            script,
        )
