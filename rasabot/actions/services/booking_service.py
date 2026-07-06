from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import requests

from actions.parsers.branch_parser import normalize_branch_name

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://spring-app:8080")
BLOCKING_BOOKING_STATUSES = (
    "PENDING",
    "APPROVED",
    "PAID",
    "CHECKED_IN",
)

SLOT_MINUTES = 45
TIMEZONE_SUFFIX = "+07"


def _parse_time_str(time_str: str) -> tuple[int, int] | None:
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
            "error_key": _missing_fields_error_key(missing_fields),
            "missing_fields": missing_fields,
        }

    try:
        datetime.strptime(booking_date, "%Y-%m-%d")
    except ValueError:
        return {
            "ok": False,
            "error_key": "invalid_booking_date",
            "missing_fields": [],
        }

    if _parse_time_str(start_time) is None:
        return {
            "ok": False,
            "error_key": "invalid_start_time_format",
            "missing_fields": [],
        }

    if _parse_time_str(end_time) is None:
        return {
            "ok": False,
            "error_key": "invalid_end_time_format",
            "missing_fields": [],
        }

    if not is_valid_slot_boundary(start_time):
        return {
            "ok": False,
            "error_key": "invalid_start_slot_boundary",
            "missing_fields": [],
        }

    if not is_valid_slot_boundary(end_time):
        return {
            "ok": False,
            "error_key": "invalid_end_slot_boundary",
            "missing_fields": [],
        }

    if not is_valid_time_range(start_time, end_time):
        return {
            "ok": False,
            "error_key": "invalid_time_range",
            "missing_fields": [],
        }

    return {
        "ok": True,
        "error_key": None,
        "missing_fields": [],
    }


def _missing_fields_error_key(missing_fields: list[str]) -> str:
    if missing_fields == ["booking_date"]:
        return "missing_booking_date"

    if missing_fields == ["start_time"]:
        return "missing_start_time"

    if missing_fields == ["end_time"]:
        return "missing_end_time"

    if set(missing_fields) == {"booking_date", "start_time"}:
        return "missing_booking_date_start_time"

    if set(missing_fields) == {"booking_date", "end_time"}:
        return "missing_booking_date_end_time"

    if set(missing_fields) == {"start_time", "end_time"}:
        return "missing_start_end_time"

    return "missing_datetime"


def build_datetime_with_timezone(booking_date: str, time_str: str) -> str:
    return f"{booking_date}T{time_str}:00{TIMEZONE_SUFFIX}:00"


def get_available_pitches(
    branch_name: str,
    start_time: str,
    end_time: str,
    booking_date: str | None = None,
) -> dict[str, Any]:
    validation = validate_booking_input(booking_date, start_time, end_time)
    if not validation["ok"]:
        return {
            "ok": False,
            "error_key": validation["error_key"],
            "data": [],
        }

    normalized_branch_name = normalize_branch_name(branch_name)
    if not normalized_branch_name:
        return {
            "ok": False,
            "error_key": "invalid_branch_name",
            "data": [],
        }

    start_at = build_datetime_with_timezone(booking_date, start_time)
    end_at = build_datetime_with_timezone(booking_date, end_time)

    try:
        response = requests.get(
            f"{BACKEND_BASE_URL}/api/chatbot/branches",
            timeout=5,
        )
        response.raise_for_status()
        branches = response.json()
        branch = next(
            (item for item in branches if item["name"].lower() == normalized_branch_name.lower()),
            None,
        )
        if not branch:
            return {
                "ok": True,
                "error_key": None,
                "data": [],
            }

        response = requests.get(
            f"{BACKEND_BASE_URL}/api/chatbot/pitches",
            params={"branchId": branch["id"]},
            timeout=5,
        )
        response.raise_for_status()
        pitches = response.json()

        available_pitches = []
        for pitch in pitches:
            availability_response = requests.post(
                f"{BACKEND_BASE_URL}/api/chatbot/availability/check",
                json={
                    "pitchId": pitch["id"],
                    "startAt": start_at,
                    "endAt": end_at,
                },
                timeout=5,
            )
            availability_response.raise_for_status()
            availability_payload = availability_response.json()

            if availability_payload.get("available", False):
                available_pitches.append((pitch["id"], pitch["name"], pitch["location"]))

        return {
            "ok": True,
            "error_key": None,
            "data": available_pitches,
        }
    except Exception:
        return {
            "ok": False,
            "error_key": "database_error",
            "data": [],
        }


