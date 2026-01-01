import os
from pathlib import Path

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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    return Settings()
