FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY stocksense.db .
COPY baseline_results.json .
COPY saved_models/ ./saved_models/

EXPOSE 8000

ENV ENVIRONMENT=production

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
