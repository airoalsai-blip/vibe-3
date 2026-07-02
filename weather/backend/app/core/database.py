import sqlite3
from pathlib import Path

from app.core.config import settings


def get_database_path() -> Path:
    prefix = "sqlite:///"
    if not settings.database_url.startswith(prefix):
        raise RuntimeError("DATABASE_URL must use sqlite:/// for the initial scaffold.")
    return Path(settings.database_url.removeprefix(prefix))


def get_connection() -> sqlite3.Connection:
    database_path = get_database_path()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    uploads_dir = get_database_path().parent / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    with get_connection() as connection:
        connection.executescript(
          """
          CREATE TABLE IF NOT EXISTS regions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              sido_name TEXT NOT NULL,
              sigungu_name TEXT NOT NULL,
              admin_code TEXT,
              is_active INTEGER NOT NULL DEFAULT 1,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT DEFAULT CURRENT_TIMESTAMP
          );

          CREATE TABLE IF NOT EXISTS departments (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL UNIQUE,
              description TEXT,
              is_active INTEGER NOT NULL DEFAULT 1,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT DEFAULT CURRENT_TIMESTAMP
          );

          CREATE TABLE IF NOT EXISTS employees (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              department_id INTEGER,
              name TEXT NOT NULL,
              position TEXT,
              phone TEXT,
              email TEXT,
              duty_order INTEGER NOT NULL DEFAULT 1,
              status TEXT NOT NULL DEFAULT 'active',
              memo TEXT,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY(department_id) REFERENCES departments(id)
          );

          CREATE TABLE IF NOT EXISTS weather_alerts (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              region_id INTEGER,
              alert_type TEXT NOT NULL,
              severity TEXT NOT NULL,
              issued_at TEXT,
              expires_at TEXT,
              status TEXT NOT NULL DEFAULT 'active',
              raw_json TEXT,
              collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY(region_id) REFERENCES regions(id)
          );

          CREATE TABLE IF NOT EXISTS department_weather_policy (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              department_id INTEGER NOT NULL,
              region_id INTEGER,
              alert_type TEXT NOT NULL,
              is_enabled INTEGER NOT NULL DEFAULT 1,
              editable INTEGER NOT NULL DEFAULT 1,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY(department_id) REFERENCES departments(id),
              FOREIGN KEY(region_id) REFERENCES regions(id)
          );

          CREATE TABLE IF NOT EXISTS duty_rotations (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              department_id INTEGER NOT NULL,
              current_employee_id INTEGER,
              next_employee_id INTEGER,
              pre_alert_minutes INTEGER NOT NULL DEFAULT 30,
              is_active INTEGER NOT NULL DEFAULT 1,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY(department_id) REFERENCES departments(id),
              FOREIGN KEY(current_employee_id) REFERENCES employees(id),
              FOREIGN KEY(next_employee_id) REFERENCES employees(id)
          );

          CREATE TABLE IF NOT EXISTS notification_rules (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              department_id INTEGER NOT NULL,
              region_id INTEGER,
              alert_type TEXT NOT NULL,
              immediate_enabled INTEGER NOT NULL DEFAULT 1,
              prealert_enabled INTEGER NOT NULL DEFAULT 1,
              prealert_channel TEXT NOT NULL DEFAULT 'sms',
              immediate_channel TEXT NOT NULL DEFAULT 'sms',
              created_at TEXT DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY(department_id) REFERENCES departments(id),
              FOREIGN KEY(region_id) REFERENCES regions(id)
          );

          CREATE TABLE IF NOT EXISTS notification_logs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              employee_id INTEGER,
              department_id INTEGER,
              region_id INTEGER,
              alert_type TEXT NOT NULL,
              notify_kind TEXT NOT NULL,
              channel TEXT NOT NULL,
              target_time TEXT,
              sent_at TEXT,
              status TEXT NOT NULL DEFAULT 'pending',
              failure_reason TEXT,
              retry_count INTEGER NOT NULL DEFAULT 0,
              external_message_id TEXT,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY(employee_id) REFERENCES employees(id),
              FOREIGN KEY(department_id) REFERENCES departments(id),
              FOREIGN KEY(region_id) REFERENCES regions(id)
          );

          CREATE TABLE IF NOT EXISTS file_uploads (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              file_name TEXT NOT NULL,
              file_path TEXT NOT NULL,
              file_format TEXT NOT NULL,
              size_bytes INTEGER NOT NULL DEFAULT 0,
              status TEXT NOT NULL DEFAULT 'received',
              message TEXT,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT DEFAULT CURRENT_TIMESTAMP
          );

          CREATE TABLE IF NOT EXISTS file_import_jobs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              file_name TEXT NOT NULL,
              file_format TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'pending',
              processed_count INTEGER NOT NULL DEFAULT 0,
              success_count INTEGER NOT NULL DEFAULT 0,
              failure_count INTEGER NOT NULL DEFAULT 0,
              failure_reason TEXT,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP,
              finished_at TEXT
          );

          CREATE TABLE IF NOT EXISTS manual_entries (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              department_id INTEGER,
              name TEXT NOT NULL,
              position TEXT,
              phone TEXT,
              email TEXT,
              duty_order INTEGER NOT NULL DEFAULT 1,
              status TEXT NOT NULL DEFAULT 'active',
              created_at TEXT DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY(department_id) REFERENCES departments(id)
          );
          """
        )

        region_count = connection.execute("SELECT COUNT(*) AS count FROM regions").fetchone()["count"]
        if region_count == 0:
            connection.executemany(
                """
                INSERT INTO regions (sido_name, sigungu_name, admin_code)
                VALUES (?, ?, ?)
                """,
                [
                    ("서울특별시", "전체", "11"),
                    ("경기도", "전체", "41"),
                    ("인천광역시", "전체", "28"),
                ],
            )

        department_count = connection.execute("SELECT COUNT(*) AS count FROM departments").fetchone()["count"]
        if department_count == 0:
            connection.executemany(
                """
                INSERT INTO departments (name, description)
                VALUES (?, ?)
                """,
                [
                    ("총무팀", "행정 및 일반 관리"),
                    ("안전팀", "비상근무 및 안전 대응"),
                    ("행정팀", "민원 및 행정 지원"),
                ],
            )

        employee_count = connection.execute("SELECT COUNT(*) AS count FROM employees").fetchone()["count"]
        if employee_count == 0:
            department_rows = connection.execute("SELECT id, name FROM departments ORDER BY id").fetchall()
            department_map = {row["name"]: row["id"] for row in department_rows}
            connection.executemany(
                """
                INSERT INTO employees (department_id, name, position, phone, email, duty_order, status, memo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (department_map.get("총무팀"), "김민수", "주무관", "010-0000-0001", "minsu@example.com", 1, "active", "기본 시드"),
                    (department_map.get("안전팀"), "이지은", "주무관", "010-0000-0002", "jiyoon@example.com", 2, "active", "기본 시드"),
                    (department_map.get("행정팀"), "박서연", "주무관", "010-0000-0003", "seoyeon@example.com", 3, "active", "기본 시드"),
                ],
            )
