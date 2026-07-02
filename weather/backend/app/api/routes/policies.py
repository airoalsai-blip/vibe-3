from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.core.database import get_connection

router = APIRouter(prefix="/api/policies", tags=["policies"])


class PolicyCreate(BaseModel):
    department_id: int
    region_id: int | None = None
    alert_types: list[str] = Field(default_factory=list)
    is_enabled: bool = True


class PolicyUpdate(BaseModel):
    department_id: int
    region_id: int | None = None
    alert_type: str
    is_enabled: bool = True


@router.get("")
def list_policies() -> dict[str, list[dict[str, object]]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                p.id,
                p.department_id,
                d.name AS department_name,
                p.region_id,
                r.sido_name AS region_sido_name,
                r.sigungu_name AS region_sigungu_name,
                p.alert_type,
                p.is_enabled,
                p.editable,
                p.created_at,
                p.updated_at
            FROM department_weather_policy p
            LEFT JOIN departments d ON d.id = p.department_id
            LEFT JOIN regions r ON r.id = p.region_id
            ORDER BY p.id DESC
            """
        ).fetchall()

    return {
        "items": [
            {key: row[key] for key in row.keys()}
            for row in rows
        ]
    }


@router.post("")
def save_policy(payload: PolicyCreate) -> dict[str, list[dict[str, object]]]:
    normalized_alert_types = [item.strip() for item in payload.alert_types if item.strip()]

    with get_connection() as connection:
        connection.execute(
            """
            DELETE FROM department_weather_policy
            WHERE department_id = ? AND (region_id IS ? OR region_id = ?)
            """,
            (payload.department_id, payload.region_id, payload.region_id),
        )

        for alert_type in normalized_alert_types:
            connection.execute(
                """
                INSERT INTO department_weather_policy (department_id, region_id, alert_type, is_enabled)
                VALUES (?, ?, ?, ?)
                """,
                (
                    payload.department_id,
                    payload.region_id,
                    alert_type,
                    1 if payload.is_enabled else 0,
                ),
            )

    return list_policies()


@router.put("/{policy_id}")
def update_policy(policy_id: int, payload: PolicyUpdate) -> dict[str, object]:
    with get_connection() as connection:
        exists = connection.execute(
            "SELECT id FROM department_weather_policy WHERE id = ?",
            (policy_id,),
        ).fetchone()

        if exists is None:
            raise HTTPException(status_code=404, detail="정책을 찾을 수 없습니다.")

        connection.execute(
            """
            UPDATE department_weather_policy
            SET department_id = ?, region_id = ?, alert_type = ?, is_enabled = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                payload.department_id,
                payload.region_id,
                payload.alert_type.strip(),
                1 if payload.is_enabled else 0,
                policy_id,
            ),
        )
        row = connection.execute(
            """
            SELECT
                p.id,
                p.department_id,
                d.name AS department_name,
                p.region_id,
                r.sido_name AS region_sido_name,
                r.sigungu_name AS region_sigungu_name,
                p.alert_type,
                p.is_enabled,
                p.editable,
                p.created_at,
                p.updated_at
            FROM department_weather_policy p
            LEFT JOIN departments d ON d.id = p.department_id
            LEFT JOIN regions r ON r.id = p.region_id
            WHERE p.id = ?
            """,
            (policy_id,),
        ).fetchone()

    return {"item": {key: row[key] for key in row.keys()}} if row else {"item": None}
