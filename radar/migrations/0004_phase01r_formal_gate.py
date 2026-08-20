import django.db.models.deletion
from django.db import migrations, models


def require_no_untraceable_notices(apps, schema_editor):
    RecruitmentNotice = apps.get_model("radar", "RecruitmentNotice")
    if RecruitmentNotice.objects.filter(source__isnull=True).exists():
        raise RuntimeError(
            "Cannot make RecruitmentNotice.source required while untraceable notices exist; "
            "resolve them manually before applying this migration."
        )


class Migration(migrations.Migration):
    dependencies = [
        ("radar", "0003_alter_fetchrun_status"),
    ]

    operations = [
        migrations.RunPython(require_no_untraceable_notices, migrations.RunPython.noop),
        migrations.AddField(
            model_name="officialsource",
            name="admission_state",
            field=models.CharField(
                choices=[
                    ("candidate", "候选"),
                    ("verified", "已核验"),
                    ("enabled", "已启用"),
                    ("suspended", "已暂停"),
                    ("revoked", "已撤销"),
                ],
                default="candidate",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="sourceversion",
            name="applied_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="sourceversion",
            name="is_applied",
            field=models.BooleanField(default=False),
        ),
        migrations.RemoveConstraint(
            model_name="recruitmentnotice",
            name="unique_notice_per_source_and_url",
        ),
        migrations.AddField(
            model_name="recruitmentnotice",
            name="identity_key",
            field=models.CharField(max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="recruitmentnotice",
            name="source",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="recruitment_notices",
                to="radar.officialsource",
            ),
        ),
        migrations.AddConstraint(
            model_name="recruitmentnotice",
            constraint=models.UniqueConstraint(
                fields=("source", "identity_key"),
                name="unique_notice_identity_per_source",
            ),
        ),
        migrations.CreateModel(
            name="PublicationEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "event_type",
                    models.CharField(
                        choices=[
                            ("published", "发布"),
                            ("updated", "更新"),
                            ("rejected", "拒绝"),
                            ("withdrawn", "撤回"),
                            ("out_of_scope", "超出范围"),
                            ("ambiguous", "身份冲突"),
                        ],
                        max_length=20,
                    ),
                ),
                ("identity_key", models.CharField(max_length=255)),
                ("candidate_title", models.CharField(blank=True, max_length=300)),
                ("reason_codes", models.JSONField(blank=True, default=list)),
                ("evidence_complete", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "notice",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="publication_events",
                        to="radar.recruitmentnotice",
                    ),
                ),
                (
                    "source_version",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="publication_events",
                        to="radar.sourceversion",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="recruitmentnotice",
            name="latest_publication_event",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="current_for_notices",
                to="radar.publicationevent",
            ),
        ),
    ]
