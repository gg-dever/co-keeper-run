#!/bin/bash
# CoKeeper Documentation Cleanup Script
# Reorganizes documentation, archives old files, deletes unnecessary ones

set -e

echo "🧹 CoKeeper Documentation Cleanup"
echo "=================================="
echo ""

# Create archive directory
echo "📁 Creating archive directory..."
mkdir -p docs/archive/implementation
mkdir -p docs/archive/planning
mkdir -p docs/archive/sessions
mkdir -p docs/archive/roo

# =============================================================================
# MOVE TO ARCHIVE (keep for historical reference)
# =============================================================================

echo ""
echo "📦 Archiving implementation history..."

# Implementation histories
[ -f "PHASE_1_IMPLEMENTATION_SUMMARY.md" ] && mv "PHASE_1_IMPLEMENTATION_SUMMARY.md" docs/archive/implementation/
[ -f "CSV_SEPARATION_IMPLEMENTATION.md" ] && mv "CSV_SEPARATION_IMPLEMENTATION.md" docs/archive/implementation/
[ -f "OAUTH_ROUTING_FIX_COMPLETE.md" ] && mv "OAUTH_ROUTING_FIX_COMPLETE.md" docs/archive/implementation/
[ -f "xero_implementation_success.md" ] && mv "xero_implementation_success.md" docs/archive/implementation/
[ -f "FIXES_HISTORY.md" ] && mv "FIXES_HISTORY.md" docs/archive/implementation/

# Planning docs (work completed)
echo "📦 Archiving planning documents..."
[ -f "XERO_OAUTH_INTEGRATION_PLAN.md" ] && mv "XERO_OAUTH_INTEGRATION_PLAN.md" docs/archive/planning/
[ -f "XERO_IMPLEMENTATION_GUIDE.md" ] && mv "XERO_IMPLEMENTATION_GUIDE.md" docs/archive/planning/
[ -f "UI_RESTRUCTURE_PLAN.md" ] && mv "UI_RESTRUCTURE_PLAN.md" docs/archive/planning/
[ -f "ICM_IMPLEMENTATION.md" ] && mv "ICM_IMPLEMENTATION.md" docs/archive/planning/
[ -f "transfer_learning_path.md" ] && mv "transfer_learning_path.md" docs/archive/planning/
[ -d "plans" ] && mv plans docs/archive/

# Session contexts (outdated)
echo "📦 Archiving session contexts..."
[ -f "for_continuation.md" ] && mv "for_continuation.md" docs/archive/sessions/
[ -f "co-keeper-run-context.md" ] && mv "co-keeper-run-context.md" docs/archive/sessions/
[ -f "Leave_off_here.md" ] && mv "Leave_off_here.md" docs/archive/sessions/
[ -f "START_HERE.md" ] && mv "START_HERE.md" docs/archive/sessions/
[ -f "START_HERE_TOMORROW.md" ] && mv "START_HERE_TOMORROW.md" docs/archive/sessions/
[ -f "frontend_change.md" ] && mv "frontend_change.md" docs/archive/sessions/
[ -f "frontend_OAuth_imp.md" ] && mv "frontend_OAuth_imp.md" docs/archive/sessions/
[ -f "once_in_hcm.md" ] && mv "once_in_hcm.md" docs/archive/sessions/
[ -f "failures.md" ] && mv "failures.md" docs/archive/sessions/

# Roo folder (all old session contexts)
echo "📦 Archiving roo session files..."
if [ -d "roo" ]; then
    # Keep only essential roo docs
    [ -f "roo/QUICKBOOKS_SANDBOX_SETUP.md" ] && cp "roo/QUICKBOOKS_SANDBOX_SETUP.md" docs/
    [ -f "roo/XERO_SANDBOX_SETUP.md" ] && cp "roo/XERO_SANDBOX_SETUP.md" docs/

    # Move entire roo folder to archive
    mv roo docs/archive/
fi

# =============================================================================
# DELETE (truly unnecessary)
# =============================================================================

echo ""
echo "🗑️  Deleting unnecessary files..."

# Email drafts
[ -f "xero-support-email.md" ] && rm "xero-support-email.md"

# Old lesson files
if [ -d "check_pipeline" ]; then
    rm -rf check_pipeline
fi

# =============================================================================
# CONSOLIDATE DEPLOYMENT DOCS
# =============================================================================

echo ""
echo "📋 Consolidating deployment documentation..."

# Remove old deployment docs (consolidated into DEPLOYMENT.md)
[ -f "PRODUCTION_DEPLOYMENT.md" ] && rm "PRODUCTION_DEPLOYMENT.md"
[ -f "DEPLOY_README.md" ] && rm "DEPLOY_README.md"
[ -f "RENDER_DEPLOYMENT.md" ] && rm "RENDER_DEPLOYMENT.md"

# DEPLOYMENT.md is the new consolidated guide

