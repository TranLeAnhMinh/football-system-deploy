import os
import requests

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://spring-app:8080")


def count_branches():
    try:
        response = requests.get(f"{BACKEND_BASE_URL}/api/chatbot/branches", timeout=5)
        response.raise_for_status()
        return len(response.json())
    except Exception:
        return 0


def get_branches():
    try:
        response = requests.get(f"{BACKEND_BASE_URL}/api/chatbot/branches", timeout=5)
        response.raise_for_status()
        return [(branch["id"], branch["name"]) for branch in response.json()]
    except Exception:
        return []


def get_branches_with_pitch_count():
    return []