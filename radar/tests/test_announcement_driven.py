import json
import subprocess
import tempfile
from dataclasses import replace
from datetime import datetime, timezone as datetime_timezone
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.management import call_command, get_commands
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from radar.models import (
    AnnouncementDiscoveryCandidate,
    ApplicationLink,
    OfficialSource,
    Organization,
    RecruitmentAnnouncement,
    RecruitmentBatch,
    RecruitmentPolicy,
    RecruitmentPolicyEvent,
    RecruitmentPosition,
    WeChatAccountIdentity,
)
from radar.services.admission import transition_source
from radar.services.announcement_discovery import (
    DiscoveryContractError,
    discover_official_candidates_bulk_with_codex,
    fetch_official_candidate_for_verification,
    OfficialSiteCandidate,
    RefetchedOfficialCandidate,
    RenderedOfficialPage,
    known_source_candidate_batch,
    parse_official_candidate_batch,
    parse_bulk_official_candidate_batch,
    probe_official_candidates,
    refetch_official_candidate,
    render_official_candidate,
    snapshot_official_candidate,
    store_official_candidates,
)
from radar.services.announcements import (
    admit_official_domain_announcement_source,
    admit_batch_with_announcement,
    create_announcement_only_batch,
    import_wechat_oa_announcement,
    migration_preview_digest,
    migration_preview_payload,
    mark_batch_pending_with_announcement,
    observed_application_channel_candidates,
    record_migration_preview,
    split_verified_announcement_project,
    activate_announcement_gate,
    build_batch_signature,
    compare_batch_signatures,
    verify_official_announcement,
)
from radar.services.dashboard_data import canonical_audience
from radar.services.exa_discovery import ExaDiscoveryError
from radar.services.update_runner import run_update
from radar.services.wechat_oa_client import (
    WeChatOAClient,
    WeChatOAError,
    build_wechat_candidate_batch,
    validate_wechat_candidate_batch,
)
from radar.tests.helpers import create_enabled_source, publish_formal_notice


def announcement_evidence(batch, *, recruitment_type=None, target_audience=None):
    return {
        "title": (batch.title, batch.title, "article/title"),
        "recruitment_type": (
            recruitment_type or batch.recruitment_type,
            "明确写明招聘项目类型",
            "article/body/project-type",
        ),
        "target_audience": (
            target_audience or batch.target_audience,
            "明确写明招聘对象",
            "article/body/audience",
        ),
        "availability": (
            RecruitmentBatch.Status.ACTIVE,
            "报名入口当前开放",
            "application-entry/status",
        ),
    }


