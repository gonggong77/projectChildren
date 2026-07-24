"""백엔드 환경 변수 설정."""

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent / ".env"
DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


@dataclass(frozen=True)
class Settings:
    kopis_service: str
    playground_service_key: str


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"필수 환경 변수 {name}가 설정되지 않았습니다.")
    return value


def get_cors_origins() -> list[str]:
    """쉼표로 구분한 허용 오리진을 읽고, 전체 허용 설정은 거부한다."""
    load_dotenv(ENV_PATH)
    configured = os.getenv("CORS_ALLOWED_ORIGINS", "")
    origins = [origin.strip() for origin in configured.split(",") if origin.strip()]
    origins = origins or list(DEFAULT_CORS_ORIGINS)
    if "*" in origins:
        raise RuntimeError("CORS_ALLOWED_ORIGINS에는 '*'를 사용할 수 없습니다.")
    return origins


@lru_cache
def get_settings() -> Settings:
    """프로젝트 실행 위치와 무관하게 backend/.env를 한 번만 읽는다."""
    load_dotenv(ENV_PATH)
    return Settings(
        kopis_service=_required_env("KOPIS_SERVICE_KEY"),
        playground_service_key=_required_env("PLAYGROUND_SERVICE_KEY"),
    )
