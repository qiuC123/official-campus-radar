import hashlib

from django.db import migrations
from django.utils import timezone


TENCENT_INTERNSHIP_BATCHES = (
    {
        "identity_key": "official-project:tencent:project:2",
        "announcement_identity": "official-project:tencent:announcement:project:2",
        "title": "腾讯 2026 应届实习招聘",
        "url": "https://join.qq.com/post.html?query=p_2",
        "target_audience": "毕业时间为2026年9月至2027年12月",
        "title_excerpt": "实习生招聘；2026实习生招聘；应届实习",
        "audience_excerpt": "毕业时间：2026年9月1日-2027年12月31日",
        "locator": "official-project-mapping[mappingId=2,projectId=2]",
    },
    {
        "identity_key": "official-project:tencent:projects:4-12",
        "announcement_identity": "official-project:tencent:announcement:mapping:104",
        "title": "腾讯日常实习招聘",
        "url": "https://join.qq.com/post.html?query=p_104",
        "target_audience": "全体在校生",
        "title_excerpt": "实习生招聘；日常实习",
        "audience_excerpt": "面向全体在校生，提供实习机会",
        "locator": "official-project-mapping[mappingId=104,projectId=4|12]",
    },
    {
        "identity_key": "official-project:tencent:project:20",
        "announcement_identity": "official-project:tencent:announcement:project:20",
        "title": "腾讯青云计划（实习生）",
        "url": "https://join.qq.com/post.html?query=p_20",
        "target_audience": "毕业时间为2026年9月以后",
        "title_excerpt": "人才专项；青云计划-实习生",
        "audience_excerpt": "毕业时间：2026年9月以后毕业的本硕博同学",
        "locator": "official-project-mapping[mappingId=20,projectId=20]",
    },
)


def _value_hash(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def add_tencent_internship_batches(apps, schema_editor):
    OfficialSource = apps.get_model("radar", "OfficialSource")
    RecruitmentAnnouncement = apps.get_model("radar", "RecruitmentAnnouncement")
    RecruitmentBatch = apps.get_model("radar", "RecruitmentBatch")
    AnnouncementFieldEvidence = apps.get_model(
        "radar", "AnnouncementFieldEvidence"
    )
    source = OfficialSource.objects.filter(
        organization__name="腾讯",
        organization__official_domain="qq.com",
        adapter_name="json_api",
    ).first()
    if source is None:
        return
    verified_at = timezone.now()
    for item in TENCENT_INTERNSHIP_BATCHES:
        fingerprint = hashlib.sha256(
            (
                f"{item['title']}|{item['target_audience']}|"
                f"{item['url']}|{item['locator']}"
            ).encode("utf-8")
        ).hexdigest()
        announcement, _ = RecruitmentAnnouncement.objects.update_or_create(
            organization_id=source.organization_id,
            source_kind="recruiting_system",
            identity_key=item["announcement_identity"],
            defaults={
                "source_id": source.pk,
                "title": item["title"],
                "url": item["url"],
                "last_verified_at": verified_at,
                "identity_evidence": (
                    "腾讯官网首页招聘项目与官方 getProjectMapping 接口的稳定映射"
                ),
                "content_sha256": fingerprint,
                "evidence_sha256": fingerprint,
                "verification_status": "verified",
                "verification_method": "http",
            },
        )
        batch, _ = RecruitmentBatch.objects.update_or_create(
            source_id=source.pk,
            identity_key=item["identity_key"],
            defaults={
                "organization_id": source.organization_id,
                "title": item["title"],
                "official_page_url": item["url"],
                "primary_announcement_id": announcement.pk,
                "announcement_admission": "admitted",
                "recruitment_type": "internship",
                "target_audience": item["target_audience"],
                "status": "active",
            },
        )
        fields = {
            "title": (item["title"], item["title_excerpt"], "title"),
            "recruitment_type": (
                "internship",
                item["title_excerpt"],
                "recruitment-type",
            ),
            "target_audience": (
                item["target_audience"],
                item["audience_excerpt"],
                "target-audience",
            ),
            "availability": ("active", "立即投递", "availability"),
        }
        for field_name, (parsed_value, excerpt, suffix) in fields.items():
            locator = f"{item['locator']}/{suffix}"
            AnnouncementFieldEvidence.objects.get_or_create(
                batch_id=batch.pk,
                announcement_id=announcement.pk,
                field_name=field_name,
                locator=locator,
                parsed_value=parsed_value,
                defaults={
                    "excerpt": excerpt,
                    "value_hash": _value_hash(parsed_value),
                },
            )


def exclude_tencent_internship_batches(apps, schema_editor):
    RecruitmentBatch = apps.get_model("radar", "RecruitmentBatch")
    RecruitmentBatch.objects.filter(
        organization__name="腾讯",
        identity_key__in=[
            item["identity_key"] for item in TENCENT_INTERNSHIP_BATCHES
        ],
    ).update(announcement_admission="excluded")


class Migration(migrations.Migration):
    dependencies = [
        ("radar", "0029_classify_shared_campaign_projects_and_dji_early_autumn"),
    ]

    operations = [
        migrations.RunPython(
            add_tencent_internship_batches,
            exclude_tencent_internship_batches,
        ),
    ]
