FROM node:20-bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv python3-pip unzip ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g gmgn-cli

WORKDIR /opt/app
COPY dist/app_bundle.zip /tmp/app_bundle.zip
RUN mkdir -p /opt/radar && unzip -q /tmp/app_bundle.zip -d /opt/radar && rm /tmp/app_bundle.zip

RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --disable-pip-version-check -r /opt/radar/requirements.txt

COPY cloud/run.py /opt/app/run.py

ENV PATH="/opt/venv/bin:$PATH" \
    RADAR_ROOT="/opt/radar" \
    PYTHONUNBUFFERED="1"

CMD ["python", "/opt/app/run.py"]
