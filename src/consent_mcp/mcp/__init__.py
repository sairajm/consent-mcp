"""MCP layer for Consent MCP."""

from consent_mcp.mcp.v1 import (
    ConsentMcpServer,
    create_mcp_server,
)

__all__ = [
    "create_mcp_server",
    "ConsentMcpServer",
]
