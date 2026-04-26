from __future__ import annotations

from datetime import datetime
from typing import Any

from actions.db import get_connection
from actions.parsers.branch_parser import normalize_branch_name

BLOCKING_BOOKING_STATUSES = (
    "PENDING",
    "APPROVED",
    "PAID",
    "CHECKED_IN",
)

SLOT_MINUTES = 45
TIMEZONE_SUFFIX = "+07"


def _parse_time_str(time_str: str) -> tuple[int, int] | None:
    """
    Nhận HH:MM, trả về (hour, minute)
    """
    if not time_str:
        return None

    try:
        hour_str, minute_str = time_str.strip().split(":")
        hour = int(hour_str)
        minute = int(minute_str)
    except (ValueError, AttributeError):
        return None

    if hour < 0 or hour > 23:
        return None

    if minute < 0 or minute > 59:
        return None

    return hour, minute


def _minutes_from_midnight(time_str: str) -> int | None:
    parsed = _parse_time_str(time_str)
    if not parsed:
        return None

    hour, minute = parsed
    return hour * 60 + minute


def is_valid_slot_boundary(time_str: str) -> bool:
    """
    Mốc giờ phải nằm đúng biên slot 45 phút tính từ 00:00.
    Ví dụ hợp lệ:
    00:00, 00:45, 01:30, 02:15, 03:00...
    """
    total_minutes = _minutes_from_midnight(time_str)
    if total_minutes is None:
        return False

    return total_minutes % SLOT_MINUTES == 0


def is_valid_time_range(start_time: str, end_time: str) -> bool:
    start_minutes = _minutes_from_midnight(start_time)
    end_minutes = _minutes_from_midnight(end_time)

    if start_minutes is None or end_minutes is None:
        return False

    if end_minutes <= start_minutes:
        return False

    if start_minutes % SLOT_MINUTES != 0 or end_minutes % SLOT_MINUTES != 0:
        return False

    return (end_minutes - start_minutes) % SLOT_MINUTES == 0


def validate_booking_input(
    booking_date: str | None,
    start_time: str | None,
    end_time: str | None,
) -> dict[str, Any]:
    """
    Validate input theo rule:
    - phải có ngày
    - phải có giờ bắt đầu
    - phải có giờ kết thúc
    - giờ đúng format HH:MM
    - đúng biên slot 45 phút
    - end > start
    """
    missing_fields: list[str] = []

    if not booking_date:
        missing_fields.append("booking_date")
    if not start_time:
        missing_fields.append("start_time")
    if not end_time:
        missing_fields.append("end_time")

    if missing_fields:
        return {
            "ok": False,
            "missing_fields": missing_fields,
            "message": _build_missing_fields_message(missing_fields),
        }

    try:
        datetime.strptime(booking_date, "%Y-%m-%d")
    except ValueError:
        return {
            "ok": False,
            "missing_fields": [],
            "message": "Ngày đặt không hợp lệ. Vui lòng nhập theo định dạng YYYY-MM-DD.",
        }

    if _parse_time_str(start_time) is None:
        return {
            "ok": False,
            "missing_fields": [],
            "message": "Giờ bắt đầu không hợp lệ. Vui lòng nhập theo định dạng HH:MM.",
        }

    if _parse_time_str(end_time) is None:
        return {
            "ok": False,
            "missing_fields": [],
            "message": "Giờ kết thúc không hợp lệ. Vui lòng nhập theo định dạng HH:MM.",
        }

    if not is_valid_slot_boundary(start_time):
        return {
            "ok": False,
            "missing_fields": [],
            "message": (
                "Giờ bắt đầu không hợp lệ. Hệ thống dùng slot 45 phút tính từ 00:00. "
                "Ví dụ hợp lệ: 00:00, 00:45, 01:30."
            ),
        }

    if not is_valid_slot_boundary(end_time):
        return {
            "ok": False,
            "missing_fields": [],
            "message": (
                "Giờ kết thúc không hợp lệ. Hệ thống dùng slot 45 phút tính từ 00:00. "
                "Ví dụ hợp lệ: 00:00, 00:45, 01:30."
            ),
        }

    if not is_valid_time_range(start_time, end_time):
        return {
            "ok": False,
            "missing_fields": [],
            "message": (
                "Khung giờ không hợp lệ. Giờ kết thúc phải lớn hơn giờ bắt đầu "
                "và khoảng thời gian phải theo bội số 45 phút."
            ),
        }

    return {
        "ok": True,
        "missing_fields": [],
        "message": None,
    }


