import hashlib

from django.db import migrations


SEASON_CLASSIFICATIONS = (
    {
        "company": "腾讯",
        "domain": "qq.com",
        "identity_key": "official-project:tencent:project:14",
        "previous_type": "special_program",
        "season_type": "autumn",
        "excerpt": (
            "腾讯2027校园招聘启动公告&FAQ于2026年8月11日发布；"
            "官网在同一2027校园招聘项目页列出青云计划（应届生）"
        ),
        "locator": (
            "official-campaign[腾讯2027校园招聘]/"
            "announcement[2026-08-11]+project[id=14]"
        ),
    },
    {
        "company": "腾讯",
        "domain": "qq.com",
        "identity_key": "official-project:tencent:project:9",
        "previous_type": "special_program",
        "season_type": "autumn",
        "excerpt": (
            "腾讯2027校园招聘启动公告&FAQ于2026年8月11日发布；"
            "官网在同一2027校园招聘项目页列出AI产品经理培训生"
        ),
        "locator": (
            "official-campaign[腾讯2027校园招聘]/"
            "announcement[2026-08-11]+project[id=9]"
        ),
    },
    {
        "company": "大疆创新",
        "domain": "dji.com",
        "identity_key": "official-project:dji:tuojiangzhe:2027",
        "previous_type": "campus_recruitment",
        "season_type": "autumn_early",
        "excerpt": "2027拓疆者校园招聘；2026年6月25日开启，招满即止",
        "locator": (
            "official-campaign[2027拓疆者校园招聘]/"
            "started[2026-06-25]/classification[autumn_early]"
        ),
    },
)


def classify_campaign_seasons(apps, schema_editor):
    RecruitmentBatch = apps.get_model("radar", "RecruitmentBatch")
    AnnouncementFieldEvidence = apps.get_model(
        "radar", "AnnouncementFieldEvidence"
    )
    for item in SEASON_CLASSIFICATIONS:
        batch = RecruitmentBatch.objects.filter(
            identity_key=item["identity_key"],
            organization__name=item["company"],
            organization__official_domain=item["domain"],
            announcement_admission="admitted",
            primary_announcement__isnull=False,
            recruitment_type=item["previous_type"],
        ).first()
        if batch is None:
            continue
        evidence_exists = AnnouncementFieldEvidence.objects.filter(
            batch_id=batch.pk,
            announcement_id=batch.primary_announcement_id,
            field_name="recruitment_type",
            locator=item["locator"],
            parsed_value=item["season_type"],
        ).exists()
        if not evidence_exists:
            AnnouncementFieldEvidence.objects.create(
                batch_id=batch.pk,
                announcement_id=batch.primary_announcement_id,
                field_name="recruitment_type",
                excerpt=item["excerpt"],
                locator=item["locator"],
                parsed_value=item["season_type"],
                value_hash=hashlib.sha256(
                    item["season_type"].encode("utf-8")
                ).hexdigest(),
            )
        batch.recruitment_type = item["season_type"]
        batch.save(update_fields=["recruitment_type"])


def restore_previous_types(apps, schema_editor):
    RecruitmentBatch = apps.get_model("radar", "RecruitmentBatch")
    AnnouncementFieldEvidence = apps.get_model(
        "radar", "AnnouncementFieldEvidence"
    )
    for item in SEASON_CLASSIFICATIONS:
        batch = RecruitmentBatch.objects.filter(
            identity_key=item["identity_key"],
            organization__name=item["company"],
            organization__official_domain=item["domain"],
            recruitment_type=item["season_type"],
            primary_announcement__isnull=False,
        ).first()
        if batch is None:
            continue
        reverse_locator = f"migration-reverse/{item['locator']}"
        evidence_exists = AnnouncementFieldEvidence.objects.filter(
            batch_id=batch.pk,
            announcement_id=batch.primary_announcement_id,
            field_name="recruitment_type",
            locator=reverse_locator,
            parsed_value=item["previous_type"],
        ).exists()
        if not evidence_exists:
            AnnouncementFieldEvidence.objects.create(
                batch_id=batch.pk,
                announcement_id=batch.primary_announcement_id,
                field_name="recruitment_type",
                excerpt="恢复迁移前的招聘类型",
                locator=reverse_locator,
                parsed_value=item["previous_type"],
                value_hash=hashlib.sha256(
                    item["previous_type"].encode("utf-8")
                ).hexdigest(),
            )
        batch.recruitment_type = item["previous_type"]
        batch.save(update_fields=["recruitment_type"])


class Migration(migrations.Migration):
    dependencies = [
        ("radar", "0028_classify_tencent_2027_main_campaign_as_autumn"),
    ]

    operations = [
        migrations.RunPython(classify_campaign_seasons, restore_previous_types),
    ]
