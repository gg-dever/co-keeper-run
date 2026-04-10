# CoKeeper Conductor Guide - ICM Invocation Commands

**Purpose**: Quick reference for invoking the Interpretable Context Methodology (ICM) with low token usage
**Created**: April 9, 2026
**Use**: Reference these commands when starting AI agent tasks

---

## 🎯 Starting Fresh (First Read)

### "Read CLAUDE.md and help me with [task]"
Forces agent to start at Layer 0 (orientation), then cascade to CONTEXT.md → Stage CONTEXT.md → specific files

**Example**:
```
"Read CLAUDE.md and help me implement Xero OAuth"
```

### "Navigate to [stage name] and [action]"
Agent reads CLAUDE.md → CONTEXT.md → stage CONTEXT.md → only needed files

**Examples**:
```
"Navigate to oauth-integration and build the Xero connector"
"Navigate to frontend-development and create the Xero API workflow page"
"Navigate to testing and validate the CSV workflow"
```

---

## 🔄 Continuing Work (Mid-Stage)

### "Continue in [stage name]"
Agent loads current stage context, picks up where it left off

**Examples**:
```
"Continue in frontend-development"
"Continue in oauth-integration"
"Continue in testing"
```

### "Check [stage name] stage and [action]"
Agent goes directly to that stage's CONTEXT.md

**Examples**:
```
"Check testing stage and run CSV workflow tests"
"Check deployment stage and configure production environment"
"Check documentation stage and update the API guide"
```

---

## 📋 Following the Process

### "Execute [stage name] stage"
Agent reads that stage's CONTEXT.md and follows the Process steps

**Examples**:
```
"Execute oauth-integration stage"
"Execute testing stage"
"Execute deployment stage"
```

### "Run audit checklist for [stage name]"
Agent validates quality gates before marking complete

**Examples**:
```
"Run audit checklist for oauth-integration"
"Run audit checklist for frontend-development"
```

---

## 🎨 ICM-Specific Commands

### "Load only what's in the Inputs table"
Makes agent respect the scoped context loading

**Example**:
```
"Load only what's in the Inputs table for oauth-integration"
```

### "What does my stage CONTEXT.md say?"
Agent reads current stage instructions without loading extras

**Example**:
```
"What does my stage CONTEXT.md say for testing?"
```

### "Follow the ICM process for [task]"
Explicitly invokes the layered methodology

**Example**:
```
"Follow the ICM process for building the Xero OAuth connector"
```

---

## 💡 Best Practice Invocations

### ❌ DON'T Say This (High Token Usage)

```
"Build a Xero OAuth connector using all the documentation"
→ Loads everything: 30,000-50,000 tokens

"Here's all my code, docs, and context. Help me test."
→ Loads everything: massive context window

"Look at everything and build the frontend"
→ No scoping, loads entire codebase
```

### ✅ DO Say This (Low Token Usage)

```
"Read CLAUDE.md, then navigate to oauth-integration stage for Xero"
→ Loads only: CLAUDE.md + CONTEXT.md + oauth-integration/CONTEXT.md + Inputs table files
→ ~2,000-8,000 tokens

"Execute testing stage for CSV workflow"
→ Loads only: testing stage context + referenced test files
→ ~3,000-5,000 tokens

"Navigate to frontend-development and build Xero API page"
→ Loads only: frontend stage context + UI patterns + current app.py sections
→ ~4,000-6,000 tokens
```

---

## 📊 Token Budget Comparison

| Approach | Command | Tokens Loaded |
|----------|---------|---------------|
| **Traditional** | "Here's everything, build X" | 30,000-50,000 |
| **ICM** | "Navigate to [stage] and [action]" | 2,000-8,000 |
| **Savings** | — | **75-85% reduction** |

---

## 🚀 Quick Reference Card

| I Want To... | Command to Use |
|--------------|----------------|
| Start new task | `"Read CLAUDE.md and [task]"` |
| Continue current work | `"Continue in [stage]"` |
| Test functionality | `"Execute testing stage"` |
| Deploy to production | `"Navigate to deployment stage"` |
| Write documentation | `"Execute documentation stage"` |
| Build OAuth connector | `"Navigate to oauth-integration stage"` |
| Create UI pages | `"Navigate to frontend-development stage"` |
| Check code quality | `"Run audit checklist for [stage]"` |
| Review what to do | `"What does my stage CONTEXT.md say?"` |

---

## 🎯 Stage-Specific Commands

### Backend Development
```
"Navigate to backend-development and add /train_xero endpoint"
"Continue in backend-development with ML pipeline work"
"Run audit checklist for backend-development"
```

### Frontend Development
```
"Navigate to frontend-development and build Xero workflow page"
"Continue in frontend-development with results dashboard"
"Execute frontend-development stage"
```

### OAuth Integration
```
"Navigate to oauth-integration and build Xero connector"
"Continue in oauth-integration with token refresh"
"Run audit checklist for oauth-integration"
```

### ML Pipeline
```
"Navigate to ml-pipeline and adapt for Xero format"
"Continue in ml-pipeline with confidence calibration"
"Execute ml-pipeline stage"
```

### Testing
```
"Navigate to testing and validate CSV workflow"
"Execute testing stage for QuickBooks API"
"Run audit checklist for testing"
```

### Deployment
```
"Navigate to deployment and configure production"
"Execute deployment stage for Cloud Run"
"Continue in deployment with environment setup"
```

### Documentation
```
"Navigate to documentation and update API guide"
"Execute documentation stage for Xero OAuth"
"Continue in documentation with troubleshooting section"
```

