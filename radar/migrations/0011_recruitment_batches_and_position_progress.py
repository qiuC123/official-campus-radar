from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def _rename_json_api_config(config, *, forward):
    if not isinstance(config, dict):
        return config
    old_group, new_group = (("notice", "batch") if forward else ("batch", "notice"))
    old_url, new_url = (
        ("official_notice_url", "official_page_url")
        if forward
        else ("official_page_url", "official_notice_url")
    )
    if old_group not in config:
        return config
    if new_group in config:
        raise RuntimeError(
            f"Cannot migrate JSON API config safely: both {old_group!r} and {new_group!r} exist."
        )
    updated = dict(config)
    group = updated.pop(old_group)
    if not isinstance(group, dict):
        raise RuntimeError(f"Cannot migrate JSON API config safely: {old_group!r} must be an object.")
    group = dict(group)
    if old_url in group and new_url in group:
        raise RuntimeError(
            f"Cannot migrate JSON API config safely: both {old_url!r} and {new_url!r} exist."
        )
    if old_url in group:
        group[new_url] = group.pop(old_url)
    updated[new_group] = group
    return updated


def migrate_phase02_contract_forward(apps, schema_editor):
    Source = apps.get_model("radar", "OfficialSource")
    Evidence = apps.get_model("radar", "Evidence")
    for source in Source.objects.filter(adapter_name="json_api"):
        updated = _rename_json_api_config(source.parser_config, forward=True)
        if updated != source.parser_config:
            source.parser_config = updated
            source.save(update_fields=["parser_config"])
    Evidence.objects.filter(field_name="notice_url").update(field_name="official_page_url")


def migrate_phase02_contract_reverse(apps, schema_editor):
    Source = apps.get_model("radar", "OfficialSource")
    Evidence = apps.get_model("radar", "Evidence")
    for source in Source.objects.filter(adapter_name="json_api"):
        updated = _rename_json_api_config(source.parser_config, forward=False)
        if updated != source.parser_config:
            source.parser_config = updated
            source.save(update_fields=["parser_config"])
    Evidence.objects.filter(field_name="official_page_url").update(field_name="notice_url")


def backfill_position_times(apps, schema_editor):
    Position = apps.get_model("radar", "RecruitmentPosition")
    for position in Position.objects.select_related("batch"):
        first_seen_at = position.batch.first_seen_at
        content_changed_at = position.removed_at or first_seen_at
        Position.objects.filter(pk=position.pk).update(
            first_seen_at=first_seen_at,
            content_changed_at=content_changed_at,
        )


def move_progress_to_position(apps, schema_editor):
    Progress = apps.get_model("radar", "ApplicationProgress")
    Position = apps.get_model("radar", "RecruitmentPosition")
    for progress in Progress.objects.select_related("notice"):
        position_ids = list(
            Position.objects.filter(batch_id=progress.notice_id).values_list("pk", flat=True)
        )
        if len(position_ids) != 1:
            raise RuntimeError(
                "Cannot move batch progress safely: every batch with progress must have exactly one position."
            )
        progress.position_id = position_ids[0]
        progress.save(update_fields=["position"])


def move_progress_to_batch(apps, schema_editor):
    Progress = apps.get_model("radar", "ApplicationProgress")
    progresses = list(Progress.objects.select_related("position__batch"))
    batch_ids = [progress.position.batch_id for progress in progresses]
    if len(batch_ids) != len(set(batch_ids)):
        raise RuntimeError(
            "Cannot reverse position progress safely: multiple position progress rows belong to one batch."
        )
    for progress in progresses:
        progress.notice_id = progress.position.batch_id
        progress.save(update_fields=["notice"])


