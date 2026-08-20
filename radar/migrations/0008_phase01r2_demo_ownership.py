from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("radar", "0007_phase01r2_notice_url_identity")]

    operations = [
        migrations.AddField(
            model_name="officialsource",
            name="local_demo_key",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="updaterun",
            name="local_demo_key",
            field=models.CharField(blank=True, max_length=64),
        ),
    ]
