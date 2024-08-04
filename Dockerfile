FROM debian:bookworm-slim

LABEL maintainer="ira.ivashko.99@gmail.com"

WORKDIR /app

ENV POETRY_VERSION=1.8.3
ENV PATH="/root/.local/bin:${PATH}"

# Установка системных зависимостей
RUN apt-get update && \
    apt-get install -y python3 python3-pip curl && \
    curl -sSL https://install.python-poetry.org | POETRY_VERSION=${POETRY_VERSION} python3 - && \
    poetry --version

# Настройка Poetry: не создавать виртуальные окружения
RUN poetry config virtualenvs.create true

COPY poetry.lock pyproject.toml ./

# Установка зависимостей проекта
RUN poetry install --no-interaction --no-ansi -vvv

# Копирование файлов
COPY poetry.lock pyproject.toml ./

RUN poetry install --no-interaction --no-ansi -vvv

COPY ./src /app

ENTRYPOINT ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

