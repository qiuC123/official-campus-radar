import hashlib

from django.db import migrations


COMPANY = "腾讯"
DOMAIN = "qq.com"
IDENTITY_KEY = "official-project:tencent:project:1"
PREVIOUS_TYPE = "campus_recruitment"
AUTUMN_EXCERPT = (
    "腾讯2027校园招聘启动公告&FAQ；官网公告列表显示"
    "2026年8月11日10:00发布"
)
AUTUMN_LOCATOR = (
    "official-announcement-list/腾讯2027校园招聘启动公告&FAQ/"
    "published[2026-08-11T10:00:00]"
)


def classify_tencent_main_campaign_as_autumn(apps, schema_editor):
    RecruitmentBatch = apps.get_model("radar", "RecruitmentBatch")
    AnnouncementFieldEvidence = apps.get_model(
        "radar", "AnnouncementFieldEvidence"
    )
    batch = RecruitmentBatch.objects.filter(
        identity_key=IDENTITY_KEY,
        organization__name=COMPANY,
        organization__official_domain=DOMAIN,
        announcement_admission="admitted",
        primary_announcement__isnull=False,
        recruitment_type=PREVIOUS_TYPE,
    ).first()
    if batch is None:
        return
    evidence_exists = AnnouncementFieldEvidence.objects.filter(
        batch_id=batch.pk,
        announcement_id=batch.primary_announcement_id,
        field_name="recruitment_type",
        locator=AUTUMN_LOCATOR,
        parsed_value="autumn",
    ).exists()
    if not evidence_exists:
        AnnouncementFieldEvidence.objects.create(
            batch_id=batch.pk,
            announcement_id=batch.primary_announcement_id,
            field_name="recruitment_type",
            excerpt=AUTUMN_EXCERPT,
            locator=AUTUMN_LOCATOR,
            parsed_value="autumn",
            value_hash=hashlib.sha256(b"autumn").hexdigest(),
        )
    batch.recruitment_type = "autumn"
    batch.save(update_fields=["recruitment_type"])


def restore_tencent_main_campaign_type(apps, schema_editor):
    RecruitmentBatch = apps.get_model("radar", "RecruitmentBatch")
    AnnouncementFieldEvidence = apps.get_model(
        "radar", "AnnouncementFieldEvidence"
    )
    batch = RecruitmentBatch.objects.filter(
        identity_key=IDENTITY_KEY,
        organization__name=COMPANY,
        organization__official_domain=DOMAIN,
        recruitment_type="autumn",
        primary_announcement__isnull=False,
    ).first()
    if batch is None:
        return
    reverse_locator = f"migration-reverse/{AUTUMN_LOCATOR}"
    evidence_exists = AnnouncementFieldEvidence.objects.filter(
        batch_id=batch.pk,
        announcement_id=batch.primary_announcement_id,
        field_name="recruitment_type",
        locator=reverse_locator,
        parsed_value=PREVIOUS_TYPE,
    ).exists()
    if not evidence_exists:
        AnnouncementFieldEvidence.objects.create(
            batch_id=batch.pk,
            announcement_id=batch.primary_announcement_id,
            field_name="recruitment_type",
            excerpt="恢复迁移前的腾讯主校招类型",
            locator=reverse_locator,
            parsed_value=PREVIOUS_TYPE,
            value_hash=hashlib.sha256(PREVIOUS_TYPE.encode("utf-8")).hexdigest(),
        )
    batch.recruitment_type = PREVIOUS_TYPE
    batch.save(update_fields=["recruitment_type"])


class Migration(migrations.Migration):
    dependencies = [
        ("radar", "0027_classify_verified_2027_autumn_batches"),
    ]

    operations = [
        migrations.RunPython(
            classify_tencent_main_campaign_as_autumn,
            restore_tencent_main_campaign_type,
        ),
    ]
