"""APScheduler 定时任务 - 定期检查并处理待发送的提醒。"""

import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.database import SessionLocal
from app.services.reminder_service import ReminderService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def check_reminders() -> None:
    """异步任务：检查并处理所有到期的待发送提醒。"""
    db = SessionLocal()
    try:
        service = ReminderService(db)
        count = await service.process_pending_reminders()
        if count > 0:
            logger.info("已处理 %d 条提醒", count)
    except Exception:
        logger.exception("处理提醒时发生错误")
    finally:
        db.close()


def start_scheduler() -> None:
    """启动定时任务调度器，每分钟检查一次待发送提醒。"""
    if scheduler.running:
        return
    scheduler.add_job(
        check_reminders,
        "interval",
        minutes=1,
        id="check_reminders",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("提醒定时任务调度器已启动")


def stop_scheduler() -> None:
    """停止定时任务调度器。"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("提醒定时任务调度器已停止")
