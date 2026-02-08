"""Web module for consent endpoints."""

from consent_mcp.web.app import ConsentWebApp, create_app
from consent_mcp.web.routes.v1.consent import create_consent_router

__all__ = ["create_app", "ConsentWebApp", "create_consent_router"]
