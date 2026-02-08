"""SQLAlchemy ORM models for consent management."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    DateTime,
    Enum,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class ConsentRequestModel(Base):
    """SQLAlchemy model for consent_requests table."""

    __tablename__ = "consent_requests"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Requester information
    requester_contact_type: Mapped[str] = mapped_column(
        Enum("phone", "email", name="contact_type_enum", create_constraint=True),
        nullable=False,
    )
    requester_contact_value: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    requester_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Target information
    target_contact_type: Mapped[str] = mapped_column(
        Enum("phone", "email", name="contact_type_enum", create_constraint=True),
        nullable=False,
    )
    target_contact_value: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    target_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Consent details
    scope: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "granted",
            "revoked",
            "expired",
            name="consent_status_enum",
            create_constraint=True,
        ),
        nullable=False,
        default="pending",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Indexes
    __table_args__ = (
        # Index for target lookups
        Index(
            "ix_consent_target_lookup",
            "target_contact_type",
            "target_contact_value",
        ),
        # Index for requester lookups
        Index(
            "ix_consent_requester_lookup",
            "requester_contact_type",
            "requester_contact_value",
        ),
        # Index for active consent queries
        Index(
            "ix_consent_status",
            "status",
            "expires_at",
        ),
        # Unique constraint: one active request per requester+target+scope
        UniqueConstraint(
            "requester_contact_type",
            "requester_contact_value",
            "target_contact_type",
            "target_contact_value",
            "scope",
            name="uq_consent_requester_target_scope",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ConsentRequest(id={self.id}, "
            f"requester={self.requester_contact_value}, "
            f"target={self.target_contact_value}, "
            f"status={self.status})>"
        )
