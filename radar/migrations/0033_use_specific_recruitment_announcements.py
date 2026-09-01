import hashlib
import json

from django.db import migrations
from django.utils import timezone


SPECIFIC_ANNOUNCEMENTS = {
    "official-project:tencent:project:1": {
        "url": "https://join.qq.com/detail.html?id=288",
        "verification_method": "http",
        "evidence": (
            "腾讯官方《腾讯2027校园招聘启动公告&FAQ》明确宣布2027校园招聘启动，"
            "并指引选择“应届毕业生-2027校园招聘”项目"
        ),
        "snapshot": (
            "腾讯2027校园招聘启动公告&FAQ|2026-08-11|"
            "应届毕业生-2027校园招聘|毕业时间2026-01至2027-12"
        ),
    },
    "official-project:midea:2027-star": {
        "url": (
            "https://careers.midea.com/schoolOut/noticeDetail"
            "?noticeId=8b8b3421a048420201a048aa9e0501dc"
        ),
        "verification_method": "browser",
        "evidence": "美的校园招聘官网发布《2027届美的校园招聘公告》",
        "snapshot": (
            "2027届美的校园招聘公告|2026-08-28|"
            "announcementId=8b8b3421a048420201a048aa9e0501dc"
        ),
    },
    "official-project:midea:2027-doctor": {
        "url": (
            "https://careers.midea.com/schoolOut/noticeDetail"
            "?noticeId=8b8b3421a048420201a048aa9e0501dc"
        ),
        "verification_method": "browser",
        "evidence": "美的校园招聘官网发布《2027届美的校园招聘公告》",
        "snapshot": (
            "2027届美的校园招聘公告|2026-08-28|"
            "announcementId=8b8b3421a048420201a048aa9e0501dc"
        ),
    },
}


APPLICATION_FALLBACKS = {
    "official-project:tencent:project:2": (
        "https://join.qq.com/post.html?query=p_2"
    ),
    "official-project:tencent:projects:4-12": (
        "https://join.qq.com/post.html?query=p_104"
    ),
    "official-project:tencent:project:14": (
        "https://join.qq.com/post.html?query=p_14"
    ),
    "official-project:tencent:project:20": (
        "https://join.qq.com/post.html?query=p_20"
    ),
    "official-project:tencent:project:9": (
        "https://join.qq.com/post.html?query=p_9"
    ),
    "phase-02:p17": "https://careers.midea.com/schoolOut/post?type=2",
}


PREVIOUS_URLS = {
    "official-project:tencent:project:1": "https://join.qq.com/",
    "official-project:tencent:project:2": "https://join.qq.com/",
    "official-project:tencent:projects:4-12": "https://join.qq.com/",
    "official-project:tencent:project:14": "https://join.qq.com/",
    "official-project:tencent:project:20": "https://join.qq.com/",
    "official-project:tencent:project:9": "https://join.qq.com/",
    "official-project:midea:2027-star": (
        "https://careers.midea.com/schoolOut/home"
    ),
    "official-project:midea:2027-doctor": (
        "https://careers.midea.com/schoolOut/home"
    ),
    "phase-02:p17": "https://careers.midea.com/schoolOut/home",
}


def _hash(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _evidence_hash(identity_key, url, content_sha256):
    payload = json.dumps(
        {
            "batch_identity": identity_key,
            "content_sha256": content_sha256,
            "url": url,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return _hash(payload)


def _update_announcement(batch, *, url, method, evidence, snapshot, verified_at):
    announcement = batch.primary_announcement
    content_sha256 = _hash(snapshot)
    announcement.url = url
    announcement.last_verified_at = verified_at
    announcement.identity_evidence = evidence
    announcement.content_sha256 = content_sha256
    announcement.evidence_sha256 = _evidence_hash(
        batch.identity_key,
        url,
        content_sha256,
    )
    announcement.verification_status = "verified"
    announcement.verification_method = method
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


def use_specific_recruitment_announcements(apps, schema_editor):
    RecruitmentBatch = apps.get_model("radar", "RecruitmentBatch")
    verified_at = timezone.now()

    batches = {
        batch.identity_key: batch
        for batch in RecruitmentBatch.objects.filter(
            identity_key__in=[
                *SPECIFIC_ANNOUNCEMENTS,
                *APPLICATION_FALLBACKS,
            ],
            primary_announcement__isnull=False,
        ).select_related("primary_announcement")
    }

    for identity_key, page in SPECIFIC_ANNOUNCEMENTS.items():
        batch = batches.get(identity_key)
        if batch is None:
            continue
        _update_announcement(
            batch,
            url=page["url"],
            method=page["verification_method"],
            evidence=page["evidence"],
            snapshot=page["snapshot"],
            verified_at=verified_at,
        )

    for identity_key, url in APPLICATION_FALLBACKS.items():
        batch = batches.get(identity_key)
        if batch is None:
            continue
        _update_announcement(
            batch,
            url=url,
            method="http",
            evidence=(
                "官网公告列表未发现与该独立招聘计划匹配的当前公告；"
                "按公告入口优先级回退到该计划的官方岗位投递页"
            ),
            snapshot=f"official-application-fallback|{identity_key}|{url}",
            verified_at=verified_at,
        )


def restore_general_recruitment_pages(apps, schema_editor):
    RecruitmentBatch = apps.get_model("radar", "RecruitmentBatch")
    batches = RecruitmentBatch.objects.filter(
        identity_key__in=PREVIOUS_URLS,
        primary_announcement__isnull=False,
    ).select_related("primary_announcement")
    for batch in batches:
        announcement = batch.primary_announcement
        announcement.url = PREVIOUS_URLS[batch.identity_key]
        announcement.verification_method = "browser"
        announcement.save(update_fields=["url", "verification_method"])


class Migration(migrations.Migration):
    dependencies = [
        ("radar", "0032_separate_announcement_and_application_urls"),
    ]

    operations = [
        migrations.RunPython(
            use_specific_recruitment_announcements,
            restore_general_recruitment_pages,
        ),
    ]
