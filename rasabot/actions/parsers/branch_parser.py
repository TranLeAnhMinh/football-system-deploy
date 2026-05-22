import re
from actions.services.branch_service import get_branches


def normalize_branch_name(raw_text: str | None) -> str | None:
    if not raw_text:
        return None

    text = re.sub(r"\s+", " ", raw_text.strip())
    lower_text = text.lower()

    match_number = re.match(
        r"^(q|quận|quan|district|branch district)\s*(\d+)$",
        lower_text,
    )
    if match_number:
        district_number = match_number.group(2)
        return f"Quận {district_number}"

    match_japanese_number = re.match(r"^第\s*(\d+)\s*区$", text)
    if match_japanese_number:
        district_number = match_japanese_number.group(1)
        return f"Quận {district_number}"

    branches = get_branches()
    for _, branch_name, *_ in branches:
        if branch_name.lower() == lower_text:
            return branch_name

    return text.title()


def extract_branch_name_from_text(text: str | None) -> str | None:
    if not text:
        return None

    raw = re.sub(r"\s+", " ", text.strip())
    lowered = raw.lower()

    branches = get_branches()

    # Ưu tiên so khớp đúng tên chi nhánh trong DB
    for _, branch_name, *_ in branches:
        if branch_name.lower() in lowered:
            return branch_name

    # Bắt q1, q 1, quận 1, quan 1
    match_number = re.search(r"\b(q|quận|quan)\s*(\d+)\b", lowered)
    if match_number:
        return f"Quận {match_number.group(2)}"

    # Bắt tiếng Anh: district 1, branch district 1
    match_en_district = re.search(r"\b(?:branch\s+)?district\s*(\d+)\b", lowered)
    if match_en_district:
        return f"Quận {match_en_district.group(1)}"

    # Bắt tiếng Nhật: 第1区, 第 1 区
    match_ja_district = re.search(r"第\s*(\d+)\s*区", raw)
    if match_ja_district:
        return f"Quận {match_ja_district.group(1)}"

    # Bắt tên không số: quận long biên, q long biên, district long bien
    match_named_district = re.search(
        r"\b(q|quận|quan|district)\s+([a-zàáạảãăắằặẳẵâấầậẩẫđèéẹẻẽêếềệểễìíịỉĩòóọỏõôốồộổỗơớờợởỡùúụủũưứừựửữỳýỵỷỹ\s]+)",
        lowered,
    )
    if match_named_district:
        district_name = match_named_district.group(2).strip()
        candidate = f"Quận {district_name.title()}"

        for _, branch_name, *_ in branches:
            if branch_name.lower() == candidate.lower():
                return branch_name

        return candidate

    return None


def looks_like_branch_query(text: str | None) -> bool:
    if not text:
        return False

    lowered = text.lower()

    keywords = [
        "sân",
        "chi nhánh",
        "cơ sở",
        "quận",
        "q",
        "pitch",
        "branch",
        "district",
        "location",
        "サッカー場",
        "店舗",
        "支店",
        "区",
    ]

    return any(keyword in lowered for keyword in keywords)


def has_branch_like_pattern(text: str | None) -> bool:
    if not text:
        return False

    raw = text.strip()
    lowered = raw.lower()

    if re.search(r"\b(q|quận|quan)\s*[a-z0-9]+\b", lowered):
        return True

    if re.search(r"\b(?:branch\s+)?district\s*[a-z0-9]+\b", lowered):
        return True

    if re.search(r"第\s*\d+\s*区", raw):
        return True

    branches = get_branches()
    for _, branch_name, *_ in branches:
        if branch_name.lower() in lowered:
            return True

    return False