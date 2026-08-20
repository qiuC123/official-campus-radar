import django.db.models.deletion
from django.db import migrations, models


def require_empty_legacy_evidence_and_positions(apps, schema_editor):
    Evidence = apps.get_model("radar", "Evidence")
    NoticePosition = apps.get_model("radar", "NoticePosition")
    if Evidence.objects.exists() or NoticePosition.objects.exists():
        raise RuntimeError(
            "Phase 01-R evidence migration requires manual handling of legacy evidence or positions."
        )


class Migration(migrations.Migration):
    dependencies = [("radar", "0005_phase01r_source_admission")]

    operations = [
        migrations.RunPython(require_empty_legacy_evidence_and_positions, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="recruitmentnotice",
            name="recruitment_type",
            field=models.CharField(
                choices=[
                    ("campus_recruitment", "校园招聘"),
                    ("internship", "实习"),
                    ("other", "其他"),
                    ("unknown", "未知"),
                ],
                default="unknown",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="noticeposition",
            name="position_key",
            field=models.CharField(max_length=255),
            preserve_default=False,
        ),
        migrations.AddConstraint(
            model_name="noticeposition",
            constraint=models.UniqueConstraint(
                fields=("notice", "position_key"),
                name="unique_position_identity_per_notice",
            ),
        ),
        migrations.AddField(
            model_name="evidence",
            name="parsed_value",
            field=models.TextField(),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="evidence",
            name="publication_event",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="evidence",
                to="radar.publicationevent",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="evidence",
            name="raw_value",
            field=models.TextField(),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="evidence",
            name="value_hash",
            field=models.CharField(max_length=64),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="evidence",
            name="locator",
            field=models.CharField(max_length=500),
        ),
        migrations.AlterField(
            model_name="evidence",
            name="source_version",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="evidence",
                to="radar.sourceversion",
            ),
        ),
    ]
