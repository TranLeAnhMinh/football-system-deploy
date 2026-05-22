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
    "pitch",
    "which pitch",
    "any pitch",
    "this pitch",
    "football pitch",
    "サッカー場",
    "このサッカー場",
    "空いているサッカー場",
}


def _normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip())


def normalize_pitch_name(pitch_name: str | None) -> str | None:
    if not pitch_name:
        return None

    pitch_name = _normalize_text(pitch_name)
    pitch_name = pitch_name.strip(" ,.?;:!-。、「」『』")

    if not pitch_name:
        return None

    lowered = pitch_name.lower()

    # English -> Vietnamese DB naming
    if lowered.startswith("pitch "):
        pitch_name = "Sân " + pitch_name[6:]

    if lowered.startswith("football pitch "):
        pitch_name = "Sân " + pitch_name[15:]

    # Japanese -> Vietnamese DB naming
    pitch_name = re.sub(
        r"^サッカー場\s*",
        "Sân ",
        pitch_name,
        flags=re.IGNORECASE,
    )

    pitch_name = re.sub(
        r"\s*サッカー場$",
        "",
        pitch_name,
        flags=re.IGNORECASE,
    )

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
        r"\bfootball\s+pitch\s+[^\s].+",
        r"\b[a-z0-9\-]+\s+pitch\b",
        r"[a-zA-Z0-9\-]+\s*サッカー場",
        r"サッカー場\s*[a-zA-Z0-9\-]+",
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
        "available",
        "free",
        "can i book",
        "can book",
        "bookable",
        "空いていますか",
        "空いてる",
        "予約できますか",
        "予約できる",
    ]

    has_pitch_word = (
        "sân" in lowered
        or "pitch" in lowered
        or "football pitch" in lowered
        or "サッカー場" in text
    )
    has_query_keyword = any(keyword in lowered for keyword in keywords)

    return has_pitch_word and has_query_keyword


def extract_pitch_name_from_text(text: str | None) -> str | None:
    if not text:
        return None

    raw_text = _normalize_text(text)
    lowered = raw_text.lower()

    generic_patterns = [
        r"\bcó sân nào\b",
        r"\bsân nào\b",
        r"\bxem sân\b",
        r"\bcác sân\b",
        r"\bsân ở\b",
        r"\bsân tại\b",
        r"\bsân theo\b",
        r"\bany pitch\b",
        r"\bwhich pitch\b",
        r"\bshow me pitches\b",
        r"\bpitches in\b",
        r"\bavailable pitches\b",
        r"空いているサッカー場",
        r"サッカー場一覧",
    ]

    if any(re.search(pattern, lowered) for pattern in generic_patterns):
        return None

    stop_patterns = [
        r"ngày\s+\d{1,2}[/\-]\d{1,2}[/\-]\d{4}",
        r"ngày\s+\d{4}[/\-]\d{1,2}[/\-]\d{1,2}",
        r"\d{4}[/\-]\d{1,2}[/\-]\d{1,2}",
        r"\d{1,2}[/\-]\d{1,2}[/\-]\d{4}",
        r"\d{4}年\s*\d{1,2}月\s*\d{1,2}日",

        r"hôm qua",
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

        r"yesterday",
        r"today",
        r"tonight",
        r"tomorrow",
        r"day after tomorrow",

        r"昨日",
        r"今日",
        r"今夜",
        r"明日",
        r"明後日",

        r"thứ\s+\d",
        r"thu\s+\d",
        r"monday",
        r"tuesday",
        r"wednesday",
        r"thursday",
        r"friday",
        r"saturday",
        r"sunday",
        r"月曜日",
        r"火曜日",
        r"水曜日",
        r"木曜日",
        r"金曜日",
        r"土曜日",
        r"日曜日",

        r"từ\s+\d{1,2}",
        r"from\s+\d{1,2}",
        r"lúc\s+\d{1,2}",
        r"khoảng\s+\d{1,2}",
        r"\d{1,2}:\d{2}",
        r"\d{1,2}h",
        r"\d{1,2}時",

        r"có trống không",
        r"có rảnh không",
        r"còn trống không",
        r"còn rảnh không",
        r"rảnh không",
        r"trống không",
        r"đặt được không",
        r"book được không",

        r"is available",
        r"available",
        r"is free",
        r"free",
        r"can i book",
        r"can book",
        r"bookable",

        r"空いていますか",
        r"空いてる",
        r"予約できますか",
        r"予約できる",
    ]

    stop_regex = "|".join(stop_patterns)

    patterns = [
        # Vietnamese: sân A1 ngày mai...
        rf"\b(sân\s+.+?)(?=\s+(?:{stop_regex})|$)",

        # English: pitch A1 tomorrow...
        rf"\b(pitch\s+.+?)(?=\s+(?:{stop_regex})|$)",

        # English: football pitch A1 tomorrow...
        rf"\b(football\s+pitch\s+.+?)(?=\s+(?:{stop_regex})|$)",

        # English: A1 pitch tomorrow...
        rf"\b([a-zA-Z0-9][a-zA-Z0-9\s\-]*?\s+pitch)(?=\s+(?:{stop_regex})|$)",

        # Japanese: A1サッカー場は明日...
        rf"([a-zA-Z0-9\-]+\s*サッカー場)(?=(?:は|が|を|で|に|の|、|\s|{stop_regex})|$)",

        # Japanese: サッカー場A1は明日...
        rf"(サッカー場\s*[a-zA-Z0-9\-]+)(?=(?:は|が|を|で|に|の|、|\s|{stop_regex})|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, raw_text, flags=re.IGNORECASE)
        if not match:
            continue

        pitch_name = normalize_pitch_name(match.group(1))

        if pitch_name and not _is_generic_pitch_phrase(pitch_name):
            return pitch_name

    if looks_like_pitch_query(raw_text):
        fallback_patterns = [
            r"\b(sân\s+[^\?,\.!。]+)",
            r"\b(pitch\s+[^\?,\.!。]+)",
            r"\b(football\s+pitch\s+[^\?,\.!。]+)",
            r"\b([a-zA-Z0-9][a-zA-Z0-9\s\-]*?\s+pitch)",
            r"([a-zA-Z0-9\-]+\s*サッカー場)",
            r"(サッカー場\s*[a-zA-Z0-9\-]+)",
        ]

        for fallback_pattern in fallback_patterns:
            fallback = re.search(
                fallback_pattern,
                raw_text,
                flags=re.IGNORECASE,
            )

            if not fallback:
                continue

            pitch_name = normalize_pitch_name(fallback.group(1))

            if pitch_name:
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