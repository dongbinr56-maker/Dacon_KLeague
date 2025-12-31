from pydantic import BaseModel


class UploadResponse(BaseModel):
    file_id: str
    storage_url: str
