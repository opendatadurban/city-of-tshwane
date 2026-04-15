# code inspired by https://github.com/gianfa/poetry/blob/docs/docker-best-practices/docker-examples/poetry-multistage/Dockerfile
FROM python:3.12-slim as builder

# --- Install Poetry ---
ARG POETRY_VERSION=2.2.1

ENV POETRY_HOME=/opt/poetry
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_IN_PROJECT=1
ENV POETRY_VIRTUALENVS_CREATE=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Tell Poetry where to place its cache and virtual environment
ENV POETRY_CACHE_DIR=/opt/.cache

RUN pip install "poetry==${POETRY_VERSION}"

WORKDIR /usr/src/app/

# Copy the dependencies file to the working directory
COPY pyproject.toml poetry.lock /usr/src/app/
# Install the dependencies and clear cache
ARG ENV
RUN if [ "$ENV" = "test" ]; then \
    poetry install --no-root; \
    else \
    poetry install --no-root --without test; \
    fi \
    && rm -rf $POETRY_CACHE_DIR


# Copy over dependencies from the builder image
FROM python:3.12-slim as runtime

ENV VIRTUAL_ENV=/usr/src/app/.venv
ENV PATH="/usr/src/app/.venv/bin:$PATH"
ENV DEBIAN_FRONTEND=noninteractive

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY ./src/app /usr/src/app
COPY ./src/alembic.ini /usr/src/
COPY ./scripts /usr/src/scripts
WORKDIR /usr/src/
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT"]