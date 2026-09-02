import hashlib
import json
import re
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Organization(models.Model):
    class CompanyType(models.TextChoices):
        PRIVATE = "private", "民企"
        STATE_OWNED = "state_owned", "央国企"
        FOREIGN = "foreign", "外资"
        JOINT_VENTURE = "joint_venture", "中外合资"
        BANK = "bank", "银行"
        PUBLIC_INSTITUTION = "public_institution", "事业单位"
        SOCIAL_ORGANIZATION = "social_organization", "社会机构"

    name = models.CharField(max_length=200, unique=True)
    aliases = models.JSONField(default=list, blank=True)
    company_type = models.CharField(max_length=24, choices=CompanyType.choices)
    industry = models.CharField(max_length=100)
    official_domain = models.CharField(max_length=255, blank=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT)

    def __str__(self) -> str:
        return self.name


class OrganizationAlias(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="normalized_aliases"
    )
    alias = models.CharField(max_length=200)
    normalized_alias = models.CharField(max_length=200, unique=True)

    def __str__(self) -> str:
        return self.alias


class OfficialSource(models.Model):
    class SourceType(models.TextChoices):
        WEBSITE = "website", "企业官网"
        ANNOUNCEMENT = "announcement", "企业官网公告源"
        ATS = "ats", "官网关联投递系统"
        WECHAT = "wechat", "官方招聘公众号"
        API = "api", "官方招聘接口"

    class AdmissionState(models.TextChoices):
        CANDIDATE = "candidate", "候选"
        VERIFIED = "verified", "已核验"
        ENABLED = "enabled", "已启用"
        SUSPENDED = "suspended", "已暂停"
        REVOKED = "revoked", "已撤销"

    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="official_sources")
    source_type = models.CharField(max_length=16, choices=SourceType.choices)
    source_url = models.URLField()
    official_entrypoint_url = models.URLField(blank=True)
    admission_evidence = models.TextField()
    access_policy = models.CharField(max_length=300, default="低频、公开、无需登录访问")
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    adapter_name = models.CharField(max_length=64, default="html_selector")
    parser_config = models.JSONField(default=dict, blank=True)
    allowed_link_hosts = models.JSONField(default=list, blank=True)
    admission_state = models.CharField(
        max_length=16,
        choices=AdmissionState.choices,
        default=AdmissionState.CANDIDATE,
    )
    last_etag = models.CharField(max_length=255, blank=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    local_demo_key = models.CharField(max_length=64, blank=True)

    def __str__(self) -> str:
        return f"{self.organization}: {self.source_url}"


class WeChatAccountIdentity(models.Model):
    """Radar-owned mapping from a company to an official WeChat account."""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="wechat_account_identities",
    )
    display_name = models.CharField(max_length=200)
    biz_id = models.CharField(max_length=512, blank=True)
    identity_evidence = models.TextField()
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "display_name"],
                name="unique_wechat_display_name_per_organization",
            ),
            models.UniqueConstraint(
                fields=["biz_id"],
                condition=~Q(biz_id=""),
                name="unique_nonempty_wechat_biz_id",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.organization}: {self.display_name}"

    def clean(self) -> None:
        super().clean()
        if self.is_verified and (
            not self.identity_evidence.strip() or self.verified_at is None
        ):
            raise ValidationError(
                "verified WeChat identities require evidence and verification time"
            )


