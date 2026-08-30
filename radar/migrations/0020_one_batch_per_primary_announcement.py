from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("radar", "0019_recruitmentannouncement_observed_evidence"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="recruitmentbatch",
            constraint=models.UniqueConstraint(
                fields=("primary_announcement",),
                condition=Q(primary_announcement__isnull=False),
                name="one_batch_per_primary_announcement",
            ),
        ),
    ]
