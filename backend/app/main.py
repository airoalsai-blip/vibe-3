from __future__ import annotations

from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import sqlite3
from threading import Thread
from typing import Any
from urllib.parse import parse_qs, urlparse

from app.core.config import settings
from app.core.database import db_health, get_connection, init_db, utc_now
from app.services.news_collector import collect_policy_news, list_news_articles, list_news_runs, parse_manual_target_date
from app.services.scheduler import start_news_scheduler


def json_response(handler: BaseHTTPRequestHandler, payload: dict[str, Any], status: int = 200) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, Accept, X-Admin-Pin")
    handler.end_headers()
    handler.wfile.write(body)


def error_response(handler: BaseHTTPRequestHandler, message: str, status: int = 400) -> None:
    json_response(handler, {"status": "error", "message": message}, status)


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def require_admin_pin(handler: BaseHTTPRequestHandler) -> bool:
    if handler.headers.get("X-Admin-Pin") == settings.admin_pin:
        return True
    error_response(handler, "관리자 PIN이 올바르지 않습니다.", 403)
    return False


def read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any] | None:
    length = int(handler.headers.get("Content-Length", "0"))
    if length == 0:
        return {}
    try:
        return json.loads(handler.rfile.read(length).decode("utf-8"))
    except json.JSONDecodeError:
        error_response(handler, "JSON 형식이 올바르지 않습니다.", 400)
        return None


def validate_datetime(value: str, field: str) -> str:
    if not value:
        raise ValueError(f"{field} 값이 필요합니다.")
    datetime.fromisoformat(value)
    return value


def parse_resource_id(path: str, prefix: str) -> int | None:
    if not path.startswith(prefix):
        return None
    raw_id = path.removeprefix(prefix).strip("/")
    if not raw_id:
        return None
    try:
        return int(raw_id)
    except ValueError:
        return None


def list_team_members() -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, email, department, position, phone, role, is_active, created_at, updated_at
            FROM users
            WHERE is_active = 1 AND deleted_at IS NULL
            ORDER BY name
            """
        ).fetchall()
    return [row_to_dict(row) for row in rows]


def create_team_member(payload: dict[str, Any]) -> dict[str, Any]:
    name = str(payload.get("name", "")).strip()
    if not name:
        raise ValueError("팀원 이름이 필요합니다.")

    now = utc_now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO users (name, email, department, position, phone, role, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                payload.get("email") or None,
                payload.get("department") or None,
                payload.get("position") or None,
                payload.get("phone") or None,
                payload.get("role") or "member",
                now,
                now,
            ),
        )
        connection.commit()
        row = connection.execute(
            """
            SELECT id, name, email, department, position, phone, role, is_active, created_at, updated_at
            FROM users
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
    return row_to_dict(row)


def update_team_member(member_id: int, payload: dict[str, Any]) -> dict[str, Any] | None:
    name = str(payload.get("name", "")).strip()
    if not name:
        raise ValueError("팀원 이름이 필요합니다.")

    now = utc_now()
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE users
            SET name = ?, email = ?, department = ?, position = ?, phone = ?, role = ?, updated_at = ?
            WHERE id = ? AND is_active = 1 AND deleted_at IS NULL
            """,
            (
                name,
                payload.get("email") or None,
                payload.get("department") or None,
                payload.get("position") or None,
                payload.get("phone") or None,
                payload.get("role") or "member",
                now,
                member_id,
            ),
        )
        connection.commit()
        row = connection.execute(
            """
            SELECT id, name, email, department, position, phone, role, is_active, created_at, updated_at
            FROM users
            WHERE id = ? AND is_active = 1 AND deleted_at IS NULL
            """,
            (member_id,),
        ).fetchone()
    return row_to_dict(row) if row else None


def delete_team_member(member_id: int) -> bool:
    now = utc_now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE users
            SET is_active = 0, deleted_at = ?, updated_at = ?
            WHERE id = ? AND is_active = 1 AND deleted_at IS NULL
            """,
            (now, now, member_id),
        )
        connection.execute(
            """
            UPDATE schedules
            SET is_active = 0, deleted_at = ?, updated_at = ?
            WHERE owner_id = ? AND is_active = 1 AND deleted_at IS NULL
            """,
            (now, now, member_id),
        )
        connection.commit()
    return cursor.rowcount > 0


