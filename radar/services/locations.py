import re
from collections.abc import Iterable


SPECIAL_LOCATIONS = {"全国", "远程"}
SUFFIXES = ("特别行政区", "自治区", "自治州", "地区", "省", "盟", "市")


def _parts(value: str | Iterable[str] | None) -> list[str]:
    values = [value] if isinstance(value, str) or value is None else list(value)
    parts: list[str] = []
    for item in values:
        parts.extend(
            part.strip()
            for part in re.split(r"[\s,，、/|;；·]+", str(item or ""))
            if part.strip()
        )
    return parts


def normalize_locations(value: str | Iterable[str] | None) -> list[str]:
    """Normalize common Chinese place suffixes while retaining unknown text."""
    result: list[str] = []
    for part in _parts(value):
        normalized = part
        if normalized not in SPECIAL_LOCATIONS:
            for suffix in SUFFIXES:
                if normalized.endswith(suffix) and len(normalized) > len(suffix):
                    normalized = normalized[: -len(suffix)]
                    break
        if normalized and normalized not in result:
            result.append(normalized)
    return result


def normalized_target_locations(value: str | Iterable[str] | None) -> list[str]:
    """Compatibility name: Phase 02 accepts every location, not only four cities."""
    return normalize_locations(value)


def is_target_location(value: str | Iterable[str] | None) -> bool:
    return bool(normalize_locations(value))


def matches_selected_cities(locations: Iterable[str], selected: Iterable[str]) -> bool:
    selected_set = {city for city in selected if city}
    if not selected_set:
        return True
    location_set = set(locations)
    has_concrete_city = bool(selected_set - SPECIAL_LOCATIONS)
    return bool(location_set & selected_set) or (
        has_concrete_city and bool(location_set & SPECIAL_LOCATIONS)
    )
