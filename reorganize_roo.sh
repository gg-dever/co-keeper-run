#!/bin/bash
# Roo Documentation Reorganization Script
# Date: April 1, 2026

cd /Users/gagepiercegaubert/Desktop/career_projects/co-keeper-run

echo "🗂️  Reorganizing Roo documentation..."
echo ""

# Move Index & Status files (00-09)
echo "📋 Moving index & status files..."
mv -v DOCUMENTATION_INDEX.md roo/00_START_HERE.md
mv -v PROJECT_STATUS.md roo/01_PROJECT_STATUS.md
mv -v QUICK_START.md roo/02_QUICK_START.md
echo ""

# Rename Phase 1.5.2C files (already in roo/)
echo "📋 Renaming Phase 1.5.2C files..."
mv -v roo/2026-03-31_QB_OAUTH_SUCCESS.md roo/PHASE_1.5.2C_OAUTH_SUCCESS.md
mv -v roo/SESSION_COMPLETE_QB_OAUTH.md roo/PHASE_1.5.2C_SESSION_COMPLETE.md
mv -v roo/ROO_PHASE_1.5.2_INTEGRATION_TESTING.md roo/PHASE_1.5.2C_INTEGRATION_TESTING.md
echo ""

# Move Phase 1.5.3 files
echo "📋 Moving Phase 1.5.3 files..."
mv -v NEXT_SESSION_INSTRUCTIONS.md roo/PHASE_1.5.3_INSTRUCTIONS.md
mv -v TASK_CHECKLIST.md roo/PHASE_1.5.3_TASK_CHECKLIST.md
mv -v PHASE_1_5_3_COMPLETION.md roo/PHASE_1.5.3_COMPLETION.md
mv -v ML_PIPELINE_INTEGRATION_API.md roo/PHASE_1.5.3_API_DOCUMENTATION.md
echo ""

# Move Phase 1.5.4 prep file
echo "📋 Moving Phase 1.5.4 files..."
mv -v PHASE_1_5_4_PREP.md roo/PHASE_1.5.4_PREP.md
echo ""

# Archive old session files
echo "📋 Archiving old session files..."
mv -v roo/roo_session_1.md roo/ARCHIVE_roo_session_1.md
mv -v roo/ROO_FIX_INSTRUCTIONS.md roo/ARCHIVE_fix_instructions.md
echo ""

echo "✅ Reorganization complete!"
echo ""
echo "📁 New structure:"
ls -1 roo/ | grep -E "^(00_|01_|02_|PHASE_|ARCHIVE_)" | head -20
