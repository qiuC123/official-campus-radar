import csv
import json
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from radar.collectors.base import FetchedPage
from radar.collectors.html import HtmlSourceAdapter
from radar.models import OfficialSource, Organization, RecruitmentBatch
from radar.services.admission import (approve_application_host,
                                      source_is_admitted, transition_source)
from radar.services.publication import classify_recruitment
from radar.tests.helpers import valid_html_parser_config


class SourceIdentityRemediationTests(TestCase):
    def write_catalog(self) -> str:
        file = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", suffix=".csv", delete=False)
        with file:
            fields = ["organization_name", "company_type", "industry", "official_domain", "source_type", "source_url", "official_entrypoint_url", "admission_evidence", "adapter_name", "parser_config", "is_active"]
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerow({"organization_name": "Candidate", "company_type": "private", "industry": "tech", "official_domain": "official.test", "source_type": "website", "source_url": "https://unrelated.test/jobs", "official_entrypoint_url": "", "admission_evidence": "unreviewed text", "adapter_name": "html_selector", "parser_config": json.dumps({"notice_selector": "article", "title_selector": "h2"}), "is_active": "true"})
        return file.name

    def test_catalog_row_is_always_unverified_and_inactive_candidate(self) -> None:
        call_command("import_source_catalog", "--path", self.write_catalog())
        source = OfficialSource.objects.get()
        self.assertFalse(source.is_verified)
        self.assertFalse(source.is_active)

    def test_verified_website_must_match_organization_official_domain(self) -> None:
        organization = Organization.objects.create(name="Official", company_type="internet", industry="tech", official_domain="official.test")
        source = OfficialSource.objects.create(organization=organization, source_type="website", source_url="https://unrelated.test/jobs", admission_evidence="reviewed", is_verified=True, is_active=True)
        self.assertFalse(source_is_admitted(source))

    def test_verified_ats_requires_official_entrypoint_and_permitted_host(self) -> None:
        organization = Organization.objects.create(name="ATS Org", company_type="internet", industry="tech", official_domain="official.test")
        source = OfficialSource.objects.create(organization=organization, source_type="ats", source_url="https://apply.ats.test/jobs", official_entrypoint_url="https://official.test/careers", admission_evidence="reviewed official entrypoint", parser_config=valid_html_parser_config())
        transition_source(source, to_state="verified", actor_label="owner", reason="verified", evidence="official entrypoint review")
        approve_application_host(source, host="apply.ats.test", actor_label="owner", evidence="official careers page link")
        transition_source(source, to_state="enabled", actor_label="owner", reason="enabled", evidence="fixture passed")
        source.refresh_from_db()
        self.assertTrue(source_is_admitted(source))


class NodeIdentityRemediationTests(TestCase):
    def setUp(self) -> None:
        organization = Organization.objects.create(name="Node Org", company_type="internet", industry="tech", official_domain="official.test")
        self.source = OfficialSource.objects.create(organization=organization, source_type="website", source_url="https://official.test/careers", admission_evidence="reviewed", parser_config=valid_html_parser_config())
        transition_source(self.source, to_state="verified", actor_label="owner", reason="verified", evidence="review")
        transition_source(self.source, to_state="enabled", actor_label="owner", reason="enabled", evidence="fixture")
        self.source.refresh_from_db()

    def test_non_recruitment_node_is_not_extracted_as_campus_notice(self) -> None:
        page = FetchedPage("https://official.test/careers", '<article class="job" data-notice-id="news" data-position-id="news-position"><a class="notice" href="/news">read</a><h2>Company news</h2><span class="type">新闻</span><span class="location">北京</span></article>', "a" * 64, 200, None)
        candidate = HtmlSourceAdapter().extract(self.source, page)[0]
        self.assertEqual(classify_recruitment(candidate.recruitment_type), "unknown")

    def test_nodes_require_distinct_notice_links_and_keep_them_separate(self) -> None:
        page = FetchedPage("https://official.test/careers", '<article class="job" data-notice-id="a" data-position-id="a-position"><a class="notice" href="/2027-a">a</a><h2>A</h2><span class="type">校园招聘</span><span class="location">北京</span></article><article class="job" data-notice-id="b" data-position-id="b-position"><a class="notice" href="/2027-b">b</a><h2>B</h2><span class="type">校园招聘</span><span class="location">上海</span></article>', "b" * 64, 200, None)
        candidates = HtmlSourceAdapter().extract(self.source, page)
        self.assertEqual([candidate.official_page_url for candidate in candidates], ["https://official.test/2027-a", "https://official.test/2027-b"])
        self.assertEqual(len(set(candidate.official_page_url for candidate in candidates)), 2)

    def test_notice_model_belongs_to_a_specific_source(self) -> None:
        batch = RecruitmentBatch.objects.create(organization=self.source.organization, source=self.source, identity_key="2027-a", title="2027", official_page_url="https://official.test/2027-a")
        self.assertEqual(batch.source_id, self.source.pk)

    def test_explicit_withdrawal_selector_marks_candidate_withdrawn(self) -> None:
        self.source.parser_config["withdrawn_selector"] = ".withdrawn"
        self.source.save(update_fields=["parser_config"])
        page = FetchedPage("https://official.test/careers", '<article class="job" data-notice-id="a" data-position-id="a-position"><a class="notice" href="/2027-a">a</a><h2>A</h2><span class="type">校园招聘</span><span class="location">北京</span><span class="withdrawn">已撤回</span></article>', "d" * 64, 200, None)
        self.assertTrue(HtmlSourceAdapter().extract(self.source, page)[0].withdrawn)
