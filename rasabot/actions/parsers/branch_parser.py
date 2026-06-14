import re
import unicodedata

from actions.services.branch_service import get_branches


VIETNAMESE_LETTERS = (
    "a-z"
    "àáạảãăắằặẳẵâấầậẩẫ"
    "đ"
    "èéẹẻẽêếềệểễ"
    "ìíịỉĩ"
    "òóọỏõôốồộổỗơớờợởỡ"
    "ùúụủũưứừựửữ"
    "ỳýỵỷỹ"
)


STOP_WORDS = [
    "có",
    "co",
    "còn",
    "con",
    "sân",
    "san",
    "sáng",
    "sang",
    "trưa",
    "trua",
    "chiều",
    "chieu",
    "tối",
    "toi",
    "hôm",
    "hom",
    "ngày",
    "ngay",
    "mai",
    "nay",
    "từ",
    "tu",
    "lúc",
    "luc",
    "mấy",
    "may",
    "giờ",
    "gio",
    "trống",
    "trong",
    "rảnh",
    "ranh",
    "nào",
    "nao",
    "gì",
    "gi",
    "không",
    "khong",
]


def _normalize_spaces(text: str | None) -> str:
    if not text:
        return ""

    return re.sub(r"\s+", " ", text.strip())


def _lower(text: str | None) -> str:
    return _normalize_spaces(text).lower()


def _remove_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    without_marks = "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    )
    return without_marks.replace("đ", "d").replace("Đ", "D")


def _canonical_for_compare(text: str | None) -> str:
    text = _lower(text)
    text = _remove_accents(text)
    return text


def _branch_aliases(branch_name: str) -> list[str]:
    branch_lower = _lower(branch_name)
    branch_no_accent = _canonical_for_compare(branch_name)

    aliases = {
        branch_lower,
        branch_no_accent,
    }

    match_number = re.fullmatch(r"quận\s*(\d+)", branch_lower)
    if match_number:
        number = match_number.group(1)
        aliases.update({
            f"q{number}",
            f"q {number}",
            f"quan {number}",
            f"quận {number}",
            f"district {number}",
            f"branch district {number}",
            f"第{number}区",
            f"第 {number} 区",
        })

    match_named = re.fullmatch(r"quận\s+(.+)", branch_lower)
    if match_named:
        name = match_named.group(1)
        name_no_accent = _remove_accents(name)

        aliases.update({
            name,
            name_no_accent,
            f"q {name}",
            f"q {name_no_accent}",
            f"quan {name_no_accent}",
            f"quận {name}",
            f"district {name_no_accent}",
        })

    # Alias riêng cho Thanh Xuân tiếng Nhật bạn đang dùng trong NLU
    if branch_no_accent == "quan thanh xuan":
        aliases.update({
            "thanh xuan",
            "q thanh xuan",
            "quan thanh xuan",
            "district thanh xuan",
            "タインスアン区",
            "タインスアン",
        })

    return sorted(aliases, key=len, reverse=True)


def _contains_alias(text: str, alias: str) -> bool:
    if not alias:
        return False

    # Japanese does not need word boundary.
    if re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", alias):
        return alias in text

    escaped = re.escape(alias)
    return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text) is not None


def _get_branch_by_alias(text: str | None) -> str | None:
    raw = _lower(text)
    canonical = _canonical_for_compare(text)

    branches = get_branches()

    # Ưu tiên tên/alias dài trước để tránh Quận 1 ăn nhầm Quận 10.
    branch_candidates = sorted(
        branches,
        key=lambda row: len(row[1]),
        reverse=True,
    )

    for _, branch_name, *_ in branch_candidates:
        aliases = _branch_aliases(branch_name)

        for alias in aliases:
            alias_canonical = _canonical_for_compare(alias)

            if _contains_alias(raw, alias) or _contains_alias(canonical, alias_canonical):
                return branch_name

    return None


def normalize_branch_name(raw_text: str | None) -> str | None:
    if not raw_text:
        return None

    text = _normalize_spaces(raw_text)
    lower_text = text.lower()

    matched_branch = _get_branch_by_alias(text)
    if matched_branch:
        return matched_branch

    match_number = re.fullmatch(
        r"(q|quận|quan|district|branch district)\s*(\d+)",
        lower_text,
    )
    if match_number:
        district_number = match_number.group(2)
        return f"Quận {district_number}"

    match_japanese_number = re.fullmatch(r"第\s*(\d+)\s*区", text)
    if match_japanese_number:
        district_number = match_japanese_number.group(1)
        return f"Quận {district_number}"

    return text.title()


def extract_branch_name_from_text(text: str | None) -> str | None:
    if not text:
        return None

    raw = _normalize_spaces(text)
    lowered = raw.lower()

    matched_branch = _get_branch_by_alias(raw)
    if matched_branch:
        return matched_branch

    # Bắt q1, q 1, quận 1, quan 1
    match_number = re.search(r"\b(q|quận|quan)\s*(\d+)\b", lowered)
    if match_number:
        return normalize_branch_name(f"Quận {match_number.group(2)}")

    # Bắt tiếng Anh: district 1, branch district 1
    match_en_district = re.search(r"\b(?:branch\s+)?district\s*(\d+)\b", lowered)
    if match_en_district:
        return normalize_branch_name(f"Quận {match_en_district.group(1)}")

    # Bắt tiếng Nhật: 第1区, 第 1 区
    match_ja_district = re.search(r"第\s*(\d+)\s*区", raw)
    if match_ja_district:
        return normalize_branch_name(f"Quận {match_ja_district.group(1)}")

    # Bắt tên không số: quận long biên, q long biên, district long bien
    pattern = rf"\b(q|quận|quan|district)\s+([{VIETNAMESE_LETTERS}\s]+)"
    match_named_district = re.search(pattern, lowered)

    if match_named_district:
        district_name = match_named_district.group(2).strip()

        # Cắt tại các từ khóa phía sau, ví dụ:
        # "quận thanh xuân có sân nào" -> "thanh xuân"
        words = district_name.split()
        cleaned_words = []

        for word in words:
            if word in STOP_WORDS:
                break
            cleaned_words.append(word)

        district_name = " ".join(cleaned_words).strip()

        if not district_name:
            return None

        candidate = f"Quận {district_name.title()}"
        return normalize_branch_name(candidate)

    return None


def looks_like_branch_query(text: str | None) -> bool:
    if not text:
        return False

    lowered = _lower(text)

    keywords = [
        "sân",
        "san",
        "chi nhánh",
        "chi nhanh",
        "cơ sở",
        "co so",
        "quận",
        "quan",
        "pitch",
        "branch",
        "district",
        "location",
        "サッカー場",
        "店舗",
        "支店",
        "区",
    ]

    if any(keyword in lowered for keyword in keywords):
        return True

    return _get_branch_by_alias(lowered) is not None


def has_branch_like_pattern(text: str | None) -> bool:
    if not text:
        return False

    raw = _normalize_spaces(text)
    lowered = raw.lower()

    if _get_branch_by_alias(raw):
        return True

    if re.search(r"\b(q|quận|quan)\s*[a-z0-9]+\b", lowered):
        return True

    if re.search(r"\b(?:branch\s+)?district\s*[a-z0-9]+\b", lowered):
        return True

    if re.search(r"第\s*\d+\s*区", raw):
        return True

    return False