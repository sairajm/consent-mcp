"""V1 Response schemas for MCP tools."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MessageDeliveryV1Response(BaseModel):
    """V1: Message delivery details."""

    success: bool
    provider: str
    message_id: Optional[str] = None


class ConsentRequestV1Response(BaseModel):
    """V1: Response after requesting consent."""

    request_id: str
    status: str  # 'pending', 'already_granted'
    message: str
    expires_at: datetime
    delivery: Optional[MessageDeliveryV1Response] = None


class ConsentCheckV1Response(BaseModel):
    """V1: Consent check result."""

    has_consent: bool
    status: Optional[str] = None
    expires_at: Optional[datetime] = None


class AdminSimulateV1Response(BaseModel):
    """V1: Admin simulation result."""

    success: bool
    new_status: Optional[str] = None
    message: str


class ConsentRequestSummaryV1Response(BaseModel):
    """V1: Summary of a consent request."""

    id: str
    requester: dict
    target: dict
    scope: str
    status: str
    expires_at: str
    created_at: str


class ListRequestsV1Response(BaseModel):
    """V1: List of consent requests."""

    requests: list[ConsentRequestSummaryV1Response]
    total: int