class RecruitmentAnnouncement(models.Model):
    """The single official notice that admits one or more recruitment batches."""

    class SourceKind(models.TextChoices):
        WEBSITE = "website", "企业官网公告"
        RECRUITING_SYSTEM = "recruiting_system", "官方招聘系统项目页"
        WECHAT_ARTICLE = "wechat_article", "微信公众号文章"
        WECHAT_MINIPROGRAM = "wechat_miniprogram", "微信小程序通知"

    class VerificationStatus(models.TextChoices):
        CANDIDATE = "candidate", "候选"
        VERIFIED = "verified", "已核验"
        PENDING_IMAGE = "pending_image", "图片待核验"
        REJECTED = "rejected", "已拒绝"

    class VerificationMethod(models.TextChoices):
        HTTP = "http", "官网 HTTP 回读"
        BROWSER = "browser", "隔离浏览器回读"
        WECHAT_OA = "wechat_oa", "wechat-oa 微信证据"
        HUMAN_SNAPSHOT = "human_snapshot", "人工确认快照"
        MANUAL_REVIEW = "manual_review", "人工审核"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="recruitment_announcements",
    )
    source = models.ForeignKey(
        OfficialSource,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="recruitment_announcements",
    )
    identity_key = models.CharField(max_length=512)
    source_kind = models.CharField(max_length=24, choices=SourceKind.choices)
    title = models.CharField(max_length=500)
    url = models.URLField(blank=True)
    miniprogram_name = models.CharField(max_length=200, blank=True)
    miniprogram_path = models.CharField(max_length=500, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    last_verified_at = models.DateTimeField(null=True, blank=True)
    identity_evidence = models.TextField()
    account_display_name = models.CharField(max_length=200, blank=True)
    account_biz_id = models.CharField(max_length=512, blank=True)
    content_sha256 = models.CharField(max_length=64, blank=True)
    evidence_sha256 = models.CharField(max_length=64, blank=True)
    observed_external_links = models.JSONField(default=list, blank=True)
    observed_media = models.JSONField(default=list, blank=True)
    verification_status = models.CharField(
        max_length=24,
        choices=VerificationStatus.choices,
        default=VerificationStatus.CANDIDATE,
    )
    verification_method = models.CharField(
        max_length=24,
        choices=VerificationMethod.choices,
        default=VerificationMethod.MANUAL_REVIEW,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "source_kind", "identity_key"],
                name="unique_announcement_identity_per_organization",
            ),
        ]

    @property
    def priority(self) -> int:
        if self.source_kind == self.SourceKind.WECHAT_ARTICLE:
            return 1
        if (
            self.source_kind == self.SourceKind.WECHAT_MINIPROGRAM
            and self.miniprogram_path.strip()
        ):
            return 1
        return {
            self.SourceKind.WEBSITE: 2,
            self.SourceKind.RECRUITING_SYSTEM: 3,
            self.SourceKind.WECHAT_MINIPROGRAM: 4,
        }[self.source_kind]

    def clean(self) -> None:
        super().clean()
        if self.source_id and self.source.organization_id != self.organization_id:
            raise ValidationError("announcement source must belong to its organization")
        if self.source_kind == self.SourceKind.WECHAT_MINIPROGRAM:
            if not self.miniprogram_name.strip():
                raise ValidationError("mini-program announcements require a name")
        elif not self.url.strip():
            raise ValidationError("web announcements require a URL")
        if self.url and urlsplit(self.url).scheme != "https":
            raise ValidationError("announcement URLs must use HTTPS")
        if (
            self.source_kind == self.SourceKind.WECHAT_ARTICLE
            and (urlsplit(self.url).hostname or "").casefold() != "mp.weixin.qq.com"
        ):
            raise ValidationError("WeChat article announcements require an mp.weixin.qq.com URL")
        if self.verification_status == self.VerificationStatus.VERIFIED:
            if not self.identity_evidence.strip() or self.last_verified_at is None:
                raise ValidationError("verified announcements require identity evidence and verification time")
            if len(self.content_sha256) != 64 or any(
                character not in "0123456789abcdef"
                for character in self.content_sha256.casefold()
            ):
                raise ValidationError("verified announcements require a SHA-256 content fingerprint")
            if self.source_kind in {self.SourceKind.WEBSITE, self.SourceKind.RECRUITING_SYSTEM} and not self.source_id:
                raise ValidationError("verified official-site announcements require a source")

    def __str__(self) -> str:
        return self.title


