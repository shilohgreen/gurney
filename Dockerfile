# ── Gurney — Cloud Run Dockerfile ─────────────────────────────────────────────
# Uses Microsoft's official Playwright image (includes Chromium + system deps)

FROM mcr.microsoft.com/playwright/python:v1.50.0-noble

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium only to keep image smaller)
RUN playwright install chromium

# Copy application code
COPY . .

# Cloud Run uses PORT env var (defaults to 8080)
ENV PORT=8080

EXPOSE 8080

CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT}"]

