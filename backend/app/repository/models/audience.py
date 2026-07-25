"""SQLAlchemy models for audience simulation (PRD §6.9)."""

from __future__ import annotations

import uuid
from enum import Enum as PyEnum

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.repository.models.base.base import Base
from app.repository.models.base.mixins import TimestampMixin


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class SimRunStatus(str, PyEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PatchStatus(str, PyEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class CalibrationStatus(str, PyEnum):
    UNCALIBRATED = "UNCALIBRATED"
    CALIBRATED = "CALIBRATED"


# ---------------------------------------------------------------------------
# SimRun  — one full audience simulation run for a series/episode
# ---------------------------------------------------------------------------


class SimRun(TimestampMixin, Base):
    """Records a single audience simulation job execution."""

    __tablename__ = "sim_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    episode_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    series_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    project_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    status: Mapped[SimRunStatus] = mapped_column(
        SAEnum(SimRunStatus, name="sim_run_status"),
        default=SimRunStatus.PENDING,
        nullable=False,
    )
    calibration_status: Mapped[CalibrationStatus] = mapped_column(
        SAEnum(CalibrationStatus, name="calibration_status"),
        default=CalibrationStatus.UNCALIBRATED,
        nullable=False,
    )

    # Full EngagementReport JSON blob (filled on COMPLETED)
    engagement_report: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Structural audit result JSON blob
    audit_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Error message if FAILED
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Number of synthetic personas instantiated
    persona_count: Mapped[int | None] = mapped_column(nullable=True)

    patches: Mapped[list[SimPatch]] = relationship(
        "SimPatch", back_populates="sim_run", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# SimPatch  — individual rewrite suggestion from a simulation run
# ---------------------------------------------------------------------------


class SimPatch(TimestampMixin, Base):
    """One structured edit proposal belonging to a SimRun."""

    __tablename__ = "sim_patches"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    sim_run_id: Mapped[str] = mapped_column(
        ForeignKey("sim_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Where in the script this patch applies
    beat_id: Mapped[str] = mapped_column(String(64), nullable=False)
    part: Mapped[int] = mapped_column(nullable=False)

    # Patch operation type (e.g. "shorten", "move_reveal", "raise_stakes")
    patch_type: Mapped[str] = mapped_column(String(64), nullable=False)

    # Human-readable rationale from the simulation
    rationale: Mapped[str] = mapped_column(Text, nullable=False)

    # Suggested diff / replacement text (nullable if structural-only)
    suggested_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Expected metric delta and confidence, stored as JSONB
    expected_delta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Human accept/reject decision
    status: Mapped[PatchStatus] = mapped_column(
        SAEnum(PatchStatus, name="patch_status"),
        default=PatchStatus.PENDING,
        nullable=False,
    )

    sim_run: Mapped[SimRun] = relationship("SimRun", back_populates="patches")