class AnnouncementGateTests(TestCase):
    def setUp(self):
        self.source = create_enabled_source(name="公告门控公司", host="announcement.test")
        self.batch = publish_formal_notice(self.source, identity_key="autumn-2027")
        self.policy, _ = RecruitmentPolicy.objects.get_or_create(key="default")

    def verified_announcement(self, *, kind="website", title="官网公告"):
        account_fields = {}
        if kind in {
            RecruitmentAnnouncement.SourceKind.WECHAT_ARTICLE,
            RecruitmentAnnouncement.SourceKind.WECHAT_MINIPROGRAM,
        }:
            WeChatAccountIdentity.objects.get_or_create(
                organization=self.source.organization,
                display_name="公告门控招聘",
                defaults={
                    "biz_id": "announcement-gate-biz",
                    "identity_evidence": "企业官网公示该公众号",
                    "is_verified": True,
                    "verified_at": timezone.now(),
                },
            )
            account_fields = {
                "account_display_name": "公告门控招聘",
                "account_biz_id": "announcement-gate-biz",
            }
        return RecruitmentAnnouncement.objects.create(
            organization=self.source.organization,
            source=self.source,
            identity_key=f"notice-{kind}-{title}",
            source_kind=kind,
            title=title,
            url=(
                f"https://mp.weixin.qq.com/s/test-{len(title)}"
                if kind == RecruitmentAnnouncement.SourceKind.WECHAT_ARTICLE
                else f"https://announcement.test/notices/{kind}/{len(title)}"
            ),
            identity_evidence="企业官网域名与已准入主体一致",
            content_sha256="a" * 64,
            last_verified_at=timezone.now(),
            verification_status=RecruitmentAnnouncement.VerificationStatus.VERIFIED,
            verification_method=(
                RecruitmentAnnouncement.VerificationMethod.WECHAT_OA
                if kind in {
                    RecruitmentAnnouncement.SourceKind.WECHAT_ARTICLE,
                    RecruitmentAnnouncement.SourceKind.WECHAT_MINIPROGRAM,
                }
                else RecruitmentAnnouncement.VerificationMethod.HTTP
            ),
            **account_fields,
        )

    def test_gate_is_compatible_until_preview_is_confirmed(self):
        self.assertTrue(RecruitmentBatch.objects.formal().filter(pk=self.batch.pk).exists())
        self.policy.announcement_gate_enforced = True
        self.policy.save(update_fields=["announcement_gate_enforced"])
        self.assertFalse(RecruitmentBatch.objects.formal().filter(pk=self.batch.pk).exists())

    def test_verified_announcement_can_mark_unresolved_batch_pending(self):
        announcement = self.verified_announcement()
        mark_batch_pending_with_announcement(self.batch, announcement)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.primary_announcement, announcement)
        self.assertEqual(
            self.batch.announcement_admission,
            RecruitmentBatch.AnnouncementAdmission.PENDING,
        )
        self.assertEqual(
            next(
                item
                for item in migration_preview_payload()["batches"]
                if item["batch_id"] == self.batch.pk
            )["outcome"],
            "pending",
        )

    def test_pending_link_cannot_replace_an_existing_primary_announcement(self):
        first = self.verified_announcement(title="第一篇")
        second = self.verified_announcement(title="第二篇")
        mark_batch_pending_with_announcement(self.batch, first)
        with self.assertRaises(ValidationError):
            mark_batch_pending_with_announcement(self.batch, second)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.primary_announcement, first)

    def test_verified_primary_announcement_admits_batch(self):
        announcement = self.verified_announcement()
        admit_batch_with_announcement(
            self.batch,
            announcement,
            field_evidence=announcement_evidence(
                self.batch,
                recruitment_type=RecruitmentBatch.RecruitmentType.AUTUMN,
                target_audience="2027届",
            ),
        )
        self.policy.announcement_gate_enforced = True
        self.policy.save(update_fields=["announcement_gate_enforced"])
        self.assertTrue(RecruitmentBatch.objects.formal().filter(pk=self.batch.pk).exists())
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.recruitment_type, RecruitmentBatch.RecruitmentType.AUTUMN)
        self.assertEqual(self.batch.target_audience, "2027届")

    def test_preview_uses_post_cutover_field_ownership_before_gate_is_enabled(self):
        announcement = self.verified_announcement()
        admit_batch_with_announcement(
            self.batch,
            announcement,
            field_evidence=announcement_evidence(
                self.batch,
                recruitment_type=RecruitmentBatch.RecruitmentType.AUTUMN,
                target_audience="2027届",
            ),
        )
        payload = migration_preview_payload()
        row = next(item for item in payload["batches"] if item["batch_id"] == self.batch.pk)
        self.assertEqual(row["outcome"], "keep")

    def test_exact_announcement_audience_is_preserved_but_filter_uses_cohort_tags(self):
        announcement = self.verified_announcement()
        exact_audience = "2027届（部分项目同时接受2026届）"
        admit_batch_with_announcement(
            self.batch,
            announcement,
            field_evidence=announcement_evidence(
                self.batch,
                target_audience=exact_audience,
            ),
        )
        self.policy.announcement_gate_enforced = True
        self.policy.save(update_fields=["announcement_gate_enforced"])
        response = self.client.get("/")
        self.assertContains(response, '<option value="2026届"')
        self.assertContains(response, '<option value="2027届"')
        self.assertNotContains(response, f'<option value="{exact_audience}"')
        self.assertContains(response, f"官方招聘对象：{exact_audience}")
        self.assertContains(self.client.get("/?audience=2026届"), self.batch.title)
        self.assertContains(self.client.get("/?audience=2027届"), self.batch.title)

    def test_wechat_replaces_website_but_website_cannot_replace_wechat(self):
        website = self.verified_announcement(kind="website", title="官网公告")
        admit_batch_with_announcement(
            self.batch,
            website,
            field_evidence=announcement_evidence(self.batch),
        )
        wechat = self.verified_announcement(kind="wechat_article", title="微信公告")
        wechat_evidence = announcement_evidence(self.batch)
        wechat_evidence["title"] = (
            "微信公告中的批次名称",
            "微信原文标题明确写出批次名称",
            "article/title",
        )
        admit_batch_with_announcement(
            self.batch,
            wechat,
            field_evidence=wechat_evidence,
        )
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.primary_announcement_id, wechat.pk)
        self.assertEqual(self.batch.title, "微信公告中的批次名称")
        with self.assertRaises(ValidationError):
            admit_batch_with_announcement(
                self.batch,
                website,
                field_evidence=announcement_evidence(self.batch),
            )

    def test_conflicting_wechat_fields_require_explicit_confirmation(self):
        website = self.verified_announcement(kind="website", title="官网公告")
        admit_batch_with_announcement(
            self.batch,
            website,
            field_evidence=announcement_evidence(
                self.batch,
                recruitment_type=RecruitmentBatch.RecruitmentType.AUTUMN,
                target_audience="2027届",
            ),
        )
        wechat = self.verified_announcement(kind="wechat_article", title="微信公告")
        conflicting_evidence = announcement_evidence(
            self.batch,
            recruitment_type=RecruitmentBatch.RecruitmentType.INTERNSHIP,
            target_audience="在校生",
        )

        admit_batch_with_announcement(
            self.batch,
            wechat,
            field_evidence=conflicting_evidence,
        )
        self.batch.refresh_from_db()
        self.assertEqual(
            self.batch.announcement_admission,
            RecruitmentBatch.AnnouncementAdmission.PENDING,
        )
        self.assertEqual(self.batch.primary_announcement_id, website.pk)
        self.assertEqual(self.batch.target_audience, "2027届")

        admit_batch_with_announcement(
            self.batch,
            wechat,
            field_evidence=conflicting_evidence,
            confirm_field_conflicts=True,
        )
        self.batch.refresh_from_db()
        self.assertEqual(
            self.batch.announcement_admission,
            RecruitmentBatch.AnnouncementAdmission.ADMITTED,
        )
        self.assertEqual(self.batch.primary_announcement_id, wechat.pk)
        self.assertEqual(self.batch.recruitment_type, RecruitmentBatch.RecruitmentType.INTERNSHIP)
        self.assertEqual(self.batch.target_audience, "在校生")

    def test_admit_command_reports_pending_until_conflicts_are_confirmed(self):
        website = self.verified_announcement(kind="website", title="官网公告")
        admit_batch_with_announcement(
            self.batch,
            website,
            field_evidence=announcement_evidence(
                self.batch,
                recruitment_type=RecruitmentBatch.RecruitmentType.AUTUMN,
                target_audience="2027届",
            ),
        )
        wechat = self.verified_announcement(kind="wechat_article", title="微信公告")
        evidence = announcement_evidence(
            self.batch,
            recruitment_type=RecruitmentBatch.RecruitmentType.INTERNSHIP,
            target_audience="在校生",
        )
        payload = {
            field_name: {
                "parsed_value": values[0],
                "excerpt": values[1],
                "locator": values[2],
            }
            for field_name, values in evidence.items()
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", encoding="utf-8", delete=False
        ) as handle:
            json.dump(payload, handle, ensure_ascii=False)
            path = handle.name
        try:
            pending_output = StringIO()
            call_command(
                "admit_recruitment_batch",
                batch_id=self.batch.pk,
                announcement_id=wechat.pk,
                evidence=path,
                stdout=pending_output,
            )
            self.assertEqual(
                json.loads(pending_output.getvalue())["announcement_admission"],
                RecruitmentBatch.AnnouncementAdmission.PENDING,
            )

            admitted_output = StringIO()
            call_command(
                "admit_recruitment_batch",
                batch_id=self.batch.pk,
                announcement_id=wechat.pk,
                evidence=path,
                confirm_field_conflicts=True,
                stdout=admitted_output,
            )
            self.assertEqual(
                json.loads(admitted_output.getvalue())["announcement_admission"],
                RecruitmentBatch.AnnouncementAdmission.ADMITTED,
            )
        finally:
            import os

            os.unlink(path)

    def test_one_announcement_cannot_expand_to_two_batches_without_project_split(self):
        announcement = self.verified_announcement()
        admit_batch_with_announcement(
            self.batch,
            announcement,
            field_evidence=announcement_evidence(self.batch),
        )
        second = publish_formal_notice(
            self.source,
            identity_key="second-project",
            title="第二项目",
            hash_character="b",
        )
        with self.assertRaises(ValidationError):
            admit_batch_with_announcement(
                second,
                announcement,
                field_evidence=announcement_evidence(second),
            )
        split = split_verified_announcement_project(
            announcement,
            project_key="second-project",
            project_title="第二项目公告",
            project_evidence="页面第二项目区块明确写出独立岗位池",
        )
        admit_batch_with_announcement(
            second,
            split,
            field_evidence=announcement_evidence(second),
        )
        self.assertEqual(second.primary_announcement_id, split.pk)

    def test_announcement_and_application_can_share_official_page_fallback(self):
        response = self.client.get("/")
        self.assertNotContains(response, "投递待确认")
        self.assertContains(response, f'href="{self.batch.official_page_url}"', count=2)

    def test_miniprogram_announcement_keeps_notice_and_uses_job_page_for_application(self):
        website = self.verified_announcement(kind="website", title="官网公告")
        admit_batch_with_announcement(
            self.batch,
            website,
            field_evidence=announcement_evidence(self.batch),
        )
        WeChatAccountIdentity.objects.create(
            organization=self.source.organization,
            display_name="公告门控招聘小程序",
            biz_id="mini-program-biz",
            identity_evidence="企业官网公示该招聘账号和小程序",
            is_verified=True,
            verified_at=timezone.now(),
        )
        announcement = RecruitmentAnnouncement.objects.create(
            organization=self.source.organization,
            identity_key="mini-program-notice",
            source_kind=RecruitmentAnnouncement.SourceKind.WECHAT_MINIPROGRAM,
            title="2027小程序招聘通知",
            miniprogram_name="公告门控招聘",
            miniprogram_path="2027校园招聘",
            account_display_name="公告门控招聘小程序",
            account_biz_id="mini-program-biz",
            identity_evidence="企业官网公示该招聘账号和小程序",
            content_sha256="b" * 64,
            last_verified_at=timezone.now(),
            verification_status=RecruitmentAnnouncement.VerificationStatus.VERIFIED,
            verification_method=RecruitmentAnnouncement.VerificationMethod.WECHAT_OA,
        )
        admit_batch_with_announcement(
            self.batch,
            announcement,
            field_evidence=announcement_evidence(self.batch),
        )
        self.policy.announcement_gate_enforced = True
        self.policy.save(update_fields=["announcement_gate_enforced"])
        response = self.client.get("/")
        self.assertContains(response, "小程序公告")
        self.assertContains(response, "微信小程序：公告门控招聘 2027校园招聘")
        self.assertContains(response, f'href="{self.batch.official_page_url}"', count=1)
        self.assertNotContains(response, "投递待确认")
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.primary_announcement_id, announcement.pk)

    def test_miniprogram_without_stable_path_cannot_replace_website(self):
        website = self.verified_announcement(kind="website", title="官网公告")
        admit_batch_with_announcement(
            self.batch,
            website,
            field_evidence=announcement_evidence(self.batch),
        )
        WeChatAccountIdentity.objects.create(
            organization=self.source.organization,
            display_name="不稳定小程序账号",
            biz_id="unstable-mini-program-biz",
            identity_evidence="企业官网公示该小程序账号",
            is_verified=True,
            verified_at=timezone.now(),
        )
        miniprogram = RecruitmentAnnouncement.objects.create(
            organization=self.source.organization,
            identity_key="unstable-mini-program-notice",
            source_kind=RecruitmentAnnouncement.SourceKind.WECHAT_MINIPROGRAM,
            title="没有稳定路径的小程序通知",
            miniprogram_name="示例招聘",
            account_display_name="不稳定小程序账号",
            account_biz_id="unstable-mini-program-biz",
            identity_evidence="企业官网公示该小程序账号",
            content_sha256="c" * 64,
            last_verified_at=timezone.now(),
            verification_status=RecruitmentAnnouncement.VerificationStatus.VERIFIED,
            verification_method=RecruitmentAnnouncement.VerificationMethod.WECHAT_OA,
        )

        with self.assertRaises(ValidationError):
            admit_batch_with_announcement(
                self.batch,
                miniprogram,
                field_evidence=announcement_evidence(self.batch),
            )

    def test_batch_level_email_is_a_real_application_channel(self):
        ApplicationLink.objects.create(
            batch=self.batch,
            link_type=ApplicationLink.LinkType.EMAIL,
            email="jobs@announcement.test",
            verification_evidence="主要公告明确写出该招聘邮箱",
        )
        response = self.client.get("/")
        self.assertContains(response, 'href="mailto:jobs@announcement.test"')

    def test_server_enforces_five_province_selection_limit(self):
        response = self.client.get("/", {
            "city": ["北京", "上海", "天津", "重庆", "广东", "浙江"],
        })
        self.assertEqual(
            response.context["selected_cities"],
            ["北京", "上海", "天津", "重庆", "广东"],
        )

    def test_announcement_only_email_batch_uses_job_directions_without_inventing_titles(self):
        announcement = self.verified_announcement()
        batch = create_announcement_only_batch(
            announcement,
            identity_key="announcement-only-2027",
            field_evidence={
                "title": ("公告型2027招聘", "公告型2027招聘", "article/title"),
                "recruitment_type": (RecruitmentBatch.RecruitmentType.AUTUMN, "秋季招聘", "article/type"),
                "target_audience": ("2027届", "面向2027届", "article/audience"),
                "availability": (RecruitmentBatch.Status.ACTIVE, "邮箱接收简历", "article/application"),
            },
            directions=[{
                "title": "研发类",
                "location": "全国",
                "excerpt": "招聘方向：研发类；工作地点全国",
                "locator": "article/directions/1",
            }],
            application_email="campus@announcement.test",
            application_evidence="公告明确给出招聘邮箱",
        )
        self.policy.announcement_gate_enforced = True
        self.policy.save(update_fields=["announcement_gate_enforced"])
        self.assertTrue(RecruitmentBatch.objects.formal().filter(pk=batch.pk).exists())
        response = self.client.get("/")
        self.assertContains(response, "岗位方向：研发类")
        self.assertContains(response, 'href="mailto:campus@announcement.test"')

    def test_application_miniprogram_without_stable_url_remains_usable(self):
        announcement = self.verified_announcement()
        batch = create_announcement_only_batch(
            announcement,
            identity_key="announcement-only-miniprogram",
            field_evidence={
                "title": ("小程序投递招聘", "小程序投递招聘", "article/title"),
                "recruitment_type": (RecruitmentBatch.RecruitmentType.CAMPUS_RECRUITMENT, "校园招聘", "article/type"),
                "target_audience": ("2027届", "面向2027届", "article/audience"),
                "availability": (RecruitmentBatch.Status.ACTIVE, "小程序当前可投递", "article/application"),
            },
            directions=[{
                "title": "研发类",
                "location": "全国",
                "excerpt": "招聘方向：研发类；工作地点全国",
                "locator": "article/directions/1",
            }],
            application_miniprogram_name="示例招聘",
            application_miniprogram_path="校园招聘/2027届",
            application_instructions="微信搜索小程序后进入校园招聘栏目",
            application_evidence="公告明确给出小程序名称和进入路径",
        )
        self.policy.announcement_gate_enforced = True
        self.policy.save(update_fields=["announcement_gate_enforced"])
        self.assertTrue(RecruitmentBatch.objects.formal().filter(pk=batch.pk).exists())
        response = self.client.get("/")
        self.assertContains(response, "小程序投递")
        self.assertContains(response, "微信小程序：示例招聘")

    def test_expired_announcement_only_batch_moves_to_history(self):
        announcement = self.verified_announcement()
        batch = create_announcement_only_batch(
            announcement,
            identity_key="announcement-only-history",
            field_evidence={
                "title": ("公告型历史招聘", "公告型历史招聘", "article/title"),
                "recruitment_type": (RecruitmentBatch.RecruitmentType.CAMPUS_RECRUITMENT, "校园招聘", "article/type"),
                "target_audience": ("2027届", "面向2027届", "article/audience"),
                "availability": (RecruitmentBatch.Status.ACTIVE, "邮箱接收简历", "article/application"),
            },
            directions=[{
                "title": "研发类",
                "location": "全国",
                "excerpt": "招聘方向：研发类；工作地点全国",
                "locator": "article/directions/1",
            }],
            application_email="history@announcement.test",
            application_evidence="公告明确给出招聘邮箱",
        )
        batch.status = RecruitmentBatch.Status.EXPIRED
        batch.save(update_fields=["status"])
        self.policy.announcement_gate_enforced = True
        self.policy.save(update_fields=["announcement_gate_enforced"])
        self.assertFalse(RecruitmentBatch.objects.formal().filter(pk=batch.pk).exists())
        self.assertTrue(RecruitmentBatch.objects.historical().filter(pk=batch.pk).exists())

    def test_batch_application_link_can_be_proved_by_separate_announcement_source(self):
        application_source = OfficialSource.objects.create(
            organization=self.source.organization,
            source_type=OfficialSource.SourceType.WEBSITE,
            source_url="https://apply.announcement.test/campus",
            admission_evidence="企业官网子域名",
            parser_config=self.source.parser_config,
        )
        transition_source(
            application_source,
            to_state=OfficialSource.AdmissionState.VERIFIED,
            actor_label="test-owner",
            reason="official subdomain verified",
            evidence="test fixture review",
        )
        transition_source(
            application_source,
            to_state=OfficialSource.AdmissionState.ENABLED,
            actor_label="test-owner",
            reason="source enabled",
            evidence="test fixture passed",
        )
        announcement = RecruitmentAnnouncement.objects.create(
            organization=self.source.organization,
            source=application_source,
            identity_key="separate-application-source",
            source_kind=RecruitmentAnnouncement.SourceKind.WEBSITE,
            title="独立公告入口",
            url="https://apply.announcement.test/campus/2027",
            identity_evidence="企业官网子域名与主体一致",
            content_sha256="c" * 64,
            last_verified_at=timezone.now(),
            verification_status=RecruitmentAnnouncement.VerificationStatus.VERIFIED,
            verification_method=RecruitmentAnnouncement.VerificationMethod.HTTP,
        )
        ApplicationLink.objects.create(
            batch=self.batch,
            link_type=ApplicationLink.LinkType.APPLICATION,
            url="https://apply.announcement.test/campus/apply",
            verification_evidence="主要公告明确给出投递入口",
        )
        admit_batch_with_announcement(
            self.batch,
            announcement,
            field_evidence=announcement_evidence(self.batch),
        )
        self.policy.announcement_gate_enforced = True
        self.policy.save(update_fields=["announcement_gate_enforced"])
        self.assertTrue(RecruitmentBatch.objects.formal().filter(pk=self.batch.pk).exists())

    def test_audience_is_never_inferred_from_position_text(self):
        RecruitmentPosition.objects.filter(batch=self.batch).update(
            raw_text="仅此岗位详情提到2027届"
        )
        self.batch.target_audience = "应届毕业生"
        self.batch.save(update_fields=["target_audience"])
        self.assertEqual(
            canonical_audience(self.batch.recruitment_type, self.batch.target_audience),
            "届次未说明",
        )

    def test_admission_rejects_unknown_type_and_out_of_scope_old_cohort(self):
        announcement = self.verified_announcement()
        for recruitment_type, audience in (
            (RecruitmentBatch.RecruitmentType.UNKNOWN, "2027届"),
            (RecruitmentBatch.RecruitmentType.CAMPUS_RECRUITMENT, "2026届"),
        ):
            with self.assertRaises(ValidationError):
                admit_batch_with_announcement(
                    self.batch,
                    announcement,
                    field_evidence=announcement_evidence(
                        self.batch,
                        recruitment_type=recruitment_type,
                        target_audience=audience,
                    ),
                )

    def test_unstructured_manual_review_method_cannot_bypass_source_verification(self):
        announcement = self.verified_announcement()
        announcement.verification_method = (
            RecruitmentAnnouncement.VerificationMethod.MANUAL_REVIEW
        )
        announcement.save(update_fields=["verification_method"])
        with self.assertRaises(ValidationError):
            admit_batch_with_announcement(
                self.batch,
                announcement,
                field_evidence=announcement_evidence(self.batch),
            )

    def test_preview_digest_must_match_current_database(self):
        payload, digest = record_migration_preview()
        self.assertEqual(digest, migration_preview_digest(payload))
        RecruitmentPosition.objects.create(
            batch=self.batch,
            position_key="new-after-preview",
            title="预演后新增岗位",
            location_text="北京",
        )
        with self.assertRaises(ValidationError):
            activate_announcement_gate(digest)

    def test_preview_command_is_read_only_unless_record_is_explicit(self):
        output = StringIO()
        call_command("preview_announcement_migration", stdout=output)
        self.policy.refresh_from_db()
        self.assertEqual(self.policy.preview_digest, "")
        self.assertIn('"recorded": false', output.getvalue())

        output = StringIO()
        call_command("preview_announcement_migration", "--record", stdout=output)
        self.policy.refresh_from_db()
        self.assertRegex(self.policy.preview_digest, r"^[0-9a-f]{64}$")
        self.assertIn('"recorded": true', output.getvalue())

    def test_current_preview_reports_legacy_batch_as_excluded_without_mutation(self):
        payload = migration_preview_payload()
        row = next(item for item in payload["batches"] if item["batch_id"] == self.batch.pk)
        self.assertEqual(row["outcome"], "exclude")
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.announcement_admission, RecruitmentBatch.AnnouncementAdmission.LEGACY)

    def test_confirmed_cutover_marks_excluded_without_deleting_history_or_positions(self):
        position_count = self.batch.positions.count()
        _payload, digest = record_migration_preview()
        policy = activate_announcement_gate(digest)
        self.batch.refresh_from_db()
        self.assertTrue(policy.announcement_gate_enforced)
        self.assertEqual(
            self.batch.announcement_admission,
            RecruitmentBatch.AnnouncementAdmission.EXCLUDED,
        )
        self.assertEqual(self.batch.positions.count(), position_count)
        self.assertTrue(RecruitmentBatch.objects.filter(pk=self.batch.pk).exists())

    def test_gate_activation_is_audited_and_cannot_be_disabled(self):
        _payload, digest = record_migration_preview()
        policy = activate_announcement_gate(digest, actor_label="review-owner")
        event = RecruitmentPolicyEvent.objects.get(policy=policy)
        self.assertEqual(event.actor_label, "review-owner")
        self.assertEqual(event.preview_digest, digest)
        self.assertEqual(
            event.event_hash,
            RecruitmentPolicyEvent.calculate_hash(
                policy_id=policy.pk,
                event_type=event.event_type,
                actor_label=event.actor_label,
                preview_digest=event.preview_digest,
                previous_event_hash=event.previous_event_hash,
            ),
        )
        policy.announcement_gate_enforced = False
        with self.assertRaisesRegex(ValidationError, "cannot be disabled"):
            policy.save(update_fields=["announcement_gate_enforced"])

    def test_gate_cannot_be_activated_twice(self):
        _payload, digest = record_migration_preview()
        policy = activate_announcement_gate(digest, actor_label="first-owner")

        with self.assertRaisesRegex(ValidationError, "already activated"):
            activate_announcement_gate(digest, actor_label="second-owner")

        self.assertEqual(RecruitmentPolicyEvent.objects.filter(policy=policy).count(), 1)

    def test_superseded_batch_stays_distinct_from_pending_in_preview(self):
        self.batch.announcement_admission = (
            RecruitmentBatch.AnnouncementAdmission.SUPERSEDED
        )
        self.batch.save(update_fields=["announcement_admission"])
        row = next(
            item for item in migration_preview_payload()["batches"]
            if item["batch_id"] == self.batch.pk
        )
        self.assertEqual(row["outcome"], "superseded")


