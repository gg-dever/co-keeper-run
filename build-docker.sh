#!/bin/bash

# Build Docker images locally for testing

set -e

echo "Building Backend Docker image..."
docker build -t cokeeper-backend:latest ./backend

echo "Building Frontend Docker image..."
docker build -t cokeeper-frontend:latest ./frontend

echo ""
echo "Build complete!"
echo ""
echo "To run locally with docker-compose:"
echo "  docker-compose up"
echo ""
echo "To run individual containers:"
echo "  docker run -p 8000:8000 cokeeper-backend:latest"
echo "  docker run -p 8501:8501 -e BACKEND_URL=http://localhost:8000 cokeeper-frontend:latest"
