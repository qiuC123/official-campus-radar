from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("radar", "0017_officialsource_announcement_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="applicationlink",
            name="miniprogram_name",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="applicationlink",
            name="miniprogram_path",
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
