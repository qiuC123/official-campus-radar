from django.db import migrations, models


def rename_wxcli_to_wechat_oa(apps, schema_editor):
    RecruitmentAnnouncement = apps.get_model("radar", "RecruitmentAnnouncement")
    RecruitmentAnnouncement.objects.filter(verification_method="wxcli").update(
        verification_method="wechat_oa"
    )


def restore_wxcli_name(apps, schema_editor):
    RecruitmentAnnouncement = apps.get_model("radar", "RecruitmentAnnouncement")
    RecruitmentAnnouncement.objects.filter(verification_method="wechat_oa").update(
        verification_method="wxcli"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("radar", "0033_use_specific_recruitment_announcements"),
    ]

    operations = [
        migrations.RunPython(rename_wxcli_to_wechat_oa, restore_wxcli_name),
        migrations.AlterField(
            model_name="recruitmentannouncement",
            name="verification_method",
            field=models.CharField(
                choices=[
                    ("http", "官网 HTTP 回读"),
                    ("browser", "隔离浏览器回读"),
                    ("wechat_oa", "wechat-oa 微信证据"),
                    ("human_snapshot", "人工确认快照"),
                    ("manual_review", "人工审核"),
                ],
                default="manual_review",
                max_length=24,
            ),
        ),
    ]
