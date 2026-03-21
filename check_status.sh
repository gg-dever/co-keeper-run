#!/bin/bash
# Check deployment status

PROJECT="co-keeper-run-1773629710"
REGION="us-central1"

echo ""
echo "Checking Cloud Run services..."
echo ""

echo "Backend service:"
gcloud run services describe cokeeper-backend \
    --region $REGION \
    --project $PROJECT \
    --format='value(status.url,status.conditions[0].status)' 2>/dev/null || echo "Not ready yet"

echo ""
echo "Frontend service:"
gcloud run services describe cokeeper-frontend \
    --region $REGION \
    --project $PROJECT \
    --format='value(status.url,status.conditions[0].status)' 2>/dev/null || echo "Not ready yet"

echo ""
echo "Checking recent builds:"
gcloud builds list --project $PROJECT --limit 3 --format='table(ID, STATUS, CREATE_TIME)' 2>/dev/null || echo "Builds not available yet"

echo ""
echo "Check backend logs:"
gcloud run logs read cokeeper-backend --limit 20 --region $REGION --project $PROJECT 2>/dev/null | head -20 || echo "Logs not available yet"