class BatchIdentityTests(TestCase):
    def test_spring_supplement_is_separate_from_spring(self):
        spring = build_batch_signature(
            organization_id=1,
            target_audience="2027届",
            recruitment_type=RecruitmentBatch.RecruitmentType.SPRING,
            job_pool_key="main",
        )
        supplement = replace(
            spring,
            recruitment_type=RecruitmentBatch.RecruitmentType.SPRING_SUPPLEMENT,
        )
        self.assertEqual(compare_batch_signatures(spring, supplement), "separate")

    def test_exact_project_and_job_pool_can_merge(self):
        signature = build_batch_signature(
            organization_id=1,
            target_audience="2027届",
            recruitment_type=RecruitmentBatch.RecruitmentType.AUTUMN,
            named_program="理想+",
            job_pool_key="top-tech-2027",
        )
        self.assertEqual(compare_batch_signatures(signature, signature), "merge")

    def test_missing_job_pool_requires_manual_review(self):
        signature = build_batch_signature(
            organization_id=1,
            target_audience="2027届",
            recruitment_type=RecruitmentBatch.RecruitmentType.AUTUMN,
            named_program="理想+",
        )
        self.assertEqual(compare_batch_signatures(signature, signature), "manual_review")


class OfficialDiscoveryContractTests(TestCase):
    def setUp(self):
        self.source = create_enabled_source(name="官网发现公司", host="official-discovery.test")

    def payload(self):
        return {
            "schema_version": "1",
            "query": "官网发现公司 2027 校园招聘",
            "source": {"orchestrator": "codex", "providers": ["exa"]},
            "candidates": [{
                "url": "https://official-discovery.test/campus/2027",
                "title_hint": "2027校园招聘",
                "provider": "exa",
                "rank": 1,
                "result_id": "result-1",
            }],
        }

    def test_strict_contract_deduplicates_and_stores_candidates_only(self):
        payload = self.payload()
        payload["candidates"].append(dict(payload["candidates"][0], rank=2))
        batch = parse_official_candidate_batch(payload)
        self.assertEqual(len(batch.candidates), 1)
        stored = store_official_candidates(self.source.organization, batch)
        self.assertEqual(stored[0].state, AnnouncementDiscoveryCandidate.State.NEW)
        self.assertFalse(RecruitmentAnnouncement.objects.exists())

    def test_contract_rejects_wechat_credentials_and_unknown_fields(self):
        for mutation in (
            lambda value: value["candidates"][0].update(url="https://mp.weixin.qq.com/s/token"),
            lambda value: value["candidates"][0].update(url="http://official-discovery.test/campus/2027"),
            lambda value: value.update(cookie="secret"),
            lambda value: value["candidates"][0].update(title_hint="token=secret"),
        ):
            payload = self.payload()
            mutation(payload)
            with self.assertRaises(DiscoveryContractError):
                parse_official_candidate_batch(payload)

    def test_known_sources_are_used_before_external_search(self):
        batch = known_source_candidate_batch(self.source.organization)
        self.assertEqual(batch.orchestrator, "radar")
        self.assertEqual(batch.providers, ("known_source",))
        self.assertTrue(batch.candidates)

    def test_probe_refetches_known_source_but_keeps_it_as_candidate(self):
        batch = parse_official_candidate_batch(self.payload())
        stored = store_official_candidates(self.source.organization, batch)

        class Response:
            url = "https://official-discovery.test/campus/2027"
            content = "<html><title>2027校园招聘</title><body>秋招岗位</body></html>".encode()

            @staticmethod
            def raise_for_status():
                return None

        session = SimpleNamespace(get=lambda *args, **kwargs: Response())
        probed = probe_official_candidates(
            self.source.organization,
            stored,
            session=session,
            resolver=lambda _host: ("8.8.8.8",),
        )
        self.assertTrue(probed[0].recruitment_signal_found)
        self.assertEqual(probed[0].state, AnnouncementDiscoveryCandidate.State.NEW)
        self.assertFalse(RecruitmentAnnouncement.objects.exists())

    def test_http_refetch_rejects_redirect_before_private_target_request(self):
        candidate = OfficialSiteCandidate(
            url="https://official-discovery.test/campus/2027",
            title_hint="2027校园招聘",
            provider="known_source",
            rank=1,
            result_id="redirect-private",
        )
        calls = []

        class Response:
            status_code = 302
            headers = {"Location": "http://169.254.169.254/latest/meta-data"}
            url = candidate.url

            @staticmethod
            def raise_for_status():
                return None

        def get(url, **kwargs):
            calls.append((url, kwargs))
            return Response()

        with self.assertRaises(DiscoveryContractError):
            refetch_official_candidate(
                self.source.organization,
                candidate,
                session=SimpleNamespace(get=get),
                resolver=lambda _host: ("8.8.8.8",),
            )
        self.assertEqual(len(calls), 1)
        self.assertFalse(calls[0][1]["allow_redirects"])

    def test_bulk_codex_contract_routes_candidates_to_exact_company(self):
        other = create_enabled_source(name="第二官网公司", host="second-official.test")
        payload = {
            "schema_version": "1",
            "source": {"orchestrator": "codex", "providers": ["exa"]},
            "candidates": [{
                "company": "第二官网公司",
                "url": "https://second-official.test/campus",
                "title_hint": "第二公司校招",
                "provider": "exa",
                "rank": 1,
                "result_id": "second-1",
            }],
        }
        batches = parse_bulk_official_candidate_batch(
            payload,
            [self.source.organization, other.organization],
        )
        self.assertFalse(batches[self.source.organization_id].candidates)
        self.assertEqual(batches[other.organization_id].candidates[0].title_hint, "第二公司校招")

    def test_bulk_contract_rejects_non_integer_rank(self):
        payload = {
            "schema_version": "1",
            "source": {"orchestrator": "codex", "providers": ["exa"]},
            "candidates": [{
                "company": "官网发现公司",
                "url": "https://official-discovery.test/campus",
                "title_hint": "官网校招",
                "provider": "exa",
                "rank": "first",
                "result_id": "bad-rank",
            }],
        }
        with self.assertRaises(DiscoveryContractError):
            parse_bulk_official_candidate_batch(payload, [self.source.organization])

    def test_bulk_contract_rejects_credentials_hidden_in_metadata(self):
        payload = {
            "schema_version": "1",
            "source": {"orchestrator": "codex", "providers": ["exa"]},
            "candidates": [{
                "company": "官网发现公司",
                "url": "https://official-discovery.test/campus",
                "title_hint": "authorization=secret",
                "provider": "exa",
                "rank": 1,
                "result_id": "unsafe",
            }],
        }
        with self.assertRaises(DiscoveryContractError):
            parse_bulk_official_candidate_batch(payload, [self.source.organization])

    def test_raw_html_without_keywords_stays_pending_for_dynamic_page_review(self):
        stored = store_official_candidates(
            self.source.organization,
            parse_official_candidate_batch(self.payload()),
        )

        class Response:
            url = "https://official-discovery.test/campus/2027"
            content = b"<html><title>Loading</title><body><div id='app'></div></body></html>"

            @staticmethod
            def raise_for_status():
                return None

        probed = probe_official_candidates(
            self.source.organization,
            stored,
            session=SimpleNamespace(get=lambda *args, **kwargs: Response()),
            resolver=lambda _host: ("8.8.8.8",),
        )
        self.assertEqual(probed[0].state, AnnouncementDiscoveryCandidate.State.NEW)
        self.assertEqual(probed[0].error_code, "CONTENT_REVIEW_REQUIRED")

    def test_isolated_render_can_verify_dynamic_official_page_without_cookies(self):
        candidate = OfficialSiteCandidate(
            url="https://official-discovery.test/campus/2027",
            title_hint="动态校招",
            provider="known_source",
            rank=1,
            result_id="dynamic-1",
        )
        rendered = render_official_candidate(
            self.source.organization,
            candidate,
            renderer=lambda *args, **kwargs: RenderedOfficialPage(
                url=f"{candidate.url}?challenge=temporary",
                title="2027校园招聘",
                body_text="2027届校园招聘正在投递",
                html="<html><body>2027届校园招聘正在投递</body></html>",
            ),
        )
        self.assertTrue(rendered.recruitment_signal_found)
        self.assertEqual(rendered.title, "2027校园招聘")
        self.assertEqual(rendered.url, candidate.url)
        same_text = render_official_candidate(
            self.source.organization,
            candidate,
            renderer=lambda *args, **kwargs: RenderedOfficialPage(
                url=candidate.url,
                title="2027校园招聘",
                body_text="2027届校园招聘正在投递",
                html="<html data-random='different-token'></html>",
            ),
        )
        self.assertEqual(rendered.content_sha256, same_text.content_sha256)

    def test_verification_fetch_uses_http_before_explicit_browser_fallback(self):
        candidate = OfficialSiteCandidate(
            url="https://official-discovery.test/campus/2027",
            title_hint="动态校招",
            provider="known_source",
            rank=1,
            result_id="dynamic-fallback",
        )

        class Response:
            url = candidate.url
            content = b"<html><body><div id='app'></div></body></html>"

            @staticmethod
            def raise_for_status():
                return None

        render_calls = []

        def renderer(*args, **kwargs):
            render_calls.append(args[0])
            return RenderedOfficialPage(
                url=candidate.url,
                title="2027校园招聘",
                body_text="2027届校园招聘正在投递",
                html="<html><body>2027届校园招聘正在投递</body></html>",
            )

        result = fetch_official_candidate_for_verification(
            self.source.organization,
            candidate,
            allow_browser=True,
            session=SimpleNamespace(get=lambda *args, **kwargs: Response()),
            resolver=lambda _host: ("8.8.8.8",),
            renderer=renderer,
        )
        self.assertTrue(result.recruitment_signal_found)
        self.assertEqual(render_calls, [candidate.url])

    def test_verification_can_force_browser_for_generic_dynamic_html(self):
        candidate = OfficialSiteCandidate(
            url="https://official-discovery.test/campus/2027",
            title_hint="动态校招",
            provider="known_source",
            rank=1,
            result_id="dynamic-force",
        )

        class Response:
            url = candidate.url
            content = b"<html><body>campus</body></html>"

            @staticmethod
            def raise_for_status():
                return None

        http_calls = []

        def get(*args, **kwargs):
            http_calls.append(args)
            return Response()

        session = SimpleNamespace(get=get)
        renderer = lambda *args, **kwargs: RenderedOfficialPage(
            url=candidate.url,
            title="2027校园招聘",
            body_text="青云计划 2027届招聘正在投递",
            html="<html><body>青云计划 2027届招聘正在投递</body></html>",
        )

        result = fetch_official_candidate_for_verification(
            self.source.organization,
            candidate,
            allow_browser=True,
            force_browser=True,
            session=session,
            renderer=renderer,
        )

        self.assertEqual(result.verification_method, "browser")
        self.assertEqual(http_calls, [])

    def test_force_browser_requires_explicit_browser_permission(self):
        candidate = OfficialSiteCandidate(
            url="https://official-discovery.test/campus/2027",
            title_hint="动态校招",
            provider="known_source",
            rank=1,
            result_id="dynamic-force-denied",
        )
        with self.assertRaisesRegex(DiscoveryContractError, "permission"):
            fetch_official_candidate_for_verification(
                self.source.organization,
                candidate,
                force_browser=True,
            )

    def test_isolated_render_rejects_redirect_outside_known_hosts(self):
        candidate = OfficialSiteCandidate(
            url="https://official-discovery.test/campus/2027",
            title_hint="动态校招",
            provider="known_source",
            rank=1,
            result_id="dynamic-2",
        )
        with self.assertRaises(DiscoveryContractError):
            render_official_candidate(
                self.source.organization,
                candidate,
                renderer=lambda *args, **kwargs: RenderedOfficialPage(
                    url="https://evil.example/campus",
                    title="伪造招聘",
                    body_text="2027校园招聘",
                    html="<html></html>",
                ),
            )

    def test_human_snapshot_is_explicit_and_field_locators_bind_to_its_hash(self):
        candidate = OfficialSiteCandidate(
            url="https://official-discovery.test/campus/2027",
            title_hint="2027校园招聘",
            provider="known_source",
            rank=1,
            result_id="snapshot-1",
        )
        with self.assertRaises(DiscoveryContractError):
            snapshot_official_candidate(
                self.source.organization,
                candidate,
                snapshot_bytes=b"snapshot",
                snapshot_title="2027校园招聘",
                human_confirmed_signal=False,
            )
        snapshot = snapshot_official_candidate(
            self.source.organization,
            candidate,
            snapshot_bytes=b"reviewed official screenshot",
            snapshot_title="2027校园招聘",
            human_confirmed_signal=True,
        )
        stored = AnnouncementDiscoveryCandidate.objects.create(
            organization=self.source.organization,
            source_kind=RecruitmentAnnouncement.SourceKind.WEBSITE,
            url=candidate.url,
            provider="known_source",
        )
        announcement = verify_official_announcement(
            stored,
            snapshot,
            identity_evidence="企业官网域名和人工截图已核验",
        )
        self.assertEqual(
            announcement.verification_method,
            RecruitmentAnnouncement.VerificationMethod.HUMAN_SNAPSHOT,
        )
        batch = publish_formal_notice(
            self.source,
            identity_key="snapshot-batch",
            title="2027校园招聘",
        )
        locator = f"snapshot[{snapshot.content_sha256}]/fields"
        admit_batch_with_announcement(
            batch,
            announcement,
            field_evidence={
                name: (value, excerpt, locator)
                for name, (value, excerpt, _old_locator) in announcement_evidence(batch).items()
            },
        )
        self.assertEqual(batch.announcement_admission, RecruitmentBatch.AnnouncementAdmission.ADMITTED)
        policy, _ = RecruitmentPolicy.objects.get_or_create(key="default")
        policy.announcement_gate_enforced = True
        policy.save(update_fields=["announcement_gate_enforced"])
        self.assertTrue(RecruitmentBatch.objects.filter(pk=batch.pk).formal().exists())
        batch.announcement_evidence.update(locator="snapshot[wrong-hash]/fields")
        self.assertFalse(RecruitmentBatch.objects.filter(pk=batch.pk).formal().exists())

    def test_known_ats_candidate_is_typed_as_recruiting_system(self):
        organization = Organization.objects.create(
            name="ATS 类型公司",
            company_type="private",
            industry="tech",
            official_domain="ats-type.test",
        )
        OfficialSource.objects.create(
            organization=organization,
            source_type=OfficialSource.SourceType.ATS,
            source_url="https://vendor-ats.test/campus",
            official_entrypoint_url="https://ats-type.test/careers",
            admission_evidence="候选 ATS",
        )
        batch = parse_official_candidate_batch({
            "schema_version": "1",
            "query": "ATS 类型公司校招",
            "source": {"orchestrator": "codex", "providers": ["exa"]},
            "candidates": [{
                "url": "https://vendor-ats.test/campus/2027",
                "title_hint": "2027 校招",
                "provider": "exa",
                "rank": 1,
                "result_id": "ats-1",
            }],
        })
        stored = store_official_candidates(organization, batch)
        self.assertEqual(
            stored[0].source_kind,
            RecruitmentAnnouncement.SourceKind.RECRUITING_SYSTEM,
        )

    def test_candidate_on_api_backed_recruiting_host_is_typed_as_recruiting_system(self):
        organization = Organization.objects.create(
            name="API 招聘系统公司",
            company_type="private",
            industry="tech",
            official_domain="api-owner.test",
        )
        OfficialSource.objects.create(
            organization=organization,
            source_type=OfficialSource.SourceType.API,
            source_url="https://jobs.api-owner.test/api/positions",
            admission_evidence="候选 API",
        )
        batch = parse_official_candidate_batch({
            "schema_version": "1",
            "query": "API 招聘系统公司校招",
            "source": {"orchestrator": "codex", "providers": ["exa"]},
            "candidates": [{
                "url": "https://jobs.api-owner.test/campus/2027",
                "title_hint": "2027 校招",
                "provider": "exa",
                "rank": 1,
                "result_id": "api-1",
            }],
        })
        stored = store_official_candidates(organization, batch)
        self.assertEqual(
            stored[0].source_kind,
            RecruitmentAnnouncement.SourceKind.RECRUITING_SYSTEM,
        )

    def test_provider_label_is_normalized_but_must_match_declared_source(self):
        payload = self.payload()
        payload["source"]["providers"] = ["OpenAI Web Search"]
        payload["candidates"][0]["provider"] = "OpenAI Web Search"
        batch = parse_official_candidate_batch(payload)
        self.assertEqual(batch.providers, ("openai_web_search",))
        self.assertEqual(batch.candidates[0].provider, "openai_web_search")

    def test_verified_official_candidate_needs_refetched_signal_and_identity(self):
        candidate = AnnouncementDiscoveryCandidate.objects.create(
            organization=self.source.organization,
            source_kind=RecruitmentAnnouncement.SourceKind.WEBSITE,
            url="https://official-discovery.test/campus/2027",
            provider="known_source",
        )
        refetched = RefetchedOfficialCandidate(
            candidate.url,
            "2027校园招聘",
            "a" * 64,
            timezone.now(),
            True,
        )
        announcement = verify_official_announcement(
            candidate,
            refetched,
            identity_evidence="官网域名与企业主体一致",
        )
        self.assertEqual(announcement.verification_status, "verified")
        candidate.refresh_from_db()
        self.assertEqual(candidate.state, "verified")

    def test_verification_preserves_discovered_url_and_records_safe_final_url(self):
        candidate = AnnouncementDiscoveryCandidate.objects.create(
            organization=self.source.organization,
            source_kind=RecruitmentAnnouncement.SourceKind.WEBSITE,
            url="https://official-discovery.test/campus",
            provider="known_source",
        )
        final_url = "https://official-discovery.test/university/campus"
        verify_official_announcement(
            candidate,
            RefetchedOfficialCandidate(
                final_url,
                "2027校园招聘",
                "f" * 64,
                timezone.now(),
                True,
            ),
            identity_evidence="官网域名与企业主体一致",
        )
        candidate.refresh_from_db()
        self.assertEqual(candidate.url, "https://official-discovery.test/campus")
        self.assertEqual(candidate.final_url, final_url)

    def test_verification_rejects_matching_but_unadmitted_external_source(self):
        organization = Organization.objects.create(
            name="未准入外部源公司",
            company_type="private",
            industry="tech",
            official_domain="identity-owner.test",
        )
        OfficialSource.objects.create(
            organization=organization,
            source_type=OfficialSource.SourceType.ATS,
            source_url="https://unadmitted-vendor.test/campus",
            official_entrypoint_url="https://identity-owner.test/careers",
            admission_evidence="尚未完成准入",
        )
        candidate = AnnouncementDiscoveryCandidate.objects.create(
            organization=organization,
            source_kind=RecruitmentAnnouncement.SourceKind.RECRUITING_SYSTEM,
            url="https://unadmitted-vendor.test/campus/2027",
            provider="codex_search",
        )
        refetched = RefetchedOfficialCandidate(
            candidate.url,
            "2027校园招聘",
            "d" * 64,
            timezone.now(),
            True,
        )
        with self.assertRaises(ValidationError):
            verify_official_announcement(
                candidate,
                refetched,
                identity_evidence="只有搜索结果，来源尚未准入",
            )

    def test_official_domain_notice_can_admit_identity_only_source(self):
        organization = Organization.objects.create(
            name="公告官网源公司",
            company_type="private",
            industry="tech",
            official_domain="corporate-notice.test",
        )
        source = admit_official_domain_announcement_source(
            organization,
            "https://www.corporate-notice.test/notices/2027",
            actor_label="project-owner",
            identity_evidence="企业备案官网域名与公司主体一致",
        )
        self.assertEqual(source.source_type, OfficialSource.SourceType.ANNOUNCEMENT)
        self.assertEqual(source.admission_state, OfficialSource.AdmissionState.ENABLED)
        candidate = AnnouncementDiscoveryCandidate.objects.create(
            organization=organization,
            source_kind=RecruitmentAnnouncement.SourceKind.WEBSITE,
            url="https://www.corporate-notice.test/notices/2027",
            provider="known_source",
        )
        announcement = verify_official_announcement(
            candidate,
            RefetchedOfficialCandidate(
                candidate.url,
                "2027校园招聘",
                "e" * 64,
                timezone.now(),
                True,
            ),
            identity_evidence="企业备案官网域名与公司主体一致",
        )
        self.assertEqual(announcement.source_id, source.pk)

    def test_identity_only_announcement_source_is_never_sent_to_job_collector(self):
        organization = Organization.objects.create(
            name="只读公告源公司",
            company_type="private",
            industry="tech",
            official_domain="notice-only.test",
        )
        source = admit_official_domain_announcement_source(
            organization,
            "https://notice-only.test/notices/2027",
            actor_label="project-owner",
            identity_evidence="企业官方域名",
        )
        with patch("radar.collectors.registry.AdapterRegistry.get") as adapter_get:
            summary = run_update(trigger="manual", source_ids=[source.pk])
        adapter_get.assert_not_called()
        self.assertEqual(summary.sources_checked, 0)

    def test_discovery_command_uses_nonzero_failure_semantics(self):
        output = StringIO()
        with patch(
            "radar.management.commands.discover_official_announcements.build_exa_client_from_environment",
            side_effect=ExaDiscoveryError("AUTH_INVALID", fallback_allowed=False),
        ):
            with self.assertRaises(CommandError):
                call_command(
                    "discover_official_announcements",
                    organization=[self.source.organization.name],
                    allow_live_search=True,
                    audience=["2027届"],
                    recruitment_type=["秋招"],
                    published_after="2026-06-01",
                    published_before="2026-12-31",
                    stdout=output,
                )
        self.assertIn('"ok": false', output.getvalue())


