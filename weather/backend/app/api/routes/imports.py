from base64 import b64decode
from csv import DictReader
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.database import get_connection, get_database_path

router = APIRouter(prefix="/api/imports", tags=["imports"])
ALLOWED_EXTENSIONS = {"xlsx", "csv", "hwp", "hwpx", "pdf"}


class ImportUploadPayload(BaseModel):
    file_name: str
    file_format: str = Field(min_length=1)
    content_base64: str | None = None


def _uploads_dir() -> Path:
    return get_database_path().parent / "uploads"


def _decode_base64_content(content_base64: str | None) -> bytes:
    if not content_base64:
        return b""

    encoded = content_base64.split(",", 1)[-1]
    return b64decode(encoded)


@router.get("/jobs")
def list_import_jobs() -> dict[str, list[dict[str, object]]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, file_name, file_format, status, processed_count, success_count, failure_count,
                   failure_reason, created_at, finished_at
            FROM file_import_jobs
            ORDER BY id DESC
            """
        ).fetchall()

    return {"items": [{key: row[key] for key in row.keys()} for row in rows]}


@router.get("/uploads")
def list_uploads() -> dict[str, list[dict[str, object]]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, file_name, file_path, file_format, size_bytes, status, message, created_at, updated_at
            FROM file_uploads
            ORDER BY id DESC
            """
        ).fetchall()

    return {"items": [{key: row[key] for key in row.keys()} for row in rows]}


@router.post("/upload")
def upload_file(payload: ImportUploadPayload) -> dict[str, object]:
    suffix = payload.file_format.lower().lstrip(".")
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다.")

    uploads_dir = _uploads_dir()
    uploads_dir.mkdir(parents=True, exist_ok=True)
    safe_name = payload.file_name.replace("\\", "_").replace("/", "_")
    stored_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{safe_name}"
    stored_path = uploads_dir / stored_name

    raw_bytes = _decode_base64_content(payload.content_base64)
    stored_path.write_bytes(raw_bytes)
    size_bytes = len(raw_bytes)

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO file_uploads (file_name, file_path, file_format, size_bytes, status, message)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (payload.file_name, str(stored_path), suffix, size_bytes, "received", "파일 저장 완료"),
        )

        import_status = "stored"
        processed_count = 0
        success_count = 0
        failure_count = 0
        failure_reason = None

        if suffix == "csv" and raw_bytes:
            try:
                csv_text = raw_bytes.decode("utf-8-sig")
                rows = list(DictReader(csv_text.splitlines()))
                processed_count = len(rows)
                success_count = len(rows)
                import_status = "completed"
            except Exception as exc:  # noqa: BLE001
                failure_count = 1
                failure_reason = str(exc)
                import_status = "failed"
        else:
            failure_reason = f"{suffix} 파일은 업로드만 저장했고, 파싱은 다음 단계에서 연결합니다."

        connection.execute(
            """
            INSERT INTO file_import_jobs (
                file_name, file_format, status, processed_count, success_count, failure_count, failure_reason, finished_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                payload.file_name,
                suffix,
                import_status,
                processed_count,
                success_count,
                failure_count,
                failure_reason,
            ),
        )

    return {
        "item": {
            "file_name": payload.file_name,
            "file_format": suffix,
            "size_bytes": size_bytes,
            "status": import_status,
            "failure_reason": failure_reason,
        }
    }
