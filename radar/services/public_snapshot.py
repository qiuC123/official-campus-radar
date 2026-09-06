"""An explicit display-only export, never a copy of the operational database."""

from contextlib import closing
from dataclasses import replace
from datetime import date, datetime
import json
from pathlib import Path
import re
import sqlite3
from urllib.parse import parse_qsl, quote, urlsplit

from django.core.paginator import Paginator
from django.http import QueryDict
from django.utils import timezone

from radar.services.dashboard_data import (
    _summary, available_city_choices, build_orm_dashboard, filter_position_vms,
)
from radar.viewmodels import (
    PREVIEW_COMPANY_TYPE_CHOICES, RECRUITMENT_TYPE_CHOICES,
    RecruitmentBatchVM, RecruitmentPositionVM,
)

BATCH_FIELDS = (
    "id", "company", "company_type", "industry", "title", "recruitment_type",
    "target_audience", "deadline", "status", "official_page_url",
    "announcement_url", "announcement_label", "batch_application_urls", "target_audience_source",
)
POSITION_FIELDS = (
    "id", "title", "locations", "details", "application_url", "uses_batch_page",
    "effective_updated_on", "is_current", "kind",
)
MAX_SNAPSHOT_BYTES = 64 * 1024 * 1024


def _check_url(value):
    if not value:
        return
    parsed = urlsplit(value)
    if parsed.scheme == "mailto" and "@" in parsed.path and not parsed.query:
        return
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.hostname.lower() in {"mp.weixin.qq.com", "localhost", "127.0.0.1"}):
        raise ValueError("Snapshot contains a non-public recruitment URL")
    if any(key.lower() in {"access_token", "api_key", "apikey", "secret", "password", "authorization"}
           for key, _ in parse_qsl(parsed.query)):
        raise ValueError("Snapshot URL contains a credential-like parameter")


def _encode(batch):
    if batch.progress_value or batch.progress_label:
        raise ValueError("Personal progress must not enter a snapshot")
    value = {field: getattr(batch, field) for field in BATCH_FIELDS}
    value["deadline"] = batch.deadline.isoformat() if batch.deadline else None
    value["positions"] = []
    for position in batch.positions:
        item = {field: getattr(position, field) for field in POSITION_FIELDS}
        item["effective_updated_on"] = position.effective_updated_on.isoformat()
        _check_url(position.application_url)
        value["positions"].append(item)
    for url in (batch.official_page_url, batch.announcement_url, *batch.batch_application_urls):
        _check_url(url)
    text = json.dumps(value, ensure_ascii=False)
    if re.search(r"(?i)(?:EXA_API_KEY|ACCESSKEY_SECRET|BEGIN (?:RSA |OPENSSH )?PRIVATE KEY|authorization\s*[:=]\s*bearer)", text):
        raise ValueError("Snapshot contains credential-like text; manual review required")
    return text


def _decode(text):
    value = json.loads(text)
    if set(value) != set(BATCH_FIELDS) | {"positions"}:
        raise ValueError("Unexpected public snapshot batch fields")
    positions = []
    for item in value.pop("positions"):
        if set(item) != set(POSITION_FIELDS):
            raise ValueError("Unexpected public snapshot position fields")
        item["effective_updated_on"] = date.fromisoformat(item["effective_updated_on"])
        item["locations"] = tuple(item["locations"])
        positions.append(RecruitmentPositionVM(**item))
    if not positions:
        raise ValueError("Empty snapshot batch")
    value["deadline"] = date.fromisoformat(value["deadline"]) if value["deadline"] else None
    value["batch_application_urls"] = tuple(value["batch_application_urls"])
    batch = RecruitmentBatchVM(**value, positions=tuple(positions), progress_value="", progress_label="")
    _encode(batch)  # Same URL and credential boundary on import.
    return batch


def export_snapshot(path):
    """Caller holds a read transaction; the output is new and has only two tables."""
    path = Path(path)
    if not path.is_absolute():
        raise ValueError("Snapshot output must be absolute")
    rows = []
    for history in (False, True):
        page, *_ = build_orm_dashboard(QueryDict(), history=history, include_progress=False)
        rows.extend((int(batch.id), int(history), _encode(batch)) for batch in page.paginator.object_list)
    if not rows:
        raise ValueError("Refusing an empty public snapshot")
    path.open("xb").close()  # Never overwrite a database or an earlier snapshot.
    try:
        with closing(sqlite3.connect(path)) as target:
            target.executescript(
                "CREATE TABLE snapshot_meta (schema_version INTEGER NOT NULL, generated_at TEXT NOT NULL);"
                "CREATE TABLE public_batch (id INTEGER PRIMARY KEY, history INTEGER NOT NULL, data TEXT NOT NULL);"
            )
            target.execute("INSERT INTO snapshot_meta VALUES (1, ?)", (timezone.now().isoformat(),))
            target.executemany("INSERT INTO public_batch VALUES (?, ?, ?)", rows)
            target.commit()
        read_snapshot(path)
    except Exception:
        path.unlink()  # Only the newly created output, never the source or existing files.
        raise
    return {"batches": len(rows), "active_batches": sum(not row[1] for row in rows)}


def read_snapshot(path):
    path = Path(path)
    if not path.is_absolute() or not path.is_file() or path.stat().st_size > MAX_SNAPSHOT_BYTES:
        raise ValueError("Missing or oversized public snapshot")
    uri = "file:" + quote(path.as_posix(), safe="/:") + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as db:
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if tables != {"snapshot_meta", "public_batch"}:
            raise ValueError("Not a display-only database")
        meta = db.execute("SELECT schema_version, generated_at FROM snapshot_meta").fetchall()
        if len(meta) != 1 or meta[0][0] != 1:
            raise ValueError("Unsupported public snapshot version")
        rows = [(identity, history, _decode(data)) for identity, history, data in db.execute(
            "SELECT id, history, data FROM public_batch ORDER BY id"
        )]
    if not rows or any(identity != batch.id or history not in (0, 1) for identity, history, batch in rows):
        raise ValueError("Invalid snapshot identities")
    return meta[0][1], rows


def build_snapshot_dashboard(params, *, path, history=False):
    generated_at, rows = read_snapshot(path)
    company_types = {dict(PREVIEW_COMPANY_TYPE_CHOICES).get(key, key) for key in params.getlist("company_type")}
    recruitment_types = {dict(RECRUITMENT_TYPE_CHOICES).get(key, key) for key in params.getlist("recruitment_type")}
    audience = params.get("audience") or params.get("target_audience")
    batches, audiences = [], set()
    for _, historical, batch in rows:
        if bool(historical) != history:
            continue
        if params.get("company", "").casefold() not in batch.company.casefold():
            continue
        if company_types and batch.company_type not in company_types:
            continue
        if params.get("industry", "").casefold() not in batch.industry.casefold():
            continue
        if recruitment_types and batch.recruitment_type not in recruitment_types:
            continue
        audiences.update(batch.audience_labels)
        if audience and audience not in batch.audience_labels:
            continue
        positions = filter_position_vms(batch.positions, params)
        if positions:
            batches.append(replace(batch, positions=tuple(positions)))
    batches.sort(key=lambda item: item.effective_updated_on, reverse=True)
    page = Paginator(batches, 20).get_page(params.get("page", 1))
    page.snapshot_generated_at = datetime.fromisoformat(generated_at)
    return (page,
            _summary(batches, date.today()), available_city_choices(batches), tuple(sorted(audiences)))
