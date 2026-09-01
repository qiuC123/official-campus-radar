import hashlib
import json

from django.db import migrations
from django.utils import timezone


PAGE_SNAPSHOTS = {
    "lixiang": {
        "url": "https://www.lixiang.com/employ/campus/preach.html?type=1&fromJob=1",
        "content_sha256": "dca640379cb11e689cd6a47be6a3ab08ac2d3cb77fd5e1229372255fb6165e90",
        "evidence": "理想汽车官网招聘动态页展示校园招聘活动与“理想+”技术沙龙",
    },
    "midea": {
        "url": "https://careers.midea.com/schoolOut/home",
        "content_sha256": "3f5bb820f6f01264d40eea82bc2674127fbbd9833ce48daf556f85cd69671445",
        "evidence": "美的校园招聘官网首页明确列出应届博士、应届生和实习生招聘对象",
    },
    "tencent": {
        "url": "https://join.qq.com/",
        "content_sha256": "87e0519f78a97d4767894f066629081c049c8d9b97ea4c9991aab35b63a8c4a1",
        "evidence": "腾讯校招首页明确列出实习生招聘、人才专项和2027校园招聘公告",
    },
}


ANNOUNCEMENT_MAPPINGS = (
    ("理想汽车", "official-project:lixiang:25", "lixiang"),
    ("理想汽车", "official-project:lixiang:24", "lixiang"),
    ("理想汽车", "official-project:lixiang:23", "lixiang"),
    ("美的集团", "official-project:midea:2027-star", "midea"),
    ("美的集团", "official-project:midea:2027-doctor", "midea"),
    ("美的集团", "phase-02:p17", "midea"),
    ("腾讯", "official-project:tencent:project:2", "tencent"),
    ("腾讯", "official-project:tencent:projects:4-12", "tencent"),
    ("腾讯", "official-project:tencent:project:20", "tencent"),
)


PREVIOUS_URLS = {
    "official-project:lixiang:25": "https://www.lixiang.com/employ/campus/list.html?project_id=25",
    "official-project:lixiang:24": "https://www.lixiang.com/employ/campus/list.html?project_id=24",
    "official-project:lixiang:23": "https://www.lixiang.com/employ/campus/list.html?project_id=23",
    "official-project:midea:2027-star": "https://careers.midea.com/schoolOut/post?type=1",
    "official-project:midea:2027-doctor": "https://careers.midea.com/schoolOut/post?type=5",
    "phase-02:p17": "https://careers.midea.com/schoolOut/post?type=2",
    "official-project:tencent:project:2": "https://join.qq.com/post.html?query=p_2",
    "official-project:tencent:projects:4-12": "https://join.qq.com/post.html?query=p_104",
    "official-project:tencent:project:20": "https://join.qq.com/post.html?query=p_20",
}


def _evidence_hash(batch_identity, page):
    payload = json.dumps(
        {
            "batch_identity": batch_identity,
            "content_sha256": page["content_sha256"],
            "url": page["url"],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def separate_announcement_urls(apps, schema_editor):
    RecruitmentBatch = apps.get_model("radar", "RecruitmentBatch")
    verified_at = timezone.now()
    for company, batch_identity, page_key in ANNOUNCEMENT_MAPPINGS:
        batch = RecruitmentBatch.objects.filter(
            organization__name=company,
            identity_key=batch_identity,
            primary_announcement__isnull=False,
        ).select_related("primary_announcement").first()
        if batch is None:
            continue
        page = PAGE_SNAPSHOTS[page_key]
        announcement = batch.primary_announcement
        announcement.url = page["url"]
        announcement.last_verified_at = verified_at
        announcement.identity_evidence = page["evidence"]
        announcement.content_sha256 = page["content_sha256"]
        announcement.evidence_sha256 = _evidence_hash(batch_identity, page)
        announcement.verification_status = "verified"
        announcement.verification_method = "browser"
        announcement.save(
            update_fields=[
                "url",
                "last_verified_at",
                "identity_evidence",
                "content_sha256",
                "evidence_sha256",
                "verification_status",
                "verification_method",
            ]
        )


def restore_previous_announcement_urls(apps, schema_editor):
    RecruitmentBatch = apps.get_model("radar", "RecruitmentBatch")
    for company, batch_identity, _ in ANNOUNCEMENT_MAPPINGS:
        batch = RecruitmentBatch.objects.filter(
            organization__name=company,
            identity_key=batch_identity,
            primary_announcement__isnull=False,
        ).select_related("primary_announcement").first()
        if batch is None:
            continue
        announcement = batch.primary_announcement
        announcement.url = PREVIOUS_URLS[batch_identity]
        announcement.verification_method = "http"
        announcement.save(update_fields=["url", "verification_method"])


class Migration(migrations.Migration):
    dependencies = [
        ("radar", "0031_admit_first_official_site_group"),
    ]

    operations = [
        migrations.RunPython(
            separate_announcement_urls,
            restore_previous_announcement_urls,
        ),
    ]
