import re


TARGET_LOCATION_ALIASES = {
    "北京": {"北京", "北京市"},
    "上海": {"上海", "上海市"},
    "广州": {"广州", "广州市"},
    "深圳": {"深圳", "深圳市"},
}


def normalized_target_locations(location_text: str) -> list[str]:
    normalized = re.sub(r"[\s,，、/|]+", " ", location_text or "")
    return [city for city, aliases in TARGET_LOCATION_ALIASES.items() if any(alias in normalized for alias in aliases)]


def is_target_location(location_text: str) -> bool:
    return bool(normalized_target_locations(location_text))
