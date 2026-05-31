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
from app.api.websocket import router as websocket_router
from app.api.reminders import router as reminders_router
from app.api.weather import router as weather_router
from app.api.holidays import router as holidays_router
from app.api.share import router as share_router
from app.api.lunar import router as lunar_router
from app.api.export_import import router as export_import_router
from app.tasks.reminder_task import start_scheduler, stop_scheduler, scheduler
from app.tasks.daily_briefing import register_briefing_jobs

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(events_router)
app.include_router(categories_router)
app.include_router(voice_router)
app.include_router(ai_router)
app.include_router(websocket_router)
app.include_router(reminders_router)
app.include_router(weather_router)
app.include_router(holidays_router)
app.include_router(share_router)
app.include_router(lunar_router)
app.include_router(export_import_router)


@app.on_event("startup")
async def on_startup() -> None:
    start_scheduler()
    register_briefing_jobs(scheduler)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    stop_scheduler()
