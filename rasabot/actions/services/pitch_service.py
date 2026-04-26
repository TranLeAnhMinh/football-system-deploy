from actions.db import get_connection
from actions.queries import (
    GET_ALL_PITCHES_WITH_BRANCH,
    GET_PITCHES_BY_BRANCH_ID,
    GET_PITCHES_BY_BRANCH_NAME,
)
from actions.parsers.branch_parser import normalize_branch_name


def get_all_pitches_with_branch():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(GET_ALL_PITCHES_WITH_BRANCH)
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_pitches_by_branch_id(branch_id: str):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(GET_PITCHES_BY_BRANCH_ID, (branch_id,))
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_pitches_by_branch_name(branch_name: str):
    normalized_branch_name = normalize_branch_name(branch_name)

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(GET_PITCHES_BY_BRANCH_NAME, (normalized_branch_name,))
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_pitch_by_name(pitch_name: str):
    """
    Tìm sân theo tên gần đúng (ILIKE).
    Trả về 1 sân đầu tiên match.
    """
    if not pitch_name:
        return None

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
        SELECT 
            p.id,
            p.name,
            p.location,
            b.id AS branch_id,
            b.name AS branch_name
        FROM pitches p
        JOIN branches b ON b.id = p.branch_id
        WHERE LOWER(p.name) LIKE LOWER(%s)
          AND p.active = TRUE
        ORDER BY p.name
        LIMIT 1;
        """

        # thêm % để match gần đúng
        like_pattern = f"%{pitch_name}%"

        cursor.execute(query, (like_pattern,))
        row = cursor.fetchone()

        return row

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()