#!/bin/bash

set -e

echo "========================================="
echo "Fixing GCP Project Configuration"
echo "========================================="

# Get the project ID (not number)
PROJECT_ID=$(gcloud projects list --filter="name:CoKeeper" --format="value(projectId)" | head -1)

if [ -z "$PROJECT_ID" ]; then
  echo "❌ Could not find CoKeeper project"
  echo "Available projects:"
  gcloud projects list --format="table(projectId,name)"
  echo ""
  read -p "Enter your project ID: " PROJECT_ID
fi

echo "Using Project ID: $PROJECT_ID"

# Unset any incorrect configuration
gcloud config unset project 2>/dev/null || true

# Set the correct project ID
gcloud config set project "$PROJECT_ID"

# Verify
CURRENT_PROJECT=$(gcloud config get-value project)
echo "Current project set to: $CURRENT_PROJECT"

# Enable required APIs
echo ""
echo "Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com

echo ""
echo "========================================="
echo "Deploying Backend to Cloud Run"
echo "========================================="

# Deploy backend with explicit project flag
gcloud run deploy cokeeper-backend \
    --source ./backend \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8000 \
    --memory 2Gi \
    --cpu 2 \
    --project "$PROJECT_ID"

# Get backend URL
BACKEND_URL=$(gcloud run services describe cokeeper-backend \
    --region us-central1 \
    --project "$PROJECT_ID" \
    --format 'value(status.url)')

echo ""
echo "✅ Backend deployed at: $BACKEND_URL"

echo ""
echo "========================================="
echo "Deploying Frontend to Cloud Run"
echo "========================================="

# Deploy frontend with explicit project flag
gcloud run deploy cokeeper-frontend \
    --source ./frontend \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8501 \
    --memory 2Gi \
    --cpu 2 \
    --set-env-vars "BACKEND_URL=${BACKEND_URL}" \
    --project "$PROJECT_ID"

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe cokeeper-frontend \
    --region us-central1 \
    --project "$PROJECT_ID" \
    --format 'value(status.url)')

echo ""
echo "========================================="
echo "🎉 Deployment Complete!"
echo "========================================="
echo ""
echo "Backend URL:  $BACKEND_URL"
echo "Frontend URL: $FRONTEND_URL"
echo ""
echo "🌐 Visit your app: $FRONTEND_URL"
echo "📚 API Docs: $BACKEND_URL/docs"
echo ""