### Planning
```
"Navigate to planning and design Xero architecture"
"Execute planning stage for new feature"
"Continue in planning with implementation phases"
```

---

## 📝 How the ICM Cascade Works

When you say: **"Navigate to oauth-integration and build Xero connector"**

Agent reads in sequence:
1. **Layer 0**: `CLAUDE.md` (~800 tokens) - Orientation, agent roles
2. **Layer 1**: `CONTEXT.md` (~300 tokens) - Task routing
3. **Layer 2**: `stages/oauth-integration/CONTEXT.md` (~500 tokens) - Stage instructions
4. **Layer 3**: Only files in Inputs table (~1,000-2,000 tokens) - References
5. **Layer 4**: Only working files specified (~1,000-3,000 tokens) - Current code

**Total**: ~2,000-8,000 tokens (focused, relevant context)

---

## 🔥 Pro Tips

### 1. Always Name the Stage Explicitly
✅ "Navigate to testing stage"
❌ "Help me test" (could load everything)

### 2. Use Action Verbs
✅ "Execute", "Navigate to", "Continue in", "Run audit"
❌ "I need help with..." (ambiguous, may load extra context)

### 3. Reference the ICM Structure
✅ "Follow the ICM process"
✅ "Load only what's in the Inputs table"
✅ "What does my stage CONTEXT.md say?"

### 4. Complete Stages Before Moving On
✅ "Run audit checklist for [current stage]"
Then: "Navigate to [next stage]"

### 5. When Stuck, Re-Orient
```
"Read CLAUDE.md again and remind me where I am"
```

---

## 🛠️ Troubleshooting

### Agent Loading Too Much Context?
Say: **"Load only what's in the Inputs table for [stage]"**

### Not Sure What Stage to Use?
Say: **"Read CONTEXT.md and tell me which stage I need"**

### Agent Seems Lost?
Say: **"Read CLAUDE.md and re-orient to the project"**

### Need to See Stage Instructions?
Say: **"What does my stage CONTEXT.md say for [stage]?"**

### Want to Validate Quality?
Say: **"Run audit checklist for [current stage]"**

---

## 🎓 Training Examples

### Example 1: Starting Xero OAuth Implementation
```
User: "Read CLAUDE.md, then navigate to oauth-integration stage for Xero"

Agent:
1. Reads CLAUDE.md (orientation)
2. Reads CONTEXT.md (routes to oauth-integration)
3. Reads stages/oauth-integration/CONTEXT.md
4. Loads XERO_OAUTH_INTEGRATION_PLAN.md (from Inputs table)
5. Loads quickbooks_connector.py (from Inputs table)
6. Follows Process steps 1-5
7. Creates xero_connector.py

Total tokens: ~4,000
```

### Example 2: Testing CSV Workflow
```
User: "Execute testing stage for CSV workflow"

Agent:
1. Reads CLAUDE.md (orientation)
2. Reads CONTEXT.md (routes to testing)
3. Reads stages/testing/CONTEXT.md
4. Loads sample CSV data (from Inputs table)
5. Follows Test 1 steps
6. Creates test-results.md in output/

Total tokens: ~3,500
```

### Example 3: Continuing Frontend Work
```
User: "Continue in frontend-development with results dashboard"

Agent:
1. Reads stages/frontend-development/CONTEXT.md
2. Loads current frontend/app.py sections (from Inputs table)
3. Loads UI_RESTRUCTURE_PLAN.md (from Inputs table)
4. Resumes at Step 4 (Add Analytics Dashboard)
5. Updates frontend/app.py

Total tokens: ~5,000
```

---

## 📚 Stage Dependency Flow

Follow this order for new features:

```
1. Planning → "Navigate to planning and design [feature]"
2. Backend → "Navigate to backend-development and build [component]"
3. Frontend → "Navigate to frontend-development and create [UI]"
4. Testing → "Execute testing stage for [workflow]"
5. Deployment → "Navigate to deployment and configure [environment]"
6. Documentation → "Execute documentation stage for [feature]"
```

Parallel stages (can do simultaneously):
- OAuth Integration (while Backend/Frontend in progress)
- ML Pipeline (while OAuth in progress)

---

## ✅ Success Checklist

Before completing any stage:
```
"Run audit checklist for [stage]"
```

Audit will verify:
- [ ] All quality gates passed
- [ ] Outputs created in correct location
- [ ] No syntax errors
- [ ] Documentation updated
- [ ] Ready for next stage

---

## 🎬 Session Start Template

Beginning a new session? Use this:

```
"Read CLAUDE.md and remind me:
1. Where we are in the project
2. What stage I should work on next
3. What the current priorities are"
```

Agent will:
1. Load orientation (Layer 0)
2. Check current state
3. Review todo list
4. Recommend next stage

---

## 📞 Quick Command Reference

| Command Pattern | Purpose | Token Budget |
|----------------|---------|--------------|
| `Read CLAUDE.md and [task]` | Start fresh | 800 + cascade |
| `Navigate to [stage] and [action]` | Stage-specific work | 2,000-8,000 |
| `Continue in [stage]` | Resume work | 3,000-6,000 |
| `Execute [stage] stage` | Run full process | 4,000-8,000 |
| `Run audit checklist for [stage]` | Quality check | 2,000-3,000 |
| `What does my stage CONTEXT.md say?` | Review instructions | 1,500-2,500 |
| `Load only what's in the Inputs table` | Minimize context | Varies |

---

**Remember**: The key to low token usage is **naming the stage explicitly**. This triggers the agent to read that stage's CONTEXT.md and follow its Inputs table, keeping context minimal and focused.

**Pro Tip**: Bookmark this guide and reference it at the start of each coding session!
