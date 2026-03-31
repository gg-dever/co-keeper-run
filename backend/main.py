"""
FastAPI Backend for CoKeeper Transaction Categorization
Minimal demo with 2 endpoints: /train and /predict
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import io
import os
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


def get_qb_pipeline():
    """Lazy initialize QuickBooks pipeline"""
    global ml_pipeline
    if not ML_QB_AVAILABLE:
        raise HTTPException(status_code=503, detail="QuickBooks ML pipeline is not available")
    Pipeline = _lazy_load_qb()  # Load the class on first call
    if ml_pipeline is None:
        ml_pipeline = Pipeline()
    return ml_pipeline


def get_xero_pipeline():
    """Lazy initialize Xero pipeline"""
    global ml_pipeline_xero
    if not ML_XERO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Xero ML pipeline is not available")
    Pipeline = _lazy_load_xero()  # Load the class on first call
    if ml_pipeline_xero is None:
        ml_pipeline_xero = Pipeline()
    return ml_pipeline_xero


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

        # Get the pipeline
        pipeline = get_qb_pipeline()

        # Try to load model from disk if not already loaded (important for Cloud Run persistence)
        default_model_path = "models/naive_bayes_model.pkl"
        if not pipeline.is_model_loaded():
            if os.path.exists(default_model_path):
                logger.info(f"Loading trained model from {default_model_path}")
                pipeline = MLPipeline.load_model(default_model_path)
                # Update the global pipeline
                globals()['ml_pipeline'] = pipeline
            else:
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

        # Get the pipeline
        pipeline = get_xero_pipeline()

        # Try to load model from disk if not already loaded (important for Cloud Run persistence)
        default_model_path = "models/xero_model.pkl"
        if not pipeline.is_model_loaded():
            if os.path.exists(default_model_path):
                logger.info(f"Loading trained Xero model from {default_model_path}")
                pipeline.load_model(default_model_path)
            else:
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

qb_sessions = {}


@app.get("/api/quickbooks/connect")
async def quickbooks_connect():
    """Step 1: Initiate QuickBooks OAuth flow."""
    try:
        from services.quickbooks_connector import QuickBooksConnector
        connector = QuickBooksConnector()
        auth_url = connector.get_authorization_url()
        return {
            "auth_url": auth_url,
            "message": "Redirect user to this URL to grant QuickBooks access"
        }
    except Exception as e:
        logger.error(f"QB OAuth init error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/quickbooks/callback")
async def quickbooks_callback(code: str, realmId: str, state: Optional[str] = None):
    """Step 2: OAuth callback endpoint after user approves."""
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

        return {
            "session_id": session_id,
            "realm_id": realmId,
            "message": "Successfully connected to QuickBooks"
        }
    except Exception as e:
        logger.error(f"QB callback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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


@app.get("/health")
async def health_check():
    """Detailed health check for deployment monitoring"""
    qb_loaded = False
    xero_loaded = False

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

    return {
        "status": "healthy",
        "ml_qb_available": ML_QB_AVAILABLE,
        "ml_xero_available": ML_XERO_AVAILABLE,
        "qb_model_loaded": qb_loaded,
        "xero_model_loaded": xero_loaded,
        "api_version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
