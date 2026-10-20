# Multi-stage Dockerfile for FlowForge n8n Workflow Library
FROM python:3.11-slim

WORKDIR /app

# Prevent Python from writing .pyc files & enable unbuffered stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install git and essential tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application assets, catalog, scripts, and web UI
COPY config/ ./config/
COPY workflows/ ./workflows/
COPY scripts/ ./scripts/
COPY web/ ./web/
COPY WORKFLOW_MANIFEST.csv ./
COPY workflow_manifest.json ./
COPY validation_report.csv ./
COPY duplicate_report.csv ./
COPY license_audit.csv ./

# Expose web application port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/web/ || exit 1

# Start the server
CMD ["python", "scripts/serve.py", "8080"]
