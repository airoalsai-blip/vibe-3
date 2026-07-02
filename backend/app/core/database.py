import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sqlite_path() -> Path:
    prefix = "sqlite:///"
    if not settings.database_url.startswith(prefix):
        raise RuntimeError("This scaffold health check currently supports sqlite DATABASE_URL values.")
    return Path(settings.database_url.removeprefix(prefix))


def get_connection() -> sqlite3.Connection:
    db_path = _sqlite_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def _ensure_column(connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    if column not in {row["name"] for row in rows}:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                department TEXT,
                position TEXT,
                phone TEXT,
                role TEXT NOT NULL DEFAULT 'member',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                deleted_at TEXT
            );

            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                location TEXT,
                start_at TEXT NOT NULL,
                end_at TEXT NOT NULL,
                visibility TEXT NOT NULL DEFAULT 'team',
                status TEXT NOT NULL DEFAULT 'confirmed',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                deleted_at TEXT,
                FOREIGN KEY(owner_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS excel_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                job_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                options TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS manual_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                version TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                indexed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS news_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                published_at TEXT,
                summary TEXT,
                category TEXT,
                collected_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS news_collection_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_date TEXT NOT NULL,
                mode TEXT NOT NULL,
                status TEXT NOT NULL,
                fetched_count INTEGER NOT NULL DEFAULT 0,
                inserted_count INTEGER NOT NULL DEFAULT 0,
                duplicate_count INTEGER NOT NULL DEFAULT 0,
                error_message TEXT,
                started_at TEXT NOT NULL,
                finished_at TEXT
            );
            """
        )
        _ensure_column(connection, "users", "department", "TEXT")
        _ensure_column(connection, "users", "position", "TEXT")
        _ensure_column(connection, "users", "phone", "TEXT")
        _ensure_column(connection, "users", "created_at", "TEXT")
        _ensure_column(connection, "users", "updated_at", "TEXT")
        _ensure_column(connection, "users", "deleted_at", "TEXT")
        _ensure_column(connection, "schedules", "location", "TEXT")
        _ensure_column(connection, "schedules", "status", "TEXT NOT NULL DEFAULT 'confirmed'")
        _ensure_column(connection, "schedules", "is_active", "INTEGER NOT NULL DEFAULT 1")
        _ensure_column(connection, "schedules", "created_at", "TEXT")
        _ensure_column(connection, "schedules", "updated_at", "TEXT")
        _ensure_column(connection, "schedules", "deleted_at", "TEXT")

        now = utc_now()
        connection.execute("UPDATE users SET created_at = ? WHERE created_at IS NULL", (now,))
        connection.execute("UPDATE users SET updated_at = ? WHERE updated_at IS NULL", (now,))
        connection.execute("UPDATE schedules SET created_at = ? WHERE created_at IS NULL", (now,))
        connection.execute("UPDATE schedules SET updated_at = ? WHERE updated_at IS NULL", (now,))
        connection.execute(
            """
            INSERT OR IGNORE INTO users (id, name, email, department, position, role, created_at, updated_at)
            VALUES (1, '시스템 관리자', 'admin@example.local', '운영지원', '관리자', 'admin', ?, ?)
            """,
            (now, now),
        )
        connection.commit()


def db_health() -> dict[str, object]:
    init_db()
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()

    return {
        "status": "ok",
        "database": "sqlite",
        "checked_at": utc_now(),
        "tables": [row["name"] for row in rows],
    }
