import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import sessions, uploads, ws
from app.core.config import get_settings

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


@app.get("/")
async def root():
    return {"message": "KLeague tactical feedback backend", "service": settings.app_name}

app.mount(
    f"{settings.api_prefix}/evidence",
    StaticFiles(directory=settings.evidence_path),
    name="evidence",
)


app.include_router(sessions.router, prefix=f"{settings.api_prefix}/sessions", tags=["sessions"])
app.include_router(uploads.router, prefix=f"{settings.api_prefix}/uploads", tags=["uploads"])
app.include_router(ws.router, prefix=f"{settings.api_prefix}", tags=["ws"])
