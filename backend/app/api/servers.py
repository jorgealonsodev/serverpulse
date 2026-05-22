from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.security import generate_agent_token, hash_agent_token
from app.database import get_db
from app.models.metric import Metric
from app.models.server import Server
from app.models.user import User
from app.schemas.metric import MetricResponse
from app.schemas.server import ServerCreate, ServerDetail, ServerResponse, ServerWithToken

router = APIRouter()

_STATUS_WINDOW = timedelta(minutes=2)


def _compute_status(last_seen_at: datetime | None) -> str:
    if last_seen_at and (datetime.now(UTC) - last_seen_at) < _STATUS_WINDOW:
        return "online"
    return "offline"


def _to_response(server: Server) -> dict:
    return {
        "id": server.id,
        "name": server.name,
        "hostname": server.hostname,
        "last_seen_at": server.last_seen_at,
        "status": _compute_status(server.last_seen_at),
        "created_at": server.created_at,
    }


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ServerWithToken)
async def create_server(
    data: ServerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    plain_token = generate_agent_token()
    token_hash = hash_agent_token(plain_token)

    server = Server(
        user_id=current_user.id,
        name=data.name,
        hostname=data.hostname,
        api_token_hash=token_hash,
    )
    db.add(server)
    await db.commit()
    await db.refresh(server)

    result = _to_response(server)
    result["api_token"] = plain_token
    return result


@router.get("/", response_model=list[ServerResponse])
async def list_servers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    result = await db.execute(
        select(Server).where(Server.user_id == current_user.id).order_by(Server.created_at)
    )
    servers = result.scalars().all()
    return [_to_response(s) for s in servers]


@router.get(
    "/{server_id}/metrics",
    response_model=list[MetricResponse],
)
async def query_server_metrics(
    server_id: UUID,
    from_date: datetime = Query(alias="from"),
    to_date: datetime = Query(alias="to"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Metric]:
    # Validate server belongs to user
    result = await db.execute(
        select(Server).where(Server.id == server_id, Server.user_id == current_user.id)
    )
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    # Validate range
    if to_date - from_date > timedelta(hours=24):
        raise HTTPException(status_code=400, detail="Time range exceeds 24 hours")

    # Query metrics
    result = await db.execute(
        select(Metric)
        .where(
            Metric.server_id == server_id,
            Metric.recorded_at >= from_date,
            Metric.recorded_at <= to_date,
        )
        .order_by(Metric.recorded_at)
        .limit(2880)
    )
    return list(result.scalars().all())


@router.get("/{server_id}", response_model=ServerDetail)
async def get_server_detail(
    server_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    result = await db.execute(
        select(Server).where(Server.id == server_id, Server.user_id == current_user.id)
    )
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return _to_response(server)


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(
    server_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    result = await db.execute(
        select(Server).where(Server.id == server_id, Server.user_id == current_user.id)
    )
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    await db.delete(server)
    await db.commit()


@router.post("/{server_id}/regenerate-token", response_model=ServerWithToken)
async def regenerate_token(
    server_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    result = await db.execute(
        select(Server).where(Server.id == server_id, Server.user_id == current_user.id)
    )
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    plain_token = generate_agent_token()
    server.api_token_hash = hash_agent_token(plain_token)
    await db.commit()
    await db.refresh(server)

    resp = _to_response(server)
    resp["api_token"] = plain_token
    return resp
