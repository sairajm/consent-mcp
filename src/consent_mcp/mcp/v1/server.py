"""Shared MCP Server logic for consent management."""

import logging
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool

from consent_mcp.config import settings
from consent_mcp.domain.auth import IAuthProvider
from consent_mcp.domain.services import ConsentService
from consent_mcp.domain.value_objects import ContactInfo, ContactType
from consent_mcp.mcp.v1.requests import (
    AdminSimulateV1Request,
    CheckConsentEmailV1Request,
    CheckConsentSmsV1Request,
    RequestConsentEmailV1Request,
    RequestConsentSmsV1Request,
)
from consent_mcp.mcp.v1.responses import (
    AdminSimulateV1Response,
    ConsentCheckV1Response,
    ConsentRequestV1Response,
    MessageDeliveryV1Response,
)
from consent_mcp.utils.schema_utils import pydantic_to_input_schema

logger = logging.getLogger(__name__)


class ConsentMcpServer:
    """MCP Server for consent management."""

    def __init__(
        self,
        consent_service: ConsentService,
        auth_provider: IAuthProvider,
    ):
        """
        Initialize the MCP server.

        Args:
            consent_service: Domain service for consent operations.
            auth_provider: Authentication provider.
        """
        self.service = consent_service
        self.auth = auth_provider
        self.server = Server("consent-mcp")
        self._auth_header = ""  # Will be set by transport layer
        self._setup_tools()

    def _setup_tools(self) -> None:
        """Register MCP tools."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            tools = [
                Tool(
                    name="request_consent_sms",
                    description=(
                        "Request consent from a target via SMS. "
                        "Sends an SMS to the target phone number asking for permission."
                    ),
                    inputSchema=pydantic_to_input_schema(RequestConsentSmsV1Request),
                ),
                Tool(
                    name="request_consent_email",
                    description=(
                        "Request consent from a target via email. "
                        "Sends an email to the target asking for permission."
                    ),
                    inputSchema=pydantic_to_input_schema(RequestConsentEmailV1Request),
                ),
                Tool(
                    name="check_consent_sms",
                    description=(
                        "BLOCKING: Check if requester has active consent to contact target via SMS. "
                        "Returns true ONLY if consent is GRANTED and not expired."
                    ),
                    inputSchema=pydantic_to_input_schema(CheckConsentSmsV1Request),
                ),
                Tool(
                    name="check_consent_email",
                    description=(
                        "BLOCKING: Check if requester has active consent to contact target via email. "
                        "Returns true ONLY if consent is GRANTED and not expired."
                    ),
                    inputSchema=pydantic_to_input_schema(CheckConsentEmailV1Request),
                ),
            ]

            # Add admin tools only in test environment
            if settings.is_test_env:
                tools.append(
                    Tool(
                        name="admin_simulate_response",
                        description=(
                            "[TEST ONLY] Simulate a consent response without real SMS/email. "
                            "Use for testing workflows."
                        ),
                        inputSchema=pydantic_to_input_schema(AdminSimulateV1Request),
                    )
                )

            return tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Handle tool calls."""
            try:
                ctx = self.server.request_context

                headers = ctx.request.headers    
                
                credentials = self.auth.extract_credentials(headers)
                auth_context = await self.auth.authenticate(credentials)
                
                if not auth_context:
                    return [TextContent(type="text", text="Error: Unauthorized - Invalid or missing API key")]

                if name == "request_consent_sms":
                    result = await self._request_consent_sms(arguments)
                elif name == "request_consent_email":
                    result = await self._request_consent_email(arguments)
                elif name == "check_consent_sms":
                    result = await self._check_consent_sms(arguments)
                elif name == "check_consent_email":
                    result = await self._check_consent_email(arguments)
                elif name == "admin_simulate_response":
                    result = await self._admin_simulate_response(arguments)
                else:
                    result = {"error": f"Unknown tool: {name}"}

                return [TextContent(type="text", text=str(result))]
            except Exception as e:
                logger.exception(f"Error in tool {name}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _request_consent_sms(self, args: dict) -> dict:
        """Handle request_consent_sms tool."""
        req = RequestConsentSmsV1Request(**args)

        requester = ContactInfo(
            contact_type=ContactType.PHONE,
            contact_value=req.requester_phone,
            name=req.requester_name,
        )
        target = ContactInfo(
            contact_type=ContactType.PHONE,
            contact_value=req.target_phone,
            name=req.target_name,
        )

        result = await self.service.request_consent(
            requester=requester,
            target=target,
            scope=req.scope,
            expires_in_days=req.expires_in_days,
        )

        delivery = None
        if "delivery" in result:
            delivery = MessageDeliveryV1Response(**result["delivery"])

        response = ConsentRequestV1Response(
            request_id=result["request_id"],
            status=result["status"],
            message=result["message"],
            expires_at=result["expires_at"],
            delivery=delivery,
        )
        return response.model_dump(mode="json")

    async def _request_consent_email(self, args: dict) -> dict:
        """Handle request_consent_email tool."""
        req = RequestConsentEmailV1Request(**args)

        requester = ContactInfo(
            contact_type=ContactType.EMAIL,
            contact_value=req.requester_email,
            name=req.requester_name,
        )
        target = ContactInfo(
            contact_type=ContactType.EMAIL,
            contact_value=req.target_email,
            name=req.target_name,
        )

        result = await self.service.request_consent(
            requester=requester,
            target=target,
            scope=req.scope,
            expires_in_days=req.expires_in_days,
        )

        delivery = None
        if "delivery" in result:
            delivery = MessageDeliveryV1Response(**result["delivery"])

        response = ConsentRequestV1Response(
            request_id=result["request_id"],
            status=result["status"],
            message=result["message"],
            expires_at=result["expires_at"],
            delivery=delivery,
        )
        return response.model_dump(mode="json")

    async def _check_consent_sms(self, args: dict) -> dict:
        """Handle check_consent_sms tool."""
        req = CheckConsentSmsV1Request(**args)

        requester = ContactInfo(
            contact_type=ContactType.PHONE,
            contact_value=req.requester_phone,
        )
        target = ContactInfo(
            contact_type=ContactType.PHONE,
            contact_value=req.target_phone,
        )

        has_consent = await self.service.check_consent(requester, target)

        response = ConsentCheckV1Response(has_consent=has_consent)
        return response.model_dump(mode="json")

    async def _check_consent_email(self, args: dict) -> dict:
        """Handle check_consent_email tool."""
        req = CheckConsentEmailV1Request(**args)

        requester = ContactInfo(
            contact_type=ContactType.EMAIL,
            contact_value=req.requester_email,
        )
        target = ContactInfo(
            contact_type=ContactType.EMAIL,
            contact_value=req.target_email,
        )

        has_consent = await self.service.check_consent(requester, target)

        response = ConsentCheckV1Response(has_consent=has_consent)
        return response.model_dump(mode="json")

    async def _admin_simulate_response(self, args: dict) -> dict:
        """Handle admin_simulate_response tool."""
        if not settings.is_test_env:
            raise PermissionError("Admin tools only available in TEST environment")

        req = AdminSimulateV1Request(**args)

        target = ContactInfo(
            contact_type=ContactType(req.target_contact_type),
            contact_value=req.target_contact_value,
        )

        result = await self.service.simulate_response(
            target=target,
            requester_contact_value=req.requester_contact_value,
            response=req.response,
        )

        response = AdminSimulateV1Response(**result)
        return response.model_dump(mode="json")