class AnnouncementDiscoveryCandidate(models.Model):
    """Temporary, untrusted search result awaiting source verification."""

    class State(models.TextChoices):
        NEW = "new", "待核验"
        VERIFIED = "verified", "已核验"
        MERGED = "merged", "已合并"
        SEPARATE = "separate", "独立批次"
        DISCARDED = "discarded", "已丢弃"
        FAILED = "failed", "读取失败"

    class RouteState(models.TextChoices):
        UNROUTED = "unrouted", "尚未分流"
        KNOWN_OFFICIAL = "known_official", "已知官网"
        KNOWN_ATS = "known_ats", "已知招聘系统"
        SOURCE_IDENTITY_REVIEW_REQUIRED = (
            "source_identity_review_required",
            "来源身份待审查",
        )
        REJECTED = "rejected", "已拒绝"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="announcement_candidates",
    )
    source_kind = models.CharField(max_length=24, choices=RecruitmentAnnouncement.SourceKind.choices)
    url = models.URLField()
    identity_url = models.URLField(blank=True)
    route_state = models.CharField(
        max_length=40,
        choices=RouteState.choices,
        default=RouteState.UNROUTED,
    )
    title_hint = models.CharField(max_length=500, blank=True)
    provider = models.CharField(max_length=64)
    provider_result_id = models.CharField(max_length=128, blank=True)
    state = models.CharField(max_length=16, choices=State.choices, default=State.NEW)
    error_code = models.CharField(max_length=64, blank=True)
    final_url = models.URLField(blank=True)
    content_sha256 = models.CharField(max_length=64, blank=True)
    recruitment_signal_found = models.BooleanField(default=False)
    technical_verified_at = models.DateTimeField(null=True, blank=True)
    announcement = models.ForeignKey(
        RecruitmentAnnouncement,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="discovery_candidates",
    )
    discovered_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "url"],
                name="unique_announcement_candidate_url_per_organization",
            ),
            models.UniqueConstraint(
                fields=["organization", "identity_url"],
                name="unique_announcement_candidate_identity_per_org",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.identity_url:
            self.identity_url = self.url
        return super().save(*args, **kwargs)


class AnnouncementDiscoveryRun(models.Model):
    """One bounded announcement discovery execution."""

    class Status(models.TextChoices):
        COMPLETE = "complete", "完成"
        PARTIAL = "partial", "部分完成"
        FAILED = "failed", "失败"

    criteria = models.JSONField(default=dict)
    status = models.CharField(max_length=16, choices=Status.choices)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField()
    error_code = models.CharField(max_length=64, blank=True)


class AnnouncementDiscoveryOrganizationRun(models.Model):
    """The isolated result for one organization in a discovery run."""

    class Status(models.TextChoices):
        COMPLETE = "complete", "完成"
        DEGRADED = "degraded", "降级完成"
        FAILED = "failed", "失败"

    run = models.ForeignKey(
        AnnouncementDiscoveryRun,
        on_delete=models.PROTECT,
        related_name="organization_runs",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="announcement_discovery_runs",
    )
    status = models.CharField(max_length=16, choices=Status.choices)
    fallback_reason = models.CharField(max_length=64, blank=True)
    error_code = models.CharField(max_length=64, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["run", "organization"],
                name="unique_organization_per_discovery_run",
            ),
        ]


class AnnouncementDiscoveryProviderAttempt(models.Model):
    """Append-only metadata for one logical Provider query attempt."""

    class Status(models.TextChoices):
        SUCCESS = "success", "成功"
        EMPTY = "empty", "空结果"
        TRANSIENT_ERROR = "transient_error", "瞬时错误"
        PERMANENT_ERROR = "permanent_error", "永久错误"
        SKIPPED = "skipped", "跳过"

    organization_run = models.ForeignKey(
        AnnouncementDiscoveryOrganizationRun,
        on_delete=models.PROTECT,
        related_name="provider_attempts",
    )
    provider = models.CharField(max_length=64)
    request_key = models.CharField(max_length=64)
    intent_key = models.CharField(max_length=64)
    query = models.CharField(max_length=500)
    status = models.CharField(max_length=24, choices=Status.choices)
    request_id = models.CharField(max_length=128, blank=True)
    duration_ms = models.PositiveIntegerField(default=0)
    result_count = models.PositiveSmallIntegerField(default=0)
    cost_dollars = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        null=True,
        blank=True,
    )
    error_code = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization_run", "provider", "request_key"],
                name="unique_provider_attempt_per_discovery_query",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("AnnouncementDiscoveryProviderAttempt is append-only")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("AnnouncementDiscoveryProviderAttempt is append-only")


class AnnouncementDiscoveryObservation(models.Model):
    """Append-only record of a Provider returning one announcement candidate."""

    organization_run = models.ForeignKey(
        AnnouncementDiscoveryOrganizationRun,
        on_delete=models.PROTECT,
        related_name="observations",
    )
    candidate = models.ForeignKey(
        AnnouncementDiscoveryCandidate,
        on_delete=models.PROTECT,
        related_name="search_observations",
    )
    intent_key = models.CharField(max_length=64)
    request_key = models.CharField(max_length=64)
    query = models.CharField(max_length=500)
    provider = models.CharField(max_length=64)
    rank = models.PositiveSmallIntegerField()
    result_id = models.CharField(max_length=128)
    title_hint = models.CharField(max_length=500, blank=True)
    backend_date_hint = models.CharField(max_length=64, blank=True)
    snippet_sha256 = models.CharField(max_length=64, blank=True)
    company_signal_found = models.BooleanField(default=False)
    recruitment_signal_found = models.BooleanField(default=False)
    discovered_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "organization_run",
                    "candidate",
                    "provider",
                    "request_key",
                    "result_id",
                ],
                name="unique_discovery_observation_per_run",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("AnnouncementDiscoveryObservation is append-only")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("AnnouncementDiscoveryObservation is append-only")


