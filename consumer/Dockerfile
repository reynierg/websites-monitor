FROM python:3.8-slim-buster

RUN apt-get update
RUN apt-get install \
    -y \
    --no-install-recommends \
    gcc \
    libc-dev \
    libpq-dev \
    python3-dev

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

COPY ./consumer/requirements.txt /app/consumer/requirements.txt
RUN python -m pip install --upgrade pip
RUN python -m pip install -r consumer/requirements.txt --no-cache-dir

COPY ./kafka_certs /app/kafka_certs
COPY ./common /app/common
COPY ./consumer /app/consumer

ENV PYTHONPATH /app
ENV PYTHONUNBUFFERED 1

ENTRYPOINT ["python3", "consumer/consumer/main.py"]
