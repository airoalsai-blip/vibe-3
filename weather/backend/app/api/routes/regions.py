from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.core.database import get_connection

router = APIRouter(prefix="/api/regions", tags=["regions"])


class RegionCreate(BaseModel):
    sido_name: str = Field(min_length=1)
    sigungu_name: str = Field(min_length=1)
    admin_code: str | None = None


@router.get("")
def list_regions() -> dict[str, list[dict[str, object]]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, sido_name, sigungu_name, admin_code, is_active, created_at, updated_at
            FROM regions
            ORDER BY sido_name, sigungu_name, id
            """
        ).fetchall()

    return {
        "items": [
            {key: row[key] for key in row.keys()}
            for row in rows
        ]
    }


@router.post("")
def create_region(payload: RegionCreate) -> dict[str, object]:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO regions (sido_name, sigungu_name, admin_code)
            VALUES (?, ?, ?)
            """,
            (payload.sido_name.strip(), payload.sigungu_name.strip(), payload.admin_code),
        )
        row = connection.execute(
            """
            SELECT id, sido_name, sigungu_name, admin_code, is_active, created_at, updated_at
            FROM regions
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=500, detail="지역 등록에 실패했습니다.")

    return {"item": {key: row[key] for key in row.keys()}}