class RecruitmentPolicy(models.Model):
    """A guarded switch for the one-time announcement-driven cutover."""

    key = models.CharField(max_length=32, unique=True, default="default")
    announcement_gate_enforced = models.BooleanField(default=False)
    preview_digest = models.CharField(max_length=64, blank=True)
    preview_generated_at = models.DateTimeField(null=True, blank=True)
    activated_at = models.DateTimeField(null=True, blank=True)

    @classmethod
    def announcement_gate_is_enforced(cls) -> bool:
        policy = cls.objects.filter(key="default").only("announcement_gate_enforced").first()
        return bool(policy and policy.announcement_gate_enforced)

    def save(self, *args, **kwargs):
        if self.pk:
            previous = type(self).objects.filter(pk=self.pk).values_list(
                "announcement_gate_enforced", flat=True
            ).first()
            if previous and not self.announcement_gate_enforced:
                raise ValidationError("an activated announcement gate cannot be disabled")
        return super().save(*args, **kwargs)


class RecruitmentPolicyEvent(models.Model):
    class EventType(models.TextChoices):
        ACTIVATED = "activated", "公告门控已开启"

    policy = models.ForeignKey(
        RecruitmentPolicy,
        on_delete=models.PROTECT,
        related_name="events",
    )
    event_type = models.CharField(max_length=24, choices=EventType.choices)
    actor_label = models.CharField(max_length=100)
    preview_digest = models.CharField(max_length=64)
    previous_event_hash = models.CharField(max_length=64)
    event_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def calculate_hash(
        *,
        policy_id: int,
        event_type: str,
        actor_label: str,
        preview_digest: str,
        previous_event_hash: str,
    ) -> str:
        payload = json.dumps(
            {
                "policy_id": policy_id,
                "event_type": event_type,
                "actor_label": actor_label,
                "preview_digest": preview_digest,
                "previous_event_hash": previous_event_hash,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("RecruitmentPolicyEvent is append-only")
        self.actor_label = self.actor_label.strip()
        latest = type(self).objects.filter(policy_id=self.policy_id).order_by("-pk").first()
        self.previous_event_hash = latest.event_hash if latest else "0" * 64
        self.event_hash = self.calculate_hash(
            policy_id=self.policy_id,
            event_type=self.event_type,
            actor_label=self.actor_label,
            preview_digest=self.preview_digest,
            previous_event_hash=self.previous_event_hash,
        )
        if (
            not self.actor_label
            or not re.fullmatch(r"[0-9a-f]{64}", self.preview_digest)
        ):
            raise ValidationError("policy event actor and preview digest are required")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("RecruitmentPolicyEvent is append-only")


class SourceAdmissionEvent(models.Model):
    source = models.ForeignKey(
        OfficialSource, on_delete=models.PROTECT, related_name="admission_events"
    )
    from_state = models.CharField(max_length=16, blank=True)
    to_state = models.CharField(max_length=16, choices=OfficialSource.AdmissionState.choices)
    actor_label = models.CharField(max_length=100)
    reason = models.TextField()
    evidence = models.TextField()
    previous_event_hash = models.CharField(max_length=64)
    event_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def calculate_hash(
        *,
        source_id: int,
        from_state: str,
        to_state: str,
        actor_label: str,
        reason: str,
        evidence: str,
        previous_event_hash: str,
    ) -> str:
        payload = json.dumps(
            {
                "source_id": source_id,
                "from_state": from_state,
                "to_state": to_state,
                "actor_label": actor_label,
                "reason": reason,
                "evidence": evidence,
                "previous_event_hash": previous_event_hash,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def clean(self) -> None:
        super().clean()
        if not all(
            str(value or "").strip()
            for value in (self.actor_label, self.reason, self.evidence)
        ):
            raise ValidationError("actor, reason, and evidence are required")
        if not self.source_id:
            return
        source = OfficialSource.objects.get(pk=self.source_id)
        latest = (
            SourceAdmissionEvent.objects.filter(source_id=self.source_id)
            .order_by("-created_at", "-pk")
            .first()
        )
        allowed = {
            OfficialSource.AdmissionState.CANDIDATE: {
                OfficialSource.AdmissionState.VERIFIED
            },
            OfficialSource.AdmissionState.VERIFIED: {
                OfficialSource.AdmissionState.ENABLED
            },
            OfficialSource.AdmissionState.ENABLED: {
                OfficialSource.AdmissionState.SUSPENDED,
                OfficialSource.AdmissionState.REVOKED,
            },
            OfficialSource.AdmissionState.SUSPENDED: {
                OfficialSource.AdmissionState.VERIFIED,
                OfficialSource.AdmissionState.REVOKED,
            },
            OfficialSource.AdmissionState.REVOKED: set(),
        }
        if latest is None and self.from_state == "":
            if (
                source.admission_state != OfficialSource.AdmissionState.CANDIDATE
                or self.to_state != OfficialSource.AdmissionState.CANDIDATE
            ):
                raise ValidationError("invalid initial admission event")
            return
        expected_from = latest.to_state if latest else source.admission_state
        if source.admission_state != expected_from or self.from_state != expected_from:
            raise ValidationError("admission event does not continue the current chain")
        if self.to_state not in allowed[expected_from]:
            raise ValidationError("invalid admission event transition")

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("SourceAdmissionEvent is append-only")
        self.actor_label = self.actor_label.strip()
        self.reason = self.reason.strip()
        self.evidence = self.evidence.strip()
        latest = (
            SourceAdmissionEvent.objects.filter(source_id=self.source_id)
            .order_by("-created_at", "-pk")
            .first()
        )
        self.previous_event_hash = latest.event_hash if latest else "0" * 64
        self.event_hash = self.calculate_hash(
            source_id=self.source_id,
            from_state=self.from_state,
            to_state=self.to_state,
            actor_label=self.actor_label,
            reason=self.reason,
            evidence=self.evidence,
            previous_event_hash=self.previous_event_hash,
        )
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("SourceAdmissionEvent is append-only")


class ApprovedApplicationHost(models.Model):
    source = models.ForeignKey(
        OfficialSource,
        on_delete=models.PROTECT,
        related_name="approved_application_hosts",
    )
    host = models.CharField(max_length=255)
    evidence = models.TextField()
    actor_label = models.CharField(max_length=100)
    admission_event = models.ForeignKey(
        SourceAdmissionEvent,
        on_delete=models.PROTECT,
        related_name="approved_application_hosts",
    )
    approval_digest = models.CharField(max_length=64)
    approved_at = models.DateTimeField(auto_now_add=True)

    def calculate_digest(self) -> str:
        payload = json.dumps(
            {
                "source_id": self.source_id,
                "host": self.host,
                "evidence": self.evidence,
                "actor_label": self.actor_label,
                "admission_event_id": self.admission_event_id,
                "admission_event_hash": self.admission_event.event_hash,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "host"], name="unique_approved_application_host"
            )
        ]

    def clean(self) -> None:
        super().clean()
        if self.admission_event_id and self.source_id:
            if self.admission_event.source_id != self.source_id:
                raise ValidationError("approved host event must belong to its source")
            if (
                self.admission_event.to_state
                != OfficialSource.AdmissionState.VERIFIED
            ):
                raise ValidationError("approved host requires a verified admission event")
        if not all(
            str(value or "").strip()
            for value in (self.host, self.actor_label, self.evidence)
        ):
            raise ValidationError("host, actor, and evidence are required")
        if self.approval_digest and self.approval_digest != self.calculate_digest():
            raise ValidationError("approved host digest does not match its facts")

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("ApprovedApplicationHost is append-only")
        self.host = self.host.strip().lower()
        self.actor_label = self.actor_label.strip()
        self.evidence = self.evidence.strip()
        self.approval_digest = self.calculate_digest()
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("ApprovedApplicationHost is append-only")


class UpdateRun(models.Model):
    class Trigger(models.TextChoices):
        SCHEDULED = "scheduled", "计划任务"
        MANUAL = "manual", "手动更新"

    class Status(models.TextChoices):
        RUNNING = "running", "运行中"
        SUCCESS = "success", "成功"
        PARTIAL_FAILURE = "partial_failure", "部分失败"
        FAILED = "failed", "失败"

    trigger = models.CharField(max_length=16, choices=Trigger.choices)
    scheduled_for_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RUNNING)
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    local_demo_key = models.CharField(max_length=64, blank=True)

    @property
    def is_successful(self) -> bool:
        return self.status in {self.Status.SUCCESS, self.Status.PARTIAL_FAILURE}


class FetchRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = "running", "运行中"
        SUCCESS = "success", "成功"
        UNCHANGED = "unchanged", "内容未变化"
        NOT_MODIFIED = "not_modified", "未变化"
        FAILED = "failed", "失败"

    update_run = models.ForeignKey(UpdateRun, null=True, blank=True, on_delete=models.PROTECT, related_name="fetch_runs")
    source = models.ForeignKey(OfficialSource, on_delete=models.PROTECT, related_name="fetch_runs")
    fetched_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=16, choices=Status.choices)
    http_status = models.PositiveSmallIntegerField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)


