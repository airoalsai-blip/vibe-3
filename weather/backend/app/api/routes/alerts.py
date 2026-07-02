from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from app.core.database import get_connection

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


class AlertCreate(BaseModel):
    employee_id: int | None = None
    department_id: int | None = None
    region_id: int | None = None
    alert_type: str
    notify_kind: str = "immediate"
    channel: str = "sms"
    target_time: str | None = None
    sent_at: str | None = None
    status: str = "pending"
    failure_reason: str | None = None
    retry_count: int = 0
    external_message_id: str | None = None


@router.get("")
def list_alerts() -> dict[str, list[dict[str, object]]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, employee_id, department_id, region_id, alert_type, notify_kind, channel,
                   target_time, sent_at, status, failure_reason, retry_count, external_message_id, created_at
            FROM notification_logs
            ORDER BY id DESC
            """
        ).fetchall()

    return {
        "items": [
            {key: row[key] for key in row.keys()}
            for row in rows
        ]
    }


@router.post("")
def create_alert(payload: AlertCreate) -> dict[str, object]:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO notification_logs (
                employee_id, department_id, region_id, alert_type, notify_kind, channel,
                target_time, sent_at, status, failure_reason, retry_count, external_message_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.employee_id,
                payload.department_id,
                payload.region_id,
                payload.alert_type.strip(),
                payload.notify_kind.strip(),
                payload.channel.strip(),
                payload.target_time,
                payload.sent_at,
                payload.status.strip(),
                payload.failure_reason,
                payload.retry_count,
                payload.external_message_id,
            ),
        )
        row = connection.execute(
            """
            SELECT id, employee_id, department_id, region_id, alert_type, notify_kind, channel,
                   target_time, sent_at, status, failure_reason, retry_count, external_message_id, created_at
            FROM notification_logs
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=500, detail="알림 이력 저장에 실패했습니다.")

    return {"item": {key: row[key] for key in row.keys()}}