def list_schedules(query: dict[str, list[str]]) -> list[dict[str, Any]]:
    from_date = query.get("from", [""])[0]
    to_date = query.get("to", [""])[0]
    clauses = ["s.is_active = 1", "s.deleted_at IS NULL"]
    values: list[Any] = []
    if from_date:
        clauses.append("date(s.end_at) >= date(?)")
        values.append(from_date)
    if to_date:
        clauses.append("date(s.start_at) <= date(?)")
        values.append(to_date)

    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT
              s.id, s.owner_id, u.name AS owner_name, s.type, s.title, s.description,
              s.location, s.start_at, s.end_at, s.visibility, s.status,
              s.created_at, s.updated_at
            FROM schedules s
            LEFT JOIN users u ON u.id = s.owner_id
            WHERE {" AND ".join(clauses)}
            ORDER BY s.start_at, s.id
            """,
            values,
        ).fetchall()
    return [row_to_dict(row) for row in rows]


def get_schedule(schedule_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
              s.id, s.owner_id, u.name AS owner_name, s.type, s.title, s.description,
              s.location, s.start_at, s.end_at, s.visibility, s.status,
              s.created_at, s.updated_at
            FROM schedules s
            LEFT JOIN users u ON u.id = s.owner_id
            WHERE s.id = ? AND s.is_active = 1 AND s.deleted_at IS NULL
            """,
            (schedule_id,),
        ).fetchone()
    return row_to_dict(row) if row else None


def validate_schedule_payload(payload: dict[str, Any]) -> tuple[int, str, str, str | None, str | None, str, str]:
    owner_id = int(payload.get("owner_id") or 0)
    title = str(payload.get("title", "")).strip()
    schedule_type = str(payload.get("type", "")).strip()
    start_at = validate_datetime(str(payload.get("start_at", "")), "시작 일시")
    end_at = validate_datetime(str(payload.get("end_at", "")), "종료 일시")
    if not owner_id:
        raise ValueError("팀원을 선택해야 합니다.")
    if not title:
        raise ValueError("일정 제목이 필요합니다.")
    if not schedule_type:
        raise ValueError("일정 유형이 필요합니다.")
    if datetime.fromisoformat(end_at) <= datetime.fromisoformat(start_at):
        raise ValueError("종료 일시는 시작 일시보다 이후여야 합니다.")
    return (
        owner_id,
        schedule_type,
        title,
        payload.get("description") or None,
        payload.get("location") or None,
        start_at,
        end_at,
    )


def active_member_exists(connection: sqlite3.Connection, member_id: int) -> bool:
    row = connection.execute(
        "SELECT id FROM users WHERE id = ? AND is_active = 1 AND deleted_at IS NULL",
        (member_id,),
    ).fetchone()
    return row is not None


def create_schedule(payload: dict[str, Any]) -> dict[str, Any]:
    owner_id, schedule_type, title, description, location, start_at, end_at = validate_schedule_payload(payload)
    now = utc_now()
    with get_connection() as connection:
        if not active_member_exists(connection, owner_id):
            raise ValueError("선택한 팀원을 찾을 수 없습니다.")
        cursor = connection.execute(
            """
            INSERT INTO schedules
              (owner_id, type, title, description, location, start_at, end_at, visibility, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'team', 'confirmed', ?, ?)
            """,
            (owner_id, schedule_type, title, description, location, start_at, end_at, now, now),
        )
        connection.commit()
        schedule_id = int(cursor.lastrowid)
    item = get_schedule(schedule_id)
    if item is None:
        raise ValueError("생성된 일정을 조회하지 못했습니다.")
    return item


def update_schedule(schedule_id: int, payload: dict[str, Any]) -> dict[str, Any] | None:
    owner_id, schedule_type, title, description, location, start_at, end_at = validate_schedule_payload(payload)
    now = utc_now()
    with get_connection() as connection:
        if not active_member_exists(connection, owner_id):
            raise ValueError("선택한 팀원을 찾을 수 없습니다.")
        connection.execute(
            """
            UPDATE schedules
            SET owner_id = ?, type = ?, title = ?, description = ?, location = ?,
                start_at = ?, end_at = ?, updated_at = ?
            WHERE id = ? AND is_active = 1 AND deleted_at IS NULL
            """,
            (owner_id, schedule_type, title, description, location, start_at, end_at, now, schedule_id),
        )
        connection.commit()
    return get_schedule(schedule_id)


