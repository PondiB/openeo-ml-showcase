FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /work

COPY pyproject.toml uv.lock ./
COPY run_pg.py ./

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN uv sync --frozen

CMD ["uv", "run", "run_pg.py"]
