from urllib.parse import urlsplit

from django.db import migrations


def normalize_candidate_review_state(apps, schema_editor):
    Candidate = apps.get_model("radar", "AnnouncementDiscoveryCandidate")
    OfficialSource = apps.get_model("radar", "OfficialSource")

    Candidate.objects.filter(
        state="failed",
        error_code="NO_RECRUITMENT_PROJECT_SIGNAL",
    ).update(
        state="new",
        error_code="CONTENT_REVIEW_REQUIRED",
    )
    Candidate.objects.filter(state="new", error_code="").update(
        error_code="SEMANTIC_REVIEW_REQUIRED",
    )

    ats_hosts_by_organization = {}
    for source in OfficialSource.objects.filter(source_type="ats"):
        host = (urlsplit(source.source_url).hostname or "").casefold()
        if host:
            ats_hosts_by_organization.setdefault(source.organization_id, set()).add(host)
    for candidate in Candidate.objects.filter(source_kind="website"):
        host = (urlsplit(candidate.url).hostname or "").casefold()
        if any(
            host == known or host.endswith(f".{known}")
            for known in ats_hosts_by_organization.get(candidate.organization_id, set())
        ):
            Candidate.objects.filter(pk=candidate.pk).update(source_kind="recruiting_system")


class Migration(migrations.Migration):
    dependencies = [
        ("radar", "0015_announcement_candidate_probe_fields"),
    ]

    operations = [
        migrations.RunPython(normalize_candidate_review_state, migrations.RunPython.noop),
    ]
