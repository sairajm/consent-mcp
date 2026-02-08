import asyncio
import logging
import sys
from subprocess import run

from sqlalchemy import inspect

from consent_mcp.config import settings
from consent_mcp.infrastructure.database.connection import get_async_engine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_database() -> bool:
    """Check database state and return if stamping is needed."""
    logger.info("Checking database state...")
    
    # Get engine
    engine = get_async_engine()
    
    try:
        async with engine.connect() as conn:
            # Check if tables exist
            tables = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )
            
            # Check for main table and alembic table
            has_consent = "consent_requests" in tables
            has_alembic = "alembic_version" in tables
            
            logger.info(f"Database state: consent_requests={has_consent}, alembic_version={has_alembic}")
            
            if has_consent and not has_alembic:
                return True
            return False
            
    except Exception as e:
        logger.error(f"Error checking database: {e}")
        # If DB connection fails, maybe let startup retry or fail
        sys.exit(1)
    finally:
        await engine.dispose()


def run_migrations(stamp_head: bool = False):
    """Run alembic migrations."""
    try:
        if stamp_head:
            logger.info("Existing schema detected. Stamping 'head'...")
            run(["alembic", "stamp", "head"], check=True)
            
        logger.info("Running database migrations...")
        run(["alembic", "upgrade", "head"], check=True)
        
        logger.info("Database initialization complete.")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Check state
    should_stamp = asyncio.run(check_database())
    
    # Run migrations (modifies DB)
    run_migrations(should_stamp)
