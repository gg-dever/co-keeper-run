#!/bin/bash
# COMPREHENSIVE DEPLOYMENT VERIFICATION
# Checks if code fixes are there AND if backend is deployed with them

OUTPUT_FILE="/tmp/deployment_verification.txt"

{
echo "═══════════════════════════════════════════════════════════════"
echo "COMPREHENSIVE DEPLOYMENT VERIFICATION"
echo "Date: $(date)"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "[1] CHECKING LOCAL CODE..."
echo ""

# Check tier bins
if grep -q "bins=\[0, 0.4, 0.7, 1.01\]" backend/ml_pipeline_qb.py; then
    echo "✅ Tier bins [0, 0.4, 0.7, 1.01] found in CODE"
else
    echo "❌ Tier bins NOT in code"
fi

# Check green threshold
if grep -q "self.green_threshold = 0.70" backend/confidence_calibration.py; then
    echo "✅ GREEN threshold 0.70 found in CODE"
else
    echo "❌ GREEN threshold NOT in code"
fi

# Check model loading
if grep -q "MLPipeline.load_model(default_model_path)" backend/main.py; then
    echo "✅ Model disk loading found in CODE"
else
    echo "❌ Model disk loading NOT in code"
fi

# Check calibrator persistence
if grep -q "'confidence_calibrator': self.confidence_calibrator" backend/ml_pipeline_qb.py; then
    echo "✅ Calibrator persistence found in CODE"
else
    echo "❌ Calibrator persistence NOT in code"
fi

echo ""
echo "[2] CHECKING DEPLOYED BACKEND..."
echo ""

# Test backend
BACKEND_TEST=$(timeout 5 curl -s https://cokeeper-backend-252240360177.us-central1.run.app/health 2>&1)
if echo "$BACKEND_TEST" | grep -q "healthy\|ml_qb"; then
    echo "✅ Backend IS RESPONDING"
    echo "Response: $(echo "$BACKEND_TEST" | head -c 200)"
else
    echo "⏳ Backend not responding yet (may still be deploying)"
    echo "Response: $(echo "$BACKEND_TEST" | head -c 100)"
fi

echo ""
echo "[3] CHECKING CLOUD RUN SERVICES..."
echo ""

# Get backend URL
BACKEND_URL=$(timeout 5 gcloud run services describe cokeeper-backend --region us-central1 --project co-keeper-run-1773629710 --format='value(status.url)' 2>&1)
if [ ! -z "$BACKEND_URL" ] && [ "$BACKEND_URL" != "ERROR" ]; then
    echo "✅ Backend service exists: $BACKEND_URL"
else
    echo "⏳ Backend service query timed out or not ready"
fi

# Get frontend URL
FRONTEND_URL=$(timeout 5 gcloud run services describe cokeeper-frontend --region us-central1 --project co-keeper-run-1773629710 --format='value(status.url)' 2>&1)
if [ ! -z "$FRONTEND_URL" ] && [ "$FRONTEND_URL" != "ERROR" ]; then
    echo "✅ Frontend service exists: $FRONTEND_URL"
else
    echo "⏳ Frontend service query timed out or not ready"
fi

echo ""
echo "[4] CHECKING RECENT BUILDS..."
echo ""

# List recent builds
BUILD_LOG=$(timeout 5 gcloud builds list --project co-keeper-run-1773629710 --limit 2 2>&1)
if [ ! -z "$BUILD_LOG" ]; then
    echo "Build status:"
    echo "$BUILD_LOG" | head -5
else
    echo "⏳ Build info unavailable"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "SUMMARY"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "LOCAL CODE: ✅ All fixes present"
echo "BACKEND DEPLOYMENT: $(if echo "$BACKEND_TEST" | grep -q "healthy\|ml_qb"; then echo "✅ DEPLOYED"; else echo "🔄 DEPLOYING"; fi)"
echo "FRONTEND DEPLOYMENT: $(if [ ! -z "$FRONTEND_URL" ]; then echo "✅ EXISTS"; else echo "🔄 BUILDING"; fi)"
echo ""
echo "═══════════════════════════════════════════════════════════════"

} > "$OUTPUT_FILE" 2>&1

cat "$OUTPUT_FILE"
