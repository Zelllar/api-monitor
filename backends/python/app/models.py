from sqlalchemy import BigInteger, String, Text, Integer, Boolean, DateTime, CheckConstraint, Identity, true, ForeignKey, Index, desc
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from datetime import datetime

from app.database import Base


class Monitor(Base):
    __tablename__ = "monitors"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("interval_seconds > 0", name="check_interval"),
    )   

class CheckResult(Base):
    __tablename__ = "check_results"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    monitor_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("monitors.id", ondelete="CASCADE"),
        nullable=False
    )
    status: Mapped[str] = mapped_column(String(10), nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("status IN ('UP', 'DOWN')", name="check_status"),
        CheckConstraint(
            "response_time_ms IS NULL OR response_time_ms >= 0",
            name="check_response_time"
        ),
        
    Index (
        "idx_check_results_monitor_checked",
        "monitor_id",
        desc("checked_at")
    )
)