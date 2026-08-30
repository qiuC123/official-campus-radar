from django.db import migrations, models
import django.db.models.deletion
import django.db.models.query_utils
import django.utils.timezone


def create_default_policy(apps, schema_editor):
    RecruitmentPolicy = apps.get_model("radar", "RecruitmentPolicy")
    RecruitmentPolicy.objects.get_or_create(key="default")


def remove_default_policy(apps, schema_editor):
    RecruitmentPolicy = apps.get_model("radar", "RecruitmentPolicy")
    RecruitmentPolicy.objects.filter(
        key="default",
        announcement_gate_enforced=False,
        preview_digest="",
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("radar", "0013_organization_company_types"),
    ]

    operations = [
        migrations.CreateModel(
            name="RecruitmentPolicy",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(default="default", max_length=32, unique=True)),
                ("announcement_gate_enforced", models.BooleanField(default=False)),
                ("preview_digest", models.CharField(blank=True, max_length=64)),
                ("preview_generated_at", models.DateTimeField(blank=True, null=True)),
                ("activated_at", models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="RecruitmentAnnouncement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("identity_key", models.CharField(max_length=512)),
                ("source_kind", models.CharField(choices=[("website", "企业官网公告"), ("recruiting_system", "官方招聘系统项目页"), ("wechat_article", "微信公众号文章"), ("wechat_miniprogram", "微信小程序通知")], max_length=24)),
                ("title", models.CharField(max_length=500)),
                ("url", models.URLField(blank=True)),
                ("miniprogram_name", models.CharField(blank=True, max_length=200)),
                ("miniprogram_path", models.CharField(blank=True, max_length=500)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("last_verified_at", models.DateTimeField(blank=True, null=True)),
                ("identity_evidence", models.TextField()),
                ("account_display_name", models.CharField(blank=True, max_length=200)),
                ("account_biz_id", models.CharField(blank=True, max_length=512)),
                ("content_sha256", models.CharField(blank=True, max_length=64)),
                ("evidence_sha256", models.CharField(blank=True, max_length=64)),
                ("verification_status", models.CharField(choices=[("candidate", "候选"), ("verified", "已核验"), ("pending_image", "图片待核验"), ("rejected", "已拒绝")], default="candidate", max_length=24)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="recruitment_announcements", to="radar.organization")),
                ("source", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="recruitment_announcements", to="radar.officialsource")),
            ],
        ),
        migrations.CreateModel(
            name="WeChatAccountIdentity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("display_name", models.CharField(max_length=200)),
                ("biz_id", models.CharField(blank=True, max_length=512)),
                ("identity_evidence", models.TextField()),
                ("is_verified", models.BooleanField(default=False)),
                ("verified_at", models.DateTimeField(blank=True, null=True)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="wechat_account_identities", to="radar.organization")),
            ],
        ),
        migrations.CreateModel(
            name="AnnouncementDiscoveryCandidate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_kind", models.CharField(choices=[("website", "企业官网公告"), ("recruiting_system", "官方招聘系统项目页"), ("wechat_article", "微信公众号文章"), ("wechat_miniprogram", "微信小程序通知")], max_length=24)),
                ("url", models.URLField()),
                ("title_hint", models.CharField(blank=True, max_length=500)),
                ("provider", models.CharField(max_length=64)),
                ("provider_result_id", models.CharField(blank=True, max_length=128)),
                ("state", models.CharField(choices=[("new", "待核验"), ("verified", "已核验"), ("merged", "已合并"), ("separate", "独立批次"), ("discarded", "已丢弃"), ("failed", "读取失败")], default="new", max_length=16)),
                ("error_code", models.CharField(blank=True, max_length=64)),
                ("discovered_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("announcement", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="discovery_candidates", to="radar.recruitmentannouncement")),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="announcement_candidates", to="radar.organization")),
            ],
        ),
        migrations.AddField(
            model_name="recruitmentbatch",
            name="announcement_admission",
            field=models.CharField(choices=[("legacy", "旧规则待迁移"), ("admitted", "公告已准入"), ("pending", "待核验"), ("excluded", "不进入正式页")], default="legacy", max_length=16),
        ),
        migrations.AddField(
            model_name="recruitmentbatch",
            name="primary_announcement",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="recruitment_batches", to="radar.recruitmentannouncement"),
        ),
        migrations.AddField(
            model_name="recruitmentposition",
            name="kind",
            field=models.CharField(choices=[("position", "招聘岗位"), ("direction", "岗位方向")], default="position", max_length=16),
        ),
        migrations.CreateModel(
            name="AnnouncementFieldEvidence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("field_name", models.CharField(max_length=64)),
                ("excerpt", models.TextField()),
                ("locator", models.CharField(max_length=500)),
                ("parsed_value", models.TextField()),
                ("value_hash", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("announcement", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="field_evidence", to="radar.recruitmentannouncement")),
                ("batch", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="announcement_evidence", to="radar.recruitmentbatch")),
                ("position", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="announcement_evidence", to="radar.recruitmentposition")),
            ],
        ),
        migrations.AddField(
            model_name="applicationlink",
            name="email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="applicationlink",
            name="instructions",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="applicationlink",
            name="verification_evidence",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="applicationlink",
            name="link_type",
            field=models.CharField(choices=[("batch_page", "招聘批次官方页面"), ("application", "投递入口"), ("email", "招聘邮箱"), ("mini_program", "投递小程序")], max_length=16),
        ),
        migrations.AlterField(
            model_name="applicationlink",
            name="url",
            field=models.URLField(blank=True),
        ),
        migrations.AlterField(
            model_name="recruitmentbatch",
            name="recruitment_type",
            field=models.CharField(choices=[("spring", "春招"), ("spring_supplement", "春招补录"), ("autumn", "秋招"), ("autumn_supplement", "秋招补录"), ("autumn_early", "秋招提前批"), ("campus_recruitment", "校园招聘"), ("internship", "实习"), ("special_program", "专项计划"), ("other", "其他"), ("unknown", "未知")], default="unknown", max_length=32),
        ),
        migrations.AddConstraint(
            model_name="recruitmentannouncement",
            constraint=models.UniqueConstraint(fields=("organization", "source_kind", "identity_key"), name="unique_announcement_identity_per_organization"),
        ),
        migrations.AddConstraint(
            model_name="wechataccountidentity",
            constraint=models.UniqueConstraint(fields=("organization", "display_name"), name="unique_wechat_display_name_per_organization"),
        ),
        migrations.AddConstraint(
            model_name="wechataccountidentity",
            constraint=models.UniqueConstraint(condition=~django.db.models.query_utils.Q(("biz_id", "")), fields=("biz_id",), name="unique_nonempty_wechat_biz_id"),
        ),
        migrations.AddConstraint(
            model_name="announcementdiscoverycandidate",
            constraint=models.UniqueConstraint(fields=("organization", "url"), name="unique_announcement_candidate_url_per_organization"),
        ),
        migrations.RunPython(create_default_policy, remove_default_policy),
    ]
