FROM debian:bookworm-slim

LABEL maintainer="ira.ivashko.99@gmail.com"

WORKDIR /app

ENV POETRY_VERSION=1.8.3
ENV PATH="/root/.local/bin:${PATH}"

# Установка системных зависимостей
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv curl libpq-dev gcc python3-dev && \
    curl -sSL https://install.python-poetry.org | POETRY_VERSION=${POETRY_VERSION} python3 - && \
    /root/.local/bin/poetry --version

RUN poetry config virtualenvs.create true

COPY poetry.lock pyproject.toml ./

RUN poetry install --no-interaction --no-ansi -vvv

COPY ./src /app

COPY alembic.ini ./
COPY migrations/ /app/migrations
RUN poetry run alembic upgrade head

ENTRYPOINT ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
