"""V1 Request schemas for MCP tools."""

import re
from typing import Annotated, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# E.164 phone pattern
E164_PATTERN = re.compile(r"^\+[1-9]\d{1,14}$")


class RequestConsentSmsV1Request(BaseModel):
    """V1: Request consent via SMS."""

    requester_phone: Annotated[
        str,
        Field(description="Requester's phone in E.164 format (e.g., +15551234567)"),
    ]
    requester_name: Annotated[
        str,
        Field(description="Display name of the requester"),
    ]
    target_phone: Annotated[
        str,
        Field(description="Target's phone in E.164 format"),
    ]
    target_name: Annotated[
        Optional[str],
        Field(default=None, description="Display name of the target (optional)"),
    ]
    scope: Annotated[
        str,
        Field(description="What the consent is for (e.g., 'wellness_check')"),
    ]
    expires_in_days: Annotated[
        int,
        Field(description="Days until consent expires"),
    ]

    @field_validator("requester_phone", "target_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate phone number is in E.164 format."""
        if not E164_PATTERN.match(v):
            raise ValueError(
                f"Phone number must be in E.164 format (e.g., +15551234567), got: {v}"
            )
        return v

    @field_validator("expires_in_days")
    @classmethod
    def validate_expiry(cls, v: int) -> int:
        """Validate expiry is positive."""
        if v <= 0:
            raise ValueError("expires_in_days must be positive")
        if v > 3650:  # 10 years max
            raise ValueError("expires_in_days cannot exceed 3650 (10 years)")
        return v


class RequestConsentEmailV1Request(BaseModel):
    """V1: Request consent via email."""

    requester_email: Annotated[
        EmailStr,
        Field(description="Requester's email address"),
    ]
    requester_name: Annotated[
        str,
        Field(description="Display name of the requester"),
    ]
    target_email: Annotated[
        EmailStr,
        Field(description="Target's email address"),
    ]
    target_name: Annotated[
        Optional[str],
        Field(default=None, description="Display name of the target (optional)"),
    ]
    scope: Annotated[
        str,
        Field(description="What the consent is for"),
    ]
    expires_in_days: Annotated[
        int,
        Field(description="Days until consent expires"),
    ]

    @field_validator("expires_in_days")
    @classmethod
    def validate_expiry(cls, v: int) -> int:
        """Validate expiry is positive."""
        if v <= 0:
            raise ValueError("expires_in_days must be positive")
        if v > 3650:
            raise ValueError("expires_in_days cannot exceed 3650 (10 years)")
        return v


class CheckConsentSmsV1Request(BaseModel):
    """V1: Check SMS consent status."""

    requester_phone: Annotated[
        str,
        Field(description="Requester's phone in E.164 format"),
    ]
    target_phone: Annotated[
        str,
        Field(description="Target's phone in E.164 format"),
    ]

    @field_validator("requester_phone", "target_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate phone number is in E.164 format."""
        if not E164_PATTERN.match(v):
            raise ValueError(
                f"Phone number must be in E.164 format (e.g., +15551234567), got: {v}"
            )
        return v


class CheckConsentEmailV1Request(BaseModel):
    """V1: Check email consent status."""

    requester_email: Annotated[
        EmailStr,
        Field(description="Requester's email address"),
    ]
    target_email: Annotated[
        EmailStr,
        Field(description="Target's email address"),
    ]


class AdminSimulateV1Request(BaseModel):
    """V1: Simulate consent response (TEST environment only)."""

    target_contact_type: Annotated[
        str,
        Field(description="Type of target contact"),
    ]
    target_contact_value: Annotated[
        str,
        Field(description="Target's phone or email"),
    ]
    requester_contact_value: Annotated[
        str,
        Field(description="Requester's phone or email"),
    ]
    response: Annotated[
        str,
        Field(description="Simulated response"),
    ]

    @field_validator("target_contact_type")
    @classmethod
    def validate_contact_type(cls, v: str) -> str:
        """Validate contact type."""
        if v not in ("phone", "email"):
            raise ValueError("target_contact_type must be 'phone' or 'email'")
        return v

    @field_validator("response")
    @classmethod
    def validate_response(cls, v: str) -> str:
        """Validate response value."""
        v_upper = v.upper()
        if v_upper not in ("YES", "NO", "REVOKE"):
            raise ValueError("response must be 'YES', 'NO', or 'REVOKE'")
        return v_upper
