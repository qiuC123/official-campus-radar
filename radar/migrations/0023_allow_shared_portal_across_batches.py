from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("radar", "0022_recruitmentannouncement_verification_method"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="recruitmentbatch",
            name="unique_batch_url_per_source",
        ),
    ]
