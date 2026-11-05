FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive \
    U2NET_HOME=/root/.u2net

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates libgl1 libglib2.0-0 libgomp1 && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /root/.u2net

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY worker.py .

EXPOSE 8000
CMD ["uvicorn", "worker:app", "--host", "0.0.0.0", "--port", "8000"]
