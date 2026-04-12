# CoKeeper Documentation Guide

**Last Updated**: April 12, 2026

This guide helps you navigate CoKeeper's documentation.

---

## 📚 Documentation Structure

### **🚀 Getting Started** (Start Here!)

1. **[README.md](README.md)** - Project overview, quick start, deployment options
2. **[CLAUDE.md](CLAUDE.md)** - AI agent workspace orientation (for Claude/AI assistants)
3. **[LOCAL_TESTING_GUIDE.md](LOCAL_TESTING_GUIDE.md)** - Run locally for development

### **☁️ Deployment**

**Primary Guide**: [DEPLOYMENT.md](DEPLOYMENT.md) - Complete deployment guide (all platforms)

Includes:
- Render.com (free tier, recommended)
- DigitalOcean (manual, $6/month)
- Google Cloud Run (pay-per-use)
- Docker Compose (self-hosted)

### **🔐 OAuth Configuration**

1. **[OAUTH_PRODUCTION_SETUP.md](OAUTH_PRODUCTION_SETUP.md)** - Switch from sandbox to production OAuth
2. **[QUICKBOOKS_APP_URLS.md](QUICKBOOKS_APP_URLS.md)** - QuickBooks app URL configuration
3. **[LEGAL_PAGES_SETUP.md](LEGAL_PAGES_SETUP.md)** - Terms/Privacy policy setup for QB approval

### **🔌 API Integration**

1. **[QUICKBOOKS_API_INTEGRATION.md](QUICKBOOKS_API_INTEGRATION.md)** - QuickBooks API integration guide
2. **[XERO_OAUTH_INTEGRATION_PLAN.md](XERO_OAUTH_INTEGRATION_PLAN.md)** - Xero OAuth integration plan
3. **[XERO_IMPLEMENTATION_GUIDE.md](XERO_IMPLEMENTATION_GUIDE.md)** - Complete Xero API implementation

### **📁 CSV Workflows & UI**

1. **[CSV_SEPARATION_IMPLEMENTATION.md](CSV_SEPARATION_IMPLEMENTATION.md)** - CSV workflow architecture & separation
2. **[UI_RESTRUCTURE_PLAN.md](UI_RESTRUCTURE_PLAN.md)** - UI build structure & navigation
3. **[UX_STRATEGY_NON_TECHNICAL_USERS.md](UX_STRATEGY_NON_TECHNICAL_USERS.md)** - UX strategy for non-technical users

### **🎯 Demo & Marketing**

1. **[DEMO_STRATEGY.md](DEMO_STRATEGY.md)** - How to demo CoKeeper (CSV workflow, Xero OAuth)

### **🏗️ Architecture & Development**

1. **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture overview
2. **[backend/README.md](backend/README.md)** - Backend API documentation
3. **[backend/IMPLEMENTATION_GUIDE.md](backend/IMPLEMENTATION_GUIDE.md)** - Backend implementation details
4. **[backend/QUICKBOOKS_PIPELINE_DATAFLOW.md](backend/QUICKBOOKS_PIPELINE_DATAFLOW.md)** - ML pipeline dataflow

### **🧪 Testing**

1. **[backend/POSTMAN_TESTING.md](backend/POSTMAN_TESTING.md)** - API testing with Postman
2. **[test_before_deploy.py](test_before_deploy.py)** - Pre-deployment tests

---

## 📖 Quick Links by Task

### **"I want to deploy CoKeeper"**
→ [DEPLOYMENT.md](DEPLOYMENT.md)

### **"I want to enable real QuickBooks accounts"**
→ [OAUTH_PRODUCTION_SETUP.md](OAUTH_PRODUCTION_SETUP.md)

### **"I want to demo CoKeeper to someone"**
→ [DEMO_STRATEGY.md](DEMO_STRATEGY.md)

### **"I want to develop/modify CoKeeper"**
→ [LOCAL_TESTING_GUIDE.md](LOCAL_TESTING_GUIDE.md) + [backend/IMPLEMENTATION_GUIDE.md](backend/IMPLEMENTATION_GUIDE.md)

### **"I'm an AI agent joining this project"**
→ [CLAUDE.md](CLAUDE.md) (Layer 0 orientation)

---

## 🗑️ Archived Documentation

The following files have been archived (in `/docs/archive/`) as they represent completed work:
- Implementation plans (work completed)
- Session contexts (outdated)
- Fix histories (historical)

See [docs/archive/README.md](docs/archive/README.md) for archived documentation.
