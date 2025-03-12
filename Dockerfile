FROM python:3.12.9-slim-bookworm AS base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1
ENV PATH=/home/pysatluser/.local/bin:$PATH
ENV FT_APP_ENV="docker"

# Prepare environment
RUN mkdir /stattest \
  && apt-get update \
  && apt-get -y install sudo libatlas3-base curl sqlite3 libgomp1 \
  && apt-get clean \
  && useradd -u 1000 -G sudo -U -m -s /bin/bash pysatluser \
  && chown pysatluser:pysatluser /stattest \
  # Allow sudoers
  && echo "pysatluser ALL=(ALL) NOPASSWD: /bin/chown" >> /etc/sudoers

WORKDIR /stattest

# Install dependencies
FROM base AS python-deps
RUN  apt-get update \
  && apt-get -y install build-essential libssl-dev git libffi-dev libgfortran5 pkg-config cmake gcc \
  && apt-get clean \
  && pip install --upgrade pip wheel

# Install dependencies
COPY --chown=pysatluser:pysatluser requirements.txt /stattest/
USER pysatluser
RUN  pip install --user --no-cache-dir "numpy<2.0"
RUN  pip install --user --no-cache-dir "setuptools>=64.0.0"

# Copy dependencies to runtime-image
FROM base AS runtime-image
COPY --from=python-deps /usr/local/lib /usr/local/lib
ENV LD_LIBRARY_PATH /usr/local/lib

COPY --from=python-deps --chown=pysatluser:pysatluser /home/pysatluser/.local /home/pysatluser/.local

USER pysatluser
# Install and execute
COPY --chown=pysatluser:pysatluser . /stattest/

RUN pip install -e . --user --no-cache-dir --no-build-isolation \
  && mkdir /stattest/user_data/

ENTRYPOINT ["stattest"]
# Default to experiment mode
CMD [ "experiment" ]
