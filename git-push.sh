#!/bin/bash

# Git push script for CoKeeper OAuth integration
cd /Users/gagepiercegaubert/Desktop/career_projects/co-keeper-run

echo "==== Git Status ===="
git status --short

echo ""
echo "==== Adding Files ===="
git add frontend_OAuth_imp.md backend/main.py frontend/app.py backend/services/xero_connector.py

echo ""
echo "==== Committing ===="
git commit -m "feat: Complete Xero OAuth integration with isolated workflow architecture

- Implemented 3-tier routing: Platform Selection → Workflow → Pages
- Fixed OAuth callback routing (Xero no longer redirects to QB page)
- Separated QB and Xero workflows with isolated session state
- Fixed Xero data transformation (Contact, Description, Account Type columns)
- Added null Contact handling for transactions without vendors
- Enhanced logging for debugging training issues
- Updated frontend BACKEND_URL to port 8002
- Added comprehensive OAuth implementation documentation

Breaking Changes:
- Removed shared api_selected_page variable
- Added selected_platform, qb_workflow_page, xero_workflow_page

Known Issues:
- Demo company has only 13 bank transactions (need 200+ for production)
- In-memory sessions lost on backend restart (need Redis for production)"

echo ""
echo "==== Pushing to GitHub ===="
git push origin main

echo ""
echo "==== Complete ===="
git log --oneline -1
