# Stage: Frontend Development

**Layer 2: What Do I Do?**
**Agent Role**: Frontend Developer
**Expected Duration**: 3-4 hours per major feature

---

## Purpose

Build Streamlit UI pages for CSV and API workflows, implementing the 2-step train/predict pattern with session state management and analytics dashboards.

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Current Frontend | ../../frontend/app.py | Full file | Working codebase to extend |
| UI Patterns | ../../UI_RESTRUCTURE_PLAN.md | Workflow sections | Design patterns to follow |
| UX Strategy | ../../UX_STRATEGY_NON_TECHNICAL_USERS.md | Full doc | Non-technical user requirements |
| Backend Endpoints | ../../backend/main.py | API routes | Endpoints to call |
| Session Context | ../../co-keeper-run-context.md | Session State section | Current state variables |

## Process

### Step 1: Define Session State Variables
- Add new session state variables to initialization block (around line 500-600)
- Follow naming convention: `[platform]_[purpose]` (e.g., `xero_model_trained`)
- Include: OAuth tokens, workflow progress, training metrics, predictions
- Set sensible defaults (False for booleans, None for objects)
- Document purpose in inline comments

### Step 2: Create Helper Functions
- Add helper functions before "PAGE DISPLAY FUNCTIONS" section
- Follow async pattern with `(result, error)` tuple returns
- Set appropriate timeouts (120s train, 60s predict, 10s OAuth)
- Include try/except with error logging
- Return standardized dict formats

### Step 3: Build Workflow Page
- Create `render_[platform]_[workflow]_page()` function
- Follow 2-step pattern: Purple card (Train) → Green card (Predict)
- Step 1 only shown if not yet complete
- Step 2 only accessible after Step 1 complete
- Use `st.container()` with gradient backgrounds for visual separation
- Include "Retrain" option to reset workflow

### Step 4: Add Analytics Dashboard
- Create results page with summary metrics (3-column layout)
- Add Plotly charts: tier distribution, confidence histogram, top categories
- Display full predictions DataFrame with filtering
- Use color coding: GREEN/YELLOW/RED for confidence tiers
- Show counts and percentages

### Step 5: Implement Export Features
- Add CSV download button (unfiltered full results)
- Add Excel download button with openpyxl  error handling
- Include tier multiselect filter (GREEN/YELLOW/RED)
- Add confidence slider (0.0-1.0 threshold)
- Show filtered match count before download

### Checkpoints

**After Step 2**:
- Test one helper function manually
- Verify error tuple returns work
- Check timeout values are reasonable

**After Step 3**:
- Verify purple/green gradient cards display correctly
- Test state transitions between steps
- Confirm retrain resets state properly

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Updated Frontend | ../../frontend/app.py | Python with Streamlit |
| UI Screenshots | output/ui-preview.md | Markdown with descriptions |
| Session State Map | output/session-state.md | Variable documentation |

## Audit Checklist

Run these checks before marking stage complete:

- [ ] **No syntax errors**: Run `get_errors` on frontend/app.py
- [ ] **Session state initialized**: All new variables in initialization block
- [ ] **Helper functions return tuples**: All backend calls return `(result, error)`
- [ ] **Error messages user-friendly**: No stack traces shown to end users
- [ ] **Gradient cards match pattern**: Purple for train, green for predict
- [ ] **Disabled states work**: Buttons disable after action (train, predict)
- [ ] **Charts render**: All Plotly charts have data and labels
- [ ] **Export works**: CSV and Excel downloads function correctly
- [ ] **Responsive layout**: Works on different screen sizes
- [ ] **Loading indicators**: Spinners shown during backend calls

## UI Pattern Requirements

### Visual Hierarchy
```
Title (st.title)
  ├── Description (st.markdown)
  ├── Step 1 Card (Purple gradient, training)
  │   ├── File uploader
  │   ├── Action button
  │   └── Results display
  └── Step 2 Card (Green gradient, prediction)
      ├── File uploader (conditional on Step 1 complete)
      ├── Action button
      └── Results summary
```

### Color Palette
- **Purple gradient**: `#667eea` to `#764ba2` (training actions)
- **Green gradient**: `#11998e` to `#38ef7d` (prediction actions)
- **Info cards**: Light blue background
- **Success**: Green text/background
- **Warning**: Yellow/orange text/background
- **Error**: Red text/background

### Button States
- **Primary action**: `type="primary"`, full width
- **After completion**: `disabled=True` with checkmark
- **Retrain**: Secondary button, smaller, below metrics

## Session State Patterns

### Workflow Progress
```python
'[platform]_model_trained': False  # Training complete flag
'[platform]_training_metrics': None  # Accuracy, categories, transactions
'[platform]_predictions': None  # Prediction results DataFrame
```

### OAuth State
```python
'[platform]_connected': False  # OAuth connection status
'[platform]_access_token': None  # Current access token
'[platform]_refresh_token': None  # For token refresh
'[platform]_tenant_id': None  # Organization/realm ID
'[platform]_token_expires_at': None  # Expiry timestamp
```

## Quality Floor

The frontend UI must:
1. Work for non-technical users (no jargon, clear instructions)
2. Show loading states during backend calls
3. Display errors in user-friendly language
4. Maintain state across page reloads (session_state)
5. Disable buttons after actions to prevent double-submission
6. Match existing UI patterns (purple/green, 2-step, metrics display)

## Next Stage

After frontend pages are complete:
→ Go to `stages/testing/CONTEXT.md` to validate end-to-end workflows

## References

- Streamlit Docs: https://docs.streamlit.io/
- Plotly Charts: https://plotly.com/python/
- Existing CSV Workflow: Lines 2070-2518 in `../../frontend/app.py`
- Existing QB API Workflow: Lines 600-800 in `../../frontend/app.py`
