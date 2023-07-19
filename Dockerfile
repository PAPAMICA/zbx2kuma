FROM debian:bullseye-slim

WORKDIR /usr/src/app

COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends python3-pip iputils-ping && \
    pip3 install -r  /usr/src/app/requirements.txt && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY app.py .

CMD ["python3", "-u", "app.py"]
