# CoKeeper ICM Structure - Implementation Summary

**Created**: April 9, 2026
**Methodology**: Interpretable Context Methodology (ICM)
**Author**: Claude (GitHub Copilot)

---

## What Was Created

Following the Interpretable Context Methodology, I've structured the CoKeeper workspace so that a single AI agent can navigate the codebase by reading the right files at the right moment. The folder structure tells the agent what role to play at each step.

## Five-Layer Context Architecture

### Layer 0: CLAUDE.md (~800 tokens)
**"Where am I?"** - Always loaded

- Workspace orientation
- Project architecture overview
- 7 specialized agent roles defined
- Core technical constraints
- Success metrics
- Quality gates

**Location**: `/CLAUDE.md`

### Layer 1: CONTEXT.md (~300 tokens)
**"Where do I go?"** - Read on entry

- Task → Stage mapping
- 8 stages defined with clear routing
- Current priority identification
- Quick reference table
- Stage dependency graph

**Location**: `/CONTEXT.md`

### Layer 2: Stage CONTEXT.md (~200-500 tokens each)
**"What do I do?"** - Read per-task

Created 3 core stage contracts:
1. **OAuth Integration** (`stages/oauth-integration/CONTEXT.md`)
2. **Frontend Development** (`stages/frontend-development/CONTEXT.md`)
3. **Testing & QA** (`stages/testing/CONTEXT.md`)

Each includes:
- Inputs table (what files to load)
- Process steps (what to do)
- Outputs specification (what to produce)
- Audit checklist (quality gates)
- Checkpoints (human review points)

**Locations**: `stages/[stage-name]/CONTEXT.md`

### Layer 3: Reference Material (Variable)
**"What rules apply?"** - Loaded selectively

Existing project documentation that stages reference:
- `XERO_OAUTH_INTEGRATION_PLAN.md` - Complete Xero implementation spec
- `XERO_IMPLEMENTATION_GUIDE.md` - ML pipeline adaptation guide
- `roo/XERO_SANDBOX_SETUP.md` - Developer platform setup
- `UI_RESTRUCTURE_PLAN.md` - Frontend design patterns
- `UX_STRATEGY_NON_TECHNICAL_USERS.md` - User experience requirements
- `DEPLOYMENT_METHODS.md` - Deployment strategies
- Existing code: `backend/services/quickbooks_connector.py` (reference pattern)

### Layer 4: Working Artifacts (Variable)
**"What am I working with?"** - Loaded selectively

Current working code and data:
- `backend/main.py` - FastAPI application
- `backend/ml_pipeline_qb.py`, `ml_pipeline_xero.py` - ML pipelines
- `frontend/app.py` - Streamlit UI
- `backend/.env` - Environment configuration
- `CSV_data/` - Training and test data

---

## Stage Directory Structure

```
co-keeper-run/
├── CLAUDE.md                    # Layer 0: Workspace orientation
├── CONTEXT.md                   # Layer 1: Task routing
├── stages/                      # Layer 2: Stage contracts
│   ├── backend-development/
│   │   ├── CONTEXT.md          # Build APIs, ML pipelines
│   │   ├── references/         # Stage-specific docs
│   │   └── output/             # Generated code/artifacts
│   ├── frontend-development/
│   │   ├── CONTEXT.md          # Build Streamlit UI
│   │   ├── references/
│   │   └── output/
│   ├── oauth-integration/
│   │   ├── CONTEXT.md          # OAuth connectors
│   │   ├── references/
│   │   └── output/
│   ├── ml-pipeline/
│   │   ├── CONTEXT.md          # ML model work
│   │   ├── references/
│   │   └── output/
│   ├── testing/
│   │   ├── CONTEXT.md          # QA and validation
│   │   ├── references/
│   │   └── output/
│   ├── deployment/
│   │   ├── CONTEXT.md          # Production deployment
│   │   ├── references/
│   │   └── output/
│   ├── documentation/
│   │   ├── CONTEXT.md          # Technical writing
│   │   ├── references/
│   │   └── output/
│   └── planning/
│       ├── CONTEXT.md          # Architecture & design
│       ├── references/
│       └── output/
├── backend/                     # Layer 4: Working code
├── frontend/                    # Layer 4: Working code
└── [other project files]        # Layer 3 & 4: References and artifacts
```

---

