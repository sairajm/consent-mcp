"""FastAPI web application for consent endpoints.

This module provides the main FastAPI application that mounts
versioned routes for consent management.
"""

from fastapi import FastAPI

from consent_mcp.domain.services import ConsentService
from consent_mcp.web.routes.v1.consent import create_consent_router


class ConsentWebApp:
    """Web application for consent management."""

    def __init__(self, service: ConsentService):
        """Initialize the consent web app.

        Args:
            service: Consent service for business logic.
        """
        self.service = service
        self.app = self._create_app()

    def _create_app(self) -> FastAPI:
        """Create and configure the FastAPI application."""
        app = FastAPI(
            title="Consent Gateway",
            description="Web endpoints for consent management",
            version="1.0.0",
        )

        # Mount v1 consent routes
        consent_router = create_consent_router(self.service)
        app.include_router(consent_router)

        @app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy"}

        return app


def create_app(service: ConsentService) -> FastAPI:
    """Create a consent web app instance.

    Args:
        service: Consent service for business logic.

    Returns:
        Configured FastAPI application.
    """
    consent_app = ConsentWebApp(service)
    return consent_app.app
