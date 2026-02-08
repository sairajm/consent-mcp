"""HTTP Server for MCP v1 using Streamable HTTP transport."""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount
from starlette.types import ASGIApp, Receive, Scope, Send
import uvicorn

from consent_mcp.config import settings
from consent_mcp.domain.services import ConsentService
from consent_mcp.infrastructure.auth import get_auth_provider
from consent_mcp.infrastructure.database import (
    PostgresConsentRepository,
    get_async_session,
)
from consent_mcp.infrastructure.providers import get_email_provider, get_sms_provider
from consent_mcp.mcp.v1.server import ConsentMcpServer

logger = logging.getLogger(__name__)


async def create_app() -> Starlette:
    """Create the Starlette application."""
    # These will be initialized in the lifespan context
    mcp_server = None
    session_manager = None
    db_session = None
    
    @asynccontextmanager
    async def lifespan(app: Starlette):
        """Manage the lifespan of the application and session manager."""
        nonlocal mcp_server, session_manager, db_session
        
        # Startup: Create database session and MCP server
        logger.info("Starting application...")
        
        # Get auth provider
        auth_provider = get_auth_provider()

        # Get message providers
        sms_provider = get_sms_provider()
        email_provider = get_email_provider()

        # Create database session that will live for the entire application
        session_context = get_async_session()
        db_session = await session_context.__aenter__()
        
        try:
            # Create repository with the long-lived session
            repository = PostgresConsentRepository(db_session)

            consent_service = ConsentService(
                repository=repository,
                sms_provider=sms_provider,
                email_provider=email_provider,
            )

            mcp_server = ConsentMcpServer(
                consent_service=consent_service,
                auth_provider=auth_provider,
            )
            
            # Store auth header for authentication
            mcp_server._auth_header = ""
            
            # Create session manager with the MCP server
            session_manager = StreamableHTTPSessionManager(app=mcp_server.server)
            
            # Initialize the session manager's task group using run()
            async with session_manager.run():
                logger.info("Session manager initialized")
                yield
                
        finally:
            # Shutdown: Clean up database session
            logger.info("Shutting down application...")
            if db_session is not None:
                await session_context.__aexit__(None, None, None)
            logger.info("Application shut down")
    
    # Create ASGI handler for the session manager
    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        """ASGI handler for Streamable HTTP requests."""
        if session_manager is None:
            raise RuntimeError("Session manager not initialized")
        await session_manager.handle_request(scope, receive, send)
    
    app = Starlette(
        debug=not settings.is_production,
        routes=[
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    # Add CORS middleware for local development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if not settings.is_production else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


async def run_server() -> None:
    """Run the HTTP server."""
    app = await create_app()
    
    port = settings.web_server_port
    logger.info(f"Starting MCP HTTP server on http://localhost:{port}/mcp")
    
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


def main() -> None:
    """Entry point for the HTTP server."""
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)

    # Suppress SQL logs
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.WARNING)

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