## Seven Agent Roles Defined

Each role loads only the context it needs:

1. **Backend Developer** - APIs, ML pipelines, OAuth connectors
2. **Frontend Developer** - Streamlit UI, session management
3. **Integration Specialist** - OAuth flows, API connections
4. **ML Pipeline Engineer** - Model training, predictions, features
5. **Testing & QA** - Workflow validation, bug reports
6. **DevOps Engineer** - Deployment, environment configuration
7. **Documentation Maintainer** - Guides, API docs, troubleshooting

---

## How It Works in Practice

### Example: Implementing Xero OAuth

**Step 1**: Agent reads `CLAUDE.md`
- Understands this is the CoKeeper transaction categorization system
- Sees Xero OAuth is a pending feature
- Identifies as needing "Integration Specialist" role

**Step 2**: Agent reads `CONTEXT.md`
- Maps task "Implement Xero OAuth" to `oauth-integration` stage
- Navigates to `stages/oauth-integration/CONTEXT.md`

**Step 3**: Agent reads Stage CONTEXT.md
- Loads Inputs table: `XERO_OAUTH_INTEGRATION_PLAN.md`, `quickbooks_connector.py`
- Follows Process steps 1-5
- Executes checkpoints after Steps 2 and 3
- Produces Outputs: `xero_connector.py`, updated `.env`

**Step 4**: Agent runs Audit Checklist
- Validates 10 quality checks
- Ensures credentials validation, error handling, type hints, etc.

**Step 5**: Agent marks complete, routes to next stage
- Reads `CONTEXT.md` to find next stage: `backend-development`
- Loads that stage's CONTEXT.md to add API endpoints

**Total context loaded**: ~2,500 tokens (not 30,000+)

---

## Key Principles Applied

### 1. One Stage, One Job
- OAuth integration doesn't also build frontend
- Frontend development doesn't also handle deployment
- Each stage has a single, clear responsibility

### 2. Plain Text Interface
- All context is markdown files
- All outputs can be edited by humans before next stage
- No binary formats, no database dependencies

### 3. Layered Context Loading
- Agent reads 0 → 1 → 2, then selectively loads 3 & 4
- Less irrelevant context = better model performance
- Typical total: 2,000-8,000 tokens per stage

### 4. Every Output is an Edit Surface
- `output/` folders contain generated artifacts
- Humans can edit any file before next stage runs
- Next stage picks up whatever the human left there

### 5. Configure the Factory, Not the Product
- Agent roles are defined once in CLAUDE.md
- Stage contracts are reusable across many runs
- Project-specific context in Layer 3 references

---

## Observability by Default

The entire system is glass-box:
- Every stage's input is a file you can read
- Every stage's process is documented in CONTEXT.md
- Every stage's output is a plain text file
- No logging layer needed - just open folders and read

If a stage fails:
1. Read its CONTEXT.md to see instructions
2. Check Inputs table to see what it loaded
3. Look in output/ to see what it produced
4. Edit the output and re-run next stage

---

## Portability

This workspace is:
- ✅ Self-contained (carries all its prompts and context)
- ✅ Version-controllable (all plain text, no binaries)
- ✅ Transferable (copy folder = copy entire system)
- ✅ Framework-independent (no CrewAI, LangChain, etc.)
- ✅ Human-editable (any text editor works)

---

## What Makes This Different from a Framework

**Traditional Multi-Agent Framework**:
```
[Orchestrator]
    ↓
[Agent 1] → [Agent 2] → [Agent 3]
    ↓          ↓          ↓
[Memory] ← [Tools] ← [State]
```
- Requires deployment
- Abstractions to understand
- Code changes to modify workflow
- Often 30,000-50,000 token contexts

**ICM Approach**:
```
[One Agent] reads [Right Files] at [Right Moment]
    ↓
Folder structure = workflow order
File reads = context scoping
Output files = state management
```
- No deployment (just folders)
- No abstractions (just files)
- Modify workflow = edit markdown files
- Typical 2,000-8,000 token contexts

---

## Stage Completion Tracking

Use the todo list to track progress through stages:

```markdown
Current Todo List:
- [x] Create ICM structure (CLAUDE.md, CONTEXT.md, stage contracts)
- [ ] Test complete CSV workflow (→ stages/testing/)
- [ ] Implement Xero OAuth connector (→ stages/oauth-integration/)
- [ ] Build Xero API workflow UI (→ stages/frontend-development/)
```

