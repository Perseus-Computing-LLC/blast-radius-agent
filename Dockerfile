# Blast Radius Agent — multi-stage Docker image
FROM python:3.12-slim AS base
WORKDIR /app

# Install orbit CLI (if available)
# RUN curl -sSL https://gitlab.com/gitlab-org/orbit/-/releases/permalink/latest/downloads/orbit-linux-amd64 -o /usr/local/bin/orbit && chmod +x /usr/local/bin/orbit

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY blast_radius/ ./blast_radius/
COPY skills/ ./skills/

ENTRYPOINT ["python", "-m", "blast_radius"]
CMD ["--help"]
