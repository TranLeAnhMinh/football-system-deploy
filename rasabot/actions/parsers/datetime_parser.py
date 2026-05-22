import re
from datetime import datetime, timedelta
from typing import Any


SLOT_MINUTES = 45


def _normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip().lower())


def _extract_date(text: str) -> str | None:
    """
    Hỗ trợ:
    - 2025-09-18
    - 2025/09/18
    - 18/09/2025
    - 18-09-2025
    - 2025年09月18日
    - 09/18/2025
    """
    if not text:
        return None

    patterns = [
        # yyyy-mm-dd / yyyy/mm/dd
        ("ymd", r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b"),

        # dd-mm-yyyy / dd/mm/yyyy
        ("dmy", r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b"),

        # yyyy年mm月dd日
        ("ymd_ja", r"(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日"),

        # mm/dd/yyyy - English style, fallback only
        ("mdy", r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b"),
    ]

    for date_type, pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue

        try:
            if date_type in ["ymd", "ymd_ja"]:
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))
            elif date_type == "dmy":
                day = int(match.group(1))
                month = int(match.group(2))
                year = int(match.group(3))
            else:
                month = int(match.group(1))
                day = int(match.group(2))
                year = int(match.group(3))

            parsed = datetime(year, month, day)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


def _match_any_pattern(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def _weekday_to_index(text: str) -> int | None:
    weekday_patterns = [
        (6, [
            r"\bchủ nhật\b", r"\bchu nhat\b", r"\bcn\b", r"\bcnhat\b",
            r"\bsunday\b", r"\bsun\b",
            r"日曜日", r"日曜"
        ]),
        (0, [
            r"\bthứ 2\b", r"\bthu 2\b", r"\bt2\b",
            r"\bmonday\b", r"\bmon\b",
            r"月曜日", r"月曜"
        ]),
        (1, [
            r"\bthứ 3\b", r"\bthu 3\b", r"\bt3\b",
            r"\btuesday\b", r"\btue\b",
            r"火曜日", r"火曜"
        ]),
        (2, [
            r"\bthứ 4\b", r"\bthu 4\b", r"\bt4\b",
            r"\bwednesday\b", r"\bwed\b",
            r"水曜日", r"水曜"
        ]),
        (3, [
            r"\bthứ 5\b", r"\bthu 5\b", r"\bt5\b",
            r"\bthursday\b", r"\bthu\b",
            r"木曜日", r"木曜"
        ]),
        (4, [
            r"\bthứ 6\b", r"\bthu 6\b", r"\bt6\b",
            r"\bfriday\b", r"\bfri\b",
            r"金曜日", r"金曜"
        ]),
        (5, [
            r"\bthứ 7\b", r"\bthu 7\b", r"\bt7\b",
            r"\bsaturday\b", r"\bsat\b",
            r"土曜日", r"土曜"
        ]),
    ]

    for weekday_index, patterns in weekday_patterns:
        if _match_any_pattern(text, patterns):
            return weekday_index

    return None


def _extract_relative_date(text: str, now: datetime | None = None) -> str | None:
    """
    Hỗ trợ:
    - hôm qua / yesterday / 昨日
    - hôm nay / today / 今日
    - ngày mai / tomorrow / 明日
    - ngày mốt / day after tomorrow / 明後日
    - thứ X tuần này / this Monday / 今週の月曜日
    - thứ X tuần sau / next Monday / 来週の月曜日
    """
    if not text:
        return None

    now = now or datetime.now()
    lowered = _normalize_text(text)

    yesterday_patterns = [
        r"\bhôm qua\b", r"\bhom qua\b",
        r"\bsáng qua\b", r"\bsang qua\b",
        r"\btrưa qua\b", r"\btrua qua\b",
        r"\bchiều qua\b", r"\bchieu qua\b",
        r"\btối qua\b", r"\btoi qua\b",
        r"\byesterday\b",
        r"昨日",
        r"昨夜",
    ]

    if _match_any_pattern(lowered, yesterday_patterns):
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")

    today_patterns = [
        r"\bhôm nay\b", r"\bhom nay\b",
        r"\bsáng nay\b", r"\bsang nay\b",
        r"\btrưa nay\b", r"\btrua nay\b",
        r"\bchiều nay\b", r"\bchieu nay\b",
        r"\btối nay\b", r"\btoi nay\b",
        r"\btoday\b",
        r"\btonight\b",
        r"今日",
        r"今夜",
    ]

    if _match_any_pattern(lowered, today_patterns):
        return now.strftime("%Y-%m-%d")

    tomorrow_patterns = [
        r"\bngày mai\b", r"\bngay mai\b", r"\bmai\b",
        r"\btomorrow\b",
        r"明日",
    ]

    if _match_any_pattern(lowered, tomorrow_patterns):
        return (now + timedelta(days=1)).strftime("%Y-%m-%d")

    day_after_tomorrow_patterns = [
        r"\bngày mốt\b", r"\bngay mot\b", r"\bmốt\b", r"\bmot\b",
        r"\bday after tomorrow\b",
        r"明後日",
    ]

    if _match_any_pattern(lowered, day_after_tomorrow_patterns):
        return (now + timedelta(days=2)).strftime("%Y-%m-%d")

    weekday_index = _weekday_to_index(lowered)
    if weekday_index is None:
        return None

    current_weekday = now.weekday()
    delta = weekday_index - current_weekday

    if _match_any_pattern(lowered, [
        r"\btuần sau\b", r"\btuan sau\b",
        r"\bnext week\b", r"\bnext\b",
        r"来週",
    ]):
        delta += 7
    elif _match_any_pattern(lowered, [
        r"\btuần này\b", r"\btuan nay\b",
        r"\bthis week\b", r"\bthis\b",
        r"今週",
    ]):
        pass
    else:
        if delta < 0:
            delta += 7

    target_date = now + timedelta(days=delta)
    return target_date.strftime("%Y-%m-%d")


def extract_booking_date(text: str | None, now: datetime | None = None) -> str | None:
    lowered = _normalize_text(text)
    if not lowered:
        return None

    absolute_date = _extract_date(lowered)
    if absolute_date:
        return absolute_date

    return _extract_relative_date(lowered, now=now)


def _normalize_time(hour: int, minute: int) -> str | None:
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return None
    return f"{hour:02d}:{minute:02d}"


def _extract_time_token(token: str) -> str | None:
    token = token.strip().lower()
    token = token.replace("時", "h").replace("分", "")

    match = re.fullmatch(r"(\d{1,2}):(\d{2})", token)
    if match:
        return _normalize_time(int(match.group(1)), int(match.group(2)))

    match = re.fullmatch(r"(\d{1,2})h(\d{1,2})", token)
    if match:
        return _normalize_time(int(match.group(1)), int(match.group(2)))

    match = re.fullmatch(r"(\d{1,2})h", token)
    if match:
        return _normalize_time(int(match.group(1)), 0)

    match = re.fullmatch(r"(\d{1,2})", token)
    if match:
        return _normalize_time(int(match.group(1)), 0)

    return None


def extract_time_range_from_text(text: str | None) -> tuple[str | None, str | None]:
    if not text:
        return None, None

    lowered = _normalize_text(text)
    lowered = lowered.replace("〜", "-").replace("～", "-")

    patterns = [
        # Vietnamese: từ 18:00 đến 18:45
        r"(?:\btừ\b\s*)?(\d{1,2}(?::\d{2}|h\d{1,2}|h|時\d{1,2}分?|時)?)\s*(?:\-|\bđến\b|\bden\b|\btới\b|\btoi\b|\bto\b)\s*(\d{1,2}(?::\d{2}|h\d{1,2}|h|時\d{1,2}分?|時)?)",

        # English: from 18:00 to 18:45
        r"(?:\bfrom\b\s*)?(\d{1,2}(?::\d{2}|h\d{1,2}|h|時\d{1,2}分?|時)?)\s*(?:\-|\bto\b|\buntil\b)\s*(\d{1,2}(?::\d{2}|h\d{1,2}|h|時\d{1,2}分?|時)?)",

        # Japanese: 18時から18時45分まで
        r"(\d{1,2}(?:時\d{1,2}分?|時|:\d{2}))\s*(?:から|-)\s*(\d{1,2}(?:時\d{1,2}分?|時|:\d{2}))\s*(?:まで)?",
    ]

    for pattern in patterns:
        match = re.search(pattern, lowered)
        if not match:
            continue

        return _extract_time_token(match.group(1)), _extract_time_token(match.group(2))

    return None, None


def extract_start_time(text: str | None) -> str | None:
    start_time, _ = extract_time_range_from_text(text)
    return start_time


def extract_end_time(text: str | None) -> str | None:
    _, end_time = extract_time_range_from_text(text)
    return end_time


def _time_to_minutes(time_str: str) -> int:
    hour, minute = map(int, time_str.split(":"))
    return hour * 60 + minute


def is_valid_slot_boundary(time_str: str | None) -> bool:
    if not time_str:
        return False

    total_minutes = _time_to_minutes(time_str)
    return total_minutes % SLOT_MINUTES == 0


def is_valid_slot_range(start_time: str | None, end_time: str | None) -> tuple[bool, str | None]:
    if not start_time or not end_time:
        return False, "Thiếu giờ bắt đầu hoặc giờ kết thúc."

    if not is_valid_slot_boundary(start_time):
        return False, (
            "Giờ bắt đầu không hợp lệ. Hệ thống dùng slot 45 phút tính từ 00:00. "
            "Ví dụ hợp lệ: 00:00, 00:45, 01:30, 19:30, 20:15."
        )

    if not is_valid_slot_boundary(end_time):
        return False, (
            "Giờ kết thúc không hợp lệ. Hệ thống dùng slot 45 phút tính từ 00:00. "
            "Ví dụ hợp lệ: 00:00, 00:45, 01:30, 19:30, 20:15."
        )

    start_minutes = _time_to_minutes(start_time)
    end_minutes = _time_to_minutes(end_time)

    if end_minutes <= start_minutes:
        return False, "Giờ kết thúc phải lớn hơn giờ bắt đầu."

    if (end_minutes - start_minutes) % SLOT_MINUTES != 0:
        return False, f"Khoảng thời gian phải là bội số của {SLOT_MINUTES} phút."

    return True, None


def get_missing_datetime_fields(
    text: str | None,
    now: datetime | None = None,
) -> list[str]:
    booking_date = extract_booking_date(text, now=now)
    start_time, end_time = extract_time_range_from_text(text)

    missing_fields: list[str] = []

    if not booking_date:
        missing_fields.append("booking_date")
    if not start_time:
        missing_fields.append("start_time")
    if not end_time:
        missing_fields.append("end_time")

    return missing_fields


def extract_booking_datetime_info(
    text: str | None,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now().replace(second=0, microsecond=0)

    booking_date = extract_booking_date(text, now=now)
    start_time, end_time = extract_time_range_from_text(text)
    missing_fields = get_missing_datetime_fields(text, now=now)

    is_past = False
    if booking_date and start_time:
        try:
            dt = datetime.strptime(f"{booking_date} {start_time}", "%Y-%m-%d %H:%M")
            if dt < now:
                is_past = True
        except ValueError:
            pass

    return {
        "booking_date": booking_date,
        "start_time": start_time,
        "end_time": end_time,
        "missing_fields": missing_fields,
        "is_complete": len(missing_fields) == 0,
        "is_past": is_past,
    }