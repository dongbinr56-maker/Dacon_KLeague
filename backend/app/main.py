from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import sessions, uploads, ws
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "KLeague tactical feedback backend", "service": settings.app_name}


app.include_router(sessions.router, prefix=f"{settings.api_prefix}/sessions", tags=["sessions"])
app.include_router(uploads.router, prefix=f"{settings.api_prefix}/uploads", tags=["uploads"])
app.include_router(ws.router, prefix=f"{settings.api_prefix}", tags=["ws"])
