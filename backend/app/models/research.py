import uuid
from datetime import datetime , timezone
from sqlalchemy import String , DateTime , ForeignKey , Text , JSON
from sqlalchemy.orm import Mapped , mapped_column , relationship
from app.database import Base


class ResearchReport(Base):
    """Stores completed AI research queries and their structured results."""

    __tablename__= "research_reports"

    id : Mapped[str] = mapped_column(
         String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    title : Mapped[str] = mapped_column(
        String(500), nullable=False
    )

    query : Mapped[str] = mapped_column(Text , nullable=False)

    # Structured AI result stored as JSON — frontend parses this to render
    # cards, tables, charts, sentiment badges, etc.
    result_data: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Raw LLM response for debugging / audit
    raw_response: Mapped[str | None] = mapped_column(Text, nullable=True)

     # Sources used in this research (list of {source, url, type})
    sources: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Tags for organizing: ["Q3 Earnings", "Competitor Analysis"]
    tags: Mapped[list | None] = mapped_column(JSON, default=list)

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20), default="completed"  # pending, processing, completed, failed
    )

    # Multi-tenant scoping
    org_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    created_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
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
    organization = relationship("Organization", back_populates="research_reports")
    created_by_user = relationship("User", back_populates="research_reports")

    

class WatchlistItem(Base):
    """Companies a user/org is tracking for quick access . """

    __tablename__ = "watchlist_items"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Multi-tenant scoping
    org_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    added_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    organization = relationship("Organization", back_populates="watchlist_items")

class AuditLog(Base):
    """Tracks all significant actions for compliance and debugging."""
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "research.created"
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "research_report"
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Who & where
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    org_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
