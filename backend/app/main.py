import os
from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import sessions, track2, uploads, ws
from app.core.config import get_settings
from app.services.data.track2 import validate_track2_data

settings = get_settings()

app = FastAPI(title=settings.app_name)

os.makedirs(settings.storage_path, exist_ok=True)
os.makedirs(settings.evidence_path, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

track2_validation: Dict[str, str] = {}
track2_error: Optional[str] = None
try:  # pragma: no cover - startup validation
    track2_validation = validate_track2_data()
except Exception as exc:  # noqa: BLE001
    track2_error = str(exc)


@app.get("/")
async def root():
    return {"message": "KLeague tactical feedback backend", "service": settings.app_name}

app.mount(
    f"{settings.api_prefix}/evidence",
    StaticFiles(directory=settings.evidence_path),
    name="evidence",
)


@app.get(f"{settings.api_prefix}/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "ok" if track2_error is None else "degraded",
        "track2": track2_validation,
        "track2_error": track2_error,
    }


app.mount(
    f"{settings.api_prefix}/evidence",
    StaticFiles(directory=settings.evidence_path),
    name="evidence",
)


app.include_router(sessions.router, prefix=f"{settings.api_prefix}/sessions", tags=["sessions"])
app.include_router(uploads.router, prefix=f"{settings.api_prefix}/uploads", tags=["uploads"])
app.include_router(track2.router, prefix=f"{settings.api_prefix}/track2", tags=["track2"])
app.include_router(ws.router, prefix=f"{settings.api_prefix}", tags=["ws"])
