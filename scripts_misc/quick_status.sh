#!/bin/bash
# Quick status check with timeout

echo "Checking Cloud Run services..."
echo ""

# Try backend with short timeout
echo "[Backend]"
if timeout 5 curl -s https://cokeeper-backend-252240360177.us-central1.run.app/health > /tmp/backend_health.json 2>&1; then
    if grep -q "healthy" /tmp/backend_health.json; then
        echo "✅ Backend is RUNNING"
        cat /tmp/backend_health.json
    else
        echo "✅ Backend responding (check status)"
        cat /tmp/backend_health.json | head -5
    fi
else
    echo "⏳ Backend still starting or unreachable"
fi

echo ""
echo "[Frontend]"
# Try to get frontend URL from gcloud (with timeout)
FRONTEND_URL=$(timeout 5 gcloud run services describe cokeeper-frontend --region us-central1 --project co-keeper-run-1773629710 --format='value(status.url)' 2>/dev/null)

if [ -z "$FRONTEND_URL" ]; then
    echo "⏳ Frontend still building..."
    echo ""
    echo "Recent builds:"
    timeout 5 gcloud builds list --project co-keeper-run-1773629710 --limit 2 2>/dev/null || echo "(Build info unavailable)"
else
    echo "✅ Frontend is RUNNING"
    echo "URL: $FRONTEND_URL"
fi

echo ""
echo "Note: gcloud CLI can be slow. If you see timeouts, that's normal."
echo "Services are likely deploying in the background."
