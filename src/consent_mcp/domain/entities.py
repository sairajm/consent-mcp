"""Domain entities for consent management."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from consent_mcp.domain.value_objects import ConsentStatus, ContactInfo


class ConsentRequest(BaseModel):
    """
    Core domain entity representing a consent request.

    A consent request tracks the permission granted (or pending) from a target
    to a requester for a specific scope of interaction.
    """

    id: UUID = Field(default_factory=uuid4)

    # Who is requesting consent
    requester: ContactInfo

    # Who is being asked for consent
    target: ContactInfo

    # What the consent is for (free-form description)
    scope: str

    # Current status of the request
    status: ConsentStatus = ConsentStatus.PENDING

    # When the consent expires
    expires_at: datetime

    # Audit timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    responded_at: datetime | None = None

    def is_active(self) -> bool:
        """Check if consent is currently active (granted and not expired)."""
        if self.status != ConsentStatus.GRANTED:
            return False
        return datetime.now(timezone.utc) < self.expires_at

    def is_expired(self) -> bool:
        """Check if consent has expired."""
        return datetime.now(timezone.utc) >= self.expires_at

    def grant(self) -> "ConsentRequest":
        """Grant the consent request."""
        now = datetime.now(timezone.utc)
        return self.model_copy(
            update={
                "status": ConsentStatus.GRANTED,
                "updated_at": now,
                "responded_at": now,
            }
        )

    def revoke(self) -> "ConsentRequest":
        """Revoke the consent request."""
        now = datetime.now(timezone.utc)
        return self.model_copy(
            update={
                "status": ConsentStatus.REVOKED,
                "updated_at": now,
                "responded_at": now,
            }
        )

    def expire(self) -> "ConsentRequest":
        """Mark the consent request as expired."""
        return self.model_copy(
            update={
                "status": ConsentStatus.EXPIRED,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    class Config:
        frozen = False  # Allow mutations via model_copy
