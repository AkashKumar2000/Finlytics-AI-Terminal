import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class UserRole(str , enum.Enum):
    ADMIN= "admin"
    ANALYST= "analyst"


class User(Base):

    __tablename__= "users"

    id : Mapped[str] = mapped_column(
        String(36), 
        primary_key=True,
        default= lambda: str(uuid.uuid4())
    )

    email : Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )

    full_name : Mapped[str] = mapped_column(
        String(255) , nullable=False
    )

    hashed_password : Mapped[str] = mapped_column(
        String(255) , nullable=False
    )

    role : Mapped[UserRole] = mapped_column(
        Enum(UserRole) , default= UserRole.ANALYST , nullable=False
    )

    # Multi-tenant: every user belongs to an organization

    org_id : Mapped[str] = mapped_column(
        String(36) , ForeignKey("organizations.id") , nullable=False, index= True
    )

    is_active = Mapped[bool]= mapped_column(default=True)

    created_at : Mapped[datetime] = mapped_column(
        DateTime(timezone=True) , default= lambda: datetime.now(timezone.utc)
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    organization = relationship("Organization", back_populates="members")
    research_reports = relationship("ResearchReport", back_populates="created_by_user", lazy="selectin")




