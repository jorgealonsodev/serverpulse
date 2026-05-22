from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MetricIngest(BaseModel):
    cpu_percent: float = Field(ge=0, le=100)
    ram_percent: float = Field(ge=0, le=100)
    ram_used_mb: int = Field(ge=0)
    ram_total_mb: int = Field(ge=0)
    disk_percent: float = Field(ge=0, le=100)
    disk_used_gb: float = Field(ge=0)
    disk_total_gb: float = Field(ge=0)
    net_rx_bytes: int = Field(ge=0)
    net_tx_bytes: int = Field(ge=0)
    uptime_seconds: int = Field(ge=0)
    load_avg_1: float | None = None
    load_avg_5: float | None = None
    load_avg_15: float | None = None
    recorded_at: datetime | None = None


class MetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    server_id: UUID
    cpu_percent: float
    ram_percent: float
    ram_used_mb: int
    ram_total_mb: int
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    net_rx_bytes: int
    net_tx_bytes: int
    uptime_seconds: int
    load_avg_1: float | None = None
    load_avg_5: float | None = None
    load_avg_15: float | None = None
    recorded_at: datetime
    received_at: datetime
