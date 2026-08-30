from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("radar", "0016_normalize_announcement_candidate_review_state"),
    ]

    operations = [
        migrations.AlterField(
            model_name="officialsource",
            name="source_type",
            field=models.CharField(
                choices=[
                    ("website", "企业官网"),
                    ("announcement", "企业官网公告源"),
                    ("ats", "官网关联投递系统"),
                    ("wechat", "官方招聘公众号"),
                    ("api", "官方招聘接口"),
                ],
                max_length=16,
            ),
        ),
    ]
