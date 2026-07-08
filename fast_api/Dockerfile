# uv 공식문서 : https://docs.astral.sh/uv/guides/integration/fastapi/#migrating-an-existing-fastapi-project

# 이미지
FROM python:3.12-slim

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application into the container.
COPY . /app

# uv sync
WORKDIR /app
RUN uv sync --frozen --no-cache

# uvicorn 실행
CMD ["/app/.venv/bin/uvicorn", "fast_api.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]