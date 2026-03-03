from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    PLANNER_SERVICE_URL: str = "http://localhost:8001"
    QUIZ_SERVICE_URL: str   = "http://localhost:8002"
    CALENDAR_SERVICE_URL: str = "http://localhost:8003"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
