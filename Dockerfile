FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port (Heroku will set $PORT)
EXPOSE 8000

# Run migrations and start server
CMD alembic upgrade head && uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
