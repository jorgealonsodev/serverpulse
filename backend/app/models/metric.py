from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    text,
)
from sqlalchemy.dialects.postgresql import BIGINT, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Metric(Base):
    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(
        BIGINT,
        primary_key=True,
        autoincrement=True,
    )
    server_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("servers.id", ondelete="CASCADE"),
        nullable=False,
    )
    cpu_percent: Mapped[float] = mapped_column(Float, nullable=False)
    ram_percent: Mapped[float] = mapped_column(Float, nullable=False)
    ram_used_mb: Mapped[int] = mapped_column(Integer, nullable=False)
    ram_total_mb: Mapped[int] = mapped_column(Integer, nullable=False)
    disk_percent: Mapped[float] = mapped_column(Float, nullable=False)
    disk_used_gb: Mapped[float] = mapped_column(Float, nullable=False)
    disk_total_gb: Mapped[float] = mapped_column(Float, nullable=False)
    net_rx_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    net_tx_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    uptime_seconds: Mapped[int] = mapped_column(BigInteger, nullable=False)
    load_avg_1: Mapped[float | None] = mapped_column(Float, nullable=True)
    load_avg_5: Mapped[float | None] = mapped_column(Float, nullable=True)
    load_avg_15: Mapped[float | None] = mapped_column(Float, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )

    server = relationship("Server", back_populates="metrics")

    __table_args__ = (
        Index("ix_metrics_server_recorded", "server_id", text("recorded_at DESC")),
    )
