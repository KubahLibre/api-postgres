FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

# Reihenfolge wichtig: uv sync baut das Projekt selbst mit. Dafuer braucht er
# src/ - also muss src/ VOR dem Sync kopiert sein, sonst schlaegt der Build fehl.
# README.md wird von uv-build gebraucht: pyproject.toml verweist darauf.
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

RUN uv sync --frozen --no-dev

EXPOSE 8000

# --no-sync: der Container baut nichts neu, er startet nur, was schon da ist.
CMD ["uv", "run", "--no-sync", "uvicorn", "api_postgres.uebung:app", \
     "--host", "0.0.0.0", "--port", "8000"]
