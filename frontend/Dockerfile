# Frontend Dockerfile for CoKeeper Streamlit Application
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Cloud Run will use PORT env variable)
ENV PORT=8501
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Configure Streamlit
RUN mkdir -p ~/.streamlit && \
    echo "[server]\nport = ${PORT}\naddress = 0.0.0.0\nheadless = true\n" > ~/.streamlit/config.toml

# Run Streamlit
CMD streamlit run app.py --server.port=${PORT} --server.address=0.0.0.0 --server.headless=true
