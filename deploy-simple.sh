#!/bin/bash

# Simple deployment script for CoKeeper Cloud Run
# Run this manually in your terminal

set -e

PROJECT_ID="co-keeper-run-1773629710"
REGION="us-central1"

echo "========================================="
echo "CoKeeper Cloud Run Deployment"
echo "========================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Step 1: Set project
echo "Step 1: Setting project..."
gcloud config set project $PROJECT_ID

# Step 2: Enable APIs (will prompt if not enabled)
echo ""
echo "Step 2: Enabling APIs..."
echo "This will take a few minutes. Press Y when prompted."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Step 3: Deploy backend
echo ""
echo "========================================="
echo "Step 3: Deploying Backend..."
echo "========================================="
gcloud run deploy cokeeper-backend \
    --source ./backend \
    --region $REGION \
    --allow-unauthenticated \
    --port 8000 \
    --memory 2Gi \
    --cpu 2 \
    --project $PROJECT_ID

# Step 4: Get backend URL
echo ""
echo "Getting backend URL..."
BACKEND_URL=$(gcloud run services describe cokeeper-backend \
    --region $REGION \
    --project $PROJECT_ID \
    --format 'value(status.url)')

echo "✅ Backend deployed: $BACKEND_URL"

# Step 5: Deploy frontend
echo ""
echo "========================================="
echo "Step 4: Deploying Frontend..."
echo "========================================="
gcloud run deploy cokeeper-frontend \
    --source ./frontend \
    --region $REGION \
    --allow-unauthenticated \
    --port 8501 \
    --memory 2Gi \
    --cpu 2 \
    --set-env-vars "BACKEND_URL=${BACKEND_URL}" \
    --project $PROJECT_ID

# Step 6: Get frontend URL
echo ""
echo "Getting frontend URL..."
FRONTEND_URL=$(gcloud run services describe cokeeper-frontend \
    --region $REGION \
    --project $PROJECT_ID \
    --format 'value(status.url)')

echo ""
echo "========================================="
echo "🎉 DEPLOYMENT COMPLETE!"
echo "========================================="
echo ""
echo "🌐 Frontend URL: $FRONTEND_URL"
echo "🔧 Backend URL:  $BACKEND_URL"
echo "📚 API Docs:     $BACKEND_URL/docs"
echo ""
echo "Visit your app at: $FRONTEND_URL"
echo ""
