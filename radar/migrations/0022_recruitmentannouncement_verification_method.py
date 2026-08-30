from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("radar", "0021_reclassify_recruiting_system_candidates"),
    ]

    operations = [
        migrations.AddField(
            model_name="recruitmentannouncement",
            name="verification_method",
            field=models.CharField(
                choices=[
                    ("http", "官网 HTTP 回读"),
                    ("browser", "隔离浏览器回读"),
                    ("wxcli", "wxcli 微信证据"),
                    ("human_snapshot", "人工确认快照"),
                    ("manual_review", "人工审核"),
                ],
                default="manual_review",
                max_length=24,
            ),
        ),
    ]