class WeChatOABoundaryTests(TestCase):
    def setUp(self):
        self.source = create_enabled_source(name="微信边界公司", host="wechat-boundary.test")
        WeChatAccountIdentity.objects.create(
            organization=self.source.organization,
            display_name="微信边界招聘",
            biz_id="biz-safe",
            identity_evidence="企业官网公示该公众号",
            is_verified=True,
            verified_at=timezone.now(),
        )

    def wx_candidate(self, *, markdown="明确招聘2027届", images=None):
        return {
            "fetch_url": "https://mp.weixin.qq.com/s/safe-token",
            "article_identity": "token:safe-token",
            "verification_status": "verified",
            "evidence": {
                "schema_version": "1",
                "article": {
                    "title": "2027校园招聘",
                    "content_markdown": markdown,
                    "source_url": "https://mp.weixin.qq.com/s/safe-token",
                    "published_at": "2026-08-20T08:00:00+00:00",
                },
                "account_identity": {
                    "observed_display_name": "微信边界招聘",
                    "observed_biz_id": "biz-safe",
                    "status": "allowlist_matched",
                },
                "images": images or [],
                "last_verified_at": "2026-08-30T08:00:00+00:00",
                "content_sha256": "b" * 64,
                "evidence_sha256": "c" * 64,
            },
        }

    def direct_candidate(self, *, token="safe-token", markdown="明确招聘2027届"):
        candidate = self.wx_candidate(markdown=markdown)
        candidate["fetch_url"] = f"https://mp.weixin.qq.com/s/{token}"
        candidate["article_identity"] = f"token:{token}"
        candidate["evidence"]["article"]["source_url"] = candidate["fetch_url"]
        candidate["search_provenance"] = {
            "provider": "exa",
            "rank": 1,
            "result_id": f"exa-{token}",
        }
        candidate["title_hint"] = "搜索标题不是公告证据"
        return candidate

    def direct_data(self, *, candidates=None, partial=False):
        values = list(candidates or [])
        return {
            "schema_version": "1",
            "search_provider": "exa",
            "summary": {
                "received": len(values),
                "accepted": len(values),
                "duplicates_removed": 0,
                "hydration_attempted": len(values),
                "verified": sum(
                    item.get("verification_status") == "verified" for item in values
                ),
                "partial": partial,
            },
            "candidates": values,
        }

    def test_wechat_oa_article_requires_radar_owned_account_allowlist(self):
        announcement = import_wechat_oa_announcement(
            self.source.organization, self.wx_candidate()
        )
        self.assertEqual(announcement.verification_status, "verified")
        self.assertEqual(announcement.account_biz_id, "biz-safe")

    def test_image_only_article_remains_pending(self):
        announcement = import_wechat_oa_announcement(
            self.source.organization,
            self.wx_candidate(markdown="", images=[{"index": 0, "url": "https://img.test/a"}]),
        )
        self.assertEqual(announcement.verification_status, "pending_image")

    def test_empty_wechat_oa_article_evidence_is_rejected(self):
        with self.assertRaises(ValidationError):
            import_wechat_oa_announcement(
                self.source.organization,
                self.wx_candidate(markdown="", images=[]),
            )

    def test_image_only_article_requires_human_confirmed_ocr_before_verification(self):
        candidate = self.wx_candidate(markdown="", images=[{
            "index": 0,
            "url": "https://img.test/a",
            "ocr_text": "OCR公告：2027届校园招聘，邮箱接收简历",
            "analysis_status": "human_confirmed",
            "ocr_engine": "wechat-oa",
        }])
        announcement = import_wechat_oa_announcement(self.source.organization, candidate)
        self.assertEqual(announcement.verification_status, "verified")
        batch = publish_formal_notice(
            self.source,
            identity_key="ocr-batch",
            title="OCR公告",
        )
        admit_batch_with_announcement(
            batch,
            announcement,
            field_evidence={
                "title": ("OCR公告", "OCR公告", "image[0]/ocr"),
                "recruitment_type": (
                    RecruitmentBatch.RecruitmentType.CAMPUS_RECRUITMENT,
                    "校园招聘",
                    "image[0]/ocr",
                ),
                "target_audience": ("2027届", "2027届", "image[0]/ocr"),
                "availability": (
                    RecruitmentBatch.Status.ACTIVE,
                    "邮箱接收简历",
                    "image[0]/ocr",
                ),
            },
        )
        self.assertEqual(batch.announcement_admission, RecruitmentBatch.AnnouncementAdmission.ADMITTED)

    def test_nonempty_biz_id_mismatch_cannot_fall_back_to_same_display_name(self):
        candidate = self.wx_candidate()
        candidate["evidence"]["account_identity"]["observed_biz_id"] = "different-biz"
        with self.assertRaises(ValidationError):
            import_wechat_oa_announcement(self.source.organization, candidate)

    def test_wechat_oa_observed_links_and_media_remain_untrusted_channel_candidates(self):
        candidate = self.wx_candidate()
        candidate["evidence"]["external_links"] = [
            {
                "index": 0,
                "source_location": "article/body/a[1]",
                "raw_value": "https://apply.example.test/campus",
                "normalized_value": "https://apply.example.test/campus",
                "kind": "external_http",
                "text": "立即投递",
            },
            {
                "index": 1,
                "source_location": "article/body/a[2]",
                "raw_value": "mailto:jobs@example.test",
                "normalized_value": "mailto:jobs@example.test",
                "kind": "email",
                "text": "招聘邮箱",
            },
        ]
        candidate["evidence"]["images"] = [{
            "index": 0,
            "url": "https://img.example.test/poster.png",
            "ocr_text": "扫码投递",
            "ocr_engine": "wechat-oa",
            "analysis_status": "human_confirmed",
            "qr_payloads": ["weixin://dl/business/?ticket=safe"],
        }]
        announcement = import_wechat_oa_announcement(self.source.organization, candidate)
        self.assertEqual(len(announcement.observed_external_links), 2)
        self.assertEqual(announcement.observed_media[0]["ocr_text"], "扫码投递")
        channels = observed_application_channel_candidates(announcement)
        self.assertEqual(
            {item["kind"] for item in channels},
            {"external_http", "email", "qr_payload"},
        )
        self.assertTrue(all(item["verification_required"] for item in channels))
        self.assertFalse(ApplicationLink.objects.filter(batch__organization=self.source.organization).exists())

    def test_client_does_not_add_browser_without_explicit_authorization(self):
        calls = []
        call_options = []

        def runner(command, **kwargs):
            calls.append(command)
            call_options.append(kwargs)
            if command[-1] == "--version":
                return subprocess.CompletedProcess(command, 0, "0.4.0\n", "")
            output = {"ok": True, "data": {
                "schema_version": "1",
                "summary": {"partial": False},
                "candidates": [],
            }}
            return subprocess.CompletedProcess(command, 0, json.dumps(output), "")

        client = WeChatOAClient(runner=runner)
        result = client.hydrate_candidate_batch({"schema_version": "1"})
        self.assertFalse(result.partial)
        self.assertEqual(calls[0][0], "wechat-oa")
        self.assertEqual(calls[1][0], "wechat-oa")
        self.assertNotIn("--browser", calls[1])
        self.assertEqual(call_options[1]["timeout"], 660)
        self.assertNotIn("EXA_API_KEY", call_options[0]["env"])
        self.assertNotIn("EXA_API_KEY", call_options[1]["env"])

    def test_client_checks_both_exit_code_and_json_envelope(self):
        responses = iter((
            subprocess.CompletedProcess([], 0, "0.4.0", ""),
            subprocess.CompletedProcess([], 0, json.dumps({"ok": False, "error": {"code": "VERIFICATION_REQUIRED"}}), ""),
        ))
        client = WeChatOAClient(runner=lambda *args, **kwargs: next(responses))
        with self.assertRaises(WeChatOAError) as raised:
            client.hydrate_candidate_batch({"schema_version": "1"})
        self.assertEqual(raised.exception.code, "VERIFICATION_REQUIRED")

    def test_direct_exa_client_uses_frozen_command_and_scrubbed_environment(self):
        calls = []

        def runner(command, **kwargs):
            calls.append((command, kwargs))
            if command[-1] == "--version":
                return subprocess.CompletedProcess(command, 0, "0.7.0\n", "")
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps({"ok": True, "data": self.direct_data()}),
                "",
            )

        result = WeChatOAClient(runner=runner).search_articles_with_exa(
            query="2027届 秋招",
            company="微信边界公司",
            account_names=("微信边界招聘",),
            published_after="2026-06-01",
            published_before="2026-09-02",
        )

        command, options = calls[1]
        self.assertFalse(result.partial)
        self.assertEqual(command[:5], [
            "wechat-oa",
            "--json",
            "discovery",
            "search",
            "2027届 秋招",
        ])
        self.assertIn("--company", command)
        self.assertIn("微信边界公司", command)
        self.assertIn("--account", command)
        self.assertIn("微信边界招聘", command)
        self.assertIn("--provider", command)
        self.assertIn("exa", command)
        self.assertIn("--hydrate", command)
        self.assertIn("--no-browser", command)
        self.assertNotIn("--browser", command)
        self.assertNotIn("--analyze-media", command)
        self.assertNotIn("EXA_API_KEY", options["env"])
        self.assertNotIn("input", options)

    def test_direct_exa_client_requires_wechat_oa_070(self):
        client = WeChatOAClient(
            runner=lambda command, **kwargs: subprocess.CompletedProcess(
                command, 0, "0.6.0\n", ""
            )
        )
        with self.assertRaises(WeChatOAError) as raised:
            client.search_articles_with_exa(
                query="2027届 秋招",
                company="微信边界公司",
                account_names=("微信边界招聘",),
            )
        self.assertEqual(raised.exception.code, "WECHAT_OA_TOO_OLD")

    def test_direct_exa_client_preserves_stable_provider_failure_reason(self):
        responses = iter((
            subprocess.CompletedProcess([], 0, "0.7.0\n", ""),
            subprocess.CompletedProcess([], 6, json.dumps({
                "ok": False,
                "error": {
                    "code": "AUTHENTICATION_ERROR",
                    "message": "safe",
                    "details": {"provider": "exa", "reason": "credential_rejected"},
                },
            }), ""),
        ))
        client = WeChatOAClient(runner=lambda *args, **kwargs: next(responses))
        with self.assertRaises(WeChatOAError) as raised:
            client.search_articles_with_exa(
                query="2027届 秋招",
                company="微信边界公司",
                account_names=("微信边界招聘",),
            )
        self.assertEqual(raised.exception.code, "AUTHENTICATION_ERROR")
        self.assertEqual(raised.exception.provider, "exa")
        self.assertEqual(raised.exception.reason, "credential_rejected")
        self.assertEqual(raised.exception.exit_code, 6)

    def test_direct_exa_client_rejects_mismatched_error_reason_contract(self):
        responses = iter((
            subprocess.CompletedProcess([], 0, "0.7.0\n", ""),
            subprocess.CompletedProcess([], 6, json.dumps({
                "ok": False,
                "error": {
                    "code": "AUTHENTICATION_ERROR",
                    "message": "safe",
                    "details": {"provider": "exa", "reason": "rate_limited"},
                },
            }), ""),
        ))
        with self.assertRaises(WeChatOAError) as raised:
            WeChatOAClient(
                runner=lambda *args, **kwargs: next(responses)
            ).search_articles_with_exa(
                query="2027届 秋招",
                company="微信边界公司",
                account_names=("微信边界招聘",),
            )
        self.assertEqual(raised.exception.code, "INVALID_ERROR_CONTRACT")

    def test_direct_exa_client_rejects_wrong_provider_or_non_article_url(self):
        for candidate in (
            dict(
                self.direct_candidate(),
                search_provenance={"provider": "brave", "rank": 1, "result_id": "bad"},
            ),
            dict(self.direct_candidate(), fetch_url="https://mp.weixin.qq.com/profile"),
        ):
            responses = iter((
                subprocess.CompletedProcess([], 0, "0.7.0\n", ""),
                subprocess.CompletedProcess([], 0, json.dumps({
                    "ok": True,
                    "data": self.direct_data(candidates=[candidate]),
                }), ""),
            ))
            with self.assertRaises(WeChatOAError) as raised:
                WeChatOAClient(
                    runner=lambda *args, **kwargs: next(responses)
                ).search_articles_with_exa(
                    query="2027届 秋招",
                    company="微信边界公司",
                    account_names=("微信边界招聘",),
                )
            self.assertEqual(raised.exception.code, "INVALID_RESULT")

    def test_candidate_batch_has_no_browser_or_credentials_fields(self):
        payload = build_wechat_candidate_batch(
            query="2027校园招聘",
            company="微信边界公司",
            expected_accounts=[{"biz_id": "biz-safe", "display_names": ["微信边界招聘"]}],
            candidates=[],
            providers=["exa"],
        )
        encoded = json.dumps(payload).casefold()
        self.assertNotIn("browser", encoded)
        self.assertNotIn("cookie", encoded)
        self.assertEqual(validate_wechat_candidate_batch(payload), payload)

    def test_candidate_batch_rejects_unknown_fields_credentials_and_non_wechat_urls(self):
        base = {
            "url": "https://mp.weixin.qq.com/s/safe-token",
            "title_hint": "2027校园招聘",
            "snippet": "公开搜索摘要",
            "backend_date_hint": "2026-08-20",
            "search_provenance": {
                "provider": "exa",
                "rank": 1,
                "result_id": "safe-1",
            },
        }
        for candidate in (
            dict(base, cookie="secret"),
            dict(base, url="https://example.test/jobs"),
            dict(base, snippet="authorization=secret"),
        ):
            with self.assertRaises(WeChatOAError):
                build_wechat_candidate_batch(
                    query="2027校园招聘",
                    company="微信边界公司",
                    expected_accounts=[{"display_names": ["微信边界招聘"]}],
                    candidates=[candidate],
                    providers=["exa"],
                )

    def test_import_command_rejects_unsafe_input_before_starting_wechat_oa(self):
        payload = build_wechat_candidate_batch(
            query="2027校园招聘",
            company="微信边界公司",
            expected_accounts=[{"display_names": ["微信边界招聘"]}],
            candidates=[],
            providers=["exa"],
        )
        payload["cookie"] = "secret"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", encoding="utf-8", delete=False
        ) as handle:
            json.dump(payload, handle, ensure_ascii=False)
            path = handle.name
        try:
            with patch(
                "radar.management.commands.import_wechat_oa_announcements.WeChatOAClient.hydrate_candidate_batch"
            ) as hydrate:
                with self.assertRaises(CommandError):
                    call_command(
                        "import_wechat_oa_announcements",
                        organization="微信边界公司",
                        input=path,
                    )
                hydrate.assert_not_called()
        finally:
            import os
            os.unlink(path)

    def test_only_canonical_wechat_oa_import_command_is_registered(self):
        commands = get_commands()
        self.assertIn("import_wechat_oa_announcements", commands)
        self.assertNotIn("import_wxcli_announcements", commands)

    def test_import_command_accepts_canonical_wechat_oa_executable_option(self):
        payload = build_wechat_candidate_batch(
            query="2027校园招聘",
            company="微信边界公司",
            expected_accounts=[{"display_names": ["微信边界招聘"]}],
            candidates=[],
            providers=["exa"],
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", encoding="utf-8", delete=False
        ) as handle:
            json.dump(payload, handle, ensure_ascii=False)
            path = handle.name
        try:
            with patch(
                "radar.management.commands.import_wechat_oa_announcements.WeChatOAClient"
            ) as client_class:
                client_class.return_value.hydrate_candidate_batch.return_value = (
                    SimpleNamespace(
                        verified_candidates=(),
                        partial=False,
                    )
                )
                output = StringIO()
                call_command(
                    "import_wechat_oa_announcements",
                    organization="微信边界公司",
                    input=path,
                    wechat_oa_path="C:/tools/wechat-oa.exe",
                    stdout=output,
                )
            client_class.assert_called_once_with("C:/tools/wechat-oa.exe")
            self.assertIn('"ok": true', output.getvalue())
        finally:
            import os
            os.unlink(path)

    def test_direct_discovery_command_is_read_only_preview_by_default(self):
        with patch(
            "radar.management.commands.discover_wechat_oa_announcements.WeChatOAClient"
        ) as client_class:
            output = StringIO()
            call_command(
                "discover_wechat_oa_announcements",
                organization="微信边界公司",
                query="2027届 秋招",
                published_after="2026-06-01",
                published_before="2026-09-02",
                stdout=output,
            )
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["status"], "preview")
        self.assertFalse(payload["recorded"])
        client_class.assert_not_called()
        self.assertFalse(
            RecruitmentAnnouncement.objects.filter(
                organization=self.source.organization,
                source_kind=RecruitmentAnnouncement.SourceKind.WECHAT_ARTICLE,
            ).exists()
        )

    def test_direct_discovery_record_requires_live_search_permission(self):
        with self.assertRaisesMessage(
            CommandError, "--record requires --allow-live-search"
        ):
            call_command(
                "discover_wechat_oa_announcements",
                organization="微信边界公司",
                query="2027届 秋招",
                record=True,
                stdout=StringIO(),
            )

    def test_direct_discovery_rejects_unsafe_query_before_cli(self):
        with patch(
            "radar.management.commands.discover_wechat_oa_announcements.WeChatOAClient"
        ) as client_class:
            with self.assertRaisesMessage(CommandError, "credential-like"):
                call_command(
                    "discover_wechat_oa_announcements",
                    organization="微信边界公司",
                    query="api_key=must-not-be-forwarded",
                    allow_live_search=True,
                    stdout=StringIO(),
                )
        client_class.assert_not_called()

    def test_direct_discovery_searches_without_recording_and_reports_partial(self):
        candidate = self.direct_candidate()
        result = SimpleNamespace(
            data=self.direct_data(candidates=[candidate], partial=True),
            verified_candidates=(candidate,),
            partial=True,
        )
        with patch(
            "radar.management.commands.discover_wechat_oa_announcements.WeChatOAClient"
        ) as client_class:
            client_class.return_value.search_articles_with_exa.return_value = result
            output = StringIO()
            call_command(
                "discover_wechat_oa_announcements",
                organization="微信边界公司",
                query="2027届 秋招",
                allow_live_search=True,
                stdout=output,
            )
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["status"], "partial")
        self.assertEqual(payload["verified_articles"], 1)
        self.assertEqual(payload["announcements_imported"], 0)
        self.assertFalse(payload["recorded"])
        client_class.return_value.search_articles_with_exa.assert_called_once_with(
            query="2027届 秋招",
            company="微信边界公司",
            account_names=("微信边界招聘",),
            published_after=None,
            published_before=None,
        )
        self.assertFalse(
            RecruitmentAnnouncement.objects.filter(
                organization=self.source.organization,
                source_kind=RecruitmentAnnouncement.SourceKind.WECHAT_ARTICLE,
            ).exists()
        )

    def test_direct_discovery_reports_safe_provider_error_contract(self):
        with patch(
            "radar.management.commands.discover_wechat_oa_announcements.WeChatOAClient"
        ) as client_class:
            client_class.return_value.search_articles_with_exa.side_effect = WeChatOAError(
                "NETWORK_ERROR",
                "upstream detail must not be copied",
                provider="exa",
                reason="rate_limited",
                exit_code=5,
            )
            output = StringIO()
            with self.assertRaisesMessage(CommandError, "NETWORK_ERROR"):
                call_command(
                    "discover_wechat_oa_announcements",
                    organization="微信边界公司",
                    query="2027届 秋招",
                    allow_live_search=True,
                    stdout=output,
                )
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["error"], {
            "code": "NETWORK_ERROR",
            "provider": "exa",
            "reason": "rate_limited",
        })
        self.assertNotIn("upstream detail", output.getvalue())

    def test_direct_discovery_records_verified_articles_only_when_explicit(self):
        candidate = self.direct_candidate()
        result = SimpleNamespace(
            data=self.direct_data(candidates=[candidate]),
            verified_candidates=(candidate,),
            partial=False,
        )
        with patch(
            "radar.management.commands.discover_wechat_oa_announcements.WeChatOAClient"
        ) as client_class:
            client_class.return_value.search_articles_with_exa.return_value = result
            output = StringIO()
            call_command(
                "discover_wechat_oa_announcements",
                organization="微信边界公司",
                query="2027届 秋招",
                allow_live_search=True,
                record=True,
                stdout=output,
            )
        payload = json.loads(output.getvalue())
        self.assertTrue(payload["recorded"])
        self.assertEqual(payload["announcements_imported"], 1)
        self.assertTrue(
            RecruitmentAnnouncement.objects.filter(
                organization=self.source.organization,
                source_kind=RecruitmentAnnouncement.SourceKind.WECHAT_ARTICLE,
                identity_key="token:safe-token",
            ).exists()
        )

    def test_direct_discovery_record_is_atomic_for_one_company(self):
        valid = self.direct_candidate(token="valid")
        invalid = self.direct_candidate(token="invalid")
        invalid["evidence"]["account_identity"]["observed_biz_id"] = "other-biz"
        result = SimpleNamespace(
            data=self.direct_data(candidates=[valid, invalid]),
            verified_candidates=(valid, invalid),
            partial=False,
        )
        with patch(
            "radar.management.commands.discover_wechat_oa_announcements.WeChatOAClient"
        ) as client_class:
            client_class.return_value.search_articles_with_exa.return_value = result
            with self.assertRaises(CommandError):
                call_command(
                    "discover_wechat_oa_announcements",
                    organization="微信边界公司",
                    query="2027届 秋招",
                    allow_live_search=True,
                    record=True,
                    stdout=StringIO(),
                )
        self.assertFalse(
            RecruitmentAnnouncement.objects.filter(
                organization=self.source.organization,
                source_kind=RecruitmentAnnouncement.SourceKind.WECHAT_ARTICLE,
            ).exists()
        )

    def test_direct_discovery_rejects_company_without_verified_account_before_cli(self):
        organization = Organization.objects.create(
            name="无公众号身份公司",
            aliases=[],
            company_type=Organization.CompanyType.PRIVATE,
            industry="科技",
        )
        with patch(
            "radar.management.commands.discover_wechat_oa_announcements.WeChatOAClient"
        ) as client_class:
            with self.assertRaisesMessage(
                CommandError, "organization has no verified WeChat account identity"
            ):
                call_command(
                    "discover_wechat_oa_announcements",
                    organization=organization.name,
                    query="2027届 秋招",
                    allow_live_search=True,
                    stdout=StringIO(),
                )
        client_class.assert_not_called()
