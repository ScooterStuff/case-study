# ---- builder -------------------------------------------------------------
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN python -m venv /venv && /venv/bin/pip install --no-cache-dir -r requirements.txt

# ---- runtime ---------------------------------------------------------------
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home appuser
WORKDIR /srv
COPY --from=builder /venv /venv
# datasets + seed.sql.gz are baked in: first boot self-heals the db, no scraping
COPY app ./backend/app
COPY data ./backend/data
COPY ingest.py ./backend/ingest.py
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x entrypoint.sh && chown -R appuser:appuser /srv
USER appuser
ENV PATH="/venv/bin:$PATH" PYTHONPATH=/srv LOG_FORMAT=json
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
  CMD curl -f http://localhost:8000/health || exit 1
CMD ["./entrypoint.sh"]
