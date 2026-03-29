# ── Loan Processing API Dockerfile ───────────────────────────────────────────
# Minimal Python 3.11 image.
# Swap DATABASE_URL env var for MySQL/PostgreSQL in any cloud environment.
# Deployable to IBM Cloud, Azure Container Apps, AWS ECS, GCP Cloud Run.

FROM python:3.11-slim

WORKDIR /app

# Install deps first — Docker layer caching skips this if requirements unchanged
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

EXPOSE 8000

# Use multiple workers in production (gunicorn + uvicorn workers)
# For SQLite dev: keep 1 worker to avoid write contention
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
