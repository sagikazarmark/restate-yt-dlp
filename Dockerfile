FROM ghcr.io/astral-sh/uv:0.10.8@sha256:88234bc9e09c2b2f6d176a3daf411419eb0370d450a08129257410de9cfafd2a AS uv

FROM denoland/deno:bin-2.7.4@sha256:6b9f51ddd4f084d4e1e40fa093a87eb81edd1c14c8161c44981846b726c5e444 AS deno


FROM python:3.14.5@sha256:89a288a9a9e9141b9f0c51744c358138da6369897792f1af3f5425e407d9529a AS builder

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



FROM python:3.14.5-slim@sha256:7a500125bc50693f2214e842a621440a1b1b9cbb2188f74ab045d29ed2ea5856

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
