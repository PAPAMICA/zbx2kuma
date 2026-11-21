FROM python:3.12-slim-bookworm

WORKDIR /usr/src/app
COPY app.py .
COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends iputils-ping && \
    pip3 install --no-cache-dir -r /usr/src/app/requirements.txt && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

CMD ["python3", "-u", "app.py"]
