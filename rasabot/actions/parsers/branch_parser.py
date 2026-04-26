import re
from actions.services.branch_service import get_branches


def normalize_branch_name(raw_text: str | None) -> str | None:
    if not raw_text:
        return None

    text = raw_text.strip()
    text = re.sub(r"\s+", " ", text)
    lower_text = text.lower()

    # q1, q 1, quận 1, quan 1
    match_number = re.match(r"^(q|quận|quan)\s*(\d+)$", lower_text)
    if match_number:
        district_number = match_number.group(2)
        return f"Quận {district_number}"

    # bỏ prefix q / quận / quan
    text_no_prefix = re.sub(r"^(q|quận|quan)\s+", "", lower_text).strip()

    special_map = {
        "thủ đức": "Quận Thủ Đức",
        "thu duc": "Quận Thủ Đức",
        "đống đa": "Quận Đống Đa",
        "dong da": "Quận Đống Đa",
        "hai bà trưng": "Quận Hai Bà Trưng",
        "hai ba trung": "Quận Hai Bà Trưng",
        "hbt": "Quận Hai Bà Trưng",
        "hoàng mai": "Quận Hoàng Mai",
        "hoang mai": "Quận Hoàng Mai",
    }

    if text_no_prefix in special_map:
        return special_map[text_no_prefix]

    return text.title()


def extract_branch_name_from_text(text: str | None) -> str | None:
    if not text:
        return None

    raw = text.strip()
    lowered = raw.lower()

    # Bắt q1, quận 1, ...
    match_number = re.search(r"\b(q|quận|quan)\s*(\d+)\b", lowered)
    if match_number:
        district_number = match_number.group(2)
        return f"Quận {district_number}"

    # Special cases cứng
    special_patterns = {
        "thủ đức": "Quận Thủ Đức",
        "thu duc": "Quận Thủ Đức",
        "đống đa": "Quận Đống Đa",
        "dong da": "Quận Đống Đa",
        "hai bà trưng": "Quận Hai Bà Trưng",
        "hai ba trung": "Quận Hai Bà Trưng",
        "hbt": "Quận Hai Bà Trưng",
        "hoàng mai": "Quận Hoàng Mai",
        "hoang mai": "Quận Hoàng Mai",
    }

    for pattern, normalized in special_patterns.items():
        if pattern in lowered:
            return normalized

    # So khớp động với branch trong DB
    branches = get_branches()
    for _, branch_name, *_ in branches:
        if branch_name.lower() in lowered:
            return branch_name

    # bắt kiểu "quận long biên", "q long biên"
    match_named_district = re.search(r"\b(q|quận|quan)\s+([a-zàáạảãăắằặẳẵâấầậẩẫđèéẹẻẽêếềệểễìíịỉĩòóọỏõôốồộổỗơớờợởỡùúụủũưứừựửữỳýỵỷỹ\s]+)", lowered)
    if match_named_district:
        district_name = match_named_district.group(2).strip()
        return f"Quận {district_name.title()}"

    return None


def looks_like_branch_query(text: str | None) -> bool:
    if not text:
        return False

    lowered = text.lower()
    keywords = ["sân", "chi nhánh", "cơ sở", "quận", "q"]

    return any(keyword in lowered for keyword in keywords)


def has_branch_like_pattern(text: str | None) -> bool:
    if not text:
        return False

    lowered = text.lower()

    if re.search(r"\b(q|quận|quan)\s*[a-z0-9]+\b", lowered):
        return True

    special_words = [
        "thủ đức",
        "thu duc",
        "đống đa",
        "dong da",
        "hai bà trưng",
        "hai ba trung",
        "hbt",
        "hoàng mai",
        "hoang mai",
    ]

    return any(word in lowered for word in special_words)