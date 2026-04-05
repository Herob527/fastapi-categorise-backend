FROM python:3.13.0-bookworm AS base

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock /app/

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-install-project

FROM base AS dev

COPY . /app

# Install the project
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen

EXPOSE 80

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
