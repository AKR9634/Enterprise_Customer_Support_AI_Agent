FROM python:3.11-slim

WORKDIR /app

# System deps needed to build psycopg/bcrypt and to run healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Install CPU-only torch first so pip doesn't pull the multi-GB CUDA runtime
# (sentence-transformers only needs torch for CPU embedding inference).
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY docs ./docs
COPY scripts ./scripts

# Railway (and most PaaS) inject $PORT at runtime; default to 8000 for local/docker-compose use
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
