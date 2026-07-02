from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.core.database import get_connection

router = APIRouter(prefix="/api/manual-entries", tags=["manual-entries"])


class ManualEntryCreate(BaseModel):
    department_id: int | None = None
    name: str = Field(min_length=1)
    position: str | None = None
    phone: str | None = None
    email: str | None = None
    duty_order: int = 1


@router.get("")
def list_manual_entries() -> dict[str, list[dict[str, object]]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                m.id,
                m.department_id,
                d.name AS department_name,
                m.name,
                m.position,
                m.phone,
                m.email,
                m.duty_order,
                m.status,
                m.created_at,
                m.updated_at
            FROM manual_entries m
            LEFT JOIN departments d ON d.id = m.department_id
            ORDER BY m.duty_order, m.id
            """
        ).fetchall()

    return {"items": [{key: row[key] for key in row.keys()} for row in rows]}


@router.post("")
def create_manual_entry(payload: ManualEntryCreate) -> dict[str, object]:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO manual_entries (department_id, name, position, phone, email, duty_order, status)
            VALUES (?, ?, ?, ?, ?, ?, 'active')
            """,
            (
                payload.department_id,
                payload.name.strip(),
                payload.position.strip() if payload.position else None,
                payload.phone.strip() if payload.phone else None,
                payload.email.strip() if payload.email else None,
                payload.duty_order,
            ),
        )
        row = connection.execute(
            """
            SELECT
                m.id,
                m.department_id,
                d.name AS department_name,
                m.name,
                m.position,
                m.phone,
                m.email,
                m.duty_order,
                m.status,
                m.created_at,
                m.updated_at
            FROM manual_entries m
            LEFT JOIN departments d ON d.id = m.department_id
            WHERE m.id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=500, detail="수기 입력 저장에 실패했습니다.")

    return {"item": {key: row[key] for key in row.keys()}}


@router.put("/{entry_id}")
def update_manual_entry(entry_id: int, payload: ManualEntryCreate) -> dict[str, object]:
    with get_connection() as connection:
        exists = connection.execute(
            "SELECT id FROM manual_entries WHERE id = ?",
            (entry_id,),
        ).fetchone()

        if exists is None:
            raise HTTPException(status_code=404, detail="수기 입력 항목을 찾을 수 없습니다.")

        connection.execute(
            """
            UPDATE manual_entries
            SET department_id = ?, name = ?, position = ?, phone = ?, email = ?, duty_order = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                payload.department_id,
                payload.name.strip(),
                payload.position.strip() if payload.position else None,
                payload.phone.strip() if payload.phone else None,
                payload.email.strip() if payload.email else None,
                payload.duty_order,
                entry_id,
            ),
        )
        row = connection.execute(
            """
            SELECT
                m.id,
                m.department_id,
                d.name AS department_name,
                m.name,
                m.position,
                m.phone,
                m.email,
                m.duty_order,
                m.status,
                m.created_at,
                m.updated_at
            FROM manual_entries m
            LEFT JOIN departments d ON d.id = m.department_id
            WHERE m.id = ?
            """,
            (entry_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=500, detail="수기 입력 수정에 실패했습니다.")

    return {"item": {key: row[key] for key in row.keys()}}
