FROM python:3.12-slim

WORKDIR /opt/biom

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=.

# Install system dependencies (for psycopg2)
RUN set -xe \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && pip install --upgrade pip \
    && pip install uv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files and install
COPY ["uv.lock", "pyproject.toml", "README.md", "./"]
RUN uv sync --frozen --no-dev

# Copy all project files (including pre-built assets)
COPY . .

# Create directories for volumes
RUN mkdir -p /opt/biom/staticfiles \
    && mkdir -p /opt/biom/media \
    && mkdir -p /opt/biom/logs

EXPOSE 8000

# Entrypoint script
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod a+x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
