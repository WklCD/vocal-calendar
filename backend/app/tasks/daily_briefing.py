"""每日摘要定时任务 — 早晚自动为用户生成日程摘要并通过 WebSocket 推送。"""

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.database import SessionLocal
from app.core.websocket_manager import ws_manager
from app.models.user import User
from app.services.ai_service import AIService
from app.services.llm.factory import create_llm

logger = logging.getLogger(__name__)


async def _send_briefing_to_all_users(period: str) -> None:
    """遍历所有用户，生成摘要并推送。

    Args:
        period: "morning" 或 "evening"
    """
    db = SessionLocal()
    try:
        users = db.query(User).all()
        if not users:
            logger.info("无注册用户，跳过 %s 摘要", period)
            return

        llm = create_llm()
        service = AIService(db=db, llm=llm)

        label = "早间" if period == "morning" else "晚间"
        sent_count = 0

        for user in users:
            try:
                briefing = await service.generate_daily_briefing(
                    user_id=user.id,
                    period=period,
                )
                if ws_manager.is_connected(user.id):
                    await ws_manager.send_to_user(user.id, {
                        "type": "daily_briefing",
                        "period": period,
                        "briefing": briefing,
                    })
                    sent_count += 1
            except Exception:
                logger.exception(
                    "为用户 %s 生成 %s 摘要时出错", user.id, label
                )

        logger.info(
            "%s摘要完成：共 %d 用户，成功推送 %d",
            label, len(users), sent_count,
        )
    except Exception:
        logger.exception("执行 %s 摘要任务时出错", period)
    finally:
        db.close()


async def send_morning_briefing() -> None:
    """早间摘要（7:30 触发），查询今日日程。"""
    logger.info("开始执行早间摘要任务")
    await _send_briefing_to_all_users("morning")


async def send_evening_briefing() -> None:
    """晚间摘要（21:00 触发），查询明日日程。"""
    logger.info("开始执行晚间摘要任务")
    await _send_briefing_to_all_users("evening")


def register_briefing_jobs(scheduler: AsyncIOScheduler) -> None:
    """向现有调度器注册每日摘要定时任务。

    - 早间摘要：每天 7:30
    - 晚间摘要：每天 21:00

    Args:
        scheduler: 已初始化的 AsyncIOScheduler 实例
    """
    scheduler.add_job(
        send_morning_briefing,
        "cron",
        hour=7,
        minute=30,
        id="morning_briefing",
        replace_existing=True,
    )
    logger.info("已注册早间摘要定时任务（每日 7:30）")

    scheduler.add_job(
        send_evening_briefing,
        "cron",
        hour=21,
        minute=0,
        id="evening_briefing",
        replace_existing=True,
    )
    logger.info("已注册晚间摘要定时任务（每日 21:00）")
