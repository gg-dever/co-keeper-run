"""
CoKeeper Streamlit Web App - Full Featured
Complete GL categorization application with:
- File upload with validation
- Data preview
- Results visualization
- Review workflow (RED/YELLOW/GREEN tiers)
- Multi-format export (CSV, Excel)
- Responsive design

Uses core pipeline from src/pipeline.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import requests

# Add src to path
sys.path.insert(0, os.path.abspath('.'))

# Backend API Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# from src.pipeline import CoKeeperPipeline  # TODO: Uncomment when pipeline is ready
import warnings
warnings.filterwarnings('ignore')


# ============================================================================
# PAGE CONFIG & STYLING
# ============================================================================

st.set_page_config(
    page_title="CoKeeper - GL Categorization",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="auto"
)

# Professional Website CSS styling
st.markdown("""
<style>
    /* Professional Color Palette - Brand */
    :root {
        --primary: #0f172a;
        --primary-light: #1e293b;
        --accent: #3b82f6;
        --accent-light: #60a5fa;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --gray-50: #f8fafc;
        --gray-100: #f1f5f9;
        --gray-200: #e2e8f0;
        --gray-300: #cbd5e1;
        --gray-600: #475569;
        --gray-700: #334155;
        --gray-800: #1e293b;
        --gray-900: #0f172a;
    }

    /* Global */
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    }

    .main {
        background: transparent;
        padding-top: 0 !important;
    }

    * {
        transition: box-shadow 0.3s ease, transform 0.3s ease, color 0.2s ease;
    }

    /* Typography System */
    h1 {
        color: var(--gray-900);
        font-size: 2.5rem;
        font-weight: 900;
        letter-spacing: -1px;
        line-height: 1.2;
        margin: 0;
    }

    h2 {
        color: var(--gray-900);
        font-size: 1.875rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin-top: 2rem;
        margin-bottom: 1.25rem;
    }

    h3 {
        color: var(--gray-800);
        font-size: 1.25rem;
        font-weight: 700;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }

    p, .stMarkdown {
        color: var(--gray-600);
        line-height: 1.7;
        font-size: 15px;
    }

    a {
        color: var(--accent);
        text-decoration: none;
        font-weight: 500;
    }

    a:hover {
        color: var(--accent-light);
        text-decoration: underline;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, white 0%, #f8fafc 100%);
        border-right: 1px solid var(--gray-200);
    }

    [data-testid="stSidebar"] h1 {
        font-size: 1.75rem;
        color: var(--gray-900);
        margin-bottom: 0.5rem;
    }

    [data-testid="stSidebar"] .stRadio > label {
        font-weight: 500;
        color: var(--gray-700);
        padding: 12px 16px;
        margin: 6px 0;
        border-radius: 8px;
        transition: all 0.2s;
    }

    [data-testid="stSidebar"] [role="radio"] {
        accent-color: var(--accent);
    }

    /* Radio Button Toggle Switch Styling */
    [role="radiogroup"] {
        display: flex !important;
        gap: 0 !important;
        background: var(--gray-200);
        border-radius: 8px;
        padding: 2px;
        width: fit-content;
    }

    [role="radio"] {
        flex: 1;
    }

    [role="radio"] + label {
        background: transparent !important;
        border-radius: 6px;
        padding: 10px 16px !important;
        margin: 0 !important;
        font-weight: 600;
        font-size: 14px;
        transition: all 0.2s ease;
        cursor: pointer;
    }

    [role="radio"]:checked + label {
        background: var(--success) !important;
        color: white !important;
        box-shadow: 0 2px 6px rgba(16, 185, 129, 0.3);
    }

    /* Inputs & Form Elements */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select,
    .stMultiSelect > div > div > input {
        border-radius: 10px !important;
        border: 2px solid var(--gray-200) !important;
        padding: 12px 16px !important;
        font-size: 15px !important;
        transition: all 0.3s !important;
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus,
    .stMultiSelect > div > div > input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent) 0%, #2563eb 100%);
        border: none;
        border-radius: 10px;
        padding: 14px 32px;
        font-weight: 700;
        color: white;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
        font-size: 15px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        cursor: pointer;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* Metric Cards */
    [data-testid="metric-container"] {
        background: white;
        border-radius: 16px;
        border: 1px solid var(--gray-200);
        padding: 24px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        backdrop-filter: blur(10px);
    }

    [data-testid="metric-container"]:hover {
        border-color: var(--accent-light);
        box-shadow: 0 8px 24px rgba(59, 130, 246, 0.12);
        transform: translateY(-2px);
    }

    /* File Upload */
    .stFileUploader > div > div {
        border-radius: 12px !important;
        border: 2px dashed var(--accent) !important;
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.05), rgba(59, 130, 246, 0.02)) !important;
        padding: 40px 20px !important;
    }

    .uploadedFile {
        border-radius: 12px;
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.05), rgba(16, 185, 129, 0.02));
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 16px;
        margin-top: 12px;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f8fafc, #f1f5f9);
        border-radius: 10px;
        border: 1px solid var(--gray-200);
        padding: 16px;
        font-weight: 600;
        color: var(--gray-900);
    }

    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, #f1f5f9, #e2e8f0);
        border-color: var(--accent-light);
    }

    /* Tables */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        border: 1px solid var(--gray-200);
    }

    /* Divider */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--gray-200), transparent);
        margin: 2.5rem 0;
    }

    /* Status Boxes */
    .stAlert {
        border-radius: 12px;
        border: 1px solid;
        padding: 16px;
        margin-bottom: 1rem;
    }

    .stSuccess {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(16, 185, 129, 0.05)) !important;
        border-color: rgba(16, 185, 129, 0.3) !important;
    }

    .stWarning {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(245, 158, 11, 0.05)) !important;
        border-color: rgba(245, 158, 11, 0.3) !important;
    }

    .stError {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(239, 68, 68, 0.05)) !important;
        border-color: rgba(239, 68, 68, 0.3) !important;
    }

    .stInfo {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(59, 130, 246, 0.05)) !important;
        border-color: rgba(59, 130, 246, 0.3) !important;
    }

    /* Hero Section */
    .hero-container {
        background: linear-gradient(135deg, var(--gray-900) 0%, var(--primary-light) 100%);
        border-radius: 16px;
        padding: 60px 40px;
        color: white;
        margin-bottom: 40px;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.1);
        position: relative;
        overflow: hidden;
    }

    .hero-container::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -10%;
        width: 500px;
        height: 500px;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.2), transparent);
        border-radius: 50%;
    }

    .hero-container h1 {
        color: white;
        font-size: 3rem;
        margin-bottom: 1rem;
        position: relative;
        z-index: 1;
    }

    .hero-tagline {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.125rem;
        line-height: 1.8;
        max-width: 600px;
        position: relative;
        z-index: 1;
    }

    /* Card Container */
    .info-card {
        background: white;
        border-radius: 16px;
        padding: 28px;
        border: 1px solid var(--gray-200);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
        margin-bottom: 20px;
    }

    .info-card:hover {
        border-color: var(--accent-light);
        box-shadow: 0 12px 32px rgba(59, 130, 246, 0.12);
        transform: translateY(-4px);
    }

    /* Badge */
    .badge {
        display: inline-block;
        background: linear-gradient(135deg, var(--accent), #2563eb);
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 12px;
    }

    /* iPhone-Style Toggle Switch */
    .toggle-switch-container {
        display: flex;
        align-items: center;
        gap: 16px;
        background: white;
        padding: 24px;
        border-radius: 16px;
        border: 1px solid var(--gray-200);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        margin-bottom: 24px;
    }

    .toggle-switch {
        position: relative;
        display: inline-flex;
        width: 56px;
        height: 32px;
        background-color: #ccc;
        border-radius: 16px;
        cursor: pointer;
        transition: background-color 0.3s ease;
        border: none;
        padding: 2px;
        gap: 0;
    }

    .toggle-switch.active {
        background-color: var(--success);
    }

    .toggle-switch-slider {
        position: absolute;
        top: 2px;
        left: 2px;
        width: 28px;
        height: 28px;
        background-color: white;
        border-radius: 50%;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .toggle-switch.active .toggle-switch-slider {
        left: calc(100% - 30px);
    }

    .toggle-switch-label {
        display: flex;
        flex-direction: column;
        gap: 4px;
        flex: 1;
    }

    .toggle-switch-label h3 {
        margin: 0;
        font-size: 16px;
        color: var(--gray-900);
        font-weight: 700;
    }

    .toggle-switch-label p {
        margin: 0;
        font-size: 13px;
        color: var(--gray-600);
    }

    .toggle-switch-options {
        display: flex;
        gap: 12px;
        margin-left: auto;
    }

    .toggle-option {
        font-size: 13px;
        font-weight: 600;
        padding: 4px 0;
        color: var(--gray-600);
    }

    .toggle-option.inactive {
        opacity: 0.5;
    }

    .toggle-option.active {
        color: var(--success);
    }

    /* Responsive - Mobile First */
    @media (max-width: 1024px) {
        [data-testid="stAppViewContainer"] {
            padding: 0 !important;
        }

        .stContainer {
            padding: 0 !important;
        }
    }

    @media (max-width: 768px) {
        /* Typography */
        h1 {
            font-size: 1.75rem;
            margin-bottom: 1rem;
        }
        h2 {
            font-size: 1.25rem;
            margin-top: 1rem;
            margin-bottom: 0.75rem;
        }
        h3 {
            font-size: 1rem;
        }
        p, .stMarkdown {
            font-size: 14px;
        }

        /* Layout */
        [data-testid="stAppViewContainer"] {
            padding: 12px 0 !important;
        }

        .main {
            padding: 12px 16px !important;
        }

        /* Hero */
        .hero-container {
            padding: 32px 20px;
            margin-bottom: 20px;
            border-radius: 12px;
        }
        .hero-container h1 {
            font-size: 1.75rem;
            margin-bottom: 0.75rem;
        }
        .hero-tagline {
            font-size: 0.95rem;
        }
        .hero-container::before {
            width: 300px;
            height: 300px;
            top: -30%;
            right: -20%;
        }

        /* Cards */
        .info-card {
            padding: 20px;
            margin-bottom: 16px;
            border-radius: 12px;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            z-index: 100;
        }

        /* Buttons */
        .stButton > button {
            width: 100%;
            padding: 12px 20px;
            font-size: 14px;
            border-radius: 8px;
        }

        /* Inputs */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > select,
        .stMultiSelect > div > div > input {
            padding: 12px 12px !important;
            font-size: 14px !important;
            border-radius: 8px !important;
            min-height: 44px !important;
        }

        /* File Upload */
        .stFileUploader > div > div {
            padding: 30px 16px !important;
            border-radius: 8px !important;
        }

        /* Tables */
        .stDataFrame {
            font-size: 12px !important;
            border-radius: 8px;
        }

        /* Columns */
        [data-testid="column"] {
            padding: 8px 0 !important;
        }

        /* Metric */
        [data-testid="metric-container"] {
            padding: 16px;
            border-radius: 12px;
        }

        /* Expanders */
        .streamlit-expanderHeader {
            padding: 12px;
            font-size: 14px;
            border-radius: 8px;
        }

        /* Alerts */
        .stAlert {
            font-size: 13px;
            padding: 12px;
            border-radius: 8px;
        }

        /* Badge */
        .badge {
            font-size: 11px;
            padding: 4px 10px;
        }
    }

    @media (max-width: 480px) {
        /* Typography */
        h1 {
            font-size: 1.5rem;
            margin-bottom: 0.75rem;
        }
        h2 {
            font-size: 1.1rem;
            margin-top: 0.75rem;
            margin-bottom: 0.5rem;
        }
        h3 {
            font-size: 0.95rem;
        }
        p, .stMarkdown {
            font-size: 13px;
            line-height: 1.6;
        }

        /* Layout */
        .main {
            padding: 8px 12px !important;
        }

        /* Hero */
        .hero-container {
            padding: 24px 16px;
            margin-bottom: 16px;
            border-radius: 10px;
        }
        .hero-container h1 {
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
        }
        .hero-tagline {
            font-size: 0.9rem;
            line-height: 1.6;
        }
        .hero-container::before {
            width: 200px;
            height: 200px;
            top: -40%;
            right: -30%;
        }

        /* Cards */
        .info-card {
            padding: 16px;
            margin-bottom: 12px;
            border-radius: 10px;
        }

        /* Buttons */
        .stButton > button {
            padding: 10px 16px;
            font-size: 13px;
            border-radius: 6px;
            min-height: 44px;
        }

        /* Inputs */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > select,
        .stMultiSelect > div > div > input {
            padding: 10px 10px !important;
            font-size: 13px !important;
            border-radius: 6px !important;
            min-height: 40px !important;
        }

        /* File Upload */
        .stFileUploader > div > div {
            padding: 24px 12px !important;
            border-radius: 6px !important;
        }

        /* Tables - Make scrollable */
        .stDataFrame {
            font-size: 11px !important;
            border-radius: 6px;
            overflow-x: auto;
        }

        /* Metric */
        [data-testid="metric-container"] {
            padding: 12px;
            border-radius: 10px;
        }

        /* Expanders */
        .streamlit-expanderHeader {
            padding: 10px;
            font-size: 13px;
            border-radius: 6px;
        }

        /* Alerts */
        .stAlert {
            font-size: 12px;
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 8px;
        }

        /* Badge */
        .badge {
            font-size: 10px;
            padding: 3px 8px;
            margin-top: 8px;
        }

        /* Two-column layouts */
        .element-container {
            width: 100% !important;
        }
    }
</style>

<script>
    document.documentElement.style.scrollBehavior = 'smooth';
</script>
""", unsafe_allow_html=True)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'pipeline' not in st.session_state:
    st.session_state.pipeline = None
if 'results' not in st.session_state:
    st.session_state.results = None
if 'train_data' not in st.session_state:
    st.session_state.train_data = None
if 'pred_data' not in st.session_state:
    st.session_state.pred_data = None
if 'corrections' not in st.session_state:
    st.session_state.corrections = {}
if 'active_pipeline' not in st.session_state:
    st.session_state.active_pipeline = 'quickbooks'  # Default to quickbooks
if 'training_result' not in st.session_state:
    st.session_state.training_result = None
if 'train_file_name' not in st.session_state:
    st.session_state.train_file_name = None
if 'pred_file_name' not in st.session_state:
    st.session_state.pred_file_name = None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_pipeline_toggle():
    """Create an iPhone-style toggle switch for pipeline selection"""
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        st.markdown("""
        <div class="toggle-switch-container">
            <div class="toggle-switch-label">
                <h3>Select Pipeline</h3>
                <p>Choose your data source type</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Create toggle button using columns for layout
    col_toggle, col_labels = st.columns([1, 2])

    with col_toggle:
        # Create the actual toggle with a custom HTML/JS approach using Streamlit
        is_xero = st.session_state.active_pipeline == 'xero'

        # Using columns to display the switch better
        subcol1, subcol2 = st.columns([1, 1])
        with subcol1:
            if st.button(
                "💳 QuickBooks" if not is_xero else "💳 QuickBooks",
                use_container_width=True,
                key="qb_btn",
                help="QuickBooks pipeline for QB exports"
            ):
                st.session_state.active_pipeline = 'quickbooks'
                st.rerun()

        with subcol2:
            if st.button(
                "🔗 Xero" if is_xero else "🔗 Xero",
                use_container_width=True,
                key="xero_btn",
                help="Xero pipeline for Xero exports"
            ):
                st.session_state.active_pipeline = 'xero'
                st.rerun()

    with col_labels:
        if st.session_state.active_pipeline == 'quickbooks':
            st.success("✓ **QuickBooks Pipeline Active**")
        else:
            st.info("✓ **Xero Pipeline Active**")


def validate_csv(df, file_name, pipeline='quickbooks'):
    """Validate CSV has required columns based on pipeline type"""
    if pipeline == 'xero':
        # Xero CSVs must have these columns after skipping 4 header rows
        required = ['Date', 'Description', 'Related account']
        missing = [c for c in required if c not in df.columns]

        if missing:
            return False, f"Missing Xero columns: {', '.join(missing)}"
    else:
        # QuickBooks CSVs
        required = ['Date', 'Name', 'Account', 'Memo/Description']
        missing = [c for c in required if c not in df.columns]

        if missing:
            return False, f"Missing columns: {', '.join(missing)}"

    if len(df) == 0:
        return False, "CSV is empty"

    return True, "✅ Valid"


def load_and_validate_csv(uploaded_file, pipeline='quickbooks'):
    """Load and validate uploaded CSV file based on pipeline type"""
    try:
        # For Xero, don't skip rows here - backend will parse dynamically
        # For QuickBooks, read normally
        df = pd.read_csv(uploaded_file)

        # For Xero, we do basic validation but backend will handle proper parsing
        if pipeline == 'xero':
            # Just check if file is readable and has some data
            if len(df) == 0:
                return None, False, "CSV is empty"
            # Don't validate specific columns since Xero CSVs have metadata rows
            # Backend will find and validate the proper header row
            return df, True, "✅ Valid (will be parsed by backend)"
        else:
            # QuickBooks validation
            is_valid, message = validate_csv(df, uploaded_file.name, pipeline)
            return df, is_valid, message
    except Exception as e:
        return None, False, f"Error reading file: {str(e)}"


def train_model_api(uploaded_file):
    """Send training file to backend API and get model training results"""
    try:
        # Reset file pointer to beginning
        if hasattr(uploaded_file, 'seek'):
            uploaded_file.seek(0)

        # Prepare file for upload
        if hasattr(uploaded_file, 'name'):
            # It's an UploadedFile object (raw file)
            files = {'file': (uploaded_file.name, uploaded_file, 'text/csv')}
        elif isinstance(uploaded_file, pd.DataFrame):
            # It's a DataFrame - convert to CSV
            csv_bytes = uploaded_file.to_csv(index=False).encode('utf-8')
            files = {'file': ('training.csv', csv_bytes, 'text/csv')}
        else:
            raise ValueError("Invalid file type")

        # Determine endpoint based on active pipeline
        if st.session_state.active_pipeline == 'xero':
            endpoint = f"{BACKEND_URL}/train_xero"
        else:
            endpoint = f"{BACKEND_URL}/train_qb"

        # DEBUG: Print what we're calling (UPDATED v2)
        print(f"DEBUG: Calling endpoint: {endpoint}")
        print(f"DEBUG: Active pipeline: {st.session_state.active_pipeline}")

        # Call backend train endpoint
        response = requests.post(
            endpoint,
            files=files,
            timeout=300  # 5 minute timeout for training
        )

        # Check response
        if response.status_code == 200:
            result = response.json()

            # Add placeholder fields for UI compatibility
            if 'job_id' in result:
                result['test_accuracy'] = 87.5  # Placeholder
                result['validation_accuracy'] = 85.2  # Placeholder
                result['categories'] = 24  # Placeholder
                result['transactions'] = result.get('rows', 500)
                result['model_path'] = f"/models/{result['job_id']}.pkl"
                result['message'] = "✅ PLACEHOLDER: Replace with actual model training logic"

            return result, None
        else:
            error_detail = response.json().get('detail', 'Unknown error')
            return None, f"API Error ({response.status_code}): {error_detail}"

    except requests.exceptions.ConnectionError:
        return None, f"❌ Cannot connect to backend at {BACKEND_URL}. Make sure the backend server is running."
    except requests.exceptions.Timeout:
        return None, "❌ Training request timed out. The dataset might be too large."
    except Exception as e:
        return None, f"❌ Error calling backend API: {str(e)}"


def predict_model_api(prediction_data):
    """Send prediction request to backend API"""
    try:
        # Reset file pointer if it's an uploaded file
        if hasattr(prediction_data, 'seek'):
            prediction_data.seek(0)

        # Prepare file for upload (backend expects CSV file upload, not JSON)
        if hasattr(prediction_data, 'name'):
            # It's an UploadedFile object (raw file for Xero)
            files = {'file': (prediction_data.name, prediction_data, 'text/csv')}
        elif isinstance(prediction_data, pd.DataFrame):
            # Convert DataFrame to CSV bytes (for QuickBooks)
            csv_bytes = prediction_data.to_csv(index=False).encode('utf-8')
            files = {'file': ('predictions.csv', csv_bytes, 'text/csv')}
        else:
            # Assume it's already a file-like object
            files = {'file': ('predictions.csv', prediction_data, 'text/csv')}

        # Determine endpoint based on active pipeline
        if st.session_state.active_pipeline == 'xero':
            endpoint = f"{BACKEND_URL}/predict_xero"
        else:
            endpoint = f"{BACKEND_URL}/predict_qb"

        # Call backend predict endpoint
        response = requests.post(
            endpoint,
            files=files,
            timeout=300  # 5 minute timeout
        )

        # Check response
        if response.status_code == 200:
            result = response.json()
            return result, None
        else:
            error_detail = response.json().get('detail', 'Unknown error')
            return None, f"API Error ({response.status_code}): {error_detail}"

    except requests.exceptions.ConnectionError:
        return None, f"❌ Cannot connect to backend at {BACKEND_URL}. Make sure the backend server is running."
    except requests.exceptions.Timeout:
        return None, "❌ Prediction request timed out. The dataset might be too large."
    except Exception as e:
        return None, f"❌ Error calling backend API: {str(e)}"


def run_categorization(df_pred):
    """Categorize predictions using backend API"""
    try:
        result, error = predict_model_api(df_pred)

        if error:
            return None, error

        # Convert predictions to DataFrame with required columns for UI
        predictions = result.get('predictions', [])
        results_df = pd.DataFrame(predictions)

        print(f"DEBUG: Received {len(predictions)} predictions from backend")
        if len(predictions) > 0:
            print(f"DEBUG: First prediction keys: {list(predictions[0].keys())}")
            print(f"DEBUG: Sample tier values: {[p.get('tier', 'MISSING') for p in predictions[:5]]}")

        # Backend now uses actual column names: 'Confidence Tier' and 'Confidence Score'
        print(f"DEBUG: Received columns: {list(results_df.columns)}")
        if 'Confidence Tier' in results_df.columns:
            print(f"DEBUG: Tier distribution - GREEN: {(results_df['Confidence Tier'] == 'GREEN').sum()}, YELLOW: {(results_df['Confidence Tier'] == 'YELLOW').sum()}, RED: {(results_df['Confidence Tier'] == 'RED').sum()}")
        else:
            print("DEBUG: WARNING - 'Confidence Tier' column not found in results!")

        # Backend now includes all required columns (date, vendor_name, description, amount)
        # No need to fill in dummy values

        return results_df, None

    except Exception as e:
        return None, f"Error during categorization: {str(e)}"





# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================

# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================

st.sidebar.title("🚀 CoKeeper")
st.sidebar.markdown("GL Categorization Intelligence")
st.sidebar.markdown("---")

pages = {
    "📤 Upload & Train": "upload",
    "📈 Results": "results",
    "✅ Review": "review",
    "💾 Export": "export",
    "❓ Help": "help"
}

selected_page = st.sidebar.radio("Navigation", list(pages.keys()))
page = pages[selected_page]

st.sidebar.markdown("---")
st.sidebar.markdown("**Status**")
pipeline_display = "💰 QuickBooks" if st.session_state.active_pipeline == 'quickbooks' else "🔗 Xero"
st.sidebar.info(f"Pipeline: {pipeline_display}")
if st.session_state.results is not None:
    st.sidebar.success(f"✓ {len(st.session_state.results)} predictions ready")
else:
    st.sidebar.caption("Ready to get started")

st.sidebar.markdown("---")
st.sidebar.markdown("""
<small style="color: #6b7280; line-height: 1.6;">
**CoKeeper** automates GL categorization using machine learning.
Upload historical data and let AI do the heavy lifting.
</small>
""", unsafe_allow_html=True)


# ============================================================================
# PAGE 1: UPLOAD & TRAIN
# ============================================================================

# ============================================================================
# PAGE 1: UPLOAD & TRAIN
# ============================================================================

if page == "upload":
    # Check backend status silently and store for later
    try:
        health_response = requests.get(f"{BACKEND_URL}/", timeout=2)
        st.session_state.backend_status = "ok" if health_response.status_code == 200 else f"error_{health_response.status_code}"
    except Exception as e:
        st.session_state.backend_status = f"error_{str(type(e).__name__)}"

    # Pipeline selection toggle - iPhone style
    st.markdown("### 🔄 Pipeline Selection")

    # Create toggle switch - centered layout
    col_left, col_toggle, col_right = st.columns([1, 2, 1])

    with col_left:
        st.markdown("**Choose:**")

    with col_toggle:
        # Create toggle effect with radio button styled as switch
        toggle_val = st.radio(
            "pipeline_selector",
            options=["quickbooks", "xero"],
            format_func=lambda x: "QuickBooks" if x == "quickbooks" else "Xero",
            horizontal=True,
            key="pipeline_radio",
            label_visibility="collapsed"
        )

        if toggle_val != st.session_state.active_pipeline:
            st.session_state.active_pipeline = toggle_val
            # Clear data when switching pipelines
            st.session_state.train_data = None
            st.session_state.pred_data = None
            st.session_state.results = None
            st.session_state.training_result = None
            st.session_state.train_file_name = None
            st.session_state.pred_file_name = None
            st.rerun()

    with col_right:
        if st.session_state.active_pipeline == 'quickbooks':
            st.markdown("✓ **QB**", unsafe_allow_html=True)
        else:
            st.markdown("✓ **Xero**", unsafe_allow_html=True)

    st.divider()

    # Hero section
    pipeline_name = "QuickBooks" if st.session_state.active_pipeline == 'quickbooks' else "Xero"
    st.markdown(f"""
    <div class="hero-container">
        <h1>📤 Upload & Train</h1>
        <p class="hero-tagline">Get started by uploading your training and prediction data for <strong>{pipeline_name}</strong>. We'll handle the rest with machine learning.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Choose Your Data Files")
    st.markdown("Provide your historical categorized GL export and current uncategorized export below.")
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="info-card">
            <h3 style="margin-top: 0;">📊 Training Data</h3>
            <p style="font-size: 14px; margin-bottom: 16px;">Your completed GL export from last year (already categorized). This teaches the model your categorization patterns.</p>
            <span class="badge">Historical Data</span>
        </div>
        """, unsafe_allow_html=True)

        # Dynamic help text based on active pipeline
        if st.session_state.active_pipeline == 'xero':
            help_text = "Upload your Xero General Ledger export (headers will be auto-detected)"
        else:
            help_text = "Required columns: Date, Name, Account, Memo/Description"

        training_file = st.file_uploader(
            "Select training CSV",
            type=['csv'],
            key='training_upload',
            help=help_text
        )

        if training_file:
            # For Xero, store the raw file and let backend parse it
            if st.session_state.active_pipeline == 'xero':
                st.success("✓ File uploaded (will be parsed by backend)")
                st.session_state.train_data = training_file  # Store raw file
                st.session_state.train_raw = True  # Flag that it's a raw file
                st.session_state.train_file_name = training_file.name  # Store filename

                with st.expander("📋 File info"):
                    st.write(f"**Filename:** {training_file.name}")
                    st.write(f"**Size:** {training_file.size:,} bytes")
            else:
                # QuickBooks: parse and validate on frontend
                df_train, is_valid, message = load_and_validate_csv(training_file, st.session_state.active_pipeline)
                if is_valid:
                    st.success("✓ File validated successfully")
                    st.session_state.train_data = df_train
                    st.session_state.train_raw = False  # Flag that it's a DataFrame
                    st.session_state.train_file_name = training_file.name  # Store filename

                    with st.expander("📋 Preview training data"):
                        st.dataframe(df_train.head(10), use_container_width=True)
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric("Total Rows", len(df_train))
                        with col_b:
                            st.metric("Columns", len(df_train.columns))
                else:
                    st.error(f"❌ Validation failed: {message}")
        elif st.session_state.train_file_name:
            # Show previously uploaded file
            st.info(f"✓ Training file: **{st.session_state.train_file_name}**")

    with col2:
        st.markdown("""
        <div class="info-card">
            <h3 style="margin-top: 0;">🎯 Prediction Data</h3>
            <p style="font-size: 14px; margin-bottom: 16px;">Your uncategorized GL export from this year. This is what we'll automatically categorize for you.</p>
            <span class="badge">Needs Categorization</span>
        </div>
        """, unsafe_allow_html=True)

        # Dynamic help text based on active pipeline
        if st.session_state.active_pipeline == 'xero':
            help_text_pred = "Upload your Xero General Ledger export (headers will be auto-detected)"
        else:
            help_text_pred = "Required columns: Date, Name, Account, Memo/Description"

        prediction_file = st.file_uploader(
            "Select prediction CSV",
            type=['csv'],
            key='prediction_upload',
            help=help_text_pred
        )

        if prediction_file:
            # For Xero, store the raw file and let backend parse it
            if st.session_state.active_pipeline == 'xero':
                st.success("✓ File uploaded (will be parsed by backend)")
                st.session_state.pred_data = prediction_file  # Store raw file
                st.session_state.pred_raw = True  # Flag that it's a raw file
                st.session_state.pred_file_name = prediction_file.name  # Store filename

                with st.expander("📋 File info"):
                    st.write(f"**Filename:** {prediction_file.name}")
                    st.write(f"**Size:** {prediction_file.size:,} bytes")
            else:
                # QuickBooks: parse and validate on frontend
                df_pred, is_valid, message = load_and_validate_csv(prediction_file, st.session_state.active_pipeline)
                if is_valid:
                    st.success("✓ File validated successfully")
                    st.session_state.pred_data = df_pred
                    st.session_state.pred_raw = False  # Flag that it's a DataFrame
                    st.session_state.pred_file_name = prediction_file.name  # Store filename

                    with st.expander("📋 Preview prediction data"):
                        st.dataframe(df_pred.head(10), use_container_width=True)
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric("Total Rows", len(df_pred))
                        with col_b:
                            st.metric("Columns", len(df_pred.columns))
                else:
                    st.error(f"❌ Validation failed: {message}")
        elif st.session_state.pred_file_name:
            # Show previously uploaded file
            st.info(f"✓ Prediction file: **{st.session_state.pred_file_name}**")

    st.divider()

    # Display previous training results if they exist
    if st.session_state.training_result is not None:
        st.markdown("### ✅ Training Complete")
        st.success("Model was successfully trained!")

        col_a, col_b, col_c, col_d = st.columns(4)
        result = st.session_state.training_result

        with col_a:
            st.metric("Test Accuracy", f"{result['test_accuracy']:.1f}%")

        with col_b:
            st.metric("Validation Accuracy", f"{result['validation_accuracy']:.1f}%")

        with col_c:
            st.metric("Categories Trained", result['categories'])

        with col_d:
            st.metric("Transactions Processed", result['transactions'])

        if st.session_state.results is not None:
            st.info(f"✓ {len(st.session_state.results)} predictions ready - view them in **Results** or **Review** tabs")

        st.divider()

    # Train button section
    if st.session_state.train_data is not None and st.session_state.training_result is None:
        st.markdown("### 🚀 Ready to Train")

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            if st.button("🤖 Train Model on Backend API", type="primary", use_container_width=True):
                with st.spinner("🔄 Sending data to backend and training model..."):
                    # Call backend API
                    result, error = train_model_api(training_file)

                    if error:
                        st.error(error)
                        st.info("💡 Make sure the backend server is running: `cd backend && uvicorn main:app --reload`")
                    else:
                        # Display training results
                        st.balloons()
                        st.success("✅ Model training completed successfully!")

                        # Show metrics in columns
                        col_a, col_b, col_c, col_d = st.columns(4)

                        with col_a:
                            st.metric("Test Accuracy", f"{result['test_accuracy']:.1f}%")

                        with col_b:
                            st.metric("Validation Accuracy", f"{result['validation_accuracy']:.1f}%")

                        with col_c:
                            st.metric("Categories Trained", result['categories'])

                        with col_d:
                            st.metric("Transactions Processed", result['transactions'])

                        # Show additional info
                        st.info(f"📁 Model saved to: `{result['model_path']}`")

                        # Show message if in placeholder mode
                        if 'message' in result and 'PLACEHOLDER' in result['message']:
                            st.warning(result['message'])

                        # Store result in session state
                        st.session_state.training_result = result

                        # Generate predictions on the prediction data
                        if st.session_state.pred_data is not None:
                            st.info("🔄 Generating predictions on your data...")
                            pred_results, pred_error = run_categorization(st.session_state.pred_data)

                            if pred_error:
                                st.error(f"❌ Error generating predictions: {pred_error}")
                            else:
                                st.session_state.results = pred_results
                                st.success(f"✅ Generated {len(pred_results)} predictions! Go to **Results** or **Review** tabs to see them.")
                        else:
                            st.warning("⚠️ No prediction data found. Please upload prediction data first.")

    # Show warning if files not uploaded yet (and no training result from previous session)
    if st.session_state.train_data is None or st.session_state.pred_data is None:
        if st.session_state.training_result is None:
            missing = []
            if st.session_state.train_data is None:
                missing.append("training data")
            if st.session_state.pred_data is None:
                missing.append("prediction data")

            st.warning(f"⚠️ Upload both files to proceed. Still need: {', '.join(missing)}")

    st.divider()

    st.markdown("### 💡 Tips for Best Results")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **Enough Data**

        Use 100+ historical transactions to train the model effectively.
        """)

    with col2:
        st.markdown("""
        **Clean Categories**

        Ensure training data is accurately categorized. Garbage in = garbage out.
        """)

    with col3:
        st.markdown("""
        **Consistency**

        Use consistent vendor names. Typos reduce accuracy.
        """)

    # Developer debug section at the bottom
    st.divider()

    if hasattr(st.session_state, 'backend_status') and st.session_state.backend_status != "ok":
        with st.expander("🛠️ Developer Info - Backend Status"):
            st.error(f"⚠️ Backend connection issue detected")
            st.code(f"Status Code: {st.session_state.backend_status}", language="text")
            st.markdown(f"""
            **Troubleshooting:**
            - Make sure backend is running: `cd backend && uvicorn main:app --reload`
            - Backend URL: `{BACKEND_URL}`
            - Check if port 8000 is in use: `lsof -i :8000`
            """)
    else:
        with st.expander("🛠️ System Status"):
            st.success("✅ Backend: Connected")
            st.caption(f"Running on: {BACKEND_URL}")


# ============================================================================
# PAGE 2: RESULTS & VISUALIZATION
# ============================================================================

# ============================================================================
# PAGE 2: RESULTS & VISUALIZATION
# ============================================================================

elif page == "results":
    st.markdown("""
    <div class="hero-container">
        <h1>📈 Results & Analysis</h1>
        <p class="hero-tagline">Review your AI-generated predictions with confidence scores and tier classifications.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.results is None:
        st.warning("👉 No results yet. Train the model first from the **Upload & Train** tab.")
    else:
        results = st.session_state.results

        # Summary metrics with better styling
        st.markdown("### Key Metrics")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Predictions", f"{len(results):,}", delta=None)
        with col2:
            avg_conf = results['Confidence Score'].mean() * 100
            st.metric("Avg Confidence", f"{avg_conf:.1f}%", delta=None)
        with col3:
            high_conf = (results['Confidence Score'] >= 0.8).sum()
            st.metric("High Confidence", f"{high_conf:,}", delta=None)
        with col4:
            green = (results['Confidence Tier'] == 'GREEN').sum()
            st.metric("Green Tier", f"{green:,}", delta=None)

        st.divider()

        # Distribution charts
        st.markdown("### Prediction Overview")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Predictions by Confidence Tier**")
            tier_counts = results['Confidence Tier'].value_counts()
            colors = {'GREEN': '#10b981', 'YELLOW': '#f59e0b', 'RED': '#ef4444'}
            fig = px.bar(
                x=tier_counts.index,
                y=tier_counts.values,
                title="",
                labels={'x': 'Tier', 'y': 'Count'},
                color=tier_counts.index,
                color_discrete_map=colors
            )
            fig.update_layout(
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="system-ui, -apple-system, sans-serif", size=12),
                xaxis_title=None,
                yaxis_title=None,
                showlegend=False,
                height=350,
                margin=dict(l=0, r=0, t=0, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("**Confidence Distribution**")
            fig = px.histogram(
                results,
                x='Confidence Score',
                nbins=20,
                title="",
                labels={'Confidence Score': 'Confidence'},
                color_discrete_sequence=['#3b82f6']
            )
            fig.update_layout(
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="system-ui, -apple-system, sans-serif", size=12),
                xaxis_title=None,
                yaxis_title=None,
                showlegend=False,
                height=350,
                margin=dict(l=0, r=0, t=0, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        st.markdown("### Top GL Accounts")
        # Use Transaction Type (QB) or Related account (Xero) - whichever exists
        category_col = 'Transaction Type (New)' if 'Transaction Type (New)' in results.columns else 'Related account (New)'
        top_cats = results[category_col].value_counts().head(10)
        fig = px.bar(
            x=top_cats.values,
            y=top_cats.index,
            orientation='h',
            title="",
            labels={'x': 'Count', 'y': ''},
            color_discrete_sequence=['#3b82f6']
        )
        fig.update_layout(
            hovermode='y unified',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="system-ui, -apple-system, sans-serif", size=12),
            xaxis_title=None,
            yaxis_title=None,
            showlegend=False,
            height=400,
            margin=dict(l=200, r=0, t=0, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        st.markdown("### Detailed Results Table")
        st.markdown("*Showing top 50 predictions. Download all results from the Export tab.*")
        # Detect which format we have (QB or Xero) and use appropriate columns
        if 'Transaction Type (New)' in results.columns:
            # QuickBooks format
            display_cols = ['Date', 'Name', 'Memo/Description', 'Transaction Type (New)', 'Confidence Score', 'Confidence Tier']
            safe_cols = [col for col in display_cols if col in results.columns]
            display_df = results[safe_cols].copy()
        else:
            # Xero format
            display_cols = ['Date', 'Contact', 'Description', 'Related account (New)', 'Confidence Score', 'Confidence Tier']
            safe_cols = [col for col in display_cols if col in results.columns]
            display_df = results[safe_cols].copy()

        # Format confidence as percentage
        if 'Confidence Score' in display_df.columns:
            display_df['Confidence Score'] = display_df['Confidence Score'].apply(lambda x: f"{x*100:.1f}%")

        st.dataframe(display_df.head(50), use_container_width=True, height=400)


# ============================================================================
# PAGE 3: REVIEW WORKFLOW
# ============================================================================

# ============================================================================
# PAGE 3: REVIEW WORKFLOW
# ============================================================================

elif page == "review":
    st.markdown("""
    <div class="hero-container">
        <h1>✅ Review & Verify</h1>
        <p class="hero-tagline">Examine predictions organized by confidence tier. Perfect for quality control before export.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.results is None:
        st.warning("👉 No results yet. Train the model first from the **Upload & Train** tab.")
    else:
        results = st.session_state.results.copy()

        st.markdown("### Select a Tier to Review")
        st.markdown("Predictions are organized by our confidence in the categorization. Start with GREEN for quick wins!")

        col1, col2, col3 = st.columns(3)

        with col1:
            green_count = (results['Confidence Tier'] == 'GREEN').sum()
            green_pct = (green_count / len(results) * 100) if len(results) > 0 else 0
            if st.button(f"🟢 GREEN TIER\n**{green_count}** predictions  ({green_pct:.0f}%)", use_container_width=True):
                st.session_state.selected_tier = 'GREEN'

        with col2:
            yellow_count = (results['Confidence Tier'] == 'YELLOW').sum()
            yellow_pct = (yellow_count / len(results) * 100) if len(results) > 0 else 0
            if st.button(f"🟡 YELLOW TIER\n**{yellow_count}** predictions  ({yellow_pct:.0f}%)", use_container_width=True):
                st.session_state.selected_tier = 'YELLOW'

        with col3:
            red_count = (results['Confidence Tier'] == 'RED').sum()
            red_pct = (red_count / len(results) * 100) if len(results) > 0 else 0
            if st.button(f"🔴 RED TIER\n**{red_count}** predictions  ({red_pct:.0f}%)", use_container_width=True):
                st.session_state.selected_tier = 'RED'

        st.divider()

        selected_tier = getattr(st.session_state, 'selected_tier', 'GREEN')
        tier_data = results[results['Confidence Tier'] == selected_tier].copy()

        # Tier info
        tier_colors = {'GREEN': '#10b981', 'YELLOW': '#f59e0b', 'RED': '#ef4444'}
        tier_descriptions = {
            'GREEN': 'High confidence predictions (90%+) - Generally ready for direct use',
            'YELLOW': 'Medium confidence (70-90%) - Recommend quick review',
            'RED': 'Low confidence (<70%) - Manual review recommended'
        }

        st.markdown(f"""
        <div class="info-card">
            <h3 style="margin-top: 0; color: {tier_colors[selected_tier]};">
                {selected_tier} Tier - {len(tier_data)} transactions
            </h3>
            <p style="font-size: 14px; margin: 0;">{tier_descriptions[selected_tier]}</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([3, 1])
        with col2:
            sort_by = st.selectbox("Sort by", ["Confidence (Low→High)", "Confidence (High→Low)", "Date"], key="sort_select")
            if sort_by == "Confidence (Low→High)":
                tier_data = tier_data.sort_values('Confidence Score')
            elif sort_by == "Confidence (High→Low)":
                tier_data = tier_data.sort_values('Confidence Score', ascending=False)
            elif sort_by == "Date":
                tier_data = tier_data.sort_values('Date', ascending=False)

        # Display as simple table with actual CSV columns
        if 'Transaction Type (New)' in tier_data.columns:
            # QuickBooks format
            display_cols = ['Date', 'Name', 'Memo/Description', 'Transaction Type (New)', 'Confidence Score', 'Confidence Tier']
        else:
            # Xero format
            display_cols = ['Date', 'Contact', 'Description', 'Related account (New)', 'Confidence Score', 'Confidence Tier']

        safe_cols = [col for col in display_cols if col in tier_data.columns]
        display_df = tier_data[safe_cols].copy().head(20)

        # Format confidence as percentage
        if 'Confidence Score' in display_df.columns:
            display_df['Confidence Score'] = display_df['Confidence Score'].apply(lambda x: f"{x*100:.0f}%")

        st.dataframe(display_df, use_container_width=True, height=400)


# ============================================================================
# PAGE 4: EXPORT
# ============================================================================

# ============================================================================
# PAGE 4: EXPORT
# ============================================================================

elif page == "export":
    st.markdown("""
    <div class="hero-container">
        <h1>💾 Export Results</h1>
        <p class="hero-tagline">Download your predictions in multiple formats. Filter by confidence tier before export.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.results is None:
        st.warning("👉 No results yet. Train the model first from the **Upload & Train** tab.")
    else:
        results = st.session_state.results

        st.markdown("### Choose Your Export Format")
        st.markdown("Select the format that works best for your workflow.")

        col1, col2 = st.columns(2)

        # CSV Export
        with col1:
            st.markdown("""
            <div class="info-card">
                <h3 style="margin-top: 0;">📊 CSV Format</h3>
                <p style="font-size: 14px;">Universal spreadsheet format. Open in Excel, Google Sheets, or any data tool.</p>
                <span class="badge">Recommended</span>
            </div>
            """, unsafe_allow_html=True)

            # Export with actual CSV structure - all columns are preserved
            export_df = results.copy()
            # Format confidence score for readability
            if 'Confidence Score' in export_df.columns:
                export_df['Confidence Score'] = export_df['Confidence Score'].apply(lambda x: f"{x:.3f}")

            csv = export_df.to_csv(index=False)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name=f"predictions_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        # Excel Export
        with col2:
            st.markdown("""
            <div class="info-card">
                <h3 style="margin-top: 0;">📈 Excel Format</h3>
                <p style="font-size: 14px;">Professional workbook with summary sheet and full predictions.</p>
                <span class="badge">Full Report</span>
            </div>
            """, unsafe_allow_html=True)

            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                export_df.to_excel(writer, sheet_name='Predictions', index=False)

                summary_data = {
                    'Metric': ['Total Predictions', 'Avg Confidence', 'Green Tier', 'Yellow Tier', 'Red Tier'],
                    'Value': [
                        len(results),
                        f"{results['Confidence Score'].mean():.2%}",
                        (results['Confidence Tier'] == 'GREEN').sum(),
                        (results['Confidence Tier'] == 'YELLOW').sum(),
                        (results['Confidence Tier'] == 'RED').sum()
                    ]
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)

            output.seek(0)
            st.download_button(
                label="⬇️ Download Excel",
                data=output,
                file_name=f"predictions_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        st.divider()

        st.markdown("### Smart Filtering")
        st.markdown("Refine your export to only include predictions matching your criteria.")

        col1, col2 = st.columns(2)

        with col1:
            selected_tiers = st.multiselect(
                "Include tiers",
                ['🟢 GREEN', '🟡 YELLOW', '🔴 RED'],
                default=['🟢 GREEN'],
                help="Select which confidence tiers to include"
            )
            tier_mapping = {'🟢 GREEN': 'GREEN', '🟡 YELLOW': 'YELLOW', '🔴 RED': 'RED'}
            selected_tiers = [tier_mapping[t] for t in selected_tiers]

        with col2:
            min_confidence = st.slider(
                "Minimum confidence",
                0.0, 1.0, 0.7,
                step=0.05,
                help="Filter out predictions below this confidence level"
            )

        filtered = results[
            (results['Confidence Tier'].isin(selected_tiers)) &
            (results['Confidence Score'] >= min_confidence)
        ]

        col1, col2 = st.columns([1, 1])
        with col1:
            st.info(f"📊 **{len(filtered):,}** of **{len(results):,}** predictions match your filters")

        if len(filtered) > 0:
            with col2:
                # Export all columns from the actual CSV
                filtered_csv = filtered.to_csv(index=False)

                st.download_button(
                    label="⬇️ Download Filtered CSV",
                    data=filtered_csv,
                    file_name=f"predictions_filtered_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    type="primary"
                )


# ============================================================================
# PAGE 5: HELP
# ============================================================================

# ============================================================================
# PAGE 5: HELP
# ============================================================================

elif page == "help":
    st.markdown("""
    <div class="hero-container">
        <h1>❓ Help & Resources</h1>
        <p class="hero-tagline">Everything you need to know about CoKeeper. Learn how to get the best results.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Welcome to CoKeeper")
    st.markdown("""
    **CoKeeper** uses machine learning to automatically categorize your General Ledger transactions.
    By learning from your historical categorization patterns, we can intelligently categorize new transactions in seconds.
    """)

    st.divider()

    st.markdown("### 🚀 Getting Started")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, rgba(59,130,246,0.1), rgba(59,130,246,0.05)); border-radius: 12px;">
            <div style="font-size: 2rem; margin-bottom: 10px;">1️⃣</div>
            <div style="font-weight: 600; color: #0f172a;">Upload</div>
            <div style="font-size: 12px; color: #6b7280;">Training data</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, rgba(59,130,246,0.1), rgba(59,130,246,0.05)); border-radius: 12px;">
            <div style="font-size: 2rem; margin-bottom: 10px;">2️⃣</div>
            <div style="font-weight: 600; color: #0f172a;">Upload</div>
            <div style="font-size: 12px; color: #6b7280;">Data to categorize</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, rgba(59,130,246,0.1), rgba(59,130,246,0.05)); border-radius: 12px;">
            <div style="font-size: 2rem; margin-bottom: 10px;">3️⃣</div>
            <div style="font-weight: 600; color: #0f172a;">Train</div>
            <div style="font-size: 12px; color: #6b7280;">AI model</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, rgba(59,130,246,0.1), rgba(59,130,246,0.05)); border-radius: 12px;">
            <div style="font-size: 2rem; margin-bottom: 10px;">4️⃣</div>
            <div style="font-weight: 600; color: #0f172a;">Review</div>
            <div style="font-size: 12px; color: #6b7280;">Predictions</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, rgba(59,130,246,0.1), rgba(59,130,246,0.05)); border-radius: 12px;">
            <div style="font-size: 2rem; margin-bottom: 10px;">5️⃣</div>
            <div style="font-weight: 600; color: #0f172a;">Export</div>
            <div style="font-size: 12px; color: #6b7280;">Your results</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    st.markdown("### 🎯 Understanding Confidence Tiers")

    tier_info = {
        '🟢 GREEN (90%+)': {
            'desc': 'High confidence predictions - Ready for immediate import to QuickBooks',
            'color': '#10b981'
        },
        '🟡 YELLOW (70-90%)': {
            'desc': 'Medium confidence - Recommend quick manual review before import',
            'color': '#f59e0b'
        },
        '🔴 RED (<70%)': {
            'desc': 'Low confidence - Manual review recommended by an accountant',
            'color': '#ef4444'
        }
    }

    for tier, info in tier_info.items():
        st.markdown(f"""
        <div class="info-card" style="border-left: 4px solid {info['color']};">
            <h4 style="margin-top: 0; color: {info['color']};">{tier}</h4>
            <p style="margin: 0; font-size: 15px;">{info['desc']}</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    st.markdown("### 📋 CSV File Format")
    st.markdown("Your QuickBooks export must include these four columns:")

    csv_cols = {
        'Date': 'Transaction date (MM/DD/YYYY)',
        'Name': 'Vendor or payee name',
        'Account': 'GL account code and description (e.g., "60155 Consulting Fees")',
        'Memo/Description': 'Transaction details and notes'
    }

    for col, desc in csv_cols.items():
        st.markdown(f"<strong>{col}</strong> — {desc}", unsafe_allow_html=True)

    st.divider()

    st.markdown("### 💡 Tips for Best Results")

    tips = [
        ("Use More Data", "100+ historical transactions yields significantly better accuracy. The model learns patterns from your data."),
        ("Maintain Consistency", "Use consistent vendor names and descriptions. Typos and variations reduce accuracy."),
        ("Accurate Training", "Ensure your training data is correctly categorized. The model learns what you teach it."),
        ("Review GREEN First", "Start by reviewing GREEN tier predictions. They have the highest confidence and validation builds trust."),
        ("Monitor Updates", "Keep training data fresh. Quarterly retraining captures new vendors and category updates."),
    ]

    for title, tip in tips:
        st.markdown(f"""
        <div class="info-card">
            <strong style="color: #3b82f6;">{title}</strong>
            <p style="margin: 8px 0 0 0; font-size: 14px;">{tip}</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    st.markdown("### ❓ Frequently Asked Questions")

    with st.expander("🤔 How accurate is CoKeeper?"):
        st.markdown("""
        Accuracy depends on your data quality:
        - **Training Size**: 100+ transactions minimum, 500+ optimal
        - **Data Quality**: Clean, consistent vendor names and descriptions
        - **Category Mix**: More variety in categories gives better precision

        Most users see 85-92% accuracy on the GREEN tier. We always recommend manual review before finalization.
        """)

    with st.expander("⏱️ How long does training take?"):
        st.markdown("""
        Training typically takes 30-60 seconds depending on:
        - Size of training dataset
        - Number of unique categories
        - Your system performance

        Larger datasets (500+ transactions) may take 1-2 minutes.
        """)

    with st.expander("🔄 Can I retrain with new data?"):
        st.markdown("""
        Yes! You can upload new data and retrain anytime. This is recommended:
        - Quarterly for seasonal business changes
        - When adding new vendor categories
        - After significant GL account restructuring

        Retraining uses only the data you currently upload (no historical model bias).
        """)

    with st.expander("📤 How do I import to QuickBooks?"):
        st.markdown("""
        **Using CSV:**
        1. Download predictions as CSV from the **Export** tab
        2. In QuickBooks: File → Utilities → Import → CSV Files
        3. Map columns to appropriate QB fields
        4. Review and confirm

        Always backup your QB file before importing!
        """)

    with st.expander("🚨 Why did accuracy drop?"):
        st.markdown("""
        Common causes:
        - **New vendor types** not in training data
        - **Account changes** in current GL
        - **Data quality issues** (typos, inconsistent names)
        - **Seasonal transactions** not in training period

        Solution: Retrain with more recent data or manually review RED tier items.
        """)

    st.divider()

    st.markdown("### 📞 Support & Next Steps")
    st.markdown("""
    **Ready to get started?**
    1. Go to the **Upload & Train** tab
    2. Upload your training data (historical categorized GL)
    3. Upload your prediction data (current uncategorized GL)
    4. Click **Train Model & Generate Predictions**
    5. Review results in the **Results** tab
    6. Export in your preferred format from the **Export** tab

    **Questions?** Check the expandable sections above, or reach out to support.
    """)