class Migration(migrations.Migration):
    dependencies = [("radar", "0010_officialsource_api_source_type")]

    operations = [
        migrations.RemoveConstraint(
            model_name="recruitmentnotice",
            name="unique_notice_identity_per_source",
        ),
        migrations.RemoveConstraint(
            model_name="recruitmentnotice",
            name="unique_notice_url_per_source",
        ),
        migrations.RemoveConstraint(
            model_name="noticeposition",
            name="unique_position_identity_per_notice",
        ),
        migrations.RenameModel(
            old_name="RecruitmentNotice", new_name="RecruitmentBatch"
        ),
        migrations.RenameModel(
            old_name="NoticePosition", new_name="RecruitmentPosition"
        ),
        migrations.RenameField(
            model_name="recruitmentbatch",
            old_name="official_notice_url",
            new_name="official_page_url",
        ),
        migrations.RunPython(
            migrate_phase02_contract_forward,
            migrate_phase02_contract_reverse,
        ),
        migrations.RenameField(
            model_name="publicationevent", old_name="notice", new_name="batch"
        ),
        migrations.RenameField(
            model_name="recruitmentposition", old_name="notice", new_name="batch"
        ),
        migrations.RenameField(
            model_name="applicationlink", old_name="notice", new_name="batch"
        ),
        migrations.RenameField(
            model_name="evidence", old_name="notice", new_name="batch"
        ),
        migrations.AddField(
            model_name="recruitmentposition",
            name="source_updated_on",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="recruitmentposition",
            name="first_seen_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="recruitmentposition",
            name="content_changed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_position_times, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="recruitmentposition",
            name="first_seen_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="recruitmentposition",
            name="content_changed_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
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
        migrations.AlterField(
            model_name="applicationprogress",
            name="notice",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="application_progress",
                to="radar.recruitmentbatch",
            ),
        ),
        migrations.RunPython(move_progress_to_position, move_progress_to_batch),
        migrations.RemoveField(model_name="applicationprogress", name="notice"),
        migrations.AlterField(
            model_name="applicationprogress",
            name="position",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="application_progress",
                to="radar.recruitmentposition",
            ),
        ),
        migrations.AlterField(
            model_name="applicationprogress",
            name="status",
            field=models.CharField(
                choices=[
                    ("not_applied", "未投递"),
                    ("applied", "已投递"),
                    ("written_test", "已笔试"),
                    ("interviewed", "已面试"),
                    ("rejected", "未通过"),
                    ("passed_interview", "面试通过"),
                    ("not_applying", "暂不投递"),
                ],
                default="not_applied",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="recruitmentbatch",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="recruitment_batches",
                to="radar.organization",
            ),
        ),
        migrations.AlterField(
            model_name="recruitmentbatch",
            name="source",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="recruitment_batches",
                to="radar.officialsource",
            ),
        ),
        migrations.AlterField(
            model_name="recruitmentbatch",
            name="latest_publication_event",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="current_for_batches",
                to="radar.publicationevent",
            ),
        ),
        migrations.AlterField(
            model_name="applicationlink",
            name="link_type",
            field=models.CharField(
                choices=[
                    ("batch_page", "招聘批次官方页面"),
                    ("application", "投递入口"),
                ],
                max_length=16,
            ),
        ),
        migrations.RunSQL(
            "UPDATE radar_applicationlink SET link_type = 'batch_page' WHERE link_type = 'notice'",
            "UPDATE radar_applicationlink SET link_type = 'notice' WHERE link_type = 'batch_page'",
        ),
        migrations.AddConstraint(
            model_name="recruitmentbatch",
            constraint=models.UniqueConstraint(
                fields=("source", "identity_key"),
                name="unique_batch_identity_per_source",
            ),
        ),
        migrations.AddConstraint(
            model_name="recruitmentbatch",
            constraint=models.UniqueConstraint(
                fields=("source", "official_page_url"),
                name="unique_batch_url_per_source",
            ),
        ),
        migrations.AddConstraint(
            model_name="recruitmentposition",
            constraint=models.UniqueConstraint(
                fields=("batch", "position_key"),
                name="unique_position_identity_per_batch",
            ),
        ),
    ]
