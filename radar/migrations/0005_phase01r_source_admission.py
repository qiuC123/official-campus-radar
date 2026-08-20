import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("radar", "0004_phase01r_formal_gate")]

    operations = [
        migrations.CreateModel(
            name="OrganizationAlias",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("alias", models.CharField(max_length=200)),
                ("normalized_alias", models.CharField(max_length=200, unique=True)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="normalized_aliases", to="radar.organization")),
            ],
        ),
        migrations.CreateModel(
            name="SourceAdmissionEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("from_state", models.CharField(blank=True, max_length=16)),
                ("to_state", models.CharField(choices=[("candidate", "候选"), ("verified", "已核验"), ("enabled", "已启用"), ("suspended", "已暂停"), ("revoked", "已撤销")], max_length=16)),
                ("actor_label", models.CharField(max_length=100)),
                ("reason", models.TextField()),
                ("evidence", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("source", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="admission_events", to="radar.officialsource")),
            ],
        ),
        migrations.CreateModel(
            name="ApprovedApplicationHost",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("host", models.CharField(max_length=255)),
                ("evidence", models.TextField()),
                ("actor_label", models.CharField(max_length=100)),
                ("approved_at", models.DateTimeField(auto_now_add=True)),
                ("admission_event", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="approved_application_hosts", to="radar.sourceadmissionevent")),
                ("source", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="approved_application_hosts", to="radar.officialsource")),
            ],
            options={"constraints": [models.UniqueConstraint(fields=("source", "host"), name="unique_approved_application_host")]},
        ),
    ]
