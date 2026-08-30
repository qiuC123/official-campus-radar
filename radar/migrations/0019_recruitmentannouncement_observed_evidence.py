from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("radar", "0018_applicationlink_miniprogram_identity"),
    ]

    operations = [
        migrations.AddField(
            model_name="recruitmentannouncement",
            name="observed_external_links",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="recruitmentannouncement",
            name="observed_media",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
