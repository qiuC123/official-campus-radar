from django.db import migrations, models


def require_empty_unhashed_audit_history(apps, schema_editor):
    SourceAdmissionEvent = apps.get_model("radar", "SourceAdmissionEvent")
    ApprovedApplicationHost = apps.get_model("radar", "ApprovedApplicationHost")
    if SourceAdmissionEvent.objects.exists() or ApprovedApplicationHost.objects.exists():
        raise RuntimeError(
            "Phase 01-R2 audit hash migration requires manual handling of existing admission or host records."
        )


class Migration(migrations.Migration):
    dependencies = [("radar", "0008_phase01r2_demo_ownership")]

    operations = [
        migrations.RunPython(
            require_empty_unhashed_audit_history,
            migrations.RunPython.noop,
        ),
        migrations.AddField(
            model_name="sourceadmissionevent",
            name="previous_event_hash",
            field=models.CharField(default="", max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="sourceadmissionevent",
            name="event_hash",
            field=models.CharField(default="", max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="approvedapplicationhost",
            name="approval_digest",
            field=models.CharField(default="", max_length=64),
            preserve_default=False,
        ),
    ]
