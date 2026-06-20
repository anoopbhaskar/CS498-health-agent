"""SQLite-backed session, profile, conversation, and progress memory."""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


PROFILE_FIELDS = [
    "age",
    "sex",
    "height_cm",
    "weight_kg",
    "activity_level",
    "health_conditions",
    "dietary_restrictions",
    "fitness_goals",
    "fitness_level",
    "current_steps",
]


class SQLiteStore:
    """Small repository layer around SQLite.

    The public methods return dictionaries so the rest of the app is not tied
    to SQLite row objects and can later move to a hosted database.
    """

    def __init__(self, database_url: str):
        self.path = self._path_from_url(database_url)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    @staticmethod
    def _path_from_url(database_url: str) -> Path:
        if database_url.startswith("sqlite:///"):
            return Path(database_url.removeprefix("sqlite:///")).expanduser()
        return Path(database_url).expanduser()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS profiles (
                    session_id TEXT PRIMARY KEY REFERENCES sessions(id),
                    age INTEGER,
                    sex TEXT,
                    height_cm REAL,
                    weight_kg REAL,
                    activity_level TEXT,
                    health_conditions TEXT NOT NULL DEFAULT '[]',
                    dietary_restrictions TEXT NOT NULL DEFAULT '[]',
                    fitness_goals TEXT NOT NULL DEFAULT '[]',
                    fitness_level TEXT,
                    current_steps INTEGER,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS profile_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL REFERENCES sessions(id),
                    snapshot_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL REFERENCES sessions(id),
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS progress_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL REFERENCES sessions(id),
                    event_type TEXT NOT NULL,
                    value_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def ensure_session(self, session_id: str | None = None) -> str:
        sid = session_id or str(uuid.uuid4())
        now = utc_now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions (id, created_at, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET updated_at=excluded.updated_at
                """,
                (sid, now, now),
            )
        return sid

    def upsert_profile(self, session_id: str, profile: dict[str, Any]) -> dict[str, Any]:
        self.ensure_session(session_id)
        existing = self.get_profile(session_id)
        merged = {**empty_profile(), **existing, **compact_profile(profile)}
        now = utc_now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO profiles (
                    session_id, age, sex, height_cm, weight_kg, activity_level,
                    health_conditions, dietary_restrictions, fitness_goals,
                    fitness_level, current_steps, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    age=excluded.age,
                    sex=excluded.sex,
                    height_cm=excluded.height_cm,
                    weight_kg=excluded.weight_kg,
                    activity_level=excluded.activity_level,
                    health_conditions=excluded.health_conditions,
                    dietary_restrictions=excluded.dietary_restrictions,
                    fitness_goals=excluded.fitness_goals,
                    fitness_level=excluded.fitness_level,
                    current_steps=excluded.current_steps,
                    updated_at=excluded.updated_at
                """,
                (
                    session_id,
                    merged["age"],
                    merged["sex"],
                    merged["height_cm"],
                    merged["weight_kg"],
                    merged["activity_level"],
                    json.dumps(merged["health_conditions"]),
                    json.dumps(merged["dietary_restrictions"]),
                    json.dumps(merged["fitness_goals"]),
                    merged["fitness_level"],
                    merged["current_steps"],
                    now,
                ),
            )
            conn.execute(
                """
                INSERT INTO profile_snapshots (session_id, snapshot_json, created_at)
                VALUES (?, ?, ?)
                """,
                (session_id, json.dumps(merged), now),
            )
            for field in ("weight_kg", "activity_level", "fitness_goals", "current_steps"):
                if merged.get(field) != existing.get(field):
                    conn.execute(
                        """
                        INSERT INTO progress_events (session_id, event_type, value_json, created_at)
                        VALUES (?, ?, ?, ?)
                        """,
                        (session_id, field, json.dumps(merged.get(field)), now),
                    )
        return merged

    def get_profile(self, session_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM profiles WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return empty_profile()
        return row_to_profile(row)

    def add_message(self, session_id: str, role: str, content: str, category: str | None = None) -> None:
        self.ensure_session(session_id)
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO messages (session_id, role, content, category, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, role, content, category, utc_now()),
            )

    def list_messages(self, session_id: str, limit: int | None = None) -> list[dict[str, Any]]:
        sql = "SELECT role, content, category, created_at FROM messages WHERE session_id = ? ORDER BY id ASC"
        params: tuple[Any, ...] = (session_id,)
        if limit is not None:
            sql = (
                "SELECT role, content, category, created_at FROM messages "
                "WHERE session_id = ? ORDER BY id DESC LIMIT ?"
            )
            params = (session_id, limit)
        with self.connect() as conn:
            rows = [dict(row) for row in conn.execute(sql, params).fetchall()]
        if limit is not None:
            rows.reverse()
        return rows

    def list_progress(self, session_id: str) -> dict[str, list[dict[str, Any]]]:
        with self.connect() as conn:
            snapshot_rows = conn.execute(
                """
                SELECT snapshot_json, created_at FROM profile_snapshots
                WHERE session_id = ? ORDER BY id ASC
                """,
                (session_id,),
            ).fetchall()
            event_rows = conn.execute(
                """
                SELECT event_type, value_json, created_at FROM progress_events
                WHERE session_id = ? ORDER BY id ASC
                """,
                (session_id,),
            ).fetchall()
        snapshots = [
            {"created_at": row["created_at"], "profile": json.loads(row["snapshot_json"])}
            for row in snapshot_rows
        ]
        events = [
            {
                "created_at": row["created_at"],
                "event_type": row["event_type"],
                "value": json.loads(row["value_json"]),
            }
            for row in event_rows
        ]
        return {"snapshots": snapshots, "events": events}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def empty_profile() -> dict[str, Any]:
    return {
        "age": None,
        "sex": None,
        "height_cm": None,
        "weight_kg": None,
        "activity_level": None,
        "health_conditions": [],
        "dietary_restrictions": [],
        "fitness_goals": [],
        "fitness_level": None,
        "current_steps": None,
    }


def compact_profile(profile: dict[str, Any]) -> dict[str, Any]:
    compacted: dict[str, Any] = {}
    for key in PROFILE_FIELDS:
        value = profile.get(key)
        if value not in (None, "", []):
            compacted[key] = value
    return compacted


def row_to_profile(row: sqlite3.Row) -> dict[str, Any]:
    profile = empty_profile()
    for key in PROFILE_FIELDS:
        if key in ("health_conditions", "dietary_restrictions", "fitness_goals"):
            profile[key] = json.loads(row[key] or "[]")
        else:
            profile[key] = row[key]
    return profile
