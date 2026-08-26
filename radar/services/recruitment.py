def classify_recruitment(value: str) -> str:
    normalized = (value or "").strip().casefold()
    if any(term in normalized for term in ("招商", "招标", "招聘会", "采购")):
        return "other"
    if normalized in {"campus_recruitment", "internship"}:
        return normalized
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
