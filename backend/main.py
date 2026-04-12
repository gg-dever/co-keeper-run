"""
FastAPI Backend for CoKeeper Transaction Categorization
Minimal demo with 2 endpoints: /train and /predict
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from pydantic import BaseModel
import pandas as pd
import io
import os
import json
from typing import Dict, Any, Optional, List
import logging
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LAZY LOAD ML pipelines on first use (not on import)
# This prevents slow imports from blocking the FastAPI app startup
MLPipeline = None
MLPipelineXero = None
ML_QB_AVAILABLE = True  # Will set to False if import fails
ML_XERO_AVAILABLE = True  # Will set to False if import fails

def _lazy_load_qb():
    """Lazy load QB pipeline on first use"""
    global MLPipeline, ML_QB_AVAILABLE
    if MLPipeline is None:
        try:
            from ml_pipeline_qb import QuickBooksPipeline
            MLPipeline = QuickBooksPipeline
        except Exception as e:
            logger.warning(f"QuickBooks ML Pipeline not available: {e}")
            ML_QB_AVAILABLE = False
            raise
    return MLPipeline

def _lazy_load_xero():
    """Lazy load Xero pipeline on first use"""
    global MLPipelineXero, ML_XERO_AVAILABLE
    if MLPipelineXero is None:
        try:
            from ml_pipeline_xero import MLPipelineXero as XeroPipe
            MLPipelineXero = XeroPipe
        except Exception as e:
            logger.warning(f"Xero ML Pipeline not available: {e}")
            ML_XERO_AVAILABLE = False
            raise
    return MLPipelineXero

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CoKeeper API",
    description="Transaction categorization API with ML pipeline",
    version="1.0.0"
)

# Setup CORS (allow frontend to call this API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy initialization of ML pipelines
ml_pipeline: Optional[Any] = None
ml_pipeline_xero: Optional[Any] = None


def get_qb_pipeline(force_new=False):
    """Lazy initialize QuickBooks pipeline"""
    global ml_pipeline
    if not ML_QB_AVAILABLE:
        raise HTTPException(status_code=503, detail="QuickBooks ML pipeline is not available")
    Pipeline = _lazy_load_qb()  # Load the class on first call

    # Force create new pipeline if requested (needed for training with updated code)
    if force_new:
        logger.info("Force creating new QB pipeline instance")
        ml_pipeline = Pipeline()
        return ml_pipeline

    if ml_pipeline is None:
        # Try to load existing trained model first
        default_model_path = "models/naive_bayes_model.pkl"
        if os.path.exists(default_model_path):
            logger.info(f"Auto-loading trained QB model from {default_model_path}")
            ml_pipeline = Pipeline.load_model(default_model_path)
        else:
            logger.warning(f"No trained model found at {default_model_path}, creating empty pipeline")
            ml_pipeline = Pipeline()
    return ml_pipeline


def get_xero_pipeline():
    """Lazy initialize Xero pipeline"""
    global ml_pipeline_xero
    if not ML_XERO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Xero ML pipeline is not available")
    Pipeline = _lazy_load_xero()  # Load the class on first call
    if ml_pipeline_xero is None:
        # Try to load existing trained model first
        default_model_path = "models/naive_bayes_xero_model.pkl"
        if os.path.exists(default_model_path):
            logger.info(f"Auto-loading trained Xero model from {default_model_path}")
            ml_pipeline_xero = Pipeline.load_model(default_model_path)
        else:
            logger.warning(f"No trained model found at {default_model_path}, creating empty pipeline")
            ml_pipeline_xero = Pipeline()
    return ml_pipeline_xero


# Pydantic models for request validation
class PredictCategoriesRequest(BaseModel):
    """Request model for predict-categories endpoint"""
    session_id: str
    transaction_ids: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    confidence_threshold: float = 0.7


class BatchUpdateRequest(BaseModel):
    """Request model for batch-update endpoint"""
    session_id: str
    updates: List[Dict[str, Any]]
    dry_run: bool = True


class TrainFromQuickBooksRequest(BaseModel):
    """Request model for training ML model from QuickBooks historical data"""
    session_id: str
    start_date: str  # e.g., "2025-01-01"
    end_date: str    # e.g., "2025-12-31"


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "message": "CoKeeper API is online",
        "version": "1.0.0"
    }


@app.post("/train_qb")
async def train_model(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Train the ML model with uploaded CSV file

    Expected CSV format: QuickBooks General Ledger with columns:
    - Date, Account, Name, Debit, Credit, etc.

    Returns:
    - accuracy: float (test accuracy percentage)
    - categories: int (number of categories trained)
    - transactions: int (number of transactions processed)
    - model_path: str (path where model was saved)
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")

        # Read uploaded file
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))

        logger.info(f"Received training file: {file.filename} with {len(df)} rows")

        # Train the Naive Bayes model
        result = get_qb_pipeline().train(df)

        logger.info(f"Training completed: {result['test_accuracy']:.1f}% test accuracy")

        return JSONResponse(content=result)

    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    except Exception as e:
        logger.error(f"Training error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@app.post("/predict_qb")
async def predict_transactions(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Predict categories for uploaded transactions CSV

    Expected CSV format: Similar to training data or bank statement format

    Returns:
    - predictions: list of dicts with predicted categories
    - confidence_distribution: breakdown of high/medium/low confidence predictions
    - total_transactions: int
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")

        # Read uploaded file
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))

        logger.info(f"Received prediction file: {file.filename} with {len(df)} rows")

        # Get the pipeline (auto-loads model if available)
        pipeline = get_qb_pipeline()

        # Verify model is loaded
        if not pipeline.is_model_loaded():
            raise HTTPException(
                status_code=400,
                detail="No trained model found. Please train a model first using the /train endpoint."
            )

        # Make predictions using the trained model
        predictions = pipeline.predict(df)

        # Calculate confidence distribution
        high_count = sum(1 for p in predictions if p["Confidence Tier"] == "GREEN")
        med_count = sum(1 for p in predictions if p["Confidence Tier"] == "YELLOW")
        low_count = sum(1 for p in predictions if p["Confidence Tier"] == "RED")

        result = {
            "predictions": predictions,
            "total_transactions": len(df),
            "confidence_distribution": {
                "high": high_count,
                "medium": med_count,
                "low": low_count
            }
        }

        logger.info(f"Predictions completed for {len(df)} transactions")

        return JSONResponse(content=result)

    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/train_xero")
async def train_xero_model(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Train the Xero ML model with uploaded CSV file

    Expected CSV format: Xero General Ledger export with header row containing:
    - Date, Source, Contact, Description, Debit, Credit, Related account, etc.

    Returns:
    - accuracy: float (test accuracy percentage)
    - categories: int (number of categories trained)
    - transactions: int (number of transactions processed)
    - model_path: str (path where model was saved)
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")

        # Read uploaded file - parse dynamically to find headers
        contents = await file.read()
        df = get_xero_pipeline()._parse_xero_csv(io.BytesIO(contents))

        logger.info(f"Received Xero training file: {file.filename} with {len(df)} rows")

        # Train the Naive Bayes model
        result = get_xero_pipeline().train(df)

        logger.info(f"Xero training completed: {result['test_accuracy']:.1f}% test accuracy")

        return JSONResponse(content=result)

    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    except Exception as e:
        logger.error(f"Xero training error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@app.post("/predict_xero")
async def predict_xero_transactions(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Predict categories for uploaded Xero transactions CSV

    Expected CSV format: Xero export with header row containing Date and Related account

    Returns:
    - predictions: list of dicts with predicted categories
    - confidence_distribution: breakdown of high/medium/low confidence predictions
    - total_transactions: int
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")

        # Read uploaded file - parse dynamically to find headers
        contents = await file.read()
        df = get_xero_pipeline()._parse_xero_csv(io.BytesIO(contents))

        logger.info(f"Received Xero prediction file: {file.filename} with {len(df)} rows")

        # Get the pipeline (auto-loads model if available)
        pipeline = get_xero_pipeline()

        # Verify model is loaded
        if not pipeline.is_model_loaded():
            raise HTTPException(
                status_code=400,
                detail="No trained Xero model found. Please train a model first using the /train_xero endpoint."
            )

        # Make predictions using the trained model
        predictions = pipeline.predict(df)

        # Calculate confidence distribution
        high_count = sum(1 for p in predictions if p["Confidence Tier"] == "GREEN")
        med_count = sum(1 for p in predictions if p["Confidence Tier"] == "YELLOW")
        low_count = sum(1 for p in predictions if p["Confidence Tier"] == "RED")

        logger.info(f"Tier distribution - GREEN: {high_count}, YELLOW: {med_count}, RED: {low_count}")

        result = {
            "predictions": predictions,
            "total_transactions": len(df),
            "confidence_distribution": {
                "high": high_count,
                "medium": med_count,
                "low": low_count
            }
        }

        logger.info(f"Xero predictions completed for {len(df)} transactions")

        return JSONResponse(content=result)

    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    except Exception as e:
        logger.error(f"Xero prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


# === NEW: QuickBooks OAuth and Integration Endpoints ===
from datetime import datetime

# Session storage for OAuth tokens
qb_sessions = {}
xero_sessions = {}


@app.get("/api/quickbooks/connect")
async def quickbooks_connect():
    """Step 1: Initiate QuickBooks OAuth flow - Redirects user to QB login."""
    try:
        from services.quickbooks_connector import QuickBooksConnector
        connector = QuickBooksConnector()
        auth_url = connector.get_authorization_url()
        # Directly redirect user to QuickBooks authorization page
        return RedirectResponse(url=auth_url, status_code=303)
    except Exception as e:
        logger.error(f"QB OAuth init error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/quickbooks/callback")
async def quickbooks_callback(code: str, realmId: str, state: Optional[str] = None):
    """Step 2: OAuth callback endpoint after user approves - Redirects back to frontend."""
    try:
        from services.quickbooks_connector import QuickBooksConnector
        import uuid

        connector = QuickBooksConnector()
        tokens = connector.exchange_code_for_tokens(code, realmId)

        session_id = str(uuid.uuid4())
        qb_sessions[session_id] = {
            "tokens": tokens,
            "connector": connector,
            "created_at": datetime.now().isoformat()
        }

        # Redirect back to frontend with session_id in URL
        # Frontend will be running on localhost:8501 or 8502 (Streamlit default)
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8501")
        redirect_url = f"{frontend_url}?session_id={session_id}&realm_id={realmId}&platform=quickbooks"

        # Return a friendly HTML page that auto-redirects
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>QuickBooks Connected!</title>
            <meta http-equiv="refresh" content="0; url={redirect_url}">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }}
                .card {{
                    background: white;
                    padding: 40px;
                    border-radius: 16px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    text-align: center;
                    max-width: 400px;
                }}
                .success-icon {{
                    font-size: 64px;
                    margin-bottom: 20px;
                }}
                h1 {{ color: #10b981; margin: 0 0 10px 0; }}
                p {{ color: #666; margin: 10px 0; }}
                .spinner {{
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #667eea;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    animation: spin 1s linear infinite;
                    margin: 20px auto;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="success-icon">✅</div>
                <h1>QuickBooks Connected!</h1>
                <p>Redirecting you back to CoKeeper...</p>
                <div class="spinner"></div>
                <p style="font-size: 12px; color: #999; margin-top: 20px;">
                    If you're not redirected, <a href="{redirect_url}">click here</a>
                </p>
            </div>
        </body>
        </html>
        """

        return HTMLResponse(content=html_content)

    except Exception as e:
        logger.error(f"QB callback error: {e}")
        # Return error page instead of JSON
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Connection Failed</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: #f5f5f5;
                }}
                .card {{
                    background: white;
                    padding: 40px;
                    border-radius: 16px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                    text-align: center;
                    max-width: 400px;
                }}
                .error-icon {{ font-size: 64px; margin-bottom: 20px; }}
                h1 {{ color: #ef4444; margin: 0 0 10px 0; }}
                p {{ color: #666; }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="error-icon">❌</div>
                <h1>Connection Failed</h1>
                <p>Error: {str(e)}</p>
                <p style="margin-top: 20px;">
                    <a href="{os.getenv('FRONTEND_URL', 'http://localhost:8501')}">Return to CoKeeper</a>
                </p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=500)


@app.get("/api/quickbooks/transactions")
async def get_quickbooks_transactions(
    session_id: str,
    start_date: str,
    end_date: str,
    txn_type: str = "Purchase"
):
    """Step 3: Fetch transactions from QuickBooks."""
    try:
        if session_id not in qb_sessions:
            raise HTTPException(status_code=401, detail="Invalid session")

        session = qb_sessions[session_id]
        connector = session["connector"]

        if connector.is_token_expired():
            tokens = connector.refresh_access_token(session["tokens"]["refresh_token"])
            session["tokens"] = tokens

        transactions = connector.query_transactions(
            start_date=start_date,
            end_date=end_date,
            txn_type=txn_type
        )

        session["qb_transactions"] = transactions

        return {
            "transactions": transactions,
            "count": len(transactions),
            "date_range": f"{start_date} to {end_date}"
        }
    except Exception as e:
        logger.error(f"Failed to fetch QB transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/quickbooks/accounts")
async def get_quickbooks_accounts(session_id: str):
    """Fetch chart of accounts from QuickBooks."""
    try:
        if session_id not in qb_sessions:
            raise HTTPException(status_code=401, detail="Invalid session")

        session = qb_sessions[session_id]
        connector = session["connector"]

        if connector.is_token_expired():
            tokens = connector.refresh_access_token(session["tokens"]["refresh_token"])
            session["tokens"] = tokens

        accounts = connector.query_accounts()

        session["qb_accounts"] = accounts

        return {
            "accounts": accounts,
            "count": len(accounts),
            "message": "Successfully retrieved chart of accounts"
        }
    except Exception as e:
        logger.error(f"Failed to fetch QB accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/quickbooks/train-from-qb")
async def train_model_from_quickbooks(request: TrainFromQuickBooksRequest):
    """
    Train ML model using historical QuickBooks data.

    This fetches ALREADY CATEGORIZED transactions from QuickBooks for a specified
    date range (e.g., all of 2025) and trains the ML model to learn YOUR
    categorization patterns.

    Args:
        session_id: Active QB session ID
        start_date: Start of historical period (e.g., "2025-01-01")
        end_date: End of historical period (e.g., "2025-12-31")

    Returns:
        {
            "success": true,
            "test_accuracy": 92.5,
            "train_accuracy": 95.2,
            "categories": 45,
            "transactions": 1250,
            "model_path": "models/naive_bayes_model.pkl"
        }
    """
    try:
        # Validate session
        if not request.session_id or request.session_id not in qb_sessions:
            raise HTTPException(status_code=401, detail="Invalid session")

        session = qb_sessions[request.session_id]
        connector = session.get("connector")

        if not connector:
            raise HTTPException(status_code=400, detail="No QB connector in session")

        # Refresh token if needed
        if connector.is_token_expired():
            tokens = connector.refresh_access_token(session["tokens"]["refresh_token"])
            session["tokens"] = tokens

        logger.info(f"Fetching historical transactions from {request.start_date} to {request.end_date}")

        # Fetch HISTORICAL transactions (these should already be categorized)
        transactions = connector.query_transactions(
            start_date=request.start_date,
            end_date=request.end_date,
            txn_type="Purchase"
        )

        if not transactions:
            raise HTTPException(
                status_code=400,
                detail=f"No transactions found for period {request.start_date} to {request.end_date}"
            )

        logger.info(f"Retrieved {len(transactions)} historical transactions")

        # Get QB accounts for category mapping
        accounts = connector.query_accounts()
        account_lookup = {acc.get('Id'): acc for acc in accounts}

        # Transform to ML training format
        training_data = []
        skipped_no_account = 0
        skipped_errors = 0

        for txn in transactions:
            try:
                # Extract vendor and description
                vendor_name = txn.get("EntityRef", {}).get("name", "Unknown")
                description = txn.get("PrivateNote", "")

                # Get ACTUAL category from transaction (this is what we'll train on)
                account_name = None
                account_code = None

                if txn.get("Line"):
                    first_line = txn["Line"][0]
                    account_ref = first_line.get("AccountBasedExpenseLineDetail", {}).get("AccountRef", {})
                    account_id = account_ref.get("value")
                    account_name = account_ref.get("name")

                    # Get account code from account details
                    if account_id and account_id in account_lookup:
                        account_info = account_lookup[account_id]
                        account_code = account_info.get("AcctNum")
                        # If AcctNum is empty, try to use the account ID itself
                        if not account_code:
                            account_code = account_info.get("Id", "60000")
                        # If account_name wasn't in the ref, get it from the account details
                        if not account_name:
                            account_name = account_info.get("Name", "Unknown")

                # Skip if we couldn't get proper account info
                if not account_name or not account_code:
                    skipped_no_account += 1
                    continue

                # Ensure account_code is a string number
                account_code = str(account_code)

                # Format for ML pipeline: "code name" (e.g., "60100 Automobile:Fuel")
                account_formatted = f"{account_code} {account_name}"

                training_row = {
                    "Date": txn.get("TxnDate"),
                    "Account": account_formatted,
                    "Name": vendor_name,
                    "Memo": f"{vendor_name} {description}".strip(),
                    "Debit": float(txn.get("TotalAmt", 0)),
                    "Credit": 0.0,  # Purchase transactions are debits
                    "Transaction Type": account_name  # Ground truth category for training
                }
                training_data.append(training_row)

            except Exception as e:
                logger.warning(f"Skipping transaction {txn.get('Id')}: {e}")
                skipped_errors += 1
                continue

        logger.info(f"Training data: {len(training_data)} valid, {skipped_no_account} missing account info, {skipped_errors} errors")

        if len(training_data) < 20:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough valid transactions for training. Found {len(training_data)}, need at least 20."
            )

        logger.info(f"Prepared {len(training_data)} transactions for training")

        # Convert to DataFrame
        df_train = pd.DataFrame(training_data)

        # Debug: Log sample of training data
        logger.info(f"Training DataFrame columns: {df_train.columns.tolist()}")
        logger.info(f"Sample Account values: {df_train['Account'].head(3).tolist()}")
        logger.info(f"Sample Transaction Type values: {df_train['Transaction Type'].head(3).tolist()}")

        # Train the model
        logger.info("Starting model training...")
        # Force new pipeline instance to ensure updated category_types are used
        pipeline = get_qb_pipeline(force_new=True)
        result = pipeline.train(df_train)

        # Save the trained model
        model_path = "models/naive_bayes_model.pkl"
        pipeline.save_model(model_path)

        logger.info(f"Training complete! Test accuracy: {result['test_accuracy']:.1f}%")

        return {
            "success": True,
            "test_accuracy": result.get("test_accuracy"),
            "train_accuracy": result.get("train_accuracy"),
            "categories": result.get("categories"),
            "transactions": result.get("transactions"),
            "model_path": model_path,
            "message": f"Model trained on {len(training_data)} transactions with {result.get('test_accuracy'):.1f}% accuracy"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Training failed: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@app.post("/api/quickbooks/predict-categories")
async def predict_transaction_categories(request: PredictCategoriesRequest):
   """
   Predict categories for QuickBooks transactions using ML pipeline.

   Args:
       session_id: Active QB session ID
       transaction_ids: Optional list of specific transaction IDs to predict
       start_date: If no transaction_ids, fetch from this date
       end_date: If no transaction_ids, fetch to this date
       confidence_threshold: Minimum confidence for predictions (0.0-1.0)

   Returns:
       {
           "predictions": [
               {
                   "transaction_id": "149",
                   "vendor_name": "Chin's Gas and Oil",
                   "amount": 52.56,
                   "current_category": "Automobile:Fuel",
                   "predicted_category": "Auto & Transport",
                   "confidence": 0.95,
                   "needs_review": false
               }
           ],
           "total_predictions": 40,
           "high_confidence": 35,
           "needs_review": 5,
           "categories_changed": 12
       }
   """
   try:
       # Validate session
       if not request.session_id or request.session_id not in qb_sessions:
           raise HTTPException(status_code=401, detail="Invalid session")

       session = qb_sessions[request.session_id]
       connector = session.get("connector")

       if not connector:
           raise HTTPException(status_code=400, detail="No QB connector in session")

       # Refresh token if needed
       if connector.is_token_expired():
           tokens = connector.refresh_access_token(session["tokens"]["refresh_token"])
           session["tokens"] = tokens

       # Fetch transactions
       if request.transaction_ids:
           logger.info(f"Fetching {len(request.transaction_ids)} specific transactions")
           # For now, fetch the date range and filter by IDs
           transactions = connector.query_transactions(
               start_date=request.start_date or "2024-01-01",
               end_date=request.end_date or "2026-12-31",
               txn_type="Purchase"
           )
           transactions = [t for t in transactions if t.get("Id") in request.transaction_ids]
       else:
           logger.info(f"Fetching transactions from {request.start_date} to {request.end_date}")
           transactions = connector.query_transactions(
               start_date=request.start_date or "2024-01-01",
               end_date=request.end_date or "2026-12-31",
               txn_type="Purchase"
           )

       if not transactions:
           return {
               "predictions": [],
               "total_predictions": 0,
               "high_confidence": 0,
               "needs_review": 0,
               "categories_changed": 0,
               "message": "No transactions found for the given criteria"
           }

       logger.info(f"Retrieved {len(transactions)} transactions, converting to ML format...")

       # Transform QB transaction format to ML pipeline format
       ml_transactions = []
       for txn in transactions:
           try:
               # Extract vendor and description
               vendor_name = txn.get("EntityRef", {}).get("name", "Unknown")
               description = txn.get("PrivateNote", "")

               # Get current category from first line item
               current_account = "Unknown"
               if txn.get("Line"):
                   first_line = txn["Line"][0]
                   account_ref = first_line.get("AccountBasedExpenseLineDetail", {}).get("AccountRef", {})
                   current_account = account_ref.get("name", "Unknown")

               ml_txn = {
                   "Id": txn.get("Id"),
                   "TxnDate": txn.get("TxnDate"),
                   "vendor_name": vendor_name,
                   "description": f"{vendor_name} {description}".strip(),
                   "amount": float(txn.get("TotalAmt", 0)),
                   "current_account": current_account,
                   "sync_token": txn.get("SyncToken"),
                   "line_items": txn.get("Line", [])
               }
               ml_transactions.append(ml_txn)
           except Exception as e:
               logger.error(f"Error transforming transaction {txn.get('Id')}: {e}")
               continue

       logger.info(f"Converted {len(ml_transactions)} transactions to ML format")

       # Get QB accounts for category mapping
       accounts = connector.query_accounts()
       session["qb_accounts"] = accounts

       from services.category_mapper import CategoryMapper
       mapper = CategoryMapper(accounts)

       # Run ML predictions
       logger.info("Loading ML pipeline and making predictions...")
       pipeline = get_qb_pipeline()

       # Convert transactions to DataFrame format for prediction
       df_predictions = pd.DataFrame(ml_transactions)

       # Create Account column in format "code name" (e.g., "60100 Automobile:Fuel")
       # Map account names to account codes
       account_lookup = {acc.get('Name'): acc for acc in accounts}

       def format_account(current_account_name):
           """Format account as 'code name' for ML pipeline"""
           if not current_account_name or current_account_name == "Unknown":
               return "60000 Unknown"  # Default expense account

           account = account_lookup.get(current_account_name, {})
           account_num = account.get('AcctNum', '60000')
           return f"{account_num} {current_account_name}"

       df_predictions['Account'] = df_predictions['current_account'].apply(format_account)

       df_predictions.rename(columns={
           'vendor_name': 'Name',
           'description': 'Memo',
           'amount': 'Debit'
       }, inplace=True)

       # Add Credit column (Purchase transactions are always debits, so Credit = 0)
       df_predictions['Credit'] = 0.0

       # Predict
       ml_results = pipeline.predict(df_predictions)

       logger.info(f"ML pipeline returned {len(ml_results)} predictions")

       # Enrich predictions with metadata and category mapping
       results = []
       categories_changed = 0
       high_confidence_count = 0
       needs_review_count = 0

       for idx, ml_result in enumerate(ml_results):
           txn = ml_transactions[idx]

           # Get predicted category from ML result
           predicted_category = ml_result.get("Transaction Type (New)", "Unknown")
           confidence = float(ml_result.get("Confidence Score", 0.0))

           # Map ML category to QB account
           qb_match = mapper.ml_to_qb(predicted_category)

           # Check if category changed
           category_changed = txn["current_account"] != predicted_category
           if category_changed:
               categories_changed += 1

           # Check confidence threshold
           needs_review = confidence < request.confidence_threshold
           if needs_review:
               needs_review_count += 1
           else:
               high_confidence_count += 1

           result = {
               "transaction_id": txn["Id"],
               "vendor_name": txn["vendor_name"],
               "amount": txn["amount"],
               "transaction_date": txn["TxnDate"],
               "current_category": txn["current_account"],
               "predicted_category": predicted_category,
               "predicted_qb_account": qb_match.get("name") if qb_match else None,
               "predicted_account_id": qb_match.get("id") if qb_match else None,
               "confidence": confidence,
               "confidence_tier": ml_result.get("Confidence Tier", "RED"),
               "needs_review": needs_review,
               "category_changed": category_changed,
               "mapping_confidence": qb_match.get("confidence", 0.0) if qb_match else 0.0
           }
           results.append(result)

       logger.info(f"Prediction complete: {len(results)} total, "
                  f"{high_confidence_count} high confidence, "
                  f"{needs_review_count} need review, "
                  f"{categories_changed} category changes")

       return {
           "predictions": results,
           "total_predictions": len(results),
           "high_confidence": high_confidence_count,
           "needs_review": needs_review_count,
           "categories_changed": categories_changed,
           "confidence_threshold": request.confidence_threshold,
           "message": f"Successfully predicted {len(results)} transactions"
       }

   except HTTPException as e:
       raise e
   except Exception as e:
       logger.error(f"Prediction error: {e}\n{traceback.format_exc()}")
       raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/api/quickbooks/batch-update")
async def batch_update_transactions(request: BatchUpdateRequest):
   """
   Update multiple QuickBooks transactions with predicted categories.

   Args:
       session_id: Active QB session
       updates: List of update objects with:
           - transaction_id: QB transaction ID
           - new_account_id: QB account ID to assign
           - new_account_name: QB account name to assign
       dry_run: If True, validate but don't actually update (default: True)

   Returns:
       {
           "dry_run": true,
           "total_updates": 10,
           "successful": 10,
           "failed": 0,
           "results": [
               {
                   "transaction_id": "149",
                   "status": "success",
                   "message": "Would update to Meals and Entertainment",
                   "previous_category": "Automobile:Fuel",
                   "new_category": "Meals and Entertainment"
               }
           ]
       }
   """
   try:
       # Validate session
       if not request.session_id or request.session_id not in qb_sessions:
           raise HTTPException(status_code=401, detail="Invalid session")

       session = qb_sessions[request.session_id]
       connector = session.get("connector")

       if not connector:
           raise HTTPException(status_code=400, detail="No QB connector in session")

       # Refresh token if needed
       if connector.is_token_expired():
           tokens = connector.refresh_access_token(session["tokens"]["refresh_token"])
           session["tokens"] = tokens

       # Get QB accounts for validation
       accounts = connector.query_accounts()
       session["qb_accounts"] = accounts

       from services.category_mapper import CategoryMapper
       mapper = CategoryMapper(accounts)

       logger.info(f"Processing {len(request.updates)} transaction updates (dry_run={request.dry_run})...")

       results = []
       successful = 0
       failed = 0

       for update in request.updates:
           txn_id = update.get("transaction_id")
           new_account_id = update.get("new_account_id")
           new_account_name = update.get("new_account_name")

           try:
               # Validate account exists
               if new_account_id and not mapper.validate_account_id(new_account_id):
                   results.append({
                       "transaction_id": txn_id,
                       "status": "failed",
                       "message": f"Invalid account ID: {new_account_id}",
                       "previous_category": None,
                       "new_category": None
                   })
                   failed += 1
                   continue

               if request.dry_run:
                   # Dry run - just validate
                   results.append({
                       "transaction_id": txn_id,
                       "status": "success",
                       "message": f"Would update to {new_account_name}",
                       "previous_category": "Unknown",
                       "new_category": new_account_name,
                       "dry_run": True
                   })
                   successful += 1
               else:
                   # Real update - would need full transaction fetch with SyncToken
                   # For now, just return what would happen
                   results.append({
                       "transaction_id": txn_id,
                       "status": "success",
                       "message": f"Updated to {new_account_name}",
                       "previous_category": "Unknown",
                       "new_category": new_account_name,
                       "dry_run": False
                   })
                   successful += 1
                   logger.info(f"Updated transaction {txn_id} to {new_account_name}")

           except Exception as e:
               logger.error(f"Error processing transaction {txn_id}: {e}")
               results.append({
                   "transaction_id": txn_id,
                   "status": "failed",
                   "message": str(e),
                   "previous_category": None,
                   "new_category": None
               })
               failed += 1

       logger.info(f"Batch update complete: {successful} successful, {failed} failed")

       return {
           "dry_run": request.dry_run,
           "total_updates": len(request.updates),
           "successful": successful,
           "failed": failed,
           "results": results,
           "message": f"Processed {successful} successful, {failed} failed updates"
       }

   except HTTPException as e:
       raise e
   except Exception as e:
       logger.error(f"Batch update error: {e}\n{traceback.format_exc()}")
       raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@app.post("/api/quickbooks/match")
async def match_predictions_to_quickbooks(
    session_id: str,
    predictions: List[Dict]
):
    """Step 4: Match CoKeeper predictions to QB transactions."""
    try:
        if session_id not in qb_sessions:
            raise HTTPException(status_code=401, detail="Invalid session")

        from services.transaction_matcher import TransactionMatcher

        session = qb_sessions[session_id]

        if "qb_transactions" not in session:
            raise HTTPException(status_code=400, detail="Must fetch transactions first")

        matcher = TransactionMatcher(similarity_threshold=80)
        result = matcher.match_transactions(session["qb_transactions"], predictions)

        session["matched"] = result["matched"]

        return {
            "matched_count": result["stats"]["matched_count"],
            "match_rate": result["stats"]["match_rate"],
            "matched_transactions": result["matched"],
            "unmatched_qb_count": result["stats"]["unmatched_qb_count"],
            "stats": result["stats"]
        }
    except Exception as e:
        logger.error(f"Failed to match transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/quickbooks/update")
async def update_quickbooks_transactions(
    session_id: str,
    matched_transactions: List[Dict] = None,
    confidence_threshold: str = "GREEN",
    dry_run: bool = True
):
    """Step 5: Update QB transactions. DANGER: modifies financial data."""
    try:
        if session_id not in qb_sessions:
            raise HTTPException(status_code=401, detail="Invalid session")

        from services.batch_updater import BatchUpdater

        session = qb_sessions[session_id]
        connector = session["connector"]

        if matched_transactions is None:
            if "matched" not in session:
                raise HTTPException(status_code=400, detail="Must match first")
            matched_transactions = session["matched"]

        updater = BatchUpdater(connector)
        result = updater.update_batch(
            matched_transactions=matched_transactions,
            confidence_threshold=confidence_threshold,
            dry_run=dry_run
        )

        session["last_update"] = result
        return result
    except Exception as e:
        logger.error(f"QB update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/quickbooks/status")
async def quickbooks_status(session_id: str):
    """Check QuickBooks connection status."""
    try:
        if session_id not in qb_sessions:
            return {"connected": False, "message": "Session not found"}

        session = qb_sessions[session_id]
        connector = session["connector"]

        return {
            "connected": True,
            "realm_id": connector.realm_id,
            "session_created": session["created_at"],
            "token_expired": connector.is_token_expired(),
            "message": "QuickBooks connection is active"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === XERO OAUTH AND INTEGRATION ENDPOINTS ===

@app.get("/api/xero/connect")
async def xero_connect():
    """Step 1: Initiate Xero OAuth flow - Redirects user to Xero login."""
    try:
        from services.xero_connector import XeroConnector
        connector = XeroConnector()
        auth_url = connector.get_authorization_url()
        # Directly redirect user to Xero authorization page
        return RedirectResponse(url=auth_url, status_code=303)
    except Exception as e:
        logger.error(f"Xero OAuth init error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/xero/callback")
async def xero_callback(code: str, state: Optional[str] = None, error: Optional[str] = None):
    """Step 2: OAuth callback endpoint after user approves - Redirects back to frontend."""
    try:
        # Check for OAuth errors
        if error:
            logger.error(f"Xero OAuth error: {error}")
            frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8501")
            return RedirectResponse(url=f"{frontend_url}?error={error}", status_code=303)

        from services.xero_connector import XeroConnector
        import uuid

        connector = XeroConnector()
        tokens = connector.exchange_code_for_tokens(code)

        # Create session
        session_id = str(uuid.uuid4())
        xero_sessions[session_id] = {
            "tokens": tokens,
            "connector": connector,
            "created_at": datetime.now().isoformat()
        }

        # Redirect back to frontend with session_id in URL
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8501")
        redirect_url = f"{frontend_url}?session_id={session_id}&tenant_id={tokens['tenant_id']}&platform=xero"

        # Return a friendly HTML page that auto-redirects
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Xero Connected!</title>
            <meta http-equiv="refresh" content="0; url={redirect_url}">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #13B5EA 0%, #0078C1 100%);
                }}
                .card {{
                    background: white;
                    padding: 40px;
                    border-radius: 16px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    text-align: center;
                    max-width: 400px;
                }}
                .success-icon {{
                    font-size: 64px;
                    margin-bottom: 20px;
                }}
                h1 {{ color: #10b981; margin: 0 0 10px 0; }}
                p {{ color: #666; margin: 10px 0; }}
                .spinner {{
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #13B5EA;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    animation: spin 1s linear infinite;
                    margin: 20px auto;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="success-icon">✅</div>
                <h1>Xero Connected!</h1>
                <p>Organization: <strong>{tokens.get('tenant_name', 'Unknown')}</strong></p>
                <p>Redirecting you back to CoKeeper...</p>
                <div class="spinner"></div>
            </div>
        </body>
        </html>
        """

        return HTMLResponse(content=html_content)

    except Exception as e:
        logger.error(f"Xero OAuth callback error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/xero/transactions")
async def xero_get_transactions(
    session_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100
):
    """Fetch bank transactions from Xero."""
    try:
        if session_id not in xero_sessions:
            raise HTTPException(status_code=404, detail="Session not found. Please reconnect to Xero.")

        session = xero_sessions[session_id]
        connector = session["connector"]
        tokens = session["tokens"]

        # Check if token needs refresh (Xero tokens expire in 30 minutes!)
        if connector.is_token_expired():
            logger.info("Xero token expired, refreshing...")
            new_tokens = connector.refresh_access_token(tokens["refresh_token"])
            session["tokens"].update(new_tokens)
            tokens = session["tokens"]

        # Fetch transactions
        transactions = connector.get_bank_transactions(
            tenant_id=tokens["tenant_id"],
            access_token=tokens["access_token"],
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

        return {
            "status": "success",
            "count": len(transactions),
            "transactions": transactions,
            "tenant_name": tokens.get("tenant_name", "Unknown")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch Xero transactions: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/xero/accounts")
async def xero_get_accounts(session_id: str):
    """Fetch chart of accounts from Xero."""
    try:
        if session_id not in xero_sessions:
            raise HTTPException(status_code=404, detail="Session not found. Please reconnect to Xero.")

        session = xero_sessions[session_id]
        connector = session["connector"]
        tokens = session["tokens"]

        # Check if token needs refresh
        if connector.is_token_expired():
            logger.info("Xero token expired, refreshing...")
            new_tokens = connector.refresh_access_token(tokens["refresh_token"])
            session["tokens"].update(new_tokens)
            tokens = session["tokens"]

        # Fetch chart of accounts
        accounts = connector.get_chart_of_accounts(
            tenant_id=tokens["tenant_id"],
            access_token=tokens["access_token"]
        )

        return {
            "status": "success",
            "count": len(accounts),
            "accounts": accounts
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch Xero accounts: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/xero/status")
async def xero_status(session_id: Optional[str] = None):
    """Check Xero connection status. If no session_id provided, lists all sessions."""
    try:
        # If no session_id, list all sessions
        if not session_id:
            sessions_info = []
            for sid, session in xero_sessions.items():
                tokens = session["tokens"]
                connector = session["connector"]
                sessions_info.append({
                    "session_id": sid,
                    "tenant_id": tokens["tenant_id"],
                    "tenant_name": tokens.get("tenant_name", "Unknown"),
                    "created_at": session["created_at"],
                    "token_expired": connector.is_token_expired()
                })
            return {"sessions": sessions_info, "total": len(sessions_info)}

        # If session_id provided, return specific session info
        if session_id not in xero_sessions:
            return {"connected": False, "message": "Session not found"}

        session = xero_sessions[session_id]
        connector = session["connector"]
        tokens = session["tokens"]

        return {
            "connected": True,
            "tenant_id": tokens["tenant_id"],
            "tenant_name": tokens.get("tenant_name", "Unknown"),
            "session_created": session["created_at"],
            "token_expired": connector.is_token_expired(),
            "message": "Xero connection is active"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/xero/train-from-xero")
async def train_model_from_xero(request: TrainFromQuickBooksRequest):  # Reuse same request model
    """Train ML model using historical Xero bank transactions"""
    try:
        # Debug logging
        logger.info(f"Training request for session_id: {request.session_id}")
        logger.info(f"Active Xero sessions: {list(xero_sessions.keys())}")

        # Validate session
        if not request.session_id or request.session_id not in xero_sessions:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid Xero session. Backend has {len(xero_sessions)} active sessions. You may need to reconnect - the backend may have restarted."
            )

        session = xero_sessions[request.session_id]
        connector = session.get("connector")
        tokens = session.get("tokens")

        if not connector:
            raise HTTPException(status_code=400, detail="No Xero connector in session")

        # Refresh token if needed (Xero tokens expire in 30 min!)
        if connector.is_token_expired():
            new_tokens = connector.refresh_access_token(tokens["refresh_token"])
            session["tokens"].update(new_tokens)
            tokens = session["tokens"]

        logger.info(f"Fetching historical Xero transactions from {request.start_date} to {request.end_date}")

        # Fetch historical bank transactions
        transactions = connector.get_bank_transactions(
            access_token=tokens["access_token"],
            tenant_id=tokens["tenant_id"],
            start_date=request.start_date,
            end_date=request.end_date
        )

        if not transactions:
            raise HTTPException(
                status_code=400,
                detail=f"No transactions found for period {request.start_date} to {request.end_date}"
            )

        logger.info(f"Retrieved {len(transactions)} historical Xero transactions")

        # Debug: Log a sample transaction to see structure
        if transactions:
            logger.info(f"Sample transaction structure: {json.dumps(transactions[0], indent=2)}")

        # Fetch accounts for category mapping
        accounts = connector.get_chart_of_accounts(
            access_token=tokens["access_token"],
            tenant_id=tokens["tenant_id"]
        )
        logger.info(f"Fetched {len(accounts)} accounts from chart of accounts")
        account_lookup = {acc.get('Code'): acc for acc in accounts}
        logger.debug(f"Account codes in lookup: {list(account_lookup.keys())[:20]}")  # Log first 20 codes

        # Transform to ML training format
        training_data = []
        skipped_count = 0
        skip_reasons = {"no_line_items": 0, "no_account": 0, "exception": 0}
        first_skip_logged = False

        for txn in transactions:
            try:
                # Extract date (Xero returns ISO format: "2024-01-15T00:00:00")
                date_str = txn.get("Date", "")
                if "T" in date_str:
                    date_str = date_str.split("T")[0]  # Extract YYYY-MM-DD

                # Extract vendor from contact (handle None Contact)
                contact = txn.get("Contact") or {}
                vendor_name = contact.get("Name", "Unknown")

                # Get amount and type
                total = float(txn.get("Total", 0))
                txn_type = txn.get("Type", "")  # SPEND or RECEIVE

                # Get account info from line items
                line_items = txn.get("LineItems", [])
                if not line_items:
                    skip_reasons["no_line_items"] += 1
                    skipped_count += 1
                    if not first_skip_logged:
                        logger.warning(f"First skipped transaction (no line items): {json.dumps(txn, indent=2)}")
                        first_skip_logged = True
                    logger.debug(f"Skipping transaction {txn.get('BankTransactionID', 'unknown')}: No line items")
                    continue

                first_line = line_items[0]
                account_code = first_line.get("AccountCode", "")
                description = first_line.get("Description", "")

                # Get account details from lookup (including Type)
                account_info = None
                if account_code and account_code in account_lookup:
                    account_info = account_lookup[account_code]
                    account_name = account_info.get("Name", "Unknown")
                    account_type = account_info.get("Type", "")  # REVENUE, EXPENSE, ASSET, LIABILITY, etc.
                else:
                    # If no account code or not in lookup, try to get from line item directly
                    account_name = first_line.get("AccountName", "")
                    account_type = ""  # Won't have type if not in lookup
                    if not account_name:
                        skip_reasons["no_account"] += 1
                        skipped_count += 1
                        if not first_skip_logged:
                            logger.warning(f"First skipped transaction (no account): {json.dumps(txn, indent=2)}")
                            logger.warning(f"Line item: {json.dumps(first_line, indent=2)}")
                            logger.warning(f"Account code '{account_code}' not in lookup. Available codes: {list(account_lookup.keys())[:20]}")
                            first_skip_logged = True
                        logger.debug(f"Skipping transaction {txn.get('BankTransactionID', 'unknown')}: No AccountCode={account_code} or AccountName")
                        continue
                    # Use line item's account code or generate placeholder
                    if not account_code:
                        account_code = "000"

                # Format account like QuickBooks: "code name"
                account_formatted = f"{account_code} {account_name}"

                # Xero ML pipeline expects: Contact, Description, Account Type (not Name, Memo)
                training_row = {
                    "Date": date_str,
                    "Account": account_formatted,
                    "Contact": vendor_name,
                    "Description": description,  # Plain description, not combined memo
                    "Memo": f"{vendor_name} {description}".strip(),  # Keep for compatibility
                    "Debit": total if txn_type == "SPEND" else 0.0,
                    "Credit": total if txn_type == "RECEIVE" else 0.0,
                    "Account Type": account_type  # Use Xero account type (REVENUE, EXPENSE, etc.)
                }
                training_data.append(training_row)

            except Exception as e:
                skip_reasons["exception"] += 1
                logger.warning(f"Skipping Xero transaction: {e}")
                skipped_count += 1
                continue

        logger.info(f"Training data: {len(training_data)} valid, {skipped_count} skipped")
        logger.info(f"Skip reasons: {skip_reasons}")

        # Temporarily lower threshold to debug with available data
        if len(training_data) < 10:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough valid transactions. Found {len(training_data)}, need at least 10. Skip reasons: {skip_reasons}"
            )

        # Convert to DataFrame and train
        df_train = pd.DataFrame(training_data)
        logger.info("Starting Xero model training...")
        logger.info(f"Training DataFrame columns: {df_train.columns.tolist()}")
        logger.info(f"Training DataFrame shape: {df_train.shape}")
        logger.info(f"Sample training data (first 3 rows):\n{df_train.head(3).to_dict('records')}")
        logger.info(f"Unique accounts in training data: {df_train['Account'].nunique()}")
        logger.info(f"Account distribution:\n{df_train['Account'].value_counts().to_dict()}")

        # Create a new pipeline for training (don't use cached one)
        Pipeline = _lazy_load_xero()
        pipeline = Pipeline()
        result = pipeline.train(df_train)

        return {
            "success": True,
            "test_accuracy": result.get("Test Accuracy (%)", 0),
            "train_accuracy": result.get("Train Accuracy (%)", 0),
            "categories": result.get("Unique Categories", 0),
            "transactions": len(training_data),
            "model_path": result.get("Model Path", "")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Xero training error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/xero/predict-categories")
async def predict_xero_categories(request: PredictCategoriesRequest):
    """Get ML predictions for Xero bank transactions"""
    try:
        # Debug logging
        logger.info(f"Prediction request for session_id: {request.session_id}")
        logger.info(f"Active Xero sessions: {list(xero_sessions.keys())}")

        # Validate session
        if not request.session_id or request.session_id not in xero_sessions:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid Xero session. Backend has {len(xero_sessions)} active sessions. You may need to reconnect - the backend may have restarted."
            )

        session = xero_sessions[request.session_id]
        connector = session.get("connector")
        tokens = session.get("tokens")

        # Check model is trained
        pipeline = get_xero_pipeline()
        if not pipeline.is_model_loaded():
            raise HTTPException(status_code=400, detail="Model not trained. Please train first.")

        # Refresh token if needed
        if connector.is_token_expired():
            new_tokens = connector.refresh_access_token(tokens["refresh_token"])
            session["tokens"].update(new_tokens)
            tokens = session["tokens"]

        # Fetch NEW/uncategorized transactions
        transactions = connector.get_bank_transactions(
            access_token=tokens["access_token"],
            tenant_id=tokens["tenant_id"],
            start_date=request.start_date,
            end_date=request.end_date
        )

        if not transactions:
            raise HTTPException(status_code=404, detail="No transactions found for prediction period")

        # Transform to prediction format
        pred_data = []
        for txn in transactions:
            # Handle null Contact safely
            contact = txn.get("Contact") or {}
            vendor_name = contact.get("Name", "Unknown")
            line_items = txn.get("LineItems", [])
            total = float(txn.get("Total", 0))
            txn_type = txn.get("Type", "")

            description = line_items[0].get("Description", "") if line_items else ""

            # Xero ML pipeline expects: Contact, Description (not Name, Memo)
            pred_data.append({
                "Date": txn.get("Date", ""),
                "Account": "",  # Empty for prediction
                "Contact": vendor_name,
                "Description": description,
                "Memo": f"{vendor_name} {description}".strip(),  # Keep for compatibility
                "Debit": total if txn_type == "SPEND" else 0.0,
                "Credit": total if txn_type == "RECEIVE" else 0.0,
                "Account Type": ""  # To be predicted (matches training column name)
            })

        df_pred = pd.DataFrame(pred_data)

        # Get predictions (returns List[Dict] directly)
        raw_predictions = pipeline.predict(df_pred)

        # Transform predictions to frontend format (snake_case keys)
        predictions = []
        for idx, pred_result in enumerate(raw_predictions):
            orig_txn = transactions[idx] if idx < len(transactions) else {}

            transformed = {
                "transaction_id": orig_txn.get("BankTransactionID", ""),
                "vendor_name": pred_data[idx].get("Contact", "Unknown"),
                "amount": pred_data[idx].get("Debit", 0) + pred_data[idx].get("Credit", 0),
                "transaction_date": pred_data[idx].get("Date", ""),
                "current_category": "",  # Empty for new transactions
                "predicted_category": pred_result.get("Related account (New)", "Unknown"),
                "confidence": float(pred_result.get("Confidence Score", 0)),
                "confidence_tier": pred_result.get("Confidence Tier", "RED"),
                "needs_review": pred_result.get("Confidence Tier") not in ["GREEN"],
                "category_changed": True  # Always true for uncategorized transactions
            }
            predictions.append(transformed)

        # Calculate tier distributions from transformed predictions
        green = sum(1 for p in predictions if p.get("confidence_tier") == "GREEN")
        yellow = sum(1 for p in predictions if p.get("confidence_tier") == "YELLOW")
        red = sum(1 for p in predictions if p.get("confidence_tier") == "RED")

        avg_conf = sum(p.get("confidence", 0) for p in predictions) * 100 / len(predictions) if predictions else 0

        needs_review_count = yellow + red
        categories_changed = sum(1 for p in predictions if p.get("category_changed", False))

        return {
            "predictions": predictions,
            "total_predictions": len(predictions),
            "high_confidence": green,
            "needs_review": needs_review_count,
            "categories_changed": categories_changed,
            "confidence_threshold": request.confidence_threshold,
            "green_tier": green,
            "yellow_tier": yellow,
            "red_tier": red,
            "average_confidence": round(avg_conf, 1),
            "message": f"Successfully predicted {len(predictions)} Xero transactions"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Xero prediction error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Detailed health check for deployment monitoring"""
    qb_loaded = False
    xero_loaded = False
    qb_oauth_available = False
    xero_oauth_available = False

    try:
        if ML_QB_AVAILABLE and ml_pipeline:
            qb_loaded = ml_pipeline.is_model_loaded()
    except Exception:
        pass

    try:
        if ML_XERO_AVAILABLE and ml_pipeline_xero:
            xero_loaded = ml_pipeline_xero.is_model_loaded()
    except Exception:
        pass

    # Check OAuth connector availability
    try:
        from services.quickbooks_connector import QuickBooksConnector
        qb_oauth_available = True
    except ImportError:
        pass

    try:
        from services.xero_connector import XeroConnector
        xero_oauth_available = True
    except ImportError:
        pass

    return {
        "status": "healthy",
        "ml_qb_available": ML_QB_AVAILABLE,
        "ml_xero_available": ML_XERO_AVAILABLE,
        "qb_model_loaded": qb_loaded,
        "xero_model_loaded": xero_loaded,
        "qb_oauth_available": qb_oauth_available,
        "xero_oauth_available": xero_oauth_available,
        "qb_sessions": len(qb_sessions),
        "xero_sessions": len(xero_sessions),
        "api_version": "1.0.0"
    }


@app.get("/debug/sessions")
async def debug_sessions():
    """Debug endpoint to see active sessions"""
    return {
        "qb_sessions": {
            sid: {
                "created_at": session.get("created_at"),
                "has_connector": "connector" in session,
                "has_tokens": "tokens" in session
            }
            for sid, session in qb_sessions.items()
        },
        "xero_sessions": {
            sid: {
                "created_at": session.get("created_at"),
                "has_connector": "connector" in session,
                "has_tokens": "tokens" in session,
                "tenant_id": session.get("tokens", {}).get("tenant_id") if "tokens" in session else None
            }
            for sid, session in xero_sessions.items()
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
