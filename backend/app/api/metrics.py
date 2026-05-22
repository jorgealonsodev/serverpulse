from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status

from app.api.deps import get_server_from_agent_token
from app.database import get_db
from app.models.metric import Metric
from app.models.server import Server
from app.schemas.metric import MetricIngest, MetricResponse

router = APIRouter()


@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_metrics(
    data: MetricIngest,
    server: Server = Depends(get_server_from_agent_token),
    db=Depends(get_db),
) -> None:
    now = datetime.now(UTC)
    metric = Metric(
        server_id=server.id,
        cpu_percent=data.cpu_percent,
        ram_percent=data.ram_percent,
        ram_used_mb=data.ram_used_mb,
        ram_total_mb=data.ram_total_mb,
        disk_percent=data.disk_percent,
        disk_used_gb=data.disk_used_gb,
        disk_total_gb=data.disk_total_gb,
        net_rx_bytes=data.net_rx_bytes,
        net_tx_bytes=data.net_tx_bytes,
        uptime_seconds=data.uptime_seconds,
        load_avg_1=data.load_avg_1,
        load_avg_5=data.load_avg_5,
        load_avg_15=data.load_avg_15,
        recorded_at=data.recorded_at or now,
        received_at=now,
    )
    db.add(metric)

    # Update last_seen_at
    server.last_seen_at = now

    await db.commit()

    # Publish to Redis (fire-and-forget)
    try:
        import json

        from app import redis_client

        metric_data = MetricResponse.model_validate(metric).model_dump(mode="json")
        await redis_client.redis_client.publish(
            f"metrics:{server.id}", json.dumps(metric_data, default=str)
        )
    except Exception:
        pass
