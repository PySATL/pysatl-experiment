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

# Build wheels
FROM base AS python-deps

ARG PIP_EXTRA_INDEX_URL=https://test.pypi.org/simple/
ENV PIP_EXTRA_INDEX_URL=${PIP_EXTRA_INDEX_URL}

RUN apt-get update \
  && apt-get -y install --no-install-recommends build-essential libssl-dev git libffi-dev libgfortran5 pkg-config cmake gcc libpq-dev libcairo2-dev \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* \
  && pip install --upgrade pip wheel build

COPY pyproject.toml poetry.lock README.md /app/
COPY src /app/src

RUN pip wheel --no-cache-dir --wheel-dir /dist .

# Runtime image only consumes built distributions
FROM base AS runtime-image

COPY --from=python-deps --chown=appuser:appuser /dist /dist

USER appuser

RUN pip install --user --no-cache-dir --no-index --find-links=/dist pysatl-experiment \
  && mkdir -p /app/user_data

ENTRYPOINT ["experiment"]
CMD ["--help"]
