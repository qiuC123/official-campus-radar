import hashlib
import json

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Organization(models.Model):
    class CompanyType(models.TextChoices):
        INTERNET = "internet", "互联网/科技"
        STATE_OWNED = "state_owned", "央企/国企"
        OTHER = "other", "其他"

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
        from radar.services.evidence import batch_projection_has_valid_evidence

        queryset = self.filter(
            source_id__in=valid_admitted_source_ids(),
            organization_id=models.F("source__organization_id"),
            latest_publication_event__event_type__in=("published", "updated"),
            latest_publication_event__evidence_complete=True,
            latest_publication_event__source_version__is_applied=True,
            latest_publication_event__batch_id=models.F("pk"),
            latest_publication_event__source_version__source_id=models.F(
                "source_id"
            ),
        )
        valid_ids = [
            batch.pk
            for batch in queryset.select_related(
                "latest_publication_event__source_version"
            )
            if batch_projection_has_valid_evidence(batch)
        ]
        return queryset.filter(pk__in=valid_ids).distinct()

    def historical(self):
        from radar.services.admission import valid_historical_source_ids
        from radar.services.evidence import batch_has_trusted_history

        queryset = self.filter(
            source_id__in=valid_historical_source_ids(),
            organization_id=models.F("source__organization_id"),
            status__in=(
                RecruitmentBatch.Status.EXPIRED,
                RecruitmentBatch.Status.WITHDRAWN,
            ),
        )
        valid_ids = [
            batch.pk
            for batch in queryset.select_related("source")
            if batch_has_trusted_history(batch)
        ]
        return queryset.filter(pk__in=valid_ids).distinct()


class RecruitmentBatch(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "招聘中"
        EXPIRED = "expired", "已截止"
        WITHDRAWN = "withdrawn", "已撤回"

    class RecruitmentType(models.TextChoices):
        CAMPUS_RECRUITMENT = "campus_recruitment", "校园招聘"
        INTERNSHIP = "internship", "实习"
        OTHER = "other", "其他"
        UNKNOWN = "unknown", "未知"

    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="recruitment_batches")
    source = models.ForeignKey(OfficialSource, on_delete=models.PROTECT, related_name="recruitment_batches")
    identity_key = models.CharField(max_length=255)
    title = models.CharField(max_length=300)
    official_page_url = models.URLField()
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
                fields=["source", "official_page_url"],
                name="unique_batch_url_per_source",
            ),
        ]

    def __str__(self) -> str:
        return self.title


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
    batch = models.ForeignKey(RecruitmentBatch, on_delete=models.PROTECT, related_name="positions")
    position_key = models.CharField(max_length=255)
    title = models.CharField(max_length=300)
    location_text = models.CharField(max_length=300)
    normalized_locations = models.JSONField(default=list, blank=True)
    raw_text = models.TextField(blank=True)
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

    batch = models.ForeignKey(RecruitmentBatch, on_delete=models.PROTECT, related_name="application_links")
    position = models.ForeignKey(RecruitmentPosition, null=True, blank=True, on_delete=models.PROTECT, related_name="application_links")
    url = models.URLField()
    link_type = models.CharField(max_length=16, choices=LinkType.choices)
    verified_at = models.DateTimeField(default=timezone.now)
    is_current = models.BooleanField(default=True)
    removed_at = models.DateTimeField(null=True, blank=True)


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
