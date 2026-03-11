FROM ghcr.io/astral-sh/uv:0.10.8@sha256:88234bc9e09c2b2f6d176a3daf411419eb0370d450a08129257410de9cfafd2a AS uv

FROM denoland/deno:bin-2.7.5@sha256:b0bc343ae5fabb4c1c1def9984f3c4834de86ccfc52f9b5f0ae10e8c06fdcfd2 AS deno


FROM python:3.14.3@sha256:b66f77a332babd8b2b0190f10a65eeb90c49d8da4696f7a3436baf1b1220eeec AS builder

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



FROM python:3.14.3-slim@sha256:6a27522252aef8432841f224d9baaa6e9fce07b07584154fa0b9a96603af7456

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
