from fastapi import APIRouter

from app.core.database import get_connection

router = APIRouter(prefix="/api/departments", tags=["departments"])


@router.get("")
def list_departments() -> dict[str, list[dict[str, object]]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, description, is_active, created_at, updated_at
            FROM departments
            ORDER BY id
            """
        ).fetchall()

    return {
        "items": [
            {key: row[key] for key in row.keys()}
            for row in rows
        ]
    }
