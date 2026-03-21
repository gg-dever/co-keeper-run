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
from typing import Dict, Any, Optional
import logging
import traceback

# Try to import ML pipelines, but don't fail if they're not available
try:
    from ml_pipeline_qb import QuickBooksPipeline as MLPipeline
    ML_QB_AVAILABLE = True
except Exception as e:
    logging.warning(f"QuickBooks ML Pipeline not available: {e}")
    MLPipeline = None
    ML_QB_AVAILABLE = False

try:
    from ml_pipeline_xero import MLPipelineXero
    ML_XERO_AVAILABLE = True
except Exception as e:
    logging.warning(f"Xero ML Pipeline not available: {e}")
    MLPipelineXero = None
    ML_XERO_AVAILABLE = False

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
    if ml_pipeline is None:
        ml_pipeline = MLPipeline()
    return ml_pipeline


def get_xero_pipeline():
    """Lazy initialize Xero pipeline"""
    global ml_pipeline_xero
    if not ML_XERO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Xero ML pipeline is not available")
    if ml_pipeline_xero is None:
        ml_pipeline_xero = MLPipelineXero()
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


@app.get("/health")
async def health_check():
    """Detailed health check for deployment monitoring"""
    try:
        qb_loaded = get_qb_pipeline().is_model_loaded() if (ML_QB_AVAILABLE and ml_pipeline) else False
    except Exception:
        qb_loaded = False

    try:
        xero_loaded = get_xero_pipeline().is_model_loaded() if (ML_XERO_AVAILABLE and ml_pipeline_xero) else False
    except Exception:
        xero_loaded = False

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
