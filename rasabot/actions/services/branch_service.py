from actions.db import get_connection
from actions.queries import COUNT_BRANCHES, GET_BRANCHES, GET_BRANCHES_WITH_PITCH_COUNT


def count_branches():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(COUNT_BRANCHES)
        return cursor.fetchone()[0]
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_branches():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(GET_BRANCHES)
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_branches_with_pitch_count():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(GET_BRANCHES_WITH_PITCH_COUNT)
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()