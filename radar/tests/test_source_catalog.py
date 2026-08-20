import csv
import json
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from radar.models import OfficialSource, Organization


HEADER = ["organization_name", "company_type", "industry", "official_domain", "source_type", "source_url", "admission_evidence", "adapter_name", "parser_config", "is_active"]


class SourceCatalogCommandTests(TestCase):
    def write_catalog(self, evidence="official evidence") -> str:
        file = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", suffix=".csv", delete=False)
        with file:
            writer = csv.DictWriter(file, fieldnames=HEADER)
            writer.writeheader()
            writer.writerow({"organization_name": "Example Corp", "company_type": "internet", "industry": "tech", "official_domain": "example.test", "source_type": "website", "source_url": "https://careers.example.test", "admission_evidence": evidence, "adapter_name": "html_selector", "parser_config": json.dumps({"notice_selector": "article", "title_selector": "h2"}), "is_active": "true"})
        return file.name

    def test_dry_run_validates_without_writing(self) -> None:
        call_command("import_source_catalog", "--path", self.write_catalog(), "--dry-run")
        self.assertEqual(OfficialSource.objects.count(), 0)
        self.assertEqual(Organization.objects.count(), 0)

    def test_invalid_batch_is_atomic(self) -> None:
        with self.assertRaises(CommandError):
            call_command("import_source_catalog", "--path", self.write_catalog(evidence=""))
        self.assertEqual(OfficialSource.objects.count(), 0)
        self.assertEqual(Organization.objects.count(), 0)
