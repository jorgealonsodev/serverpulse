from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ServerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    hostname: str | None = None


class ServerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    hostname: str | None
    last_seen_at: datetime | None
    status: str
    created_at: datetime


class ServerWithToken(ServerResponse):
    api_token: str


class ServerDetail(ServerResponse):
    pass
