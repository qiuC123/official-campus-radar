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
            fields = ["organization_name", "company_type", "industry", "official_domain", "source_type", "source_url", "official_entrypoint_url", "admission_evidence", "adapter_name", "parser_config", "is_active"]
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerow({"organization_name": "Recruiter Alias", "company_type": "private", "industry": "tech", "official_domain": "official.test", "source_type": "website", "source_url": "https://official.test/jobs", "official_entrypoint_url": "", "admission_evidence": "candidate", "adapter_name": "html_selector", "parser_config": json.dumps({"notice_selector": "article", "title_selector": "h2"}), "is_active": "false"})
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

    def test_confirmed_table_columns_are_fixed_and_have_no_visibility_controls(self) -> None:
        with self.settings(DEBUG=True):
            response = self.client.get("/preview/phase-02/")
        columns = (
            "公司名称", "公司类型", "所属行业", "招聘类型", "招聘对象", "工作地点",
            "岗位", "投递进度", "更新时间", "相关链接", "招聘公告",
        )
        self.assertNotContains(response, 'data-column=')
        for column in columns:
            self.assertContains(response, f'<th>{column}', count=1)
        self.assertNotContains(response, "投递截止")
        self.assertNotContains(response, 'aria-label="截止时间"')
        self.assertNotContains(response, 'class="positions-detail-row"')

    def test_filter_script_enforces_the_five_province_limit(self) -> None:
        script = (Path(__file__).resolve().parents[1] / "static" / "radar" / "phase02.js").read_text(encoding="utf-8")
        self.assertIn("checked >= max", script)
        self.assertIn("地点最多同时选择 5 个省份", script)
        self.assertNotIn("phase02-column-", script)
