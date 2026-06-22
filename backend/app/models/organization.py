import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Organization(Base):

    __tablename__= "organizations"

    id : Mapped[str] = mapped_column(
        String(36), primary_key=True , default = lambda : str(uuid.uuid4())
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    invite_code: Mapped[str] = mapped_column(
        String(20), unique=True, default=lambda: uuid.uuid4().hex[:8]
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    members = relationship("User", back_populates="organization", lazy="selectin")
    research_reports = relationship("ResearchReport", back_populates="organization", lazy="selectin")
    watchlist_items = relationship("WatchlistItem", back_populates="organization", lazy="selectin")

