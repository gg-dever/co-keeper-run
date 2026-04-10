# CoKeeper - AI Transaction Categorization System

**Layer 0: Workspace Orientation**
**Version**: 1.0
**Last Updated**: April 9, 2026
**Token Budget**: ~800 tokens

---

## Where Am I?

You are working in **CoKeeper**, a multi-platform AI-powered transaction categorization system. This workspace builds and maintains integrations for QuickBooks, Xero, and CSV workflows that train ML models on historical financial data and predict categories for new transactions.

## Project Architecture

```
CoKeeper System
├── Backend (FastAPI)
│   ├── ML Pipelines (QuickBooks, Xero)
│   ├── OAuth Connectors (QuickBooks, Xero)
│   └── API Endpoints (Train, Predict, OAuth)
├── Frontend (Streamlit)
│   ├── CSV Workflow (Upload → Train → Predict)
│   ├── API Workflow (QuickBooks, Xero OAuth)
│   └── Results/Review/Export Pages
└── Configuration
    ├── Environment Variables (.env)
    ├── OAuth Credentials (Sandbox/Production)
    └── VS Code Settings
```

## Core Value Proposition

**Problem**: Accountants and bookkeepers spend hours manually categorizing transactions in QuickBooks and Xero.

**Solution**: CoKeeper trains custom ML models on users' historical categorized data, then predicts categories for new transactions with confidence scores (GREEN/YELLOW/RED tiers).

**Workflows**:
1. **CSV Workflow**: Upload historical CSV → Train model → Upload new CSV → Get predictions
2. **API Workflow**: OAuth connect → Fetch transactions → Train → Predict → (Future: Push back to QB/Xero)

## Current State

### ✅ Completed
- QuickBooks CSV workflow (2-step train/predict)
- QuickBooks OAuth connector (`services/quickbooks_connector.py`)
- QuickBooks API workflow UI
- Xero CSV workflow (backend: `ml_pipeline_xero.py`)
- Xero ML pipeline and endpoints (`/train_xero`, `/predict_xero`)
- **Xero OAuth Integration Plan** (`XERO_OAUTH_INTEGRATION_PLAN.md`)

### 🔄 In Progress
- CSV workflow end-to-end testing
- Xero OAuth implementation

### ⏳ Pending
- Xero API workflow UI
- Production deployment (Cloud Run)
- Batch update features (write predictions back to QB/Xero)

## Agent Roles in This Workspace

When working in this codebase, you will act as one of these specialized agents depending on the task:

### 1. **Backend Developer**
**Domain**: Python, FastAPI, ML pipelines, OAuth
**Files**: `backend/main.py`, `backend/ml_pipeline_*.py`, `backend/services/*.py`
**Responsibilities**:
- Build and maintain API endpoints
- Implement OAuth connectors (QuickBooks, Xero)
- Create ML pipeline classes for transaction categorization
- Handle token management, refresh logic, API calls
- Write integration tests

**Context Layers**:
- Layer 2: `stages/backend-development/CONTEXT.md`
- Layer 3: `XERO_OAUTH_INTEGRATION_PLAN.md`, `XERO_IMPLEMENTATION_GUIDE.md`
- Layer 4: `backend/.env`, existing connector files

### 2. **Frontend Developer**
**Domain**: Python, Streamlit, session management, UI/UX
**Files**: `frontend/app.py`
**Responsibilities**:
- Build Streamlit pages for CSV and API workflows
- Implement 2-step train/predict UI pattern
- Manage session state for OAuth tokens and workflow progress
- Create helper functions for backend API calls
- Design analytics dashboards (charts, metrics, tables)

**Context Layers**:
- Layer 2: `stages/frontend-development/CONTEXT.md`
- Layer 3: `UI_RESTRUCTURE_PLAN.md`, `UX_STRATEGY_NON_TECHNICAL_USERS.md`
- Layer 4: Session state variables, existing workflow pages

### 3. **Integration Specialist**
**Domain**: OAuth 2.0, API design, QuickBooks/Xero platforms
**Files**: `backend/services/*_connector.py`, OAuth endpoints in `main.py`
**Responsibilities**:
- Implement OAuth authorization flows
- Handle token exchange, refresh, and expiry
- Fetch transactions from QuickBooks/Xero APIs
- Map platform-specific data formats to ML pipeline inputs
- Handle rate limiting and error recovery

**Context Layers**:
- Layer 2: `stages/oauth-integration/CONTEXT.md`
- Layer 3: `XERO_OAUTH_INTEGRATION_PLAN.md`, `roo/XERO_SANDBOX_SETUP.md`
- Layer 4: Existing `quickbooks_connector.py` as reference

### 4. **ML Pipeline Engineer**
**Domain**: Scikit-learn, feature engineering, confidence calibration
**Files**: `backend/ml_pipeline_qb.py`, `backend/ml_pipeline_xero.py`, `backend/src/features/*.py`
**Responsibilities**:
- Train Naive Bayes models on historical transaction data
- Generate predictions with confidence scores
- Implement 5-layer validation cascade for confidence tiers
- Feature extraction from vendor names, memos, amounts
- Vendor intelligence and rule-based classification

**Context Layers**:
- Layer 2: `stages/ml-pipeline/CONTEXT.md`
- Layer 3: `XERO_IMPLEMENTATION_GUIDE.md`, `backend/IMPLEMENTATION_GUIDE.md`
- Layer 4: Training CSVs, existing pipeline implementations

### 5. **Testing & QA**
**Domain**: Integration testing, OAuth flows, end-to-end workflows
**Files**: `backend/test_integration.py`, `test_before_deploy.py`
**Responsibilities**:
- Test CSV workflow (upload → train → predict → export)
- Test API workflow (OAuth → fetch → train → predict)
- Verify sandbox connections (QuickBooks, Xero)
- Validate confidence tier assignments
- Check error handling and edge cases

