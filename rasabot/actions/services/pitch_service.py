import os
import requests

from actions.parsers.branch_parser import normalize_branch_name

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://spring-app:8080")


def get_all_pitches_with_branch():
    try:
        response = requests.get(f"{BACKEND_BASE_URL}/api/chatbot/pitches", timeout=5)
        response.raise_for_status()
        return [(pitch["id"], pitch["name"], pitch["location"]) for pitch in response.json()]
    except Exception:
        return []


def get_pitches_by_branch_id(branch_id: str):
    try:
        response = requests.get(f"{BACKEND_BASE_URL}/api/chatbot/pitches", params={"branchId": branch_id}, timeout=5)
        response.raise_for_status()
        return [(pitch["id"], pitch["name"], pitch["location"]) for pitch in response.json()]
    except Exception:
        return []


def get_pitches_by_branch_name(branch_name: str):
    try:
        response = requests.get(f"{BACKEND_BASE_URL}/api/chatbot/branches", timeout=5)
        response.raise_for_status()
        branches = response.json()
        branch = next((item for item in branches if item["name"].lower() == branch_name.lower()), None)
        if not branch:
            return []
        return get_pitches_by_branch_id(branch["id"])
    except Exception:
        return []


def get_pitch_by_name(pitch_name: str):
    if not pitch_name:
        return None

    try:
        response = requests.get(f"{BACKEND_BASE_URL}/api/chatbot/pitches", timeout=5)
        response.raise_for_status()
        pitches = response.json()
        for pitch in pitches:
            if pitch_name.lower() in pitch["name"].lower():
                return (pitch["id"], pitch["name"], pitch["location"])
        return None
    except Exception:
        return None