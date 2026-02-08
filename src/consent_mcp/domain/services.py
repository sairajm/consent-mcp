"""Domain services for consent management."""

from datetime import datetime, timedelta

from consent_mcp.config import settings
from consent_mcp.domain.entities import ConsentRequest
from consent_mcp.domain.providers import (
    IMessageProvider,
    ProviderNotConfiguredError,
)
from consent_mcp.domain.repository import IConsentRepository
from consent_mcp.domain.value_objects import (
    ConsentActionResult,
    ConsentStatus,
    ContactInfo,
    ContactType,
)


class ConsentService:
    """
    Core domain service for consent management.

    This service orchestrates the consent workflow:
    1. Request consent from a target
    2. Check if consent exists
    3. Grant or revoke consent

    All business logic lives here, independent of infrastructure.
    """

    def __init__(
        self,
        repository: IConsentRepository,
        sms_provider: IMessageProvider | None = None,
        email_provider: IMessageProvider | None = None,
    ):
        """
        Initialize the consent service.

        Args:
            repository: Data access for consent requests.
            sms_provider: Provider for sending SMS messages.
            email_provider: Provider for sending email messages.
        """
        self._repository = repository
        self._sms_provider = sms_provider
        self._email_provider = email_provider

    def _get_provider(self, contact_type: ContactType) -> IMessageProvider:
        """Get the appropriate provider for the contact type."""
        if contact_type == ContactType.PHONE:
            if not self._sms_provider:
                raise ProviderNotConfiguredError("SMS provider not configured")
            if not self._sms_provider.is_configured():
                raise ProviderNotConfiguredError("SMS provider not fully configured")
            return self._sms_provider
        elif contact_type == ContactType.EMAIL:
            if not self._email_provider:
                raise ProviderNotConfiguredError("Email provider not configured")
            if not self._email_provider.is_configured():
                raise ProviderNotConfiguredError("Email provider not fully configured")
            return self._email_provider
        else:
            raise ValueError(f"Unknown contact type: {contact_type}")

    def _generate_consent_url(self, request_id: str) -> str | None:
        """Generate a consent URL for the request if base URL is configured."""
        if not settings.consent_base_url:
            return None
        base = settings.consent_base_url.rstrip("/")
        return f"{base}/v1/consent/{request_id}"

    async def request_consent(
        self,
        requester: ContactInfo,
        target: ContactInfo,
        scope: str,
        expires_in_days: int,
    ) -> dict:
        """
        Request consent from a target on behalf of a requester.

        Args:
            requester: Contact info of who is requesting consent.
            target: Contact info of who is being asked.
            scope: What the consent is for.
            expires_in_days: How many days until consent expires.

        Returns:
            Dict with request_id, status, and message.
        """
        # Check for existing active consent
        existing = await self._repository.get_active_consent(
            requester=requester,
            target=target,
            scope=scope,
        )
        if existing:
            return {
                "request_id": str(existing.id),
                "status": "already_granted",
                "message": "Active consent already exists",
                "expires_at": existing.expires_at,
            }

        # Check for pending request
        pending = await self._repository.get_pending_request(
            requester=requester,
            target=target,
            scope=scope,
        )
        if pending:
            return {
                "request_id": str(pending.id),
                "status": "pending",
                "message": "Consent request already pending",
                "expires_at": pending.expires_at,
            }

        # Create new consent request
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        consent_request = ConsentRequest(
            requester=requester,
            target=target,
            scope=scope,
            expires_at=expires_at,
        )

        # Save to repository
        saved_request = await self._repository.create(consent_request)

        # Generate consent URL for click-to-consent
        consent_url = self._generate_consent_url(str(saved_request.id))

        # Send consent request message
        provider = self._get_provider(target.contact_type)
        delivery_result = await provider.send_consent_request(
            target_contact=target.contact_value,
            requester_name=requester.name or "Someone",
            target_name=target.name,
            scope=scope,
            consent_url=consent_url,
        )

        result = {
            "request_id": str(saved_request.id),
            "status": "pending",
            "message": f"Consent request sent via {provider.provider_name}",
            "expires_at": expires_at,
            "delivery": {
                "success": delivery_result.success,
                "provider": delivery_result.provider,
                "message_id": delivery_result.message_id,
            },
        }

        if consent_url:
            result["consent_url"] = consent_url

        return result

    async def check_consent(
        self,
        requester: ContactInfo,
        target: ContactInfo,
        scope: str | None = None,
    ) -> bool:
        """
        Check if requester has active consent to contact target.

        This is the BLOCKING check that AI agents must pass.
        Returns True ONLY if consent is GRANTED and not expired.

        Args:
            requester: Contact info of the requester.
            target: Contact info of the target.
            scope: Optional scope to check. If None, checks for any consent.

        Returns:
            True if active consent exists, False otherwise.
        """
        consent = await self._repository.get_active_consent(
            requester=requester,
            target=target,
            scope=scope,
        )
        return consent is not None and consent.is_active()

    async def simulate_response(
        self,
        target: ContactInfo,
        requester_contact_value: str,
        response: str,
    ) -> dict:
        """
        Simulate a consent response for testing.

        Args:
            target: Contact info of the target.
            requester_contact_value: The requester's contact value.
            response: "YES" to grant, "NO" or "REVOKE" to revoke.

        Returns:
            Dict with success status and new status.
        """
        # Find the pending request
        # We need to construct requester ContactInfo
        ContactInfo(
            contact_type=target.contact_type,  # Assume same type
            contact_value=requester_contact_value,
        )

        # Find requests from this requester to this target
        requests = await self._repository.find_by_target(target)

        # Filter to find matching requester
        matching = [
            r
            for r in requests
            if r.requester.contact_value == requester_contact_value
            and r.status == ConsentStatus.PENDING
        ]

        if not matching:
            return {
                "success": False,
                "new_status": None,
                "message": "No pending request found",
            }

        request = matching[0]
        response_upper = response.upper()

        if response_upper == "YES":
            await self._repository.update_status(
                request.id,
                ConsentStatus.GRANTED,
            )
            return {
                "success": True,
                "new_status": "granted",
                "message": "Consent granted",
            }
        elif response_upper in ("NO", "REVOKE"):
            await self._repository.update_status(
                request.id,
                ConsentStatus.REVOKED,
            )
            return {
                "success": True,
                "new_status": "revoked",
                "message": "Consent revoked",
            }
        else:
            return {
                "success": False,
                "new_status": None,
                "message": f"Invalid response: {response}. Use YES, NO, or REVOKE.",
            }

    async def list_requests(
        self,
        target: ContactInfo | None = None,
        requester: ContactInfo | None = None,
        status: ConsentStatus | None = None,
    ) -> list[dict]:
        """
        List consent requests with optional filters.

        Args:
            target: Filter by target.
            requester: Filter by requester.
            status: Filter by status.

        Returns:
            List of consent request summaries.
        """
        if target:
            requests = await self._repository.find_by_target(target, status)
        elif requester:
            requests = await self._repository.find_by_requester(requester, status)
        else:
            # Would need a find_all method for this case
            requests = []

        return [
            {
                "id": str(r.id),
                "requester": {
                    "type": r.requester.contact_type.value,
                    "value": r.requester.contact_value,
                    "name": r.requester.name,
                },
                "target": {
                    "type": r.target.contact_type.value,
                    "value": r.target.contact_value,
                    "name": r.target.name,
                },
                "scope": r.scope,
                "status": r.status.value,
                "expires_at": r.expires_at.isoformat(),
                "created_at": r.created_at.isoformat(),
            }
            for r in requests
        ]

    # -------------------------------------------------------------------------
    # Web consent flow methods
    # -------------------------------------------------------------------------

    async def get_request_by_id(self, request_id) -> ConsentRequest | None:
        """
        Get a consent request by its ID.

        Args:
            request_id: UUID of the consent request.

        Returns:
            ConsentRequest if found, None otherwise.
        """
        return await self._repository.get_by_id(request_id)

    async def grant_consent(self, request_id) -> "ConsentActionResult":
        """
        Grant consent for a pending request.

        Args:
            request_id: UUID of the consent request.

        Returns:
            ConsentActionResult with success status and new status.
        """
        consent_request = await self._repository.get_by_id(request_id)
        if not consent_request:
            return ConsentActionResult(
                success=False,
                new_status=None,
                message="Consent request not found",
            )

        if consent_request.status != ConsentStatus.PENDING:
            return ConsentActionResult(
                success=False,
                new_status=consent_request.status,
                message=f"Request already {consent_request.status.value}",
            )

        await self._repository.update_status(request_id, ConsentStatus.GRANTED)
        return ConsentActionResult(
            success=True,
            new_status=ConsentStatus.GRANTED,
            message="Consent granted",
        )

    async def deny_consent(self, request_id) -> "ConsentActionResult":
        """
        Deny consent for a pending request.

        Args:
            request_id: UUID of the consent request.

        Returns:
            ConsentActionResult with success status and new status.
        """
        consent_request = await self._repository.get_by_id(request_id)
        if not consent_request:
            return ConsentActionResult(
                success=False,
                new_status=None,
                message="Consent request not found",
            )

        if consent_request.status != ConsentStatus.PENDING:
            return ConsentActionResult(
                success=False,
                new_status=consent_request.status,
                message=f"Request already {consent_request.status.value}",
            )

        await self._repository.update_status(request_id, ConsentStatus.REVOKED)
        return ConsentActionResult(
            success=True,
            new_status=ConsentStatus.REVOKED,
            message="Consent denied",
        )
