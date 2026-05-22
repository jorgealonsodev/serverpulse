import asyncio
import contextlib
import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.database import async_session as _app_async_session
from app.models.server import Server
from app.models.user import User
from app.redis_client import redis_client
from app.ws.manager import manager

router = APIRouter()


@asynccontextmanager
async def _get_ws_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for WS endpoint DB sessions.

    Patchable in tests to inject a test-specific session.
    """
    async with _app_async_session() as session:
        yield session


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str | None = None) -> None:
    """WebSocket endpoint for real-time metric and status delivery.

    Auth: JWT passed as ``token`` query parameter.
    On connect: subscribes to Redis pub/sub for all user's servers and sends
    initial status for each.
    On disconnect: unsubscribes, cancels listener task, removes from manager.
    """
    # --- Auth ---
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    try:
        payload = decode_token(token)
        user_id = payload["sub"]
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # --- Load user and servers ---
    async with _get_ws_session() as session:
        user = await session.get(User, user_id)
        if not user:
            await websocket.close(code=4001, reason="User not found")
            return

        result = await session.execute(select(Server).where(Server.user_id == user.id))
        servers = result.scalars().all()

    # --- Connect to manager ---
    await manager.connect(user.id, websocket)

    # --- Subscribe to Redis channels ---
    pubsub = redis_client.pubsub()
    channels = [f"metrics:{s.id}" for s in servers] + [f"status:{s.id}" for s in servers]
    if channels:
        await pubsub.subscribe(*channels)

    # --- Send initial status for each server ---
    now = datetime.now(UTC)
    threshold = timedelta(minutes=2)
    for server in servers:
        is_online = server.last_seen_at is not None and (now - server.last_seen_at) < threshold
        status = "online" if is_online else "offline"
        await websocket.send_json(
            {
                "type": "status_change",
                "server_id": str(server.id),
                "status": status,
            }
        )

    # --- Redis listener task ---
    # Build a lookup of channel -> server_id for wrapping metric messages
    channel_server_map: dict[str, str] = {}
    for s in servers:
        channel_server_map[f"metrics:{s.id}"] = str(s.id)
        channel_server_map[f"status:{s.id}"] = str(s.id)

    async def _redis_listener() -> None:
        """Forward Redis pub/sub messages to the WebSocket client."""
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        channel = message["channel"]
                        # Wrap metric messages with type field
                        if channel in channel_server_map:
                            server_id = channel_server_map[channel]
                            if channel.startswith("metrics:"):
                                await websocket.send_json(
                                    {
                                        "type": "metric",
                                        "server_id": server_id,
                                        "data": data,
                                    }
                                )
                            else:
                                # status_change messages already have type field
                                await websocket.send_json(data)
                    except Exception:
                        pass
        except Exception:
            pass

    listener_task = asyncio.create_task(_redis_listener())

    try:
        while True:
            # Keep connection alive; handle any client messages (e.g. ping)
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        listener_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await listener_task
        if channels:
            await pubsub.unsubscribe(*channels)
            await pubsub.aclose()
        manager.disconnect(user.id, websocket)
