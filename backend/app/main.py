from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.api.health import router as health_router

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.auth import router as auth_router
from app.api.events import router as events_router
from app.api.categories import router as categories_router
from app.api.voice import router as voice_router
from app.api.ai import router as ai_router

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(events_router)
app.include_router(categories_router)
app.include_router(voice_router)
app.include_router(ai_router)
