FROM ghcr.io/astral-sh/uv:0.9.15@sha256:4c1ad814fe658851f50ff95ecd6948673fffddb0d7994bdb019dcb58227abd52 AS uv

FROM denoland/deno:bin-2.6.0@sha256:e76562c56fbcbda664e9ca7dce0a934496401fe78c0f64d03f76b9b62b3064b8 AS deno


FROM python:3.15.0a2@sha256:ec037e91c5c938f8083dcaa246ec4582e225c5565bc8778a8bd295eee677a389 AS builder

RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

COPY --from=uv /uv /uvx /bin/

WORKDIR /usr/src/app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --extra app --no-install-project

COPY . .

RUN uv sync --frozen --no-dev --extra app



FROM python:3.15.0a2-slim@sha256:0673ad07b309a98ea99ab32b93e04ded3963f3f59b17edd5de4f423d95c98783

WORKDIR /usr/src/app

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY --from=deno /deno /usr/local/bin/deno

ENV PATH="/usr/src/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY --from=builder /usr/src/app .

COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

EXPOSE 9080

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD [ "python", "-m", "granian", "--interface", "asginl", "src.main:app", "--host", "0.0.0.0", "--port", "9080" ]
