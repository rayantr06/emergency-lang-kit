# ====================================
# Stage 1: Builder (Compile Deps)
# ====================================
FROM python:3.10-slim as builder

WORKDIR /app
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ====================================
# Stage 2: Runtime (Slim Image)
# ====================================
FROM python:3.10-slim

WORKDIR /app

# Install Runtime System Deps (FFmpeg for Audio)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy python env from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy Source Code
COPY . .

# Set Python Path to include root
ENV PYTHONPATH=/app

# Non-root user
RUN addgroup --system elk && adduser --system --ingroup elk --home /app elkuser \
    && chown -R elkuser:elk /app
USER elkuser

# Default Command (Overridden by Docker Compose)
CMD ["uvicorn", "elk.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
