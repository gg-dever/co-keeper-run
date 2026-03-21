# Backend Dockerfile for CoKeeper FastAPI Application
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create models directory if it doesn't exist
RUN mkdir -p models

# Expose port (Cloud Run will use PORT env variable)
ENV PORT=8000
EXPOSE 8000

# Run the application with uvicorn
# Increase timeout for Cloud Run and bind to 0.0.0.0
CMD exec uvicorn main:app --host 0.0.0.0 --port $PORT --timeout-keep-alive 300