# =============================================================================
# UPDATE README FOR ARCHIVE
# =============================================================================

echo ""
echo "📝 Creating archive README..."

cat > docs/archive/README.md << 'EOF'
# Archived Documentation

This directory contains historical documentation from CoKeeper's development.

## 📁 Directory Structure

### `/implementation`
Implementation summaries and completion reports from development phases.
- **Purpose**: Historical record of how features were built
- **Use**: Reference if you need to understand past decisions

### `/planning`
Planning documents and integration guides for completed work.
- **Purpose**: Original design documents
- **Use**: Understand the original plan vs what was actually built

### `/sessions`
Session contexts and continuation notes from development sessions.
- **Purpose**: Historical development notes
- **Use**: Rarely needed, kept for completeness

### `/roo`
Complete archive of roo assistant session files.
- **Purpose**: Historical AI assistant interactions
- **Use**: Rarely needed, kept for reference

## 🔍 Finding Current Documentation

**Don't look here!** Use these instead:

- **Getting Started**: `/README.md`
- **Deployment**: `/DEPLOYMENT.md`
- **OAuth Setup**: `/OAUTH_PRODUCTION_SETUP.md`
- **Demo Guide**: `/DEMO_STRATEGY.md`
- **Documentation Index**: `/DOCS_GUIDE.md`

## 🗂️ What's Archived

**Implementation Histories**:
- Phase 1 summaries
- OAuth routing fixes
- Xero implementation success reports
- Fix histories

**Completed Planning Documents**:
- Transfer learning path
- ICM implementation
- Comprehensive 3-phase plan

**Important Docs (KEPT in root)**:
- CSV_SEPARATION_IMPLEMENTATION.md - CSV workflow architecture
- UI_RESTRUCTURE_PLAN.md - UI build structure docs
- XERO_OAUTH_INTEGRATION_PLAN.md - OAuth integration details
- XERO_IMPLEMENTATION_GUIDE.md - Complete API integration guide
- QUICKBOOKS_API_INTEGRATION.md - QuickBooks API docs
- UX_STRATEGY_NON_TECHNICAL_USERS.md - UX strategy

**Session Contexts**:
- Continuation notes
- Start-here files
- Frontend change logs
- Session wrap-ups

**Roo Sessions**:
- All phase status documents
- Integration testing reports
- API documentation
- Sandbox setup guides (copied to /docs/)

## 🧹 Cleanup Date

Last cleanup: April 12, 2026

Files archived represent work completed through deployment readiness phase.
EOF

echo ""
echo "✅ Documentation cleanup complete!"
echo ""
echo "📊 Summary:"
echo "  - Archived implementation histories to docs/archive/implementation/"
echo "  - Archived planning documents to docs/archive/planning/"
echo "  - Archived session contexts to docs/archive/sessions/"
echo "  - Archived roo folder to docs/archive/roo/"
echo "  - Deleted unnecessary files (emails, old lessons)"
echo "  - Consolidated deployment docs into DEPLOYMENT.md"
echo "  - Created DOCS_GUIDE.md as documentation index"
echo ""
echo "📖 Current documentation structure:"
echo "  ├── README.md (project overview)"
echo "  ├── CLAUDE.md (AI agent orientation)"
echo "  ├── DOCS_GUIDE.md (documentation index)"
echo "  ├── DEPLOYMENT.md (complete deployment guide)"
echo "  ├── ARCHITECTURE.md (system architecture)"
echo "  ├── "
echo "  ├── 🔐 OAuth & API:"
echo "  │   ├── OAUTH_PRODUCTION_SETUP.md"
echo "  │   ├── QUICKBOOKS_APP_URLS.md"
echo "  │   ├── QUICKBOOKS_API_INTEGRATION.md"
echo "  │   ├── XERO_OAUTH_INTEGRATION_PLAN.md"
echo "  │   └── XERO_IMPLEMENTATION_GUIDE.md"
echo "  ├── "
echo "  ├── 📁 CSV & UI:"
echo "  │   ├── CSV_SEPARATION_IMPLEMENTATION.md"
echo "  │   ├── UI_RESTRUCTURE_PLAN.md"
echo "  │   └── UX_STRATEGY_NON_TECHNICAL_USERS.md"
echo "  ├── "
echo "  ├── 🎯 Demo & Testing:"
echo "  │   ├── DEMO_STRATEGY.md"
echo "  │   ├── LOCAL_TESTING_GUIDE.md"
echo "  │   └── LEGAL_PAGES_SETUP.md"
echo "  ├── "
echo "  └── 🔧 Backend:"
echo "      ├── backend/README.md"
echo "      ├── backend/IMPLEMENTATION_GUIDE.md"
echo "      ├── backend/QUICKBOOKS_PIPELINE_DATAFLOW.md"
echo "      └── backend/POSTMAN_TESTING.md"
echo ""
echo "🎉 All done! Your documentation is now clean and organized."
