from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    app_name: str = "weather-duty-alert"
    version: str = "0.1.0"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/weather.db")


settings = Settings()
