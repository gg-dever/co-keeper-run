#!/bin/bash

# Fix Cloud Build Permissions for CoKeeper

set -e

PROJECT_ID="co-keeper-run-1773629710"
PROJECT_NUMBER="497003729794"
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "========================================="
echo "Fixing Cloud Build Permissions"
echo "========================================="
echo "Project: $PROJECT_ID"
echo "Service Account: $SERVICE_ACCOUNT"
echo ""

# Grant Cloud Build Service Account role
echo "1. Granting Cloud Build Service Account role..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/cloudbuild.builds.builder" \
    --condition=None

# Grant Storage Admin role (needed for build artifacts)
echo ""
echo "2. Granting Storage Admin role..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/storage.admin" \
    --condition=None

# Grant Cloud Run Admin role
echo ""
echo "3. Granting Cloud Run Admin role..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/run.admin" \
    --condition=None

# Grant Service Account User role
echo ""
echo "4. Granting Service Account User role..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/iam.serviceAccountUser" \
    --condition=None

# Grant Logs Writer role
echo ""
echo "5. Granting Logs Writer role..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/logging.logWriter" \
    --condition=None

echo ""
echo "========================================="
echo "✅ Permissions Updated Successfully!"
echo "========================================="
echo ""
echo "Wait 1-2 minutes for permissions to propagate."
echo "Then run: ./deploy-simple.sh"
echo ""
