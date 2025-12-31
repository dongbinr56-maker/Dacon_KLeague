import os
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import get_settings
from app.schemas.upload import UploadResponse

router = APIRouter()
settings = get_settings()


@router.post("/", response_model=UploadResponse)
async def upload_video(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="file is required")
    os.makedirs(settings.storage_path, exist_ok=True)

    file_id = f"upload-{uuid.uuid4()}"
    destination = os.path.join(settings.storage_path, f"{file_id}_{file.filename}")

    with open(destination, "wb") as f:
        content = await file.read()
        f.write(content)

    return UploadResponse(file_id=file_id, storage_url=destination)
