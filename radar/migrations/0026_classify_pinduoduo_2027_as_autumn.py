import hashlib

from django.db import migrations


IDENTITY_KEY = "phase-02:p11"
AUTUMN_EXCERPT = "2027届校园招聘；官方岗位列表发布日期为2026年7月，属于下一届秋招窗口"
AUTUMN_LOCATOR = "body/section[校招项目]/item[2027届校园招聘]+official-job-list[2026-07]"


def classify_pinduoduo_as_autumn(apps, schema_editor):
    RecruitmentBatch = apps.get_model("radar", "RecruitmentBatch")
    AnnouncementFieldEvidence = apps.get_model("radar", "AnnouncementFieldEvidence")
    batch = RecruitmentBatch.objects.filter(
        identity_key=IDENTITY_KEY,
        organization__official_domain="pddglobalhr.com",
        announcement_admission="admitted",
        primary_announcement__isnull=False,
    ).first()
    if batch is None or batch.recruitment_type == "autumn":
        return
    AnnouncementFieldEvidence.objects.create(
        batch=batch,
        announcement_id=batch.primary_announcement_id,
        field_name="recruitment_type",
        excerpt=AUTUMN_EXCERPT,
        locator=AUTUMN_LOCATOR,
        parsed_value="autumn",
        value_hash=hashlib.sha256(b"autumn").hexdigest(),
    )
    batch.recruitment_type = "autumn"
    batch.save(update_fields=["recruitment_type"])


def restore_generic_campus_type(apps, schema_editor):
    RecruitmentBatch = apps.get_model("radar", "RecruitmentBatch")
    AnnouncementFieldEvidence = apps.get_model("radar", "AnnouncementFieldEvidence")
    batch = RecruitmentBatch.objects.filter(
        identity_key=IDENTITY_KEY,
        organization__official_domain="pddglobalhr.com",
        recruitment_type="autumn",
        primary_announcement__isnull=False,
    ).first()
    if batch is None:
        return
    parsed_value = "campus_recruitment"
    AnnouncementFieldEvidence.objects.create(
        batch=batch,
        announcement_id=batch.primary_announcement_id,
        field_name="recruitment_type",
        excerpt="校招项目 应届生招聘 2027届校园招聘",
        locator="body/section[校招项目]/item[应届生招聘]",
        parsed_value=parsed_value,
        value_hash=hashlib.sha256(parsed_value.encode()).hexdigest(),
    )
    batch.recruitment_type = parsed_value
    batch.save(update_fields=["recruitment_type"])


class Migration(migrations.Migration):

    dependencies = [
        ("radar", "0025_add_summer_recruitment_type"),
    ]

    operations = [
        migrations.RunPython(classify_pinduoduo_as_autumn, restore_generic_campus_type),
    ]