def _build_missing_fields_message(missing_fields: list[str]) -> str:
    field_map = {
        "booking_date": "ngày đặt",
        "start_time": "giờ bắt đầu",
        "end_time": "giờ kết thúc",
    }

    readable = [field_map[field] for field in missing_fields]

    if len(readable) == 1:
        return f"Bạn vui lòng cung cấp {readable[0]} cụ thể."

    if len(readable) == 2:
        return f"Bạn vui lòng cung cấp {readable[0]} và {readable[1]} cụ thể."

    return "Bạn vui lòng cung cấp ngày đặt, giờ bắt đầu và giờ kết thúc cụ thể."


def build_datetime_with_timezone(booking_date: str, time_str: str) -> str:
    """
    Trả về dạng:
    2025-09-18 07:00:00+07
    """
    return f"{booking_date} {time_str}:00{TIMEZONE_SUFFIX}"


def get_available_pitches(
    branch_name: str,
    start_time: str,
    end_time: str,
    booking_date: str | None = None,
) -> dict[str, Any]:
    """
    Trả về dict để action xử lý dễ hơn:
    {
        "ok": True/False,
        "message": "...",
        "data": [...]
    }
    """
    validation = validate_booking_input(booking_date, start_time, end_time)
    if not validation["ok"]:
        return {
            "ok": False,
            "message": validation["message"],
            "data": [],
        }

    normalized_branch_name = normalize_branch_name(branch_name)
    if not normalized_branch_name:
        return {
            "ok": False,
            "message": "Bạn vui lòng cung cấp tên chi nhánh hợp lệ.",
            "data": [],
        }

    start_at = build_datetime_with_timezone(booking_date, start_time)
    end_at = build_datetime_with_timezone(booking_date, end_time)

    query = """
    SELECT
        p.id,
        p.name,
        p.location,
        b.id AS branch_id,
        b.name AS branch_name
    FROM pitches p
    JOIN branches b
        ON b.id = p.branch_id
    WHERE LOWER(b.name) = LOWER(%s)
      AND b.active = TRUE
      AND p.active = TRUE
      AND NOT EXISTS (
          SELECT 1
          FROM booking_slots bs
          JOIN bookings bo
              ON bo.id = bs.booking_id
          WHERE bs.pitch_id = p.id
            AND bs.range && tstzrange(%s::timestamptz, %s::timestamptz, '[)')
            AND bo.status = ANY(%s)
      )
      AND NOT EXISTS (
          SELECT 1
          FROM maintenance_windows mw
          WHERE mw.pitch_id = p.id
            AND mw.range && tstzrange(%s::timestamptz, %s::timestamptz, '[)')
      )
    ORDER BY p.name;
    """

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            query,
            (
                normalized_branch_name,
                start_at,
                end_at,
                list(BLOCKING_BOOKING_STATUSES),
                start_at,
                end_at,
            ),
        )
        rows = cursor.fetchall()

        return {
            "ok": True,
            "message": None,
            "data": rows,
        }
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def is_pitch_available(
    pitch_id: str,
    booking_date: str | None,
    start_time: str | None,
    end_time: str | None,
) -> dict[str, Any]:
    """
    Check 1 sân cụ thể có rảnh không.
    """
    validation = validate_booking_input(booking_date, start_time, end_time)
    if not validation["ok"]:
        return {
            "ok": False,
            "message": validation["message"],
            "available": False,
        }

    start_at = build_datetime_with_timezone(booking_date, start_time)
    end_at = build_datetime_with_timezone(booking_date, end_time)

    query = """
    SELECT
        p.id,
        p.name,
        p.location
    FROM pitches p
    WHERE p.id = %s
      AND p.active = TRUE
      AND NOT EXISTS (
          SELECT 1
          FROM booking_slots bs
          JOIN bookings bo
              ON bo.id = bs.booking_id
          WHERE bs.pitch_id = p.id
            AND bs.range && tstzrange(%s::timestamptz, %s::timestamptz, '[)')
            AND bo.status = ANY(%s)
      )
      AND NOT EXISTS (
          SELECT 1
          FROM maintenance_windows mw
          WHERE mw.pitch_id = p.id
            AND mw.range && tstzrange(%s::timestamptz, %s::timestamptz, '[)')
      )
    LIMIT 1;
    """

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            query,
            (
                pitch_id,
                start_at,
                end_at,
                list(BLOCKING_BOOKING_STATUSES),
                start_at,
                end_at,
            ),
        )
        row = cursor.fetchone()

        if row:
            return {
                "ok": True,
                "message": None,
                "available": True,
                "data": row,
            }

        return {
            "ok": True,
            "message": None,
            "available": False,
            "data": None,
        }
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()