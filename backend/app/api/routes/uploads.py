import os
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.schemas.upload import UploadResponse
from app.services.uploads.store import UploadItem, upload_store

router = APIRouter()
settings = get_settings()


@router.post("/", response_model=UploadResponse)
async def upload_video(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="file is required")
    os.makedirs(settings.storage_path, exist_ok=True)

    file_id = f"upload-{uuid.uuid4()}"
    destination = os.path.join(settings.storage_path, f"{file_id}_{file.filename}")
    content = await file.read()
    with open(destination, "wb") as f:
        f.write(content)

    item = UploadItem(
        file_id=file_id,
        path=destination,
        filename=file.filename,
        size_bytes=len(content),
    )
    upload_store.add(item)

    return UploadResponse(
        file_id=file_id,
        storage_url=destination,
        download_url=item.download_url,
        filename=file.filename,
        size_bytes=item.size_bytes,
    )


@router.get("/{file_id}")
async def download_file(file_id: str) -> FileResponse:
    item = upload_store.get(file_id)
    if not item:
        raise HTTPException(status_code=404, detail="file not found")
    if not os.path.exists(item.path):
        raise HTTPException(status_code=404, detail="file not available")
    return FileResponse(path=item.path, filename=item.filename)
