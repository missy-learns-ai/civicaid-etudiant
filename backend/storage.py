import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

from backend.models.student_profile import StudentProfile


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/civicaid.db")


def _is_postgres() -> bool:
    return DATABASE_URL.startswith(("postgres://", "postgresql://"))


def _postgres_url() -> str:
    if DATABASE_URL.startswith("postgres://"):
        return DATABASE_URL.replace("postgres://", "postgresql://", 1)
    return DATABASE_URL


def _sqlite_path() -> Path:
    raw_path = DATABASE_URL.removeprefix("sqlite:///")
    path = Path(raw_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


@contextmanager
def _sqlite_connection() -> Iterator[sqlite3.Connection]:
    path = _sqlite_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


@contextmanager
def _postgres_connection():
    import psycopg

    with psycopg.connect(_postgres_url()) as connection:
        yield connection


@contextmanager
def _connection():
    if _is_postgres():
        with _postgres_connection() as connection:
            yield connection
    else:
        with _sqlite_connection() as connection:
            yield connection


def init_db() -> None:
    if _is_postgres():
        with _connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS student_profiles (
                        student_id TEXT PRIMARY KEY,
                        profile_json JSONB NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS call_summaries (
                        id BIGSERIAL PRIMARY KEY,
                        student_id TEXT NOT NULL,
                        conversation_id TEXT,
                        summary TEXT NOT NULL,
                        saved_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
    else:
        with _connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS student_profiles (
                    student_id TEXT PRIMARY KEY,
                    profile_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS call_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    conversation_id TEXT,
                    summary TEXT NOT NULL,
                    saved_at TEXT NOT NULL
                )
                """
            )


def get_profile(student_id: str) -> Optional[StudentProfile]:
    with _connection() as connection:
        if _is_postgres():
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT profile_json FROM student_profiles WHERE student_id = %s",
                    (student_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                profile_data = row[0]
        else:
            row = connection.execute(
                "SELECT profile_json FROM student_profiles WHERE student_id = ?",
                (student_id,),
            ).fetchone()
            if row is None:
                return None
            profile_data = json.loads(row["profile_json"])

    return StudentProfile.model_validate(profile_data)


def save_profile(profile: StudentProfile) -> None:
    profile_data = profile.model_dump(mode="json")

    with _connection() as connection:
        if _is_postgres():
            from psycopg.types.json import Json

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO student_profiles (student_id, profile_json, updated_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (student_id)
                    DO UPDATE SET profile_json = EXCLUDED.profile_json, updated_at = NOW()
                    """,
                    (profile.student_id, Json(profile_data)),
                )
        else:
            connection.execute(
                """
                INSERT INTO student_profiles (student_id, profile_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(student_id)
                DO UPDATE SET profile_json = excluded.profile_json, updated_at = excluded.updated_at
                """,
                (
                    profile.student_id,
                    json.dumps(profile_data),
                    datetime.utcnow().isoformat(),
                ),
            )


def profile_exists(student_id: str) -> bool:
    return get_profile(student_id) is not None


def add_call_summary(
    student_id: str,
    summary: str,
    conversation_id: Optional[str] = None,
) -> None:
    with _connection() as connection:
        if _is_postgres():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO call_summaries (student_id, conversation_id, summary)
                    VALUES (%s, %s, %s)
                    """,
                    (student_id, conversation_id, summary),
                )
        else:
            connection.execute(
                """
                INSERT INTO call_summaries (student_id, conversation_id, summary, saved_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    student_id,
                    conversation_id,
                    summary,
                    datetime.utcnow().isoformat(),
                ),
            )


def list_call_summaries() -> list[dict]:
    with _connection() as connection:
        if _is_postgres():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT student_id, conversation_id, summary, saved_at
                    FROM call_summaries
                    ORDER BY saved_at DESC
                    """
                )
                rows = cursor.fetchall()
                return [
                    {
                        "student_id": row[0],
                        "conversation_id": row[1],
                        "summary": row[2],
                        "saved_at": row[3].isoformat(),
                    }
                    for row in rows
                ]

        rows = connection.execute(
            """
            SELECT student_id, conversation_id, summary, saved_at
            FROM call_summaries
            ORDER BY saved_at DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]