class SourceVersion(models.Model):
    source = models.ForeignKey(OfficialSource, on_delete=models.PROTECT, related_name="versions")
    fetch_run = models.OneToOneField(FetchRun, null=True, blank=True, on_delete=models.PROTECT, related_name="source_version")
    canonical_url = models.URLField()
    content_hash = models.CharField(max_length=64)
    etag = models.CharField(max_length=255, blank=True)
    fetched_at = models.DateTimeField(default=timezone.now)
    is_applied = models.BooleanField(default=False)
    applied_at = models.DateTimeField(null=True, blank=True)


class RecruitmentBatchQuerySet(models.QuerySet):
    def formal(self):
        from radar.services.admission import valid_admitted_source_ids
        from radar.services.announcements import (
            announcement_direction_projection_is_complete,
            announcement_evidence_is_complete,
        )
        from radar.services.evidence import batch_projection_has_valid_evidence

        gate_enforced = RecruitmentPolicy.announcement_gate_is_enforced()
        queryset = self.filter(
            source_id__in=valid_admitted_source_ids(),
            organization_id=models.F("source__organization_id"),
            status=RecruitmentBatch.Status.ACTIVE,
        )
        if gate_enforced:
            queryset = queryset.filter(
                announcement_admission=RecruitmentBatch.AnnouncementAdmission.ADMITTED,
                primary_announcement__verification_status=RecruitmentAnnouncement.VerificationStatus.VERIFIED,
                primary_announcement__organization_id=models.F("organization_id"),
            )
        else:
            queryset = queryset.filter(
                latest_publication_event__event_type__in=("published", "updated"),
                latest_publication_event__evidence_complete=True,
                latest_publication_event__source_version__is_applied=True,
                latest_publication_event__batch_id=models.F("pk"),
                latest_publication_event__source_version__source_id=models.F("source_id"),
            )
        verification_queryset = queryset.select_related(
            "source__organization",
            "latest_publication_event__source_version",
            "primary_announcement__organization",
            "primary_announcement__source__organization",
        ).prefetch_related(
            "announcement_evidence",
            "evidence",
            "positions",
            "application_links",
            "source__admission_events",
            "source__approved_application_hosts__admission_event",
            "primary_announcement__source__admission_events",
            "primary_announcement__source__approved_application_hosts__admission_event",
            "primary_announcement__organization__official_sources__organization",
            "primary_announcement__organization__official_sources__admission_events",
            "primary_announcement__organization__official_sources__approved_application_hosts__admission_event",
        )
        valid_ids = [
            batch.pk
            for batch in verification_queryset
            if (
                batch_projection_has_valid_evidence(
                    batch,
                    announcement_fields=gate_enforced,
                )
                if not gate_enforced
                else announcement_evidence_is_complete(batch)
                and (
                    batch_projection_has_valid_evidence(
                        batch,
                        announcement_fields=True,
                    )
                    or announcement_direction_projection_is_complete(batch)
                )
            )
        ]
        return queryset.filter(pk__in=valid_ids).distinct()

    def historical(self):
        from radar.services.admission import valid_historical_source_ids
        from radar.services.announcements import (
            announcement_direction_projection_is_complete,
            announcement_evidence_is_complete,
        )
        from radar.services.evidence import batch_has_trusted_history

        gate_enforced = RecruitmentPolicy.announcement_gate_is_enforced()
        queryset = self.filter(
            source_id__in=valid_historical_source_ids(),
            organization_id=models.F("source__organization_id"),
            status__in=(
                RecruitmentBatch.Status.EXPIRED,
                RecruitmentBatch.Status.WITHDRAWN,
            ),
        )
        if gate_enforced:
            queryset = queryset.filter(
                announcement_admission=RecruitmentBatch.AnnouncementAdmission.ADMITTED,
                primary_announcement__verification_status=RecruitmentAnnouncement.VerificationStatus.VERIFIED,
                primary_announcement__organization_id=models.F("organization_id"),
            )
        valid_ids = [
            batch.pk
            for batch in queryset.select_related("source", "primary_announcement")
            if (
                batch_has_trusted_history(batch)
                if not gate_enforced
                else announcement_evidence_is_complete(batch)
                and (
                    batch_has_trusted_history(batch)
                    or announcement_direction_projection_is_complete(
                        batch,
                        current_only=False,
                    )
                )
            )
        ]
        return queryset.filter(pk__in=valid_ids).distinct()


