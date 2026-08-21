import hashlib
from datetime import date
from time import monotonic
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from radar.collectors.base import (
    FieldEvidenceValue,
    FetchedPage,
    NoticeCandidate,
    PositionCandidate,
)
from radar.models import OfficialSource
from radar.services.normalization import canonicalize_url


class HtmlSourceAdapter:
    timeout_seconds = 15

    @staticmethod
    def validate_source_config(source: OfficialSource) -> None:
        config = source.parser_config
        required_selectors = {
            "notice_selector",
            "notice_url_selector",
            "title_selector",
            "recruitment_type_selector",
            "target_audience_selector",
            "published_on_selector",
            "deadline_selector",
            "position_title_selector",
            "location_selector",
            "excerpt_selector",
        }
        if not isinstance(config, dict) or any(
            not str(config.get(key, "")).strip() for key in required_selectors
        ):
            raise ValueError("HTML parser contract is missing a required field selector")
        if not any(
            str(config.get(key, "")).strip()
            for key in ("notice_id_attribute", "notice_id_selector")
        ):
            raise ValueError("HTML parser contract requires a stable notice identity")
        if not any(
            str(config.get(key, "")).strip()
            for key in ("position_id_attribute", "position_id_selector")
        ):
            raise ValueError("HTML parser contract requires a stable position identity")

    def fetch(self, source: OfficialSource) -> FetchedPage:
        headers = {"User-Agent": "OfficialCampusRadar/0.1 (local low-frequency collector)"}
        if source.last_etag:
            headers["If-None-Match"] = source.last_etag
        started = monotonic()
        response = requests.Session().get(source.source_url, headers=headers, timeout=self.timeout_seconds)
        if response.status_code >= 400 and response.status_code != 304:
            raise requests.HTTPError(f"HTTP {response.status_code}")
        canonical_url = canonicalize_url(getattr(response, "url", source.source_url) or source.source_url)
        if response.status_code == 304:
            return FetchedPage(canonical_url, "", "", 304, source.last_etag or None, True)
        body = response.text
        content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
        etag = response.headers.get("ETag")
        return FetchedPage(canonical_url, body, content_hash, response.status_code, etag)

    def extract(
        self, source: OfficialSource, page: FetchedPage
    ) -> list[NoticeCandidate]:
        if page.not_modified:
            return []
        config = source.parser_config
        required = (
            "notice_selector",
            "notice_url_selector",
            "title_selector",
            "recruitment_type_selector",
        )
        if not isinstance(config, dict) or any(
            not config.get(key) for key in required
        ):
            raise ValueError(
                "selector configuration requires notice, URL, title, "
                "and recruitment type selectors"
            )
        soup = BeautifulSoup(page.body, "html.parser")
        candidates: list[NoticeCandidate] = []
        for index, node in enumerate(soup.select(config["notice_selector"]), start=1):
            title_node = node.select_one(config["title_selector"])
            notice_link = node.select_one(config["notice_url_selector"])
            recruitment_type_node = node.select_one(config["recruitment_type_selector"])
            if (
                not title_node
                or not notice_link
                or not notice_link.get("href")
                or not recruitment_type_node
            ):
                continue

            def selected(container, key):
                return (
                    container.select_one(config[key])
                    if config.get(key)
                    else None
                )

            def text_value(container, key):
                selected_node = selected(container, key)
                return selected_node.get_text(" ", strip=True) if selected_node else ""

            deadline_text = text_value(node, "deadline_selector")
            try:
                deadline = date.fromisoformat(deadline_text) if deadline_text else None
            except ValueError:
                deadline = None
            published_text = text_value(node, "published_on_selector")
            try:
                published_on = (
                    date.fromisoformat(published_text) if published_text else None
                )
            except ValueError:
                published_on = None
            recruitment_type_text = recruitment_type_node.get_text(" ", strip=True)
            notice_href = str(notice_link.get("href"))
            notice_url = canonicalize_url(urljoin(page.canonical_url, notice_href))
            identity_attribute = config.get("notice_id_attribute")
            identity_selector = config.get("notice_id_selector")
            identity_key = (
                str(node.get(identity_attribute, "")).strip()
                if identity_attribute
                else text_value(node, "notice_id_selector")
                if identity_selector
                else ""
            )
            locator = (
                f"{config['notice_selector']}[{identity_attribute}='{identity_key}']"
                if identity_attribute and identity_key
                else f"{config['notice_selector']}:nth-of-type({index})"
            )
            withdrawn = bool(
                config.get("withdrawn_selector")
                and node.select_one(config["withdrawn_selector"])
            )
            target_audience = text_value(node, "target_audience_selector")
            field_evidence = {}
            if identity_key:
                field_evidence["title"] = FieldEvidenceValue(
                    title_node.get_text(" ", strip=True),
                    f"{locator} {config['title_selector']}",
                    title_node.get_text(" ", strip=True),
                )
                field_evidence["recruitment_type"] = FieldEvidenceValue(
                    recruitment_type_text,
                    f"{locator} {config['recruitment_type_selector']}",
                    recruitment_type_text,
                )
                optional_notice_fields = (
                    ("target_audience", "target_audience_selector", target_audience, target_audience),
                    ("published_on", "published_on_selector", published_text, str(published_on or "")),
                    ("deadline", "deadline_selector", deadline_text, str(deadline or "")),
                )
                for field_name, selector_key, raw_value, parsed_value in optional_notice_fields:
                    if selected(node, selector_key) is not None:
                        field_evidence[field_name] = FieldEvidenceValue(
                            raw_value,
                            f"{locator} {config[selector_key]}",
                            parsed_value,
                        )
                field_evidence["notice_url"] = FieldEvidenceValue(
                    notice_href,
                    f"{locator} {config['notice_url_selector']}@href",
                    notice_url,
                )

            position_selector = str(config.get("position_selector", "")).strip()
            position_nodes = (
                node.select(position_selector) if position_selector else [node]
            )
            positions: list[PositionCandidate] = []
            for position_index, position_node in enumerate(
                position_nodes, start=1
            ):
                position_attribute = config.get("position_id_attribute")
                position_key = (
                    str(position_node.get(position_attribute, "")).strip()
                    if position_attribute
                    else text_value(position_node, "position_id_selector")
                )
                if position_selector and position_attribute and position_key:
                    position_locator = (
                        f"{locator} {position_selector}"
                        f"[{position_attribute}='{position_key}']"
                    )
                elif position_selector:
                    position_locator = (
                        f"{locator} {position_selector}:nth-of-type("
                        f"{position_index})"
                    )
                else:
                    position_locator = locator

                position_title_node = selected(
                    position_node, "position_title_selector"
                )
                position_title = (
                    position_title_node.get_text(" ", strip=True)
                    if position_title_node
                    else ""
                )
                location_node = selected(position_node, "location_selector")
                location = (
                    location_node.get_text(" ", strip=True)
                    if location_node
                    else ""
                )
                app_node = selected(position_node, "application_selector")
                application_href = (
                    str(app_node.get("href"))
                    if app_node and app_node.get("href")
                    else None
                )
                app_url = (
                    urljoin(page.canonical_url, application_href)
                    if application_href
                    else None
                )
                position_evidence = {}
                if identity_key and position_key and position_title_node is not None:
                    position_evidence["position_title"] = FieldEvidenceValue(
                        position_title,
                        f"{position_locator} {config['position_title_selector']}",
                        position_title,
                    )
                if identity_key and position_key and location_node is not None:
                    position_evidence["location"] = FieldEvidenceValue(
                        location,
                        f"{position_locator} {config['location_selector']}",
                        location,
                    )
                if identity_key and position_key and application_href:
                    position_evidence["application_link"] = FieldEvidenceValue(
                        application_href,
                        (
                            f"{position_locator} "
                            f"{config.get('application_selector', '')}@href"
                        ).strip(),
                        app_url,
                    )
                application_locator = (
                    f"{position_locator} "
                    f"{config.get('application_selector', '')}"
                ).strip()
                positions.append(
                    PositionCandidate(
                        position_title,
                        location,
                        position_node.get_text(" ", strip=True),
                        app_url,
                        position_locator,
                        application_locator,
                        position_key,
                        position_evidence,
                    )
                )

            candidates.append(
                NoticeCandidate(
                    title=title_node.get_text(" ", strip=True),
                    official_notice_url=notice_url,
                    recruitment_type=recruitment_type_text,
                    target_audience=target_audience,
                    published_on=published_on,
                    deadline=deadline,
                    withdrawn=withdrawn,
                    evidence_excerpt=text_value(node, "excerpt_selector"),
                    positions=tuple(positions),
                    field_locators={
                        "title": f"{locator} {config['title_selector']}",
                        "recruitment_type": (
                            f"{locator} {config['recruitment_type_selector']}"
                        ),
                        "notice_url": (
                            f"{locator} {config['notice_url_selector']}"
                        ),
                        "deadline": (
                            f"{locator} {config.get('deadline_selector', '')}"
                        ).strip(),
                    },
                    identity_key=identity_key,
                    field_evidence=field_evidence,
                    positions_complete=bool(
                        config.get("positions_complete", False)
                    ),
                )
            )
        return candidates
