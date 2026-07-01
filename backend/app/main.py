from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from typing import Any
from urllib.parse import urlparse

from app.core.config import settings
from app.core.database import db_health, init_db


def json_response(handler: BaseHTTPRequestHandler, payload: dict[str, Any], status: int = 200) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, Accept")
    handler.end_headers()
    handler.wfile.write(body)


class ApiHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        json_response(self, {"status": "ok"})

    def do_GET(self) -> None:
        path = urlparse(self.path).path

        if path == "/api/health":
            json_response(
                self,
                {
                    "status": "ok",
                    "service": settings.app_name,
                    "version": settings.version,
                },
            )
            return

        if path == "/api/db/health":
            json_response(self, db_health())
            return

        if path == "/api/schedules":
            json_response(
                self,
                {
                    "items": [
                        {
                            "id": 1,
                            "type": "근무",
                            "title": "민원 접수 현황 점검",
                            "start_at": "2026-07-01T09:00:00+09:00",
                            "end_at": "2026-07-01T10:00:00+09:00",
                        }
                    ]
                },
            )
            return

        if path == "/api/news/articles":
            json_response(
                self,
                {
                    "items": [
                        {
                            "id": 1,
                            "title": "공공 행정 서비스 개선 동향",
                            "source": "행정 브리핑",
                            "category": "전자정부",
                        }
                    ]
                },
            )
            return

        json_response(self, {"status": "not_found", "path": path}, status=404)

    def log_message(self, format: str, *args: Any) -> None:
        return


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    init_db()
    server = ThreadingHTTPServer((host, port), ApiHandler)
    print(f"Backend API running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
