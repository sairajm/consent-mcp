<#
.SYNOPSIS
Starts the Consent MCP server in local development mode.

.DESCRIPTION
This script:
1. Starts a local PostgreSQL container using docker-compose.dev.yml.
2. Waits for the database to be ready.
3. Runs Alembic migrations to ensure the schema is up to date.
4. Starts the Python MCP server natively on the host.

.EXAMPLE
.\scripts\start_local.ps1
#>

$ErrorActionPreference = "Stop"

# Set environment to development
$env:ENV = "development"
Write-Host "Starting Consent MCP in LOCAL DEVELOPMENT mode..." -ForegroundColor Cyan

# Check for .env file
if (-not (Test-Path ".env")) {
    Write-Warning ".env file not found. Creating from .env.example..."
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Warning "Created .env file. Please check configuration."
    }
    else {
        Write-Warning ".env.example not found. Using defaults."
    }
}

# 1. Start Postgres
Write-Host "`n[1/4] Starting PostgreSQL container..." -ForegroundColor Green
docker compose -f docker-compose.dev.yml up -d postgres

# 2. Wait for DB
Write-Host "`n[2/4] Waiting for database to be ready..." -ForegroundColor Green
$maxRetries = 30
$retryCount = 0
$dbReady = $false

while (-not $dbReady -and $retryCount -lt $maxRetries) {
    Start-Sleep -Seconds 1
    # Check health status
    $status = docker inspect --format='{{.State.Health.Status}}' consent-mcp-postgres-dev 2>$null
    if ($status -eq "healthy") {
        $dbReady = $true
    }
    else {
        $retryCount++
        Write-Host "Waiting for DB... ($retryCount/$maxRetries)" -NoNewline -ForegroundColor Gray
        Write-Host "`r" -NoNewline
    }
}

if (-not $dbReady) {
    Write-Error "Database failed to become healthy. Check docker logs consent-mcp-postgres-dev"
}
Write-Host "`nDatabase is ready!" -ForegroundColor Green

# 3. Run Migrations
Write-Host "`n[3/4] Running Alembic migrations..." -ForegroundColor Green
try {
    python -m alembic upgrade head
}
catch {
    Write-Error "Migration failed. Ensure you have installed dependencies (pip install -e .)"
}

# 4. Start Server
Write-Host "`n[4/4] Starting MCP HTTP Server..." -ForegroundColor Green
Write-Host "Server will be available at: http://localhost:8080/mcp" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop." -ForegroundColor Gray

# Use python -m to run the HTTP server module
$env:PYTHONPATH = "src"
python -m consent_mcp.mcp.v1.http_server
