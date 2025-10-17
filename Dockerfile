FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port (Heroku will set $PORT)
EXPOSE 8000

# Start server (migrations run in release phase via heroku.yml)
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
