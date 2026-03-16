#!/bin/bash

# CoKeeper Cloud Run Deployment Script
# This script deploys both backend and frontend to Google Cloud Run

set -e  # Exit on error

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-gcp-project-id}"
REGION="${GCP_REGION:-us-central1}"
BACKEND_SERVICE="cokeeper-backend"
FRONTEND_SERVICE="cokeeper-frontend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}CoKeeper Cloud Run Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if PROJECT_ID is set
if [ "$PROJECT_ID" = "your-gcp-project-id" ]; then
    echo -e "${YELLOW}Warning: Please set your GCP_PROJECT_ID${NC}"
    read -p "Enter your GCP Project ID: " PROJECT_ID
fi

echo -e "${YELLOW}Project ID: ${PROJECT_ID}${NC}"
echo -e "${YELLOW}Region: ${REGION}${NC}"
echo ""

# Set the project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${GREEN}Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Deploy Backend
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deploying Backend to Cloud Run...${NC}"
echo -e "${GREEN}========================================${NC}"

gcloud run deploy $BACKEND_SERVICE \
    --source ./backend \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 8000 \
    --memory 2Gi \
    --cpu 2 \
    --min-instances 0 \
    --max-instances 10 \
    --timeout 300 \
    --set-env-vars "ENVIRONMENT=production"

# Get backend URL
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE --region $REGION --format 'value(status.url)')
echo -e "${GREEN}Backend deployed at: ${BACKEND_URL}${NC}"

# Deploy Frontend
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deploying Frontend to Cloud Run...${NC}"
echo -e "${GREEN}========================================${NC}"

gcloud run deploy $FRONTEND_SERVICE \
    --source ./frontend \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 8501 \
    --memory 2Gi \
    --cpu 2 \
    --min-instances 0 \
    --max-instances 10 \
    --timeout 300 \
    --set-env-vars "BACKEND_URL=${BACKEND_URL}"

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE --region $REGION --format 'value(status.url)')

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Completed Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Backend URL:${NC}  ${BACKEND_URL}"
echo -e "${GREEN}Frontend URL:${NC} ${FRONTEND_URL}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Visit the frontend URL to access the application"
echo "2. Test the backend API at: ${BACKEND_URL}/docs"
echo "3. Monitor logs: gcloud run services logs read ${FRONTEND_SERVICE} --region ${REGION}"
