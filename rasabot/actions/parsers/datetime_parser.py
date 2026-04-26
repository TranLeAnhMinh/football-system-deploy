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
    """
    if not text:
        return None

    patterns = [
        r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b",
        r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b",
    ]

    for idx, pattern in enumerate(patterns):
        match = re.search(pattern, text)
        if not match:
            continue

        try:
            if idx == 0:
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))
            else:
                day = int(match.group(1))
                month = int(match.group(2))
                year = int(match.group(3))

            parsed = datetime(year, month, day)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            return None

    return None


def _match_any_pattern(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def _weekday_to_index(text: str) -> int | None:
    weekday_patterns = [
        (6, [r"\bchủ nhật\b", r"\bchu nhat\b", r"\bcn\b", r"\bcnhat\b"]),
        (0, [r"\bthứ 2\b", r"\bthu 2\b", r"\bt2\b"]),
        (1, [r"\bthứ 3\b", r"\bthu 3\b", r"\bt3\b"]),
        (2, [r"\bthứ 4\b", r"\bthu 4\b", r"\bt4\b"]),
        (3, [r"\bthứ 5\b", r"\bthu 5\b", r"\bt5\b"]),
        (4, [r"\bthứ 6\b", r"\bthu 6\b", r"\bt6\b"]),
        (5, [r"\bthứ 7\b", r"\bthu 7\b", r"\bt7\b"]),
    ]

    for weekday_index, patterns in weekday_patterns:
        if _match_any_pattern(text, patterns):
            return weekday_index

    return None


def _extract_relative_date(text: str, now: datetime | None = None) -> str | None:
    """
    Hỗ trợ:
    - hôm nay
    - ngày mai / mai
    - ngày mốt / mốt
    - thứ X tuần này
    - thứ X tuần sau
    - thứ X (ngày gần nhất trong tương lai)
    """
    if not text:
        return None

    now = now or datetime.now()
    lowered = _normalize_text(text)

    if _match_any_pattern(lowered, [r"\bhôm nay\b", r"\bhom nay\b"]):
        return now.strftime("%Y-%m-%d")

    if _match_any_pattern(lowered, [r"\bngày mai\b", r"\bngay mai\b", r"\bmai\b"]):
        return (now + timedelta(days=1)).strftime("%Y-%m-%d")

    if _match_any_pattern(lowered, [r"\bngày mốt\b", r"\bngay mot\b", r"\bmốt\b", r"\bmot\b"]):
        return (now + timedelta(days=2)).strftime("%Y-%m-%d")

    weekday_index = _weekday_to_index(lowered)
    if weekday_index is None:
        return None

    current_weekday = now.weekday()  # Monday = 0, Sunday = 6
    delta = weekday_index - current_weekday

    if _match_any_pattern(lowered, [r"\btuần sau\b", r"\btuan sau\b"]):
        delta += 7
    elif _match_any_pattern(lowered, [r"\btuần này\b", r"\btuan nay\b"]):
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

    # HH:MM
    match = re.fullmatch(r"(\d{1,2}):(\d{2})", token)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        return _normalize_time(hour, minute)

    # HHhMM
    match = re.fullmatch(r"(\d{1,2})h(\d{1,2})", token)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        return _normalize_time(hour, minute)

    # HHh
    match = re.fullmatch(r"(\d{1,2})h", token)
    if match:
        hour = int(match.group(1))
        return _normalize_time(hour, 0)

    # HH
    match = re.fullmatch(r"(\d{1,2})", token)
    if match:
        hour = int(match.group(1))
        return _normalize_time(hour, 0)

    return None


def extract_time_range_from_text(text: str | None) -> tuple[str | None, str | None]:
    """
    Hỗ trợ:
    - 19:30-21:00
    - 19:30 đến 21:00
    - 19:30 den 21:00
    - 19:30 tới 21:00
    - 19h30-21h
    - từ 19:30 đến 21:00
    - 7h30 - 8h15
    """
    if not text:
        return None, None

    lowered = _normalize_text(text)

    patterns = [
        r"(?:\btừ\b\s*)?(\d{1,2}(?::\d{2}|h\d{1,2}|h)?)\s*(?:\-|\bđến\b|\bden\b|\btới\b|\btoi\b|\bto\b)\s*(\d{1,2}(?::\d{2}|h\d{1,2}|h)?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, lowered)
        if not match:
            continue

        start_raw = match.group(1)
        end_raw = match.group(2)

        start_time = _extract_time_token(start_raw)
        end_time = _extract_time_token(end_raw)

        return start_time, end_time

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
    """
    Slot hợp lệ nếu nằm trên mốc 45 phút tính từ 00:00:
    00:00, 00:45, 01:30, 02:15, ...
    """
    if not time_str:
        return False

    total_minutes = _time_to_minutes(time_str)
    return total_minutes % SLOT_MINUTES == 0


def is_valid_slot_range(start_time: str | None, end_time: str | None) -> tuple[bool, str | None]:
    """
    Hợp lệ nếu:
    - start_time và end_time đều nằm trên mốc slot
    - end_time > start_time
    - khoảng thời gian là bội số của 45 phút
    """
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
        return False, (
            f"Khoảng thời gian phải là bội số của {SLOT_MINUTES} phút."
        )

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
    booking_date = extract_booking_date(text, now=now)
    start_time, end_time = extract_time_range_from_text(text)
    missing_fields = get_missing_datetime_fields(text, now=now)

    return {
        "booking_date": booking_date,
        "start_time": start_time,
        "end_time": end_time,
        "missing_fields": missing_fields,
        "is_complete": len(missing_fields) == 0,
    }