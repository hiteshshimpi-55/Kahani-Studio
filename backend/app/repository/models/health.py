from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.repository.models.base.base import Base
from app.repository.models.base.mixins import TimestampMixin


class HealthPing(TimestampMixin, Base):
    """Minimal table so compose can verify Postgres wiring."""

    __tablename__ = "health_pings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(64), default="api")
