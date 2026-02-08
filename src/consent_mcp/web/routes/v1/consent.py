"""V1 consent routes.

These routes handle the two-step consent flow:
1. GET /v1/consent/{token} - Display consent request details
2. POST /v1/consent/{token}/grant - Grant consent
3. POST /v1/consent/{token}/deny - Deny consent
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from consent_mcp.domain.services import ConsentService
from consent_mcp.domain.value_objects import ConsentStatus
from consent_mcp.web.templates.consent import (
    render_already_responded,
    render_consent_page,
    render_thank_you,
)


def create_consent_router(service: ConsentService) -> APIRouter:
    """Create a consent router with the given service.

    Args:
        service: Consent service for business logic.

    Returns:
        Configured APIRouter with consent endpoints.
    """
    router = APIRouter(prefix="/v1/consent", tags=["consent"])

    @router.get("/{token}", response_class=HTMLResponse)
    async def show_consent_page(token: str):
        """Display the consent confirmation page."""
        try:
            request_id = UUID(token)
        except ValueError as e:
            raise HTTPException(status_code=400, detail="Invalid consent token") from e

        consent_request = await service.get_request_by_id(request_id)
        if not consent_request:
            raise HTTPException(status_code=404, detail="Consent request not found")

        if consent_request.status != ConsentStatus.PENDING:
            return render_already_responded(consent_request.status)

        return render_consent_page(
            token=token,
            requester_name=consent_request.requester.name or "Someone",
            scope=consent_request.scope,
            target_name=consent_request.target.name,
        )

    @router.post("/{token}/grant", response_class=HTMLResponse)
    async def grant_consent(token: str):
        """Grant consent for the request."""
        try:
            request_id = UUID(token)
        except ValueError as e:
            raise HTTPException(status_code=400, detail="Invalid consent token") from e

        # Use service to grant consent
        result = await service.grant_consent(request_id)

        if not result.success:
            if result.new_status is None:
                raise HTTPException(status_code=404, detail="Consent request not found")
            # Already responded
            return render_already_responded(result.new_status)

        return render_thank_you(granted=True)

    @router.post("/{token}/deny", response_class=HTMLResponse)
    async def deny_consent(token: str):
        """Deny consent for the request."""
        try:
            request_id = UUID(token)
        except ValueError as e:
            raise HTTPException(status_code=400, detail="Invalid consent token") from e

        # Use service to deny consent
        result = await service.deny_consent(request_id)

        if not result.success:
            if result.new_status is None:
                raise HTTPException(status_code=404, detail="Consent request not found")
            # Already responded
            return render_already_responded(result.new_status)

        return render_thank_you(granted=False)

    return router
