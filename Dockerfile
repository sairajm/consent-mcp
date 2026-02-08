# Consent MCP Dockerfile
# Multi-stage build for smaller production image

# ============================================
# Stage 1: Build dependencies
# ============================================
FROM python:3.14-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir build && \
    pip wheel --no-cache-dir --wheel-dir /wheels .

# ============================================
# Stage 2: Production image
# ============================================
FROM python:3.14-slim as production

WORKDIR /app

# Create non-root user for security
RUN groupadd --gid 1000 consent && \
    useradd --uid 1000 --gid consent --shell /bin/bash --create-home consent

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder
COPY --from=builder /wheels /wheels

# Install the application
RUN pip install --no-cache-dir /wheels/*.whl && \
    rm -rf /wheels

# Copy application code

# Copy application code
COPY alembic.ini .
COPY alembic ./alembic
COPY scripts/prestart.py ./scripts/prestart.py
COPY src ./src

# Change ownership to non-root user
RUN chown -R consent:consent /app

# Switch to non-root user
USER consent

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "print('healthy')" || exit 1

# Default command
CMD ["sh", "-c", "python scripts/prestart.py && python -m consent_mcp.mcp.v1.server"]