class RecruitmentBatch(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "招聘中"
        EXPIRED = "expired", "已截止"
        WITHDRAWN = "withdrawn", "已撤回"

    class RecruitmentType(models.TextChoices):
        SPRING = "spring", "春招"
        SPRING_SUPPLEMENT = "spring_supplement", "春招补录"
        SUMMER = "summer", "夏招"
        AUTUMN = "autumn", "秋招"
        AUTUMN_SUPPLEMENT = "autumn_supplement", "秋招补录"
        AUTUMN_EARLY = "autumn_early", "秋招提前批"
        CAMPUS_RECRUITMENT = "campus_recruitment", "校园招聘"
        INTERNSHIP = "internship", "实习"
        SPECIAL_PROGRAM = "special_program", "专项计划"
        OTHER = "other", "其他"
        UNKNOWN = "unknown", "未知"

    class AnnouncementAdmission(models.TextChoices):
        LEGACY = "legacy", "旧规则待迁移"
        ADMITTED = "admitted", "公告已准入"
        PENDING = "pending", "待核验"
        SUPERSEDED = "superseded", "已被精确批次取代"
        EXCLUDED = "excluded", "不进入正式页"

    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="recruitment_batches")
    source = models.ForeignKey(OfficialSource, on_delete=models.PROTECT, related_name="recruitment_batches")
    identity_key = models.CharField(max_length=255)
    title = models.CharField(max_length=300)
    official_page_url = models.URLField()
    primary_announcement = models.ForeignKey(
        RecruitmentAnnouncement,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="recruitment_batches",
    )
    announcement_admission = models.CharField(
        max_length=16,
        choices=AnnouncementAdmission.choices,
        default=AnnouncementAdmission.LEGACY,
    )
    recruitment_type = models.CharField(
        max_length=32,
        choices=RecruitmentType.choices,
        default=RecruitmentType.UNKNOWN,
    )
    target_audience = models.CharField(max_length=200, blank=True)
    published_on = models.DateField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    notes = models.TextField(blank=True)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_verified_at = models.DateTimeField(default=timezone.now)
    latest_publication_event = models.ForeignKey(
        "PublicationEvent",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="current_for_batches",
    )

    objects = RecruitmentBatchQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "identity_key"],
                name="unique_batch_identity_per_source",
            ),
            models.UniqueConstraint(
                fields=["primary_announcement"],
                condition=Q(primary_announcement__isnull=False),
                name="one_batch_per_primary_announcement",
            ),
        ]

    def __str__(self) -> str:
        return self.title

    def clean(self) -> None:
        super().clean()
        if (
            self.primary_announcement_id
            and self.primary_announcement.organization_id != self.organization_id
        ):
            raise ValidationError("primary announcement must belong to the batch organization")
        if self.announcement_admission == self.AnnouncementAdmission.ADMITTED:
            if (
                not self.primary_announcement_id
                or self.primary_announcement.verification_status
                != RecruitmentAnnouncement.VerificationStatus.VERIFIED
            ):
                raise ValidationError("admitted batches require a verified primary announcement")


