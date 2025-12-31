from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = Field(default="KLeague Tactical Feedback")
    api_prefix: str = Field(default="/api")
    storage_path: str = Field(default="/workspace/storage")
    frontend_origin: str = Field(default="*")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    return Settings()
