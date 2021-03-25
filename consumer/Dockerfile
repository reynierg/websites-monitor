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

COPY ./kafka_certs /app/kafka_certs
COPY ./common /app/common
COPY ./consumer /app/consumer
# COPY ./consumer/requirements.txt /app/requirements.txt

RUN python -m pip install --upgrade pip
RUN python -m pip install -r consumer/requirements.txt --no-cache-dir

ENV PYTHONPATH /app
ENV PYTHONUNBUFFERED 1

# CMD ["python3", "/app/consumer/consumer/main.py" ]
# Trying to see how to receive KeyboarInterrupt in the python script:
# CMD ["consumer/consumer/main.py" ]
ENTRYPOINT ["python3", "consumer/consumer/main.py"]
