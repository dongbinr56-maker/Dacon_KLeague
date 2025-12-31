from pydantic import BaseModel


class UploadResponse(BaseModel):
    file_id: str
    storage_url: str
    download_url: str
    filename: str
    size_bytes: int
