# CoKeeper - Task Routing

**Layer 1: Where Do I Go?**
**Token Budget**: ~300 tokens

---

## Purpose

This file routes you to the appropriate stage based on the task you're working on. Read CLAUDE.md first for workspace orientation. Then use this file to find your stage context.

## Task → Stage Mapping

### Backend Development
**When**: Building API endpoints, ML pipelines, OAuth connectors
**Go to**: `stages/backend-development/CONTEXT.md`
**Examples**:
- "Create Xero OAuth connector"
- "Add /train_xero endpoint"
- "Implement token refresh logic"
- "Build ML pipeline class"

### Frontend Development
**When**: Building Streamlit UI, session state, helper functions
**Go to**: `stages/frontend-development/CONTEXT.md`
**Examples**:
- "Create Xero API workflow page"
- "Add CSV upload interface"
- "Build results dashboard with charts"
- "Update session state variables"

### OAuth Integration
**When**: Implementing OAuth flows, credential management, API connections
**Go to**: `stages/oauth-integration/CONTEXT.md`
**Examples**:
- "Set up Xero OAuth flow"
- "Handle authorization callback"
- "Implement token refresh"
- "Fetch transactions from API"

### ML Pipeline Work
**When**: Training models, prediction logic, feature engineering
**Go to**: `stages/ml-pipeline/CONTEXT.md`
**Examples**:
- "Adapt pipeline for Xero data format"
- "Add confidence calibration"
- "Implement vendor intelligence"
- "Create validation layers"

### Testing & QA
**When**: Testing workflows, validating functionality, finding bugs
**Go to**: `stages/testing/CONTEXT.md`
**Examples**:
- "Test CSV workflow end-to-end"
- "Verify OAuth flow works"
- "Check confidence tier assignments"
- "Validate error handling"

### Deployment
**When**: Deploying to Cloud Run, configuring environments, managing secrets
**Go to**: `stages/deployment/CONTEXT.md`
**Examples**:
- "Deploy to production"
- "Configure production OAuth credentials"
- "Set up environment variables"
- "Create Docker deployment"

### Documentation
**When**: Writing guides, updating markdown files, creating context docs
**Go to**: `stages/documentation/CONTEXT.md`
**Examples**:
- "Update implementation guide"
- "Document new API endpoint"
- "Create troubleshooting section"
- "Write session summary"

### Planning & Architecture
**When**: Creating implementation plans, architectural decisions, system design
**Go to**: `stages/planning/CONTEXT.md`
**Examples**:
- "Design Xero integration architecture"
- "Plan OAuth implementation phases"
- "Create deployment strategy"
- "Map data flow between components"

## Current Priority

**Active Stage**: Frontend Development (CSV Workflow Testing)
**Next Stage**: OAuth Integration (Xero Connector)

See todo list in current session context:
- [ ] Test complete CSV workflow
- [ ] Implement Xero OAuth connector (next priority)

## Multi-Stage Tasks

Some tasks span multiple stages. Handle them in sequence:

**"Implement Xero OAuth end-to-end"**:
1. Planning → Review `XERO_OAUTH_INTEGRATION_PLAN.md`
2. Backend → Build `xero_connector.py` (Stage 1)
3. Backend → Add API endpoints (Stage 2)
4. Frontend → Create UI pages (Stage 3)
5. Testing → Validate flow (Stage 4)
6. Documentation → Update guides (Stage 6)

**"Add new platform integration"**:
1. Planning → Create integration plan
2. ML Pipeline → Adapt data parsing
3. Backend → Build OAuth connector + endpoints
4. Frontend → Create workflow UI
5. Testing → End-to-end validation
6. Deployment → Production configuration

## Quick Reference

| I need to... | Go to stage... |
|-------------|---------------|
| Build API or service | Backend Development |
| Build UI or frontend | Frontend Development |
| Connect to external API | OAuth Integration |
| Train/predict ML models | ML Pipeline |
| Verify functionality | Testing & QA |
| Deploy to production | Deployment |
| Write documentation | Documentation |
| Design architecture | Planning |

## Stage Dependencies

Some stages depend on others being complete:

```
Planning → Backend → Frontend → Testing → Deployment
              ↓
         ML Pipeline
              ↓
      OAuth Integration
```

**Frontend** requires Backend endpoints to exist
**Testing** requires Frontend and Backend complete
**Deployment** requires Testing passed
**OAuth Integration** can happen in parallel with Frontend
**ML Pipeline** can happen in parallel with OAuth

## Session State Check

Before starting any stage, verify:
- [ ] CLAUDE.md read (orientation complete)
- [ ] This CONTEXT.md read (task routed)
- [ ] Stage CONTEXT.md loaded (instructions received)
- [ ] Required Layer 3 references identified
- [ ] Working artifacts (Layer 4) located

## What Happens Next

Once you know your stage:
1. Navigate to `stages/[your-stage]/CONTEXT.md`
2. Read the Inputs table to identify what files to load
3. Load Layer 3 references (if specified)
4. Load Layer 4 working artifacts (if specified)
5. Execute the Process steps
6. Write Outputs to the designated location
7. Run stage audits (if defined)
8. Mark stage complete in todo list

## Emergency Exits

**Stuck or unclear?** → Re-read CLAUDE.md for context
**Need project background?** → Read `co-keeper-run-context.md`
**OAuth questions?** → Read `XERO_OAUTH_INTEGRATION_PLAN.md` or `roo/XERO_SANDBOX_SETUP.md`
**ML pipeline questions?** → Read `XERO_IMPLEMENTATION_GUIDE.md`
**Deployment questions?** → Read `DEPLOYMENT_METHODS.md`

---

**Now go to your stage CONTEXT.md file and begin work.**
