import contextlib
from uuid import UUID

from fastapi import WebSocket


class ConnectionManager:
    """Tracks active WebSocket connections per user.

    Each user can have multiple concurrent connections; each connection
    is tracked independently in a list keyed by user_id.
    """

    def __init__(self) -> None:
        self.active: dict[UUID, list[WebSocket]] = {}

    async def connect(self, user_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        if user_id not in self.active:
            self.active[user_id] = []
        self.active[user_id].append(websocket)

    def disconnect(self, user_id: UUID, websocket: WebSocket) -> None:
        if user_id in self.active:
            self.active[user_id].remove(websocket)
            if not self.active[user_id]:
                del self.active[user_id]

    async def send_to_user(self, user_id: UUID, message: dict) -> None:
        """Send a JSON message to all active connections for a user."""
        if user_id in self.active:
            for ws in self.active[user_id]:
                with contextlib.suppress(Exception):
                    await ws.send_json(message)


manager = ConnectionManager()
