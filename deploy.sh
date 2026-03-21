#!/bin/bash
# MANUAL DEPLOYMENT - Run this if cloud deployment hasn't completed

set -e

PROJECT="co-keeper-run-1773629710"
REGION="us-central1"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "CO-KEEPER MANUAL CLOUD DEPLOYMENT"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Step 1: Verify code is correct
echo "[1/4] VERIFYING TIER SYSTEM FIXES IN CODE..."
echo ""

if grep -q "bins=\[0, 0.4, 0.7, 1.01\]" backend/ml_pipeline_qb.py; then
    echo "✅ Tier bins [0, 0.4, 0.7] FOUND"
else
    echo "❌ ERROR: Tier bins not found!"
    exit 1
fi

if grep -q "self.green_threshold = 0.70" backend/confidence_calibration.py; then
    echo "✅ GREEN threshold 0.70 FOUND"
else
    echo "❌ ERROR: GREEN threshold not found!"
    exit 1
fi

if grep -q "pipeline = MLPipeline.load_model(default_model_path)" backend/main.py; then
    echo "✅ Model disk loading FOUND"
else
    echo "❌ ERROR: Model loading not found!"
    exit 1
fi

if grep -q "'confidence_calibrator': self.confidence_calibrator" backend/ml_pipeline_qb.py; then
    echo "✅ Calibrator persistence FOUND"
else
    echo "❌ ERROR: Calibrator persistence not found!"
    exit 1
fi

echo ""
echo "✅ ALL CODE FIXES VERIFIED"
echo ""

# Step 2: Deploy backend
echo "[2/4] DEPLOYING BACKEND TO CLOUD RUN..."
echo ""

gcloud run deploy cokeeper-backend \
    --source ./backend \
    --region $REGION \
    --project $PROJECT \
    --memory 2Gi \
    --cpu 2 \
    --allow-unauthenticated \
    --timeout 3600 \
    --platform managed

echo ""
echo "✅ Backend deployment initiated"
echo ""

# Step 3: Deploy frontend
echo "[3/4] DEPLOYING FRONTEND TO CLOUD RUN..."
echo ""

gcloud run deploy cokeeper-frontend \
    --source ./frontend \
    --region $REGION \
    --project $PROJECT \
    --memory 2Gi \
    --cpu 2 \
    --allow-unauthenticated \
    --timeout 3600 \
    --platform managed

echo ""
echo "✅ Frontend deployment initiated"
echo ""

# Step 4: Get URLs
echo "[4/4] GETTING SERVICE URLS..."
echo ""

BACKEND_URL=$(gcloud run services describe cokeeper-backend \
    --region $REGION \
    --project $PROJECT \
    --format='value(status.url)') 2>/dev/null || echo "https://cokeeper-backend-[HASH].us-central1.run.app"

FRONTEND_URL=$(gcloud run services describe cokeeper-frontend \
    --region $REGION \
    --project $PROJECT \
    --format='value(status.url)') 2>/dev/null || echo "https://cokeeper-frontend-[HASH].us-central1.run.app"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ DEPLOYMENT COMPLETE"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "BACKEND:  $BACKEND_URL"
echo "FRONTEND: $FRONTEND_URL"
echo ""
echo "NEXT STEPS:"
echo "1. Wait 2-3 minutes for services to start"
echo "2. Go to frontend URL"
echo "3. Train model (saves with calibrator)"
echo "4. Make predictions (loads model + calibrator)"
echo "5. Check Results - should see balanced tier distribution"
echo ""
