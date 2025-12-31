from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = Field(default="KLeague Tactical Feedback")
    api_prefix: str = Field(default="/api")
    storage_path: str = Field(default="/workspace/storage")
    evidence_path: str = Field(default="/workspace/storage/evidence")
    frontend_origin: str = Field(default="http://localhost:3000")
    events_data_path: str = Field(default="/workspace/storage/train.csv")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    return Settings()
