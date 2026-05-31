"""WebSocket 路由 - 提供实时提醒推送端点。"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.security import decode_token
from app.core.websocket_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/reminder")
async def reminder_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="JWT 访问令牌"),
) -> None:
    """提醒推送 WebSocket 端点。

    客户端通过 `?token=<jwt>` 查询参数进行身份验证。
    连接成功后，服务端可以实时向客户端推送提醒消息。

    客户端可以发送以下消息：
    - {"type": "ack", "reminder_id": "..."} - 确认收到提醒
    """
    # 验证 JWT 令牌
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        await websocket.close(code=4001, reason="无效的访问令牌")
        return

    user_id = str(payload["sub"])

    # 注册连接
    await ws_manager.connect(user_id, websocket)
    logger.info(f"用户 {user_id} 建立 WebSocket 连接")

    try:
        # 持续监听客户端消息
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "ack":
                reminder_id = data.get("reminder_id")
                logger.info(f"用户 {user_id} 确认收到提醒 {reminder_id}")
                # 后续可在此处更新数据库中提醒的已读状态
            else:
                logger.warning(f"用户 {user_id} 发送未知消息类型: {message_type}")

    except WebSocketDisconnect:
        logger.info(f"用户 {user_id} 断开 WebSocket 连接")
    except Exception as e:
        logger.error(f"用户 {user_id} WebSocket 异常: {e}")
    finally:
        await ws_manager.disconnect(user_id, websocket)
