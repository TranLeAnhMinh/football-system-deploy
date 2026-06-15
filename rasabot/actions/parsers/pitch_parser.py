import re


GENERIC_PITCH_PHRASES = {
    "sân",
    "san",
    "sân nào",
    "san nao",
    "các sân",
    "cac san",
    "nhiều sân",
    "nhieu san",
    "mọi sân",
    "moi san",
    "xem sân",
    "xem san",
    "có sân",
    "co san",
    "sân này",
    "san nay",
    "sân đó",
    "san do",
    "sân kia",
    "san kia",
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


def _clean_pitch_name(pitch_name: str | None) -> str | None:
    if not pitch_name:
        return None

    pitch_name = _normalize_text(pitch_name)
    pitch_name = pitch_name.strip(" ,.?;:!-。、「」『』")

    cleanup_patterns = [
        r"\bthì\s+sao\b",
        r"\bthi\s+sao\b",
        r"\bthế\s+nào\b",
        r"\bthe\s+nao\b",
        r"\bvậy\s+thì\s+sao\b",
        r"\bvay\s+thi\s+sao\b",
        r"\bvậy\s+sao\b",
        r"\bvay\s+sao\b",
        r"\bcó\s+trống\s+không\b",
        r"\bco\s+trong\s+khong\b",
        r"\bcó\s+rảnh\s+không\b",
        r"\bco\s+ranh\s+khong\b",
        r"\bcòn\s+trống\s+không\b",
        r"\bcon\s+trong\s+khong\b",
        r"\bcòn\s+rảnh\s+không\b",
        r"\bcon\s+ranh\s+khong\b",
        r"\brảnh\s+không\b",
        r"\branh\s+khong\b",
        r"\btrống\s+không\b",
        r"\btrong\s+khong\b",
        r"\bđặt\s+được\s+không\b",
        r"\bdat\s+duoc\s+khong\b",
        r"\bbook\s+được\s+không\b",
        r"\bbook\s+duoc\s+khong\b",
        r"\bis\s+available\b",
        r"\bavailable\b",
        r"\bis\s+free\b",
        r"\bfree\b",
        r"\bcan\s+i\s+book\b",
        r"\bcan\s+book\b",
        r"\bbookable\b",
        r"空いていますか",
        r"空いてる",
        r"予約できますか",
        r"予約できる",
        r"はどうですか",
        r"どうですか",
    ]

    cleanup_regex = "|".join(cleanup_patterns)
    pitch_name = re.split(cleanup_regex, pitch_name, maxsplit=1, flags=re.IGNORECASE)[0]

    pitch_name = _normalize_text(pitch_name)
    pitch_name = pitch_name.strip(" ,.?;:!-。、「」『』")

    if not pitch_name:
        return None

    return pitch_name


def normalize_pitch_name(pitch_name: str | None) -> str | None:
    if not pitch_name:
        return None

    pitch_name = _clean_pitch_name(pitch_name)
    if not pitch_name:
        return None

    lowered = pitch_name.lower()

    if lowered.startswith("pitch "):
        pitch_name = "Sân " + pitch_name[6:]

    if lowered.startswith("football pitch "):
        pitch_name = "Sân " + pitch_name[15:]

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

    pitch_name = _clean_pitch_name(pitch_name)
    if not pitch_name:
        return None

    return pitch_name


def _is_generic_pitch_phrase(text: str) -> bool:
    lowered = text.lower().strip()
    return lowered in GENERIC_PITCH_PHRASES


def has_pitch_like_pattern(text: str | None) -> bool:
    if not text:
        return False

    patterns = [
        r"\bsân\s+[^\s].+",
        r"\bsan\s+[^\s].+",
        r"\bpitch\s+[^\s].+",
        r"\bfootball\s+pitch\s+[^\s].+",
        r"\b[a-z0-9\-]+\s+pitch\b",
        r"[a-zA-Z0-9\-]+\s*サッカー場",
        r"サッカー場\s*[a-zA-Z0-9\-]+",
        r"\b[A-Z0-9][A-Z0-9\-]*\b\s*(?:thì sao|thi sao|はどうですか|どうですか)",
    ]

    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def looks_like_pitch_query(text: str | None) -> bool:
    if not text:
        return False

    lowered = text.lower()

    keywords = [
        "có trống không",
        "co trong khong",
        "có rảnh không",
        "co ranh khong",
        "còn trống không",
        "con trong khong",
        "còn rảnh không",
        "con ranh khong",
        "rảnh không",
        "ranh khong",
        "trống không",
        "trong khong",
        "đặt được không",
        "dat duoc khong",
        "book được không",
        "book duoc khong",
        "thì sao",
        "thi sao",
        "available",
        "free",
        "can i book",
        "can book",
        "bookable",
        "空いていますか",
        "空いてる",
        "予約できますか",
        "予約できる",
        "どうですか",
    ]

    has_pitch_word = (
        "sân" in lowered
        or "san" in lowered
        or "pitch" in lowered
        or "football pitch" in lowered
        or "サッカー場" in text
    )

    has_short_pitch_follow_up = re.search(
        r"\b[A-Z0-9][A-Z0-9\-]*\b\s*(?:thì sao|thi sao)",
        text,
        flags=re.IGNORECASE,
    ) is not None

    has_query_keyword = any(keyword in lowered for keyword in keywords)

    return (has_pitch_word and has_query_keyword) or has_short_pitch_follow_up


def extract_pitch_name_from_text(text: str | None) -> str | None:
    if not text:
        return None

    raw_text = _normalize_text(text)
    lowered = raw_text.lower()

    generic_patterns = [
        r"\bcó sân nào\b",
        r"\bco san nao\b",
        r"\bsân nào\b",
        r"\bsan nao\b",
        r"\bxem sân\b",
        r"\bxem san\b",
        r"\bcác sân\b",
        r"\bcac san\b",
        r"\bsân ở\b",
        r"\bsan o\b",
        r"\bsân tại\b",
        r"\bsan tai\b",
        r"\bsân theo\b",
        r"\bsan theo\b",
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
        r"ngay\s+\d{1,2}[/\-]\d{1,2}[/\-]\d{4}",
        r"ngày\s+\d{4}[/\-]\d{1,2}[/\-]\d{1,2}",
        r"ngay\s+\d{4}[/\-]\d{1,2}[/\-]\d{1,2}",
        r"\d{4}[/\-]\d{1,2}[/\-]\d{1,2}",
        r"\d{1,2}[/\-]\d{1,2}[/\-]\d{4}",
        r"\d{4}年\s*\d{1,2}月\s*\d{1,2}日",

        r"ngày\s+\d{1,2}[/\-]\d{1,2}",
        r"ngay\s+\d{1,2}[/\-]\d{1,2}",

        # Không dùng pattern rộng \d{1,2}[/\-]\d{1,2}
        # vì dễ cắt nhầm tên sân có dấu '-' như "Sân 11 Q1 - C".
        r"\b\d{1,2}/\d{1,2}\b",
        r"\b\d{1,2}-\d{1,2}\b",

        r"hôm qua",
        r"hom qua",
        r"hôm nay",
        r"hom nay",
        r"ngày mai",
        r"ngay mai",
        r"mai",
        r"ngày mốt",
        r"ngay mot",
        r"mốt",
        r"mot",

        r"buổi\s+sáng",
        r"buoi\s+sang",
        r"buổi\s+trưa",
        r"buoi\s+trua",
        r"buổi\s+chiều",
        r"buoi\s+chieu",
        r"buổi\s+tối",
        r"buoi\s+toi",

        r"sáng nay",
        r"sang nay",
        r"sáng mai",
        r"sang mai",
        r"sáng",
        r"sang",
        r"trưa nay",
        r"trua nay",
        r"trưa mai",
        r"trua mai",
        r"trưa",
        r"trua",
        r"chiều nay",
        r"chieu nay",
        r"chiều mai",
        r"chieu mai",
        r"chiều",
        r"chieu",
        r"tối nay",
        r"toi nay",
        r"tối mai",
        r"toi mai",
        r"tối",
        r"toi",

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
        r"tu\s+\d{1,2}",
        r"from\s+\d{1,2}",
        r"lúc\s+\d{1,2}",
        r"luc\s+\d{1,2}",
        r"khoảng\s+\d{1,2}",
        r"khoang\s+\d{1,2}",
        r"\d{1,2}:\d{2}",
        r"\d{1,2}[hg]",
        r"\d{1,2}時",

        r"có trống không",
        r"co trong khong",
        r"có rảnh không",
        r"co ranh khong",
        r"còn trống không",
        r"con trong khong",
        r"còn rảnh không",
        r"con ranh khong",
        r"rảnh không",
        r"ranh khong",
        r"trống không",
        r"trong khong",
        r"đặt được không",
        r"dat duoc khong",
        r"book được không",
        r"book duoc khong",
        r"thì sao",
        r"thi sao",

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
        r"はどうですか",
        r"どうですか",
    ]

    stop_regex = "|".join(stop_patterns)

    patterns = [
        rf"\b(sân\s+.+?)(?=\s*(?:{stop_regex})|$)",
        rf"\b(san\s+.+?)(?=\s*(?:{stop_regex})|$)",
        rf"\b(pitch\s+.+?)(?=\s*(?:{stop_regex})|$)",
        rf"\b(football\s+pitch\s+.+?)(?=\s*(?:{stop_regex})|$)",
        rf"\b([a-zA-Z0-9][a-zA-Z0-9\s\-]*?\s+pitch)(?=\s*(?:{stop_regex})|$)",
        rf"\b([A-Z0-9][A-Z0-9\-]*)\b(?=\s*(?:thì sao|thi sao|available|free)|$)",
        rf"([a-zA-Z0-9\-]+\s*サッカー場)(?=(?:は|が|を|で|に|の|、|\s|{stop_regex})|$)",
        rf"(サッカー場\s*[a-zA-Z0-9\-]+)(?=(?:は|が|を|で|に|の|、|\s|{stop_regex})|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, raw_text, flags=re.IGNORECASE)
        if not match:
            continue

        pitch_name = normalize_pitch_name(match.group(1))

        if pitch_name and not _is_generic_pitch_phrase(pitch_name):
            if pitch_name.lower().startswith("san "):
                pitch_name = "Sân " + pitch_name[4:]
            return pitch_name

    if looks_like_pitch_query(raw_text):
        fallback_patterns = [
            r"\b(sân\s+[^\?,\.!。]+)",
            r"\b(san\s+[^\?,\.!。]+)",
            r"\b(pitch\s+[^\?,\.!。]+)",
            r"\b(football\s+pitch\s+[^\?,\.!。]+)",
            r"\b([a-zA-Z0-9][a-zA-Z0-9\s\-]*?\s+pitch)",
            r"\b([A-Z0-9][A-Z0-9\-]*)\b(?=\s+(?:thì sao|thi sao|available|free)|$)",
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
                    rf"\s*(?:{stop_regex})",
                    pitch_name,
                    maxsplit=1,
                    flags=re.IGNORECASE,
                )[0].strip()

                pitch_name = normalize_pitch_name(pitch_name)

                if pitch_name and pitch_name.lower().startswith("san "):
                    pitch_name = "Sân " + pitch_name[4:]

                if pitch_name and not _is_generic_pitch_phrase(pitch_name):
                    return pitch_name

    return None