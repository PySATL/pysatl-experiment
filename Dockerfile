FROM python:3.12.9-slim-bookworm AS base

WORKDIR /app

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONFAULTHANDLER=1
ENV PATH=/home/pysatluser/.local/bin:$PATH
ENV POETRY_HOME=/opt/poetry

RUN apt-get update && apt-get install -y curl && \
    curl -sSL https://install.python-poetry.org | python - && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create true

# Копируем файлы зависимостей
COPY pyproject.toml ./

# Устанавливаем зависимости
RUN poetry install --no-interaction --no-ansi

# Копируем остальные файлы
COPY . .

ENTRYPOINT ["poetry", "run", "python", "-m", "stattest.main"]
# Default to experiment mode
CMD [ "experiment", "--config", "../../config_examples/config_example.json" ]