class AnnouncementFieldEvidence(models.Model):
    """Append-only proof for fields interpreted from the batch's primary notice."""

    batch = models.ForeignKey(
        RecruitmentBatch,
        on_delete=models.PROTECT,
        related_name="announcement_evidence",
    )
    announcement = models.ForeignKey(
        RecruitmentAnnouncement,
        on_delete=models.PROTECT,
        related_name="field_evidence",
    )
    position = models.ForeignKey(
        "RecruitmentPosition",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="announcement_evidence",
    )
    field_name = models.CharField(max_length=64)
    excerpt = models.TextField()
    locator = models.CharField(max_length=500)
    parsed_value = models.TextField()
    value_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("AnnouncementFieldEvidence is append-only")
        self.value_hash = hashlib.sha256(self.parsed_value.encode("utf-8")).hexdigest()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("AnnouncementFieldEvidence is append-only")


class PublicationEvent(models.Model):
    class EventType(models.TextChoices):
        PUBLISHED = "published", "发布"
        UPDATED = "updated", "更新"
        REJECTED = "rejected", "拒绝"
        WITHDRAWN = "withdrawn", "撤回"
        OUT_OF_SCOPE = "out_of_scope", "超出范围"
        AMBIGUOUS = "ambiguous", "身份冲突"

    source_version = models.ForeignKey(
        SourceVersion,
        on_delete=models.PROTECT,
        related_name="publication_events",
    )
    batch = models.ForeignKey(
        RecruitmentBatch,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="publication_events",
    )
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    identity_key = models.CharField(max_length=255)
    candidate_title = models.CharField(max_length=300, blank=True)
    reason_codes = models.JSONField(default=list, blank=True)
    evidence_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("PublicationEvent is append-only")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("PublicationEvent is append-only")


