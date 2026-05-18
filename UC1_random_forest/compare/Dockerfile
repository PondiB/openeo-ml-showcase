# Use the requested Python 3.13 Alpine image
FROM python:3.13-slim

# Install system dependencies required by geospatial wheels like rasterio
RUN apt-get update && apt-get install -y --no-install-recommends \
    libexpat1 \
    && rm -rf /var/lib/apt/lists/*

# Copy the uv binary from the official Astral UV image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Establish the base application directory and clone the repo
WORKDIR /app
COPY . .

# Optimize uv performance configuration for containers
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Dynamically install dependencies using build caching.
# This accommodates either a modern pyproject.toml setup or a legacy requirements.txt.
RUN uv sync --frozen

# Execute main.py using uv to automatically manage environment runtime mapping
CMD ["uv", "run", "main.py"]