#!/bin/bash
set -e

# Synopsis: Starts the Consent MCP server in local development mode.

echo -e "\033[0;36mStarting Consent MCP in LOCAL DEVELOPMENT mode...\033[0m"

# Set environment to development
export ENV="development"

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "\033[0;33m.env file not found. Creating from .env.example...\033[0m"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "\033[0;33mCreated .env file. Please check configuration.\033[0m"
    else
        echo -e "\033[0;33m.env.example not found. Using defaults.\033[0m"
    fi
fi

# 1. Start Postgres
echo -e "\n\033[0;32m[1/4] Starting PostgreSQL container...\033[0m"
docker compose -f docker-compose.dev.yml up -d postgres

# 2. Wait for DB
echo -e "\n\033[0;32m[2/4] Waiting for database to be ready...\033[0m"
MAX_RETRIES=30
RETRY_COUNT=0
DB_READY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    STATUS=$(docker inspect --format='{{.State.Health.Status}}' consent-mcp-postgres-dev 2>/dev/null || echo "not-found")
    if [ "$STATUS" == "healthy" ]; then
        DB_READY=true
        break
    else
        RETRY_COUNT=$((RETRY_COUNT+1))
        echo -ne "Waiting for DB... ($RETRY_COUNT/$MAX_RETRIES)\r"
        sleep 1
    fi
done

if [ "$DB_READY" = false ]; then
    echo -e "\n\033[0;31mDatabase failed to become healthy. Check docker logs consent-mcp-postgres-dev\033[0m"
    exit 1
fi
echo -e "\nDatabase is ready!"

# 3. Run Migrations
echo -e "\n\033[0;32m[3/4] Running Alembic migrations...\033[0m"
alembic upgrade head

# 4. Start Server
echo -e "\n\033[0;32m[4/4] Starting MCP Server...\033[0m"
echo -e "\033[0;37mPress Ctrl+C to stop.\033[0m"

export PYTHONPATH="src:$PYTHONPATH"
python -m consent_mcp.mcp.v1.server