class RecruitmentPosition(models.Model):
    class Kind(models.TextChoices):
        POSITION = "position", "招聘岗位"
        DIRECTION = "direction", "岗位方向"

    batch = models.ForeignKey(RecruitmentBatch, on_delete=models.PROTECT, related_name="positions")
    position_key = models.CharField(max_length=255)
    title = models.CharField(max_length=300)
    location_text = models.CharField(max_length=300)
    normalized_locations = models.JSONField(default=list, blank=True)
    raw_text = models.TextField(blank=True)
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.POSITION)
    source_updated_on = models.DateField(null=True, blank=True)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    content_changed_at = models.DateTimeField(default=timezone.now)
    is_current = models.BooleanField(default=True)
    removed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["batch", "position_key"],
                name="unique_position_identity_per_batch",
            )
        ]


class ApplicationLink(models.Model):
    class LinkType(models.TextChoices):
        BATCH_PAGE = "batch_page", "招聘批次官方页面"
        APPLICATION = "application", "投递入口"
        EMAIL = "email", "招聘邮箱"
        MINI_PROGRAM = "mini_program", "投递小程序"

    batch = models.ForeignKey(RecruitmentBatch, on_delete=models.PROTECT, related_name="application_links")
    position = models.ForeignKey(RecruitmentPosition, null=True, blank=True, on_delete=models.PROTECT, related_name="application_links")
    url = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    miniprogram_name = models.CharField(max_length=200, blank=True)
    miniprogram_path = models.CharField(max_length=500, blank=True)
    instructions = models.CharField(max_length=500, blank=True)
    verification_evidence = models.TextField(blank=True)
    link_type = models.CharField(max_length=16, choices=LinkType.choices)
    verified_at = models.DateTimeField(default=timezone.now)
    is_current = models.BooleanField(default=True)
    removed_at = models.DateTimeField(null=True, blank=True)

    @property
    def href(self) -> str:
        if self.link_type == self.LinkType.EMAIL and self.email:
            return f"mailto:{self.email}"
        return self.url

    def clean(self) -> None:
        super().clean()
        if self.link_type == self.LinkType.EMAIL:
            if not self.email or self.url or self.miniprogram_name or self.miniprogram_path:
                raise ValidationError("email application links require only an email address")
        elif self.link_type == self.LinkType.MINI_PROGRAM:
            if not self.miniprogram_name.strip() or self.email:
                raise ValidationError("mini-program application links require a name and no email")
            if not (self.url or self.miniprogram_path.strip() or self.instructions.strip()):
                raise ValidationError("mini-program application links require an opening instruction")
        elif not self.url or self.email or self.miniprogram_name or self.miniprogram_path:
            raise ValidationError("non-email application links require a URL")
        if self.position_id is None and not self.verification_evidence.strip():
            raise ValidationError("batch-level application channels require verification evidence")


class Evidence(models.Model):
    batch = models.ForeignKey(RecruitmentBatch, on_delete=models.PROTECT, related_name="evidence")
    source_version = models.ForeignKey(SourceVersion, on_delete=models.PROTECT, related_name="evidence")
    publication_event = models.ForeignKey(
        PublicationEvent, on_delete=models.PROTECT, related_name="evidence"
    )
    position = models.ForeignKey(RecruitmentPosition, null=True, blank=True, on_delete=models.PROTECT, related_name="evidence")
    application_link = models.ForeignKey(ApplicationLink, null=True, blank=True, on_delete=models.PROTECT, related_name="evidence")
    field_name = models.CharField(max_length=64)
    excerpt = models.TextField()
    locator = models.CharField(max_length=500)
    raw_value = models.TextField()
    parsed_value = models.TextField()
    value_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Evidence is append-only")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Evidence is append-only")


class ApplicationProgress(models.Model):
    class Status(models.TextChoices):
        NOT_APPLIED = "not_applied", "未投递"
        APPLIED = "applied", "已投递"
        WRITTEN_TEST = "written_test", "已笔试"
        INTERVIEWED = "interviewed", "已面试"
        REJECTED = "rejected", "未通过"
        PASSED_INTERVIEW = "passed_interview", "面试通过"
        NOT_APPLYING = "not_applying", "暂不投递"

    batch = models.OneToOneField(RecruitmentBatch, on_delete=models.PROTECT, related_name="application_progress")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_APPLIED)
    updated_at = models.DateTimeField(auto_now=True)
