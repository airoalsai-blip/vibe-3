from dataclasses import dataclass
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    app_name: str = "public-admin-superapp"
    version: str = "0.1.0"
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'app.db'}")
    admin_pin: str = os.getenv("ADMIN_PIN", "1234")


settings = Settings()