def is_pitch_available(
    pitch_id: str,
    booking_date: str | None,
    start_time: str | None,
    end_time: str | None,
) -> dict[str, Any]:
    validation = validate_booking_input(booking_date, start_time, end_time)
    if not validation["ok"]:
        return {
            "ok": False,
            "error_key": validation["error_key"],
            "available": False,
        }

    start_at = build_datetime_with_timezone(booking_date, start_time)
    end_at = build_datetime_with_timezone(booking_date, end_time)

    try:
        response = requests.post(
            f"{BACKEND_BASE_URL}/api/chatbot/availability/check",
            json={
                "pitchId": pitch_id,
                "startAt": start_at,
                "endAt": end_at,
            },
            timeout=5,
        )
        response.raise_for_status()
        payload = response.json()

        return {
            "ok": True,
            "error_key": None,
            "available": payload.get("available", False),
            "data": payload,
        }
    except Exception:
        return {
            "ok": False,
            "error_key": "database_error",
            "available": False,
            "data": None,
        }

def get_nearest_available_slots_for_pitch(
    pitch_id: str,
    booking_date: str,
    requested_start_time: str,
    max_slots: int = 8,
) -> dict[str, Any]:
    start_minutes = ceil_to_next_slot_minutes(requested_start_time)

    if start_minutes is None:
        return {
            "ok": False,
            "error_key": "invalid_start_time_format",
            "data": [],
        }

    available_slots = []

    for i in range(max_slots):
        slot_start_minutes = start_minutes + i * SLOT_MINUTES
        slot_end_minutes = slot_start_minutes + SLOT_MINUTES

        if slot_end_minutes > 24 * 60:
            break

        slot_start = minutes_to_time_str(slot_start_minutes)
        slot_end = minutes_to_time_str(slot_end_minutes)

        result = is_pitch_available(
            pitch_id=pitch_id,
            booking_date=booking_date,
            start_time=slot_start,
            end_time=slot_end,
        )

        if not result["ok"]:
            return {
                  "ok": False,
                  "error_key": result["error_key"],
                  "data": [],
            }
        if result["available"]: 
            available_slots.append((slot_start_minutes, slot_end_minutes))

    merged_slots = merge_available_slots(available_slots)

    return {
        "ok": True,
        "error_key": None,
        "data": [
            {
                "start_time": minutes_to_time_str(start),
                "end_time": minutes_to_time_str(end),
            }
            for start, end in merged_slots
        ],
    }

def ceil_to_next_slot_minutes(time_str: str) -> int | None:
    total_minutes = _minutes_from_midnight(time_str)

    if total_minutes is None:
        return None

    if total_minutes % SLOT_MINUTES == 0:
        return total_minutes

    return ((total_minutes // SLOT_MINUTES) + 1) * SLOT_MINUTES


def minutes_to_time_str(total_minutes: int) -> str:
    hour = total_minutes // 60
    minute = total_minutes % 60
    return f"{hour:02d}:{minute:02d}"


def merge_available_slots(slots: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not slots:
        return []

    merged = [slots[0]]

    for start, end in slots[1:]:
        last_start, last_end = merged[-1]

        if start == last_end:
            merged[-1] = (last_start, end)
        else:
            merged.append((start, end))

    return merged

def floor_to_slot_minutes(time_str: str) -> int | None:
    total_minutes = _minutes_from_midnight(time_str)

    if total_minutes is None:
        return None

    return (total_minutes // SLOT_MINUTES) * SLOT_MINUTES


def get_available_slots_in_time_range_for_pitch(
    pitch_id: str,
    booking_date: str,
    requested_start_time: str,
    requested_end_time: str,
) -> dict[str, Any]:
    start_minutes = floor_to_slot_minutes(requested_start_time)
    end_minutes = ceil_to_next_slot_minutes(requested_end_time)

    if start_minutes is None:
        return {
            "ok": False,
            "error_key": "invalid_start_time_format",
            "data": [],
        }

    if end_minutes is None:
        return {
            "ok": False,
            "error_key": "invalid_end_time_format",
            "data": [],
        }

    if end_minutes <= start_minutes:
        return {
            "ok": False,
            "error_key": "invalid_time_range",
            "data": [],
        }

    available_slots = []

    current_minutes = start_minutes

    while current_minutes < end_minutes:
        slot_start_minutes = current_minutes
        slot_end_minutes = current_minutes + SLOT_MINUTES

        if slot_end_minutes > 24 * 60:
            break

        slot_start = minutes_to_time_str(slot_start_minutes)
        slot_end = minutes_to_time_str(slot_end_minutes)

        result = is_pitch_available(
            pitch_id=pitch_id,
            booking_date=booking_date,
            start_time=slot_start,
            end_time=slot_end,
        )

        if not result["ok"]:
            return {
                "ok": False,
                "error_key": result["error_key"],
                "data": [],
            }

        if result["available"]:
            available_slots.append((slot_start_minutes, slot_end_minutes))

        current_minutes += SLOT_MINUTES

    merged_slots = merge_available_slots(available_slots)

    return {
        "ok": True,
        "error_key": None,
        "rounded_start_time": minutes_to_time_str(start_minutes),
        "rounded_end_time": minutes_to_time_str(end_minutes),
        "data": [
            {
                "start_time": minutes_to_time_str(start),
                "end_time": minutes_to_time_str(end),
            }
            for start, end in merged_slots
        ],
    }