---

## Next Steps for This Workspace

### Immediate (Next Session)
1. Navigate to `stages/testing/CONTEXT.md`
2. Execute CSV workflow tests
3. Document results in `stages/testing/output/test-results.md`

### Short-Term (This Week)
1. Navigate to `stages/oauth-integration/CONTEXT.md`
2. Build Xero OAuth connector following the stage contract
3. Output to `backend/services/xero_connector.py`

### Medium-Term (This Month)
1. Complete all 8 stages for Xero integration
2. Validate end-to-end Xero workflow
3. Deploy to production (stages/deployment/)

---

## Extending the ICM Structure

### To Add a New Stage:
1. Create `stages/new-stage-name/`
2. Add `CONTEXT.md` with Inputs/Process/Outputs
3. Create `references/` and `output/` subdirectories
4. Update `CONTEXT.md` (Layer 1) routing table
5. Add stage to dependency graph

### To Add a New Platform (e.g., Sage):
1. Clone Xero integration stages as template
2. Update stage CONTEXT.md files with Sage specifics
3. Add Sage references to Layer 3
4. Execute stages in sequence
5. Output artifacts accumulate in output/ folders

---

## Quality Assurance

Every stage contract includes:
- **Inputs table**: Explicit file loading (prevents context bloat)
- **Process steps**: Numbered, sequential actions
- **Checkpoints**: Human review points in creative stages
- **Audit checklist**: 10-15 quality gates before completion
- **Outputs specification**: What artifacts to produce and where

This ensures:
- Reproducible results
- Consistent quality
- Clear success criteria
- Auditable process

---

## Documentation Maintenance

### When Code Changes:
- Update relevant stage CONTEXT.md if process changes
- Update Layer 3 references if rules change
- Keep CLAUDE.md current with major architectural changes

### When Adding Features:
- Create new stage or extend existing
- Document in appropriate CONTEXT.md
- Add references to Layer 3 if reusable knowledge

### When Bugs Are Found:
- Document in `stages/testing/output/bugs-found.md`
- Fix in appropriate stage (backend/frontend/integration)
- Re-run testing stage to validate fix

---

## Success Metrics for ICM Implementation

✅ **Structure Created**:
- Layer 0 (CLAUDE.md): Workspace orientation complete
- Layer 1 (CONTEXT.md): Task routing functional
- Layer 2 (Stage CONTEXT.md): 3 core stages documented
- Layer 3 (References): Existing docs identified and mapped
- Layer 4 (Artifacts): Working code locations specified

✅ **Agent Roles Defined**:
- 7 specialized roles with clear domains
- Each role knows what files to read
- Context budgets defined and reasonable

✅ **Quality Gates Established**:
- Every stage has audit checklist
- Checkpoints defined for creative stages
- Output specifications clear

✅ **Observability Achieved**:
- All stages visible as folders
- All context visible as files
- All outputs editable before next stage

✅ **Portability Maintained**:
- No framework dependencies
- Plain text throughout
- Self-contained workspace

---

## Credits

**Methodology**: Interpretable Context Methodology (ICM) by Jake Van Clief
**Implementation**: Claude (GitHub Copilot) - April 9, 2026
**Project**: CoKeeper - AI Transaction Categorization System
**Token Budget**: ~5,000 tokens total for all Layer 0-2 context

---

## How to Use This Structure

**For AI Agents**:
1. Always start with CLAUDE.md (orientation)
2. Read CONTEXT.md (task routing)
3. Navigate to appropriate stage CONTEXT.md
4. Load only the Layer 3/4 files specified in Inputs table
5. Follow Process steps
6. Run Audit checklist
7. Write Outputs to specified locations

**For Humans**:
1. Read this document to understand the system
2. Navigate to stages/ to see available workflows
3. Edit any output file before next stage runs
4. Add checkpoints where human review is needed
5. Update stage contracts as workflows evolve

**For Teams**:
1. Commit ICM structure to git
2. Each team member can work on different stages
3. Stage outputs are handoff points
4. Merge conflicts are just markdown file conflicts
5. No deploy/redeploy cycle needed

---

**The workspace is now ready for structured, reproducible, human-in-the-loop AI-assisted development.**
