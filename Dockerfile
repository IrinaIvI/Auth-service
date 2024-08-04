FROM debian:bookworm-slim

LABEL maintainer="ira.ivashko.99@gmail.com"

WORKDIR /app

ENV POETRY_VERSION=1.8.3

# Установка зависимостей
RUN apt-get update && \
    apt-get install -y python3 python3-pip curl build-essential libssl-dev libffi-dev python3-dev && \
    curl -sSL https://install.python-poetry.org | POETRY_VERSION=${POETRY_VERSION} python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Проверка установленной версии poetry и её конфигурации
RUN poetry --version && poetry config virtualenvs.create false

COPY poetry.lock pyproject.toml ./

# Установка зависимостей проекта
RUN poetry install

COPY ./src/app /app/

EXPOSE 8001

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]


