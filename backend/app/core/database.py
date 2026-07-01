import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings


def _sqlite_path() -> Path:
    prefix = "sqlite:///"
    if not settings.database_url.startswith(prefix):
        raise RuntimeError("This scaffold health check currently supports sqlite DATABASE_URL values.")
    return Path(settings.database_url.removeprefix(prefix))


def get_connection() -> sqlite3.Connection:
    db_path = _sqlite_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path)


def init_db() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL DEFAULT 'member',
                is_active INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                start_at TEXT NOT NULL,
                end_at TEXT NOT NULL,
                visibility TEXT NOT NULL DEFAULT 'team',
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
            """
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO users (id, name, email, role)
            VALUES (1, '시스템 관리자', 'admin@example.local', 'admin')
            """
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
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "tables": [row[0] for row in rows],
    }
