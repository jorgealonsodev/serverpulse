import asyncio
import contextlib
import json
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select

from app.database import async_session
from app.models.server import Server
from app.redis_client import redis_client

OFFLINE_THRESHOLD = timedelta(minutes=2)
CHECK_INTERVAL = 30


class OfflineDetector:
    """Polls the database for servers that haven't reported metrics recently.

    Publishes status_change events to Redis only on state transitions
    (online -> offline or offline -> online) to avoid duplicate alerts.
    """

    def __init__(self) -> None:
        self.alerted: set[UUID] = set()

    async def check_and_alert(self) -> None:
        """Check all servers and publish status changes for transitions."""
        async with async_session() as session:
            result = await session.execute(select(Server))
            servers = result.scalars().all()

            now = datetime.now(UTC)

            for server in servers:
                is_offline = (
                    server.last_seen_at is None or (now - server.last_seen_at) > OFFLINE_THRESHOLD
                )

                if is_offline and server.id not in self.alerted:
                    # Newly offline — alert
                    self.alerted.add(server.id)
                    await redis_client.publish(
                        f"status:{server.id}",
                        json.dumps(
                            {
                                "type": "status_change",
                                "server_id": str(server.id),
                                "status": "offline",
                            }
                        ),
                    )
                elif not is_offline and server.id in self.alerted:
                    # Back online — reset
                    self.alerted.discard(server.id)
                    await redis_client.publish(
                        f"status:{server.id}",
                        json.dumps(
                            {
                                "type": "status_change",
                                "server_id": str(server.id),
                                "status": "online",
                            }
                        ),
                    )


async def run_offline_detector() -> None:
    """Background task that runs the offline detector every CHECK_INTERVAL seconds."""
    detector = OfflineDetector()
    while True:
        await asyncio.sleep(CHECK_INTERVAL)
        with contextlib.suppress(Exception):
            await detector.check_and_alert()


detector = OfflineDetector()
