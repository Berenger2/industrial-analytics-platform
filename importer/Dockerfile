FROM python:3.12.8-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd --system importer \
    && useradd --system --gid importer --home-dir /app importer

COPY --chown=importer:importer src ./src

USER importer

CMD ["python", "-m", "src.main"]
