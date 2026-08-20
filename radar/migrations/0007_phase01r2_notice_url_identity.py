from urllib.parse import urlsplit, urlunsplit

from django.db import migrations, models


def require_trusted_unique_notice_urls(apps, schema_editor):
    RecruitmentNotice = apps.get_model("radar", "RecruitmentNotice")
    seen = set()
    for notice in RecruitmentNotice.objects.select_related("source").iterator():
        identity_key = (notice.identity_key or "").strip()
        parts = urlsplit((notice.official_notice_url or "").strip())
        source_parts = urlsplit(notice.source.source_url)
        canonical_url = urlunsplit(
            (parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", parts.query, "")
        )
        if (
            not identity_key
            or identity_key != notice.identity_key
            or parts.scheme.lower() != "https"
            or not parts.hostname
            or parts.hostname.lower() != (source_parts.hostname or "").lower()
            or canonical_url != notice.official_notice_url
        ):
            raise RuntimeError(
                "Phase 01-R2 notice URL migration requires manual handling of untrusted historical identity data."
            )
        key = (notice.source_id, canonical_url)
        if key in seen:
            raise RuntimeError(
                "Phase 01-R2 notice URL migration requires manual handling of duplicate historical URLs."
            )
        seen.add(key)


class Migration(migrations.Migration):
    dependencies = [("radar", "0006_phase01r_identity_evidence")]

    operations = [
        migrations.RunPython(
            require_trusted_unique_notice_urls,
            migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name="recruitmentnotice",
            constraint=models.UniqueConstraint(
                fields=("source", "official_notice_url"),
                name="unique_notice_url_per_source",
            ),
        ),
    ]