def delete_schedule(schedule_id: int) -> bool:
    now = utc_now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE schedules
            SET is_active = 0, deleted_at = ?, updated_at = ?
            WHERE id = ? AND is_active = 1 AND deleted_at IS NULL
            """,
            (now, now, schedule_id),
        )
        connection.commit()
    return cursor.rowcount > 0


class ApiHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        json_response(self, {"status": "ok"})

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/api/health":
            json_response(self, {"status": "ok", "service": settings.app_name, "version": settings.version})
            return

        if path == "/api/db/health":
            json_response(self, db_health())
            return

        if path == "/api/team-members":
            json_response(self, {"items": list_team_members()})
            return

        if path == "/api/schedules":
            json_response(self, {"items": list_schedules(query)})
            return

        if path == "/api/news/articles":
            target_date = query.get("date", [None])[0]
            json_response(self, {"items": list_news_articles(target_date)})
            return

        if path == "/api/news/runs":
            limit = query.get("limit", ["20"])[0]
            try:
                limit_value = max(1, min(100, int(limit)))
            except ValueError:
                limit_value = 20
            json_response(self, {"items": list_news_runs(limit_value)})
            return

        error_response(self, f"지원하지 않는 경로입니다: {path}", 404)

    def do_POST(self) -> None:
        if not require_admin_pin(self):
            return
        payload = read_json_body(self)
        if payload is None:
            return

        try:
            if self.path == "/api/team-members":
                json_response(self, {"item": create_team_member(payload)}, 201)
                return
            if self.path == "/api/schedules":
                json_response(self, {"item": create_schedule(payload)}, 201)
                return
            if self.path == "/api/news/collect":
                target_date = parse_manual_target_date(payload)
                result = collect_policy_news(target_date, mode="manual")
                json_response(self, result, 201)
                return
        except sqlite3.IntegrityError:
            error_response(self, "이미 사용 중인 이메일입니다.", 409)
            return
        except ValueError as exc:
            error_response(self, str(exc), 400)
            return
        except Exception as exc:
            error_response(self, str(exc), 500)
            return

        error_response(self, f"지원하지 않는 경로입니다: {self.path}", 404)

    def do_PATCH(self) -> None:
        if not require_admin_pin(self):
            return
        payload = read_json_body(self)
        if payload is None:
            return

        try:
            member_id = parse_resource_id(self.path, "/api/team-members/")
            if member_id is not None:
                item = update_team_member(member_id, payload)
                if item is None:
                    error_response(self, "팀원을 찾을 수 없습니다.", 404)
                    return
                json_response(self, {"item": item})
                return

            schedule_id = parse_resource_id(self.path, "/api/schedules/")
            if schedule_id is not None:
                item = update_schedule(schedule_id, payload)
                if item is None:
                    error_response(self, "일정을 찾을 수 없습니다.", 404)
                    return
                json_response(self, {"item": item})
                return
        except sqlite3.IntegrityError:
            error_response(self, "이미 사용 중인 이메일입니다.", 409)
            return
        except ValueError as exc:
            error_response(self, str(exc), 400)
            return

        error_response(self, f"지원하지 않는 경로입니다: {self.path}", 404)

    def do_DELETE(self) -> None:
        if not require_admin_pin(self):
            return

        member_id = parse_resource_id(self.path, "/api/team-members/")
        if member_id is not None:
            if not delete_team_member(member_id):
                error_response(self, "팀원을 찾을 수 없습니다.", 404)
                return
            json_response(self, {"status": "ok"})
            return

        schedule_id = parse_resource_id(self.path, "/api/schedules/")
        if schedule_id is not None:
            if not delete_schedule(schedule_id):
                error_response(self, "일정을 찾을 수 없습니다.", 404)
                return
            json_response(self, {"status": "ok"})
            return

        error_response(self, f"지원하지 않는 경로입니다: {self.path}", 404)

    def log_message(self, format: str, *args: Any) -> None:
        return


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    init_db()
    start_news_scheduler()
    server = ThreadingHTTPServer((host, port), ApiHandler)
    print(f"Backend API running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
