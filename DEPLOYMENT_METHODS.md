# CoKeeper Deployment Methods

## Two Deployment Approaches

### 1. **gcloud CLI** (Shell Scripts)
**What:** Direct deployment using `gcloud run deploy` commands
**When:** Development, testing, rapid iteration
**Speed:** ~5 minutes
**State:** None (imperative)

```bash
make deploy-dev
# or
./deploy-simple.sh
```

### 2. **Terraform** (Infrastructure as Code)
**What:** Declarative infrastructure management
**When:** Production, team collaboration, tracking changes
**Speed:** ~7-10 minutes (includes planning)
**State:** Tracked in terraform.tfstate

```bash
cd terraform
terraform apply
```

---

## Relationship & Workflow

```
┌─────────────────────────────────────────────┐
│  Development Cycle                          │
│                                             │
│  1. Test Locally                            │
│     make test-local                         │
│                                             │
│  2. Quick Deploy (gcloud)                   │
│     make deploy-dev  ← Fast iteration       │
│                                             │
│  3. Verify & Iterate                        │
│     make logs-backend                       │
│     (repeat steps 1-3 until stable)         │
│                                             │
│  4. Production Deploy (Terraform)           │
│     cd terraform && terraform apply         │
│     ← Locks in state for production         │
│                                             │
│  5. Sync State (if manual changes made)     │
│     terraform refresh                       │
│     terraform plan  # Check drift           │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Key Differences

| Feature | gcloud CLI | Terraform |
|---------|-----------|-----------|
| **Speed** | ✅ Fast (5 min) | Slower (7-10 min) |
| **State Tracking** | ❌ None | ✅ Yes |
| **Drift Detection** | ❌ No | ✅ Yes |
| **Rollback** | ❌ Manual | ✅ Built-in |
| **Preview Changes** | ❌ No | ✅ terraform plan |
| **Team Collaboration** | ⚠️ Limited | ✅ Remote state |
| **Complexity** | ✅ Simple | ⚠️ Learning curve |

---

## Complementary Usage

**They work together, not against each other:**

1. **Same Resources:** Both manage the same Cloud Run services
2. **Import to Terraform:** Can import gcloud-deployed resources
3. **State Sync:** Terraform can detect manual gcloud changes
4. **Flexible:** Choose based on situation, not locked in

### Example Workflow

```bash
# Day 1: Fix a bug
make test-local           # Test locally
make deploy-dev           # Quick deploy (gcloud)
make logs-backend         # Verify fix

# Day 2: Another fix
make deploy-dev           # Quick deploy again

# Week 1: Stable release
cd terraform
terraform import ...      # Import manual changes
terraform plan            # Review state
terraform apply           # Lock in production config
```

---

## When to Use Each

### Use **gcloud CLI** when:
- 🔧 Testing a fix quickly
- 🐛 Debugging issues
- 🚀 Need immediate deployment
- 👤 Solo development
- ⚡ Avoiding 10-minute deploy cycles

### Use **Terraform** when:
- 🏢 Production deployments
- 👥 Team collaboration required
- 📊 Need audit trail of changes
- 🎯 Want rollback capability
- 🔍 Need drift detection
- 📝 Infrastructure as code documentation

---

## Command Reference

```bash
# Quick Deploy (gcloud)
make deploy-dev              # Deploy both services
make deploy-backend          # Backend only
make deploy-frontend         # Frontend only

# Production Deploy (Terraform)
cd terraform
terraform init               # First time only
terraform plan               # Preview changes
terraform apply              # Deploy with state tracking

# Utilities
make test-local              # Test before deploying
make logs-backend            # View backend logs
make status                  # Check service URLs
make import                  # Import existing to Terraform
```

---

## Best Practice

**Start with gcloud, graduate to Terraform:**

1. Use gcloud CLI during active development
2. Once stable, import to Terraform for production
3. Keep both available for flexibility
4. Use Makefile commands for consistency

This gives you **speed when you need it** and **safety when it matters**. 🎯
