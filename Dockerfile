ARG PYTHON_IMAGE=python:3.12-slim-trixie

FROM ${PYTHON_IMAGE} AS base

# Setup env
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONFAULTHANDLER=1
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYSATL_APP_ENV=docker

# Prepare environment
RUN mkdir /app \
  && apt-get update \
  && apt-get -y install --no-install-recommends sudo curl sqlite3 libgomp1 libpq5 libcairo2 \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* \
  && useradd -u 1000 -G sudo -U -m -s /bin/bash appuser \
  && chown appuser:appuser /app \
  && echo "appuser ALL=(ALL) NOPASSWD: /bin/chown" >> /etc/sudoers

WORKDIR /app

# Install project dependencies with Poetry, strictly from poetry.lock.
# NOTE: this stage deliberately runs as root: `poetry install` needs to write
# system packages and compile native extensions (build-essential etc.), which
# the non-root `appuser` cannot do. The runtime stage below switches to
# `appuser` and never runs as root.
FROM base AS python-deps

ENV POETRY_VERSION=2.1.1 \
  POETRY_HOME=/opt/poetry \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_NO_INTERACTION=1 \
  PATH=/opt/poetry/bin:$PATH

# Poetry needs the explicit TestPyPI source for pysatl-criterion (declared in
# pyproject.toml). PIP_EXTRA_INDEX_URL is the pip-side equivalent for any
# pip fallback; POETRY_HTTP_BASIC_* are only needed for *private* indexes.
ARG PIP_EXTRA_INDEX_URL=https://test.pypi.org/simple/
ENV PIP_EXTRA_INDEX_URL=${PIP_EXTRA_INDEX_URL}

RUN apt-get update \
  && apt-get -y install --no-install-recommends build-essential libssl-dev git libffi-dev libgfortran5 pkg-config cmake gcc libpq-dev libcairo2-dev curl \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* \
  && curl -sSL https://install.python-poetry.org | python3 - --version ${POETRY_VERSION} \
  && poetry --version

# Copy only dependency manifests first for better layer caching: this layer
# is rebuilt only when dependencies change, not on every source edit.
COPY pyproject.toml poetry.lock README.md /app/

# --only main: dev tools (pytest, ruff, mypy, mkdocs) are not needed inside
# the experiment image. poetry.lock is the single source of truth — the exact
# pinned versions (e.g. pysatl-criterion 1.1.0.dev47) are respected.
# Two steps for cache efficiency: dependencies first (rebuilt only when the
# lock changes), then the project itself (rebuilt on every source edit, but
# fast since dependencies are already satisfied).
RUN poetry install --no-root --only main

# Project source is small and changes often — copy it last for cache efficiency.
COPY src /app/src

RUN poetry install --only main

# Runtime image: project source + already-resolved environment
FROM base AS runtime-image

COPY --from=python-deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=python-deps /usr/local/bin /usr/local/bin
COPY --from=python-deps /app/src /app/src
COPY --from=python-deps /app/pyproject.toml /app/README.md /app/

USER appuser

RUN mkdir -p /app/user_data

ENTRYPOINT ["experiment"]
CMD ["--help"]
