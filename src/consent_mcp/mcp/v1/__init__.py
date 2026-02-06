"""MCP v1 API."""

from consent_mcp.mcp.v1.server import ConsentMcpServer, create_mcp_server, main

__all__ = [
    "ConsentMcpServer",
    "create_mcp_server",
    "main",
]
