# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3
FROM python:${PYTHON_VERSION}-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN apt-get -y update && \
pip install --no-cache-dir -r requirements.txt

COPY . .

CMD python weibull_experiment.py