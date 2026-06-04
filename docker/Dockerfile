# =============================================================================
# Stage 1: Asset Builder (Node.js)
# =============================================================================
FROM node:20-slim as node-builder

WORKDIR /app

# Copy package.json and package-lock.json (if available)
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy source code for directives and templates (tailwind scanning)
COPY . .

# Build CSS
RUN npm run build


# =============================================================================
# Stage 2: Python Builder
# =============================================================================
FROM python:3.12-slim as builder

WORKDIR /app


# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


# =============================================================================
# Stage 2: Test Runner
# =============================================================================
FROM python:3.12-slim as test

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder (prod deps)
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Add dev/test tooling on top of the prod deps
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy application code
COPY . .

# Default command: run tests with coverage
CMD ["pytest", "tests/", "-v", "--cov=apps", "--cov-report=term-missing"]


# =============================================================================
# Stage 3: Production
# =============================================================================
FROM python:3.12-slim as production

WORKDIR /app

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    gettext \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=appuser:appgroup . .

# Copy built assets from node-builder
COPY --from=node-builder --chown=appuser:appgroup /app/static/css/output.css /app/static/css/output.css

# Copy and set permissions for entrypoint
COPY --chown=appuser:appgroup docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Compile translations. DEBUG=True + USE_SQLITE=True keep settings loadable at
# build time without real DB/email config (those are required only at runtime).
RUN DEBUG=True USE_SQLITE=True SECRET_KEY=dummy GEMINI_API_KEY=dummy ALLOWED_HOSTS=localhost \
    python manage.py compilemessages

# Create directories for static and media files
RUN mkdir -p /app/staticfiles /app/mediafiles \
    && chown -R appuser:appgroup /app/staticfiles /app/mediafiles

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Entrypoint
ENTRYPOINT ["/entrypoint.sh"]
