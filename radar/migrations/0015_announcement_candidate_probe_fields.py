from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("radar", "0014_announcement_driven_recruitment"),
    ]

    operations = [
        migrations.AddField(
            model_name="announcementdiscoverycandidate",
            name="content_sha256",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="announcementdiscoverycandidate",
            name="final_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="announcementdiscoverycandidate",
            name="recruitment_signal_found",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="announcementdiscoverycandidate",
            name="technical_verified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
