from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    # Database settings
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "sailing_routes"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Weather API settings
    OPENWEATHER_API_KEY: str = ""
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
    OPENWEATHER_ONECALL_URL: str = "https://api.openweathermap.org/data/3.0/onecall"

    # Redis settings
    REDIS_URL: str = "redis://localhost:6379"

    # API settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # CORS settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ]

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Route calculation settings
    DEFAULT_GRID_RESOLUTION_NM: float = 0.5
    DEFAULT_CORRIDOR_MARGIN_NM: float = 2.0
    MAX_ROUTE_CALCULATION_TIME: int = 30  # seconds

    # Geographical bounds for Gdansk Bay
    GDANSK_BAY_BOUNDS: dict = {
        "north": 54.8,
        "south": 54.3,
        "east": 19.0,
        "west": 18.3
    }

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