**Context Layers**:
- Layer 2: `stages/testing/CONTEXT.md`
- Layer 3: Test data requirements, expected outputs
- Layer 4: Sample CSVs, OAuth sandbox credentials

### 6. **DevOps Engineer**
**Domain**: Deployment, environment configuration, Docker, Cloud Run
**Files**: `Dockerfile`, `docker-compose.yml`, `deploy-*.sh`, `.env`
**Responsibilities**:
- Configure environment variables (.env files)
- Deploy to Cloud Run or container platforms
- Set up OAuth redirect URIs for production
- Manage secrets and credentials securely
- Monitor deployment health and logs

**Context Layers**:
- Layer 2: `stages/deployment/CONTEXT.md`
- Layer 3: `DEPLOYMENT_METHODS.md`, deployment scripts
- Layer 4: `.env.example`, production credentials

### 7. **Documentation Maintainer**
**Domain**: Technical writing, user guides, architecture docs
**Files**: `*.md` files, especially context and guide documents
**Responsibilities**:
- Update implementation guides as features are built
- Maintain session context documents
- Write setup and configuration guides
- Document API endpoints and data formats
- Create troubleshooting guides

**Context Layers**:
- Layer 2: `stages/documentation/CONTEXT.md`
- Layer 3: Existing markdown templates
- Layer 4: Session summaries, completion reports

## File Structure Reference

```
co-keeper-run/
├── CLAUDE.md                    # ← You are here (Layer 0)
├── CONTEXT.md                   # Layer 1: Task routing
├── stages/                      # Layer 2: Stage contracts
│   ├── 01-backend-development/
│   ├── 02-frontend-development/
│   ├── 03-oauth-integration/
│   ├── 04-ml-pipeline/
│   ├── 05-testing/
│   └── 06-deployment/
├── _config/                     # Layer 3: Brand, conventions
│   ├── coding-standards.md
│   └── ui-patterns.md
├── shared/                      # Layer 3: Cross-stage resources
│   ├── XERO_OAUTH_INTEGRATION_PLAN.md
│   ├── XERO_IMPLEMENTATION_GUIDE.md
│   └── co-keeper-run-context.md
├── backend/                     # Layer 4: Working code
│   ├── main.py
│   ├── ml_pipeline_qb.py
│   ├── ml_pipeline_xero.py
│   └── services/
│       ├── quickbooks_connector.py
│       └── xero_connector.py (pending)
└── frontend/                    # Layer 4: Working code
    └── app.py
```

## Key Technical Constraints

1. **Token Expiry**: QuickBooks (60 min), Xero (30 min) - Implement refresh before expiry
2. **Rate Limits**: QuickBooks (500/min), Xero (60/min) - Xero is much slower
3. **OAuth Environments**: Sandbox keys ≠ Production keys (currently using sandbox)
4. **Session State**: All workflow progress stored in Streamlit session state
5. **2-Step Pattern**: Train on historical data first, then predict on new data
6. **Confidence Tiers**: GREEN (high confidence), YELLOW (medium), RED (needs review)

## Coding Conventions

- **Backend**: FastAPI with type hints, async endpoints, structured logging
- **Frontend**: Streamlit with session state, gradient cards for visual hierarchy
- **OAuth**: Environment variables for credentials, never hardcode
- **ML Pipeline**: Reusable class structure, separate train/predict methods
- **UI Pattern**: Purple for training actions, green for prediction actions

## Quality Gates

Before completing any stage:
- [ ] No syntax errors (`get_errors` validation)
- [ ] Type hints on all function signatures
- [ ] Environment variables documented in `.env.example`
- [ ] Existing workflows still function (no regressions)
- [ ] Changes documented in relevant markdown files

## Success Metrics

- **CSV Workflow**: Train → Predict → Export in <3 minutes
- **API Workflow**: OAuth → Fetch → Train → Predict in <5 minutes
- **Model Accuracy**: >85% on training data
- **Confidence Distribution**: <35% RED tier (needs review)
- **User Experience**: Non-technical users can complete flow without developer help

## When to Load What

**Starting a backend task?** → Read `stages/backend-development/CONTEXT.md`
**Building frontend UI?** → Read `stages/frontend-development/CONTEXT.md`
**Implementing OAuth?** → Read `XERO_OAUTH_INTEGRATION_PLAN.md` + existing `quickbooks_connector.py`
**Testing workflows?** → Read `stages/testing/CONTEXT.md` + sample data requirements
**Deploying?** → Read `DEPLOYMENT_METHODS.md` + environment configuration

## Current Session Context

**Date**: April 5-9, 2026
**Focus**: CSV workflow implementation + Xero OAuth planning
**Recent Work**:
- Completed full CSV train/predict workflow (QuickBooks pipeline)
- Created comprehensive Xero OAuth integration plan
- Identified sandbox vs production credential requirements

**Next Actions**:
1. Test CSV workflow end-to-end
2. Implement Xero OAuth connector (Phase 1 of XERO_OAUTH_INTEGRATION_PLAN.md)
3. Build Xero API workflow UI (Phase 3 of plan)

See `co-keeper-run-context.md` for detailed session summary.

---

**Remember**: You are one agent reading the right files at the right moment. The folder structure and this orientation guide tell you what role to play and what context to load. Every intermediate output is a plain text file. Every stage is observable. Every decision is reversible.

**Start here when entering the workspace. Read CONTEXT.md next to understand task routing. Then load only the stage context you need for the current task.**
