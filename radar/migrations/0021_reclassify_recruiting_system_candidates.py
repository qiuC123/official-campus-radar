from urllib.parse import urlsplit

from django.db import migrations


def reclassify_recruiting_system_candidates(apps, schema_editor):
    Candidate = apps.get_model("radar", "AnnouncementDiscoveryCandidate")
    OfficialSource = apps.get_model("radar", "OfficialSource")

    system_hosts_by_organization = {}
    for source in OfficialSource.objects.filter(source_type__in=("ats", "api")):
        host = (urlsplit(source.source_url).hostname or "").casefold()
        if host:
            system_hosts_by_organization.setdefault(source.organization_id, set()).add(host)
    for candidate in Candidate.objects.filter(source_kind="website"):
        host = (urlsplit(candidate.url).hostname or "").casefold()
        if any(
            host == known or host.endswith(f".{known}")
            for known in system_hosts_by_organization.get(candidate.organization_id, set())
        ):
            Candidate.objects.filter(pk=candidate.pk).update(
                source_kind="recruiting_system"
            )


class Migration(migrations.Migration):
    dependencies = [
        ("radar", "0020_one_batch_per_primary_announcement"),
    ]

    operations = [
        migrations.RunPython(
            reclassify_recruiting_system_candidates,
            migrations.RunPython.noop,
        ),
    ]
