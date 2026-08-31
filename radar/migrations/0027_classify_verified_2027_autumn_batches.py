import hashlib

from django.db import migrations


AUTUMN_CLASSIFICATIONS = (
    {
        "company": "OPPO",
        "domain": "oppo.com",
        "identity_key": "phase-02:p12",
        "previous_type": "campus_recruitment",
        "excerpt": (
            "应届生（2027届应届生校园招聘）；官方应届生岗位自"
            "2026年7月15日起发布"
        ),
        "locator": (
            "official-job-list[recruitType=Graduate]/"
            "campaign[2027届应届生校园招聘]/published[2026-07-15]"
        ),
    },
    {
        "company": "中国电信集团有限公司",
        "domain": "chinatelecom.com.cn",
        "identity_key": "phase-02:s03",
        "previous_type": "campus_recruitment",
        "excerpt": (
            "2027年度校园招聘；2026年8月24日起查看招聘信息并进行网上申请"
        ),
        "locator": "official-announcement/招聘流程/网上报名[2026-08-24]",
    },
    {
        "company": "中国联合网络通信集团有限公司",
        "domain": "chinaunicom.com.cn",
        "identity_key": "phase-02:s04",
        "previous_type": "campus_recruitment",
        "excerpt": (
            "中国联通2027校园招聘；官方岗位来源于2026年8月25日起发布当前岗位"
        ),
        "locator": (
            "official-job-source[2027校园招聘]/"
            "positions/source-updated-on[min=2026-08-25]"
        ),
    },
    {
        "company": "京东",
        "domain": "jd.com",
        "identity_key": "official-project:jd:plan:56",
        "previous_type": "special_program",
        "excerpt": "2027校园招聘新星计划；网申/内推时间为8月3日至11月30日",
        "locator": "2027校园招聘/人才项目/新星计划/网申[08-03..11-30]",
    },
    {
        "company": "京东",
        "domain": "jd.com",
        "identity_key": "official-project:jd:plan:57",
        "previous_type": "special_program",
        "excerpt": "2027校园招聘TET管理培训生；网申/内推时间为7月1日至11月30日",
        "locator": "2027校园招聘/人才项目/TET管理培训生/网申[07-01..11-30]",
    },
    {
        "company": "京东",
        "domain": "jd.com",
        "identity_key": "official-project:jd:plan:58",
        "previous_type": "special_program",
        "excerpt": "2027校园招聘新锐之星；网申/内推时间为8月17日至11月30日",
        "locator": "2027校园招聘/人才项目/新锐之星/网申[08-17..11-30]",
    },
    {
        "company": "大疆创新",
        "domain": "dji.com",
        "identity_key": "official-project:dji:digital-management:2027",
        "previous_type": "special_program",
        "excerpt": "面向2027届及优秀2026届毕业生；2026年8月7日开启，招满即止",
        "locator": "数字管理构建者计划/开启时间[2026-08-07]",
    },
    {
        "company": "宁德时代",
        "domain": "catl.com",
        "identity_key": "phase-02:p15",
        "previous_type": "campus_recruitment",
        "excerpt": (
            "2027届全球校园招聘；官方岗位来源于2026年8月27日起发布当前岗位"
        ),
        "locator": (
            "official-job-source[2027届全球校园招聘]/"
            "positions/source-updated-on[min=2026-08-27]"
        ),
    },
    {
        "company": "比亚迪",
        "domain": "byd.com",
        "identity_key": "phase-02:p19",
        "previous_type": "campus_recruitment",
        "excerpt": (
            "2027届应届生校园招聘；官方岗位来源于2026年8月13日起发布当前岗位"
        ),
        "locator": (
            "official-job-source[batch=2027]/"
            "positions/source-updated-on[min=2026-08-13]"
        ),
    },
    {
        "company": "百度",
        "domain": "baidu.com",
        "identity_key": "phase-02:p06",
        "previous_type": "campus_recruitment",
        "excerpt": (
            "面向2027届毕业生的校园招聘；官方岗位自2026年7月21日起发布"
        ),
        "locator": (
            "official-job-list[recruitType=GRADUATE]/"
            "positions/source-updated-on[min=2026-07-21]"
        ),
    },
    {
        "company": "顺丰",
        "domain": "sf-express.com",
        "identity_key": "phase-02:p18",
        "previous_type": "campus_recruitment",
        "excerpt": (
            "顺丰2027届校园招聘；当前20个官方岗位均属于招聘季43、"
            "类型2，并于2026年8月11日至25日创建"
        ),
        "locator": (
            "official-position-api/season[id=43,type=2]/"
            "createDate[2026-08-11..2026-08-25]"
        ),
    },
)


def classify_verified_2027_batches_as_autumn(apps, schema_editor):
    RecruitmentBatch = apps.get_model("radar", "RecruitmentBatch")
    AnnouncementFieldEvidence = apps.get_model(
        "radar", "AnnouncementFieldEvidence"
    )
    for item in AUTUMN_CLASSIFICATIONS:
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
            parsed_value="autumn",
        ).exists()
        if not evidence_exists:
            AnnouncementFieldEvidence.objects.create(
                batch_id=batch.pk,
                announcement_id=batch.primary_announcement_id,
                field_name="recruitment_type",
                excerpt=item["excerpt"],
                locator=item["locator"],
                parsed_value="autumn",
                value_hash=hashlib.sha256(b"autumn").hexdigest(),
            )
        batch.recruitment_type = "autumn"
        batch.save(update_fields=["recruitment_type"])


def restore_previous_recruitment_types(apps, schema_editor):
    RecruitmentBatch = apps.get_model("radar", "RecruitmentBatch")
    AnnouncementFieldEvidence = apps.get_model(
        "radar", "AnnouncementFieldEvidence"
    )
    for item in AUTUMN_CLASSIFICATIONS:
        batch = RecruitmentBatch.objects.filter(
            identity_key=item["identity_key"],
            organization__name=item["company"],
            organization__official_domain=item["domain"],
            recruitment_type="autumn",
            primary_announcement__isnull=False,
        ).first()
        if batch is None:
            continue
        previous_type = item["previous_type"]
        reverse_locator = f"migration-reverse/{item['locator']}"
        evidence_exists = AnnouncementFieldEvidence.objects.filter(
            batch_id=batch.pk,
            announcement_id=batch.primary_announcement_id,
            field_name="recruitment_type",
            locator=reverse_locator,
            parsed_value=previous_type,
        ).exists()
        if not evidence_exists:
            AnnouncementFieldEvidence.objects.create(
                batch_id=batch.pk,
                announcement_id=batch.primary_announcement_id,
                field_name="recruitment_type",
                excerpt="恢复迁移前的招聘类型",
                locator=reverse_locator,
                parsed_value=previous_type,
                value_hash=hashlib.sha256(previous_type.encode("utf-8")).hexdigest(),
            )
        batch.recruitment_type = previous_type
        batch.save(update_fields=["recruitment_type"])


class Migration(migrations.Migration):
    dependencies = [
        ("radar", "0026_classify_pinduoduo_2027_as_autumn"),
    ]

    operations = [
        migrations.RunPython(
            classify_verified_2027_batches_as_autumn,
            restore_previous_recruitment_types,
        ),
    ]
