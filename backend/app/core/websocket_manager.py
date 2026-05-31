"""WebSocket 连接管理器 - 管理用户的 WebSocket 连接，支持实时提醒推送。"""

from typing import Any
from fastapi import WebSocket


class WebSocketManager:
    """管理所有用户的 WebSocket 连接。

    每个用户可以同时拥有多个连接（例如多个浏览器标签页），
    内部使用字典将 user_id 映射到一组 WebSocket 连接。
    """

    def __init__(self) -> None:
        # user_id -> set of WebSocket connections
        self._connections: dict[str, set[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        """接受 WebSocket 连接并将其添加到用户连接集合中。"""
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = set()
        self._connections[user_id].add(websocket)

    async def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        """从用户连接集合中移除 WebSocket 连接。"""
        if user_id in self._connections:
            self._connections[user_id].discard(websocket)
            if not self._connections[user_id]:
                del self._connections[user_id]

    def is_connected(self, user_id: str) -> bool:
        """检查用户是否有活跃的 WebSocket 连接。"""
        return user_id in self._connections and len(self._connections[user_id]) > 0

    async def send_to_user(self, user_id: str, message: dict[str, Any]) -> None:
        """向指定用户的所有连接发送 JSON 消息。

        如果某个连接发送失败，自动断开该连接。
        """
        if user_id not in self._connections:
            return

        disconnected: list[WebSocket] = []
        for websocket in self._connections[user_id]:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)

        # 清理失败的连接
        for ws in disconnected:
            await self.disconnect(user_id, ws)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """向所有已连接用户广播 JSON 消息。"""
        for user_id in list(self._connections.keys()):
            await self.send_to_user(user_id, message)

    @property
    def active_connections(self) -> int:
        """返回当前活跃连接总数。"""
        return sum(len(conns) for conns in self._connections.values())

    @property
    def active_users(self) -> int:
        """返回当前有活跃连接的用户数。"""
        return len(self._connections)


# 全局单例，供整个应用使用
ws_manager = WebSocketManager()
