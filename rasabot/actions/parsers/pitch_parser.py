import re


GENERIC_PITCH_PHRASES = {
    "sân",
    "sân nào",
    "các sân",
    "nhiều sân",
    "mọi sân",
    "xem sân",
    "có sân",
    "sân này",
}


def _normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip())


def normalize_pitch_name(pitch_name: str | None) -> str | None:
    if not pitch_name:
        return None

    pitch_name = _normalize_text(pitch_name)
    pitch_name = pitch_name.strip(" ,.?;:!-")

    if not pitch_name:
        return None

    return pitch_name


def _is_generic_pitch_phrase(text: str) -> bool:
    lowered = text.lower().strip()
    return lowered in GENERIC_PITCH_PHRASES


def has_pitch_like_pattern(text: str | None) -> bool:
    if not text:
        return False

    lowered = text.lower()

    patterns = [
        r"\bsân\s+[^\s].+",
        r"\bpitch\s+[^\s].+",
    ]

    return any(re.search(pattern, lowered) for pattern in patterns)


def looks_like_pitch_query(text: str | None) -> bool:
    if not text:
        return False

    lowered = text.lower()

    keywords = [
        "có trống không",
        "có rảnh không",
        "còn trống không",
        "còn rảnh không",
        "rảnh không",
        "trống không",
        "đặt được không",
        "book được không",
    ]

    has_pitch_word = "sân" in lowered or "pitch" in lowered
    has_query_keyword = any(keyword in lowered for keyword in keywords)

    return has_pitch_word and has_query_keyword


def extract_pitch_name_from_text(text: str | None) -> str | None:
    """
    Extract tên sân cụ thể từ câu user.

    Ví dụ:
    - 'Sân 5 Thủ Đức A tối mai 18h đến 20h có rảnh không'
      -> 'Sân 5 Thủ Đức A'
    - 'Sân F88 ngày mai từ 18:00 đến 19:30 có trống không'
      -> 'Sân F88'
    - 'cho tôi hỏi sân A1 có trống không'
      -> 'sân A1'

    Không match:
    - 'có sân nào không'
    - 'sân ở quận 1'
    - 'xem sân giúp tôi'
    """
    if not text:
        return None

    raw_text = _normalize_text(text)
    lowered = raw_text.lower()

    # Chặn câu hỏi chung chung, không phải tên sân cụ thể
    generic_patterns = [
        r"\bcó sân nào\b",
        r"\bsân nào\b",
        r"\bxem sân\b",
        r"\bcác sân\b",
        r"\bsân ở\b",
        r"\bsân tại\b",
        r"\bsân theo\b",
    ]

    if any(re.search(pattern, lowered) for pattern in generic_patterns):
        return None

    # Các mốc nên dừng khi parse tên sân
    stop_patterns = [
        r"ngày\s+\d{1,2}[/\-]\d{1,2}[/\-]\d{4}",
        r"ngày\s+\d{4}[/\-]\d{1,2}[/\-]\d{1,2}",
        r"\d{4}[/\-]\d{1,2}[/\-]\d{1,2}",
        r"\d{1,2}[/\-]\d{1,2}[/\-]\d{4}",

        r"hôm nay",
        r"ngày mai",
        r"mai",
        r"ngày mốt",
        r"mốt",

        r"sáng nay",
        r"sáng mai",
        r"trưa nay",
        r"trưa mai",
        r"chiều nay",
        r"chiều mai",
        r"tối nay",
        r"tối mai",

        r"thứ\s+\d",
        r"thu\s+\d",

        r"từ\s+\d{1,2}",
        r"lúc\s+\d{1,2}",
        r"khoảng\s+\d{1,2}",
        r"\d{1,2}:\d{2}",
        r"\d{1,2}h",

        r"có trống không",
        r"có rảnh không",
        r"còn trống không",
        r"còn rảnh không",
        r"rảnh không",
        r"trống không",
        r"đặt được không",
        r"book được không",
    ]

    stop_regex = "|".join(stop_patterns)

    # Bắt từ "sân ..." đến trước mốc ngày/giờ/từ khóa hỏi
    pattern = rf"\b(sân\s+.+?)(?=\s+(?:{stop_regex})|$)"

    match = re.search(pattern, raw_text, flags=re.IGNORECASE)
    if match:
        pitch_name = normalize_pitch_name(match.group(1))

        if pitch_name and not _is_generic_pitch_phrase(pitch_name):
            return pitch_name

    # Fallback nhẹ: chỉ dùng nếu câu có keyword hỏi trạng thái sân
    if looks_like_pitch_query(raw_text):
        fallback = re.search(
            r"\b(sân\s+[^\?,\.!]+)",
            raw_text,
            flags=re.IGNORECASE,
        )

        if fallback:
            pitch_name = normalize_pitch_name(fallback.group(1))

            if pitch_name:
                # Cắt tiếp nếu fallback vẫn dính mốc thời gian
                pitch_name = re.split(
                    rf"\s+(?:{stop_regex})",
                    pitch_name,
                    maxsplit=1,
                    flags=re.IGNORECASE,
                )[0].strip()

                pitch_name = normalize_pitch_name(pitch_name)

                if pitch_name and not _is_generic_pitch_phrase(pitch_name):
                    return pitch_name

    return None