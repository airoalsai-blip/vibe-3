import sqlite3
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from app.core.database import get_connection

router = APIRouter(prefix="/api/weather", tags=["weather"])


class WeatherAlertCreate(BaseModel):
    region_id: int | None = None
    alert_type: str
    severity: str = "주의보"
    issued_at: str | None = None
    expires_at: str | None = None
    status: str = "active"
    raw_json: str | None = None


@router.get("/alerts")
def list_weather_alerts() -> dict[str, list[dict[str, object]]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, region_id, alert_type, severity, issued_at, expires_at, status, collected_at
            FROM weather_alerts
            ORDER BY id DESC
            """
        ).fetchall()

    return {
        "items": [
            {key: row[key] for key in row.keys()}
            for row in rows
        ]
    }


@router.post("/alerts")
def create_weather_alert(payload: WeatherAlertCreate) -> dict[str, object]:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO weather_alerts (region_id, alert_type, severity, issued_at, expires_at, status, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.region_id,
                payload.alert_type.strip(),
                payload.severity.strip(),
                payload.issued_at,
                payload.expires_at,
                payload.status.strip(),
                payload.raw_json,
            ),
        )
        row = connection.execute(
            """
            SELECT id, region_id, alert_type, severity, issued_at, expires_at, status, collected_at
            FROM weather_alerts
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=500, detail="특보 저장에 실패했습니다.")

    return {"item": {key: row[key] for key in row.keys()}}
