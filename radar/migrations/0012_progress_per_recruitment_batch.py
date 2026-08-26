from django.db import migrations, models
import django.db.models.deletion


def move_progress_to_batch(apps, schema_editor):
    Progress = apps.get_model("radar", "ApplicationProgress")
    progresses = list(Progress.objects.select_related("position__batch"))
    batch_ids = [progress.position.batch_id for progress in progresses]
    if len(batch_ids) != len(set(batch_ids)):
        raise RuntimeError(
            "Cannot move position progress safely: multiple progress rows belong to one batch."
        )
    for progress in progresses:
        progress.batch_id = progress.position.batch_id
        progress.save(update_fields=["batch"])


def move_progress_to_position(apps, schema_editor):
    Progress = apps.get_model("radar", "ApplicationProgress")
    Position = apps.get_model("radar", "RecruitmentPosition")
    mappings = []
    for progress in Progress.objects.all():
        position_ids = list(
            Position.objects.filter(batch_id=progress.batch_id).values_list("pk", flat=True)
        )
        if len(position_ids) != 1:
            raise RuntimeError(
                "Cannot reverse batch progress safely: every batch with progress must have exactly one position."
            )
        mappings.append((progress, position_ids[0]))
    for progress, position_id in mappings:
        progress.position_id = position_id
        progress.save(update_fields=["position"])


class Migration(migrations.Migration):
    dependencies = [("radar", "0011_recruitment_batches_and_position_progress")]

    operations = [
        migrations.AddField(
            model_name="applicationprogress",
            name="batch",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="application_progress",
                to="radar.recruitmentbatch",
            ),
        ),
        migrations.AlterField(
            model_name="applicationprogress",
            name="position",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="application_progress",
                to="radar.recruitmentposition",
            ),
        ),
        migrations.RunPython(move_progress_to_batch, move_progress_to_position),
        migrations.RemoveField(model_name="applicationprogress", name="position"),
        migrations.AlterField(
            model_name="applicationprogress",
            name="batch",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="application_progress",
                to="radar.recruitmentbatch",
            ),
        ),
    ]
