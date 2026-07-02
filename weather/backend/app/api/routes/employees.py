from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.core.database import get_connection

router = APIRouter(prefix="/api/employees", tags=["employees"])


class EmployeeCreate(BaseModel):
    department_id: int | None = None
    name: str = Field(min_length=1)
    position: str | None = None
    phone: str | None = None
    email: str | None = None
    duty_order: int = 1
    memo: str | None = None


@router.get("")
def list_employees() -> dict[str, list[dict[str, object]]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                e.id,
                e.department_id,
                d.name AS department_name,
                e.name,
                e.position,
                e.phone,
                e.email,
                e.duty_order,
                e.status,
                e.memo,
                e.created_at,
                e.updated_at
            FROM employees e
            LEFT JOIN departments d ON d.id = e.department_id
            ORDER BY e.duty_order, e.id
            """
        ).fetchall()

    return {
        "items": [
            {key: row[key] for key in row.keys()}
            for row in rows
        ]
    }


@router.post("")
def create_employee(payload: EmployeeCreate) -> dict[str, object]:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO employees (department_id, name, position, phone, email, duty_order, status, memo)
            VALUES (?, ?, ?, ?, ?, ?, 'active', ?)
            """,
            (
                payload.department_id,
                payload.name.strip(),
                payload.position.strip() if payload.position else None,
                payload.phone.strip() if payload.phone else None,
                payload.email.strip() if payload.email else None,
                payload.duty_order,
                payload.memo.strip() if payload.memo else None,
            ),
        )
        row = connection.execute(
            """
            SELECT id, department_id, name, position, phone, email, duty_order, status, memo, created_at, updated_at
            FROM employees
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=500, detail="직원 등록에 실패했습니다.")

    return {"item": {key: row[key] for key in row.keys()}}
