import os
from pathlib import Path

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


def _default_base_path() -> Path:
    if os.environ.get("GITHUB_WORKSPACE"):
        return Path(os.environ["GITHUB_WORKSPACE"]).resolve()
    return Path(__file__).resolve().parents[3]


_BASE_PATH = _default_base_path()


class Settings(BaseSettings):
    app_name: str = Field(default="KLeague Tactical Feedback")
    api_prefix: str = Field(default="/api")
    storage_path: str = Field(default=str(_BASE_PATH / "storage"))
    evidence_path: str = Field(default=str(_BASE_PATH / "storage" / "evidence"))
    frontend_origin: str = Field(default="http://localhost:3000")
    events_data_path: str = Field(default=str(_BASE_PATH / "00_data" / "Track2" / "raw_data.csv"))
    match_info_path: str = Field(default=str(_BASE_PATH / "00_data" / "Track2" / "match_info.csv"))
    demo_mode: bool = Field(default=True)
    # ML 모델 설정
    enable_will_have_shot: bool = Field(default=True, description="will_have_shot ML 모델 활성화 여부")
    will_have_shot_model_path: Optional[str] = Field(
        default=None,
        description="will_have_shot 모델 파일 경로 (None이면 기본 경로 사용)",
    )
    will_have_shot_threshold: Optional[float] = Field(
        default=None,
        description="will_have_shot 알림 threshold (None이면 모델 파일에서 읽음)",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    return Settings()
