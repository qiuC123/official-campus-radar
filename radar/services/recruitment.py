def classify_recruitment(value: str) -> str:
    normalized = (value or "").strip().casefold()
    if any(term in normalized for term in ("招商", "招标", "招聘会", "采购")):
        return "other"
    known_types = {
        "spring",
        "spring_supplement",
        "summer",
        "autumn",
        "autumn_supplement",
        "autumn_early",
        "campus_recruitment",
        "internship",
        "special_program",
    }
    if normalized in known_types:
        return normalized
    if any(term in normalized for term in ("春招补录", "春季补录")):
        return "spring_supplement"
    if any(term in normalized for term in ("秋招补录", "秋季补录")):
        return "autumn_supplement"
    if any(term in normalized for term in ("秋招提前批", "秋季提前批")):
        return "autumn_early"
    if any(term in normalized for term in ("夏招", "夏季校园招聘")):
        return "summer"
    if any(term in normalized for term in ("春招", "春季校园招聘")):
        return "spring"
    if any(term in normalized for term in ("秋招", "秋季校园招聘")):
        return "autumn"
    if any(term in normalized for term in ("实习", "intern")):
        return "internship"
    if any(
        term in normalized
        for term in ("校园招聘", "校招", "应届生", "graduate program")
    ):
        return "campus_recruitment"
    if any(term in normalized for term in ("社会招聘", "社招", "招聘")):
        return "other"
    return "unknown"
