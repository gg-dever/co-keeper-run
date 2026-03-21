"""
CoKeeper Production Pipeline
============================

Core ML pipeline for GL categorization with:
- Vendor Intelligence matching
- TF-IDF feature extraction
- Dual CatBoost model architecture (matched/unmatched)
- Confidence scoring and review tier assignment
"""

import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from catboost import CatBoostClassifier

from src.features.vendor_intelligence import VendorIntelligence
from src.features.merchant_normalizer import MerchantNormalizer

logger = logging.getLogger(__name__)


class CoKeeperPipeline:
    """Production GL categorization pipeline."""
    
    def __init__(self, model_path: str = None):
        """
        Initialize pipeline.
        
        Args:
            model_path: Path to load existing model. If None, creates new.
        """
        self.model_path = Path(model_path) if model_path else None
        self.tfidf = None
        self.vendor_intelligence = None
        self.model_matched = None
        self.model_unmatched = None
        self.label_encoder = {}  # Maps category names to integers
        self.categories = []
        self.is_trained = False
        
        if model_path and Path(model_path).exists():
            self.load(model_path)
    
    def fit(self, df: pd.DataFrame, val_size=0.2):
        """
        Train the pipeline on labeled data.
        
        Args:
            df: DataFrame with columns ['vendor_name', 'description', 'amount', 'category']
            val_size: Test split ratio (no separate validation)
        
        Returns:
            Dict with training metrics
        """
        logger.info(f"Starting training on {len(df)} records (single model approach)")
        
        # Prepare data
        df_clean = df[['vendor_name', 'description', 'amount', 'category']].copy()
        df_clean = df_clean.dropna(subset=['description', 'category'])
        
        # Create label encoder
        self.categories = sorted(df_clean['category'].unique().tolist())
        self.label_encoder = {cat: idx for idx, cat in enumerate(self.categories)}
        labels = df_clean['category'].map(self.label_encoder).values
        
        # Stratified split into train and test only (no validation split)
        try:
            train, test = train_test_split(
                df_clean,
                test_size=val_size,
                random_state=42,
                stratify=labels
            )
            logger.info("✓ Using stratified split (balanced categories)")
        except ValueError as e:
            logger.warning(f"Stratification failed, using random split: {e}")
            train, test = train_test_split(
                df_clean,
                test_size=val_size,
                random_state=42
            )
        
        logger.info(f"Split: train={len(train)}, test={len(test)}")
        
        # Initialize Vendor Intelligence
        self.vendor_intelligence = VendorIntelligence(
            exact_min_consistency=0.80,
            exact_min_occurrences=2,
            use_merchant_normalization=True
        )
        
        train_vi_data = train[['vendor_name', 'description', 'amount', 'category']].copy()
        train_vi_data.rename(columns={'category': 'category_true'}, inplace=True)
        self.vendor_intelligence.fit(train_vi_data)
        
        logger.info(f"Vendor Intelligence: {len(self.vendor_intelligence.exact_matcher.vendor_map)} vendor mappings")
        
        # Build TF-IDF features
        self.tfidf = TfidfVectorizer(
            max_features=500,
            ngram_range=(1, 2),
            min_df=2,
            stop_words='english'
        )
        
        train_tfidf = self.tfidf.fit_transform(train['description'].fillna(''))
        test_tfidf = self.tfidf.transform(test['description'].fillna(''))
        
        # Create feature dataframes with TF-IDF
        tfidf_cols = [f'tfidf_{i}' for i in range(train_tfidf.shape[1])]
        train_features = pd.DataFrame(train_tfidf.toarray(), columns=tfidf_cols, index=train.index)
        test_features = pd.DataFrame(test_tfidf.toarray(), columns=tfidf_cols, index=test.index)
        
        # Add amount feature
        train_features['amount'] = train['amount'].values
        test_features['amount'] = test['amount'].values
        
        logger.info(f"TF-IDF features: {len(tfidf_cols)} features + amount")
        
        # Build Vendor Intelligence features (used for all records, not for splitting)
        def apply_vi_features(df_rows, features_df, vi_model):
            """Apply VI and return numeric features (confidence, match flag)."""
            vi_confidence = []
            vi_has_match = []
            
            for idx, row in df_rows.iterrows():
                result = vi_model.classify(
                    vendor_name=row['vendor_name'],
                    description=row['description'],
                    amount=row['amount']
                )
                vi_confidence.append(result.confidence)
                vi_has_match.append(1 if result.match_level != 'none' else 0)
            
            features_df['vi_confidence'] = vi_confidence
            features_df['vi_has_match'] = vi_has_match
            return features_df
        
        train_features = apply_vi_features(train, train_features, self.vendor_intelligence)
        test_features = apply_vi_features(test, test_features, self.vendor_intelligence)
        
        logger.info(f"Added VI features: vi_confidence, vi_has_match")
        
        # Prepare labels for all data
        y_train = train['category'].map(self.label_encoder).values
        y_test = test['category'].map(self.label_encoder).values
        
        # Train single unified model
        logger.info("Training unified CatBoost model...")
        self.model = CatBoostClassifier(
            iterations=100,
            learning_rate=0.1,
            depth=6,
            verbose=0,
            random_state=42
        )
        
        self.model.fit(train_features, y_train)
        
        # Evaluate
        test_pred = self.model.predict(test_features)
        accuracy = accuracy_score(y_test, test_pred)
        
        self.is_trained = True
        
        logger.info(f"✓ Training complete. Test accuracy: {accuracy:.1%}")
        
        return {
            'accuracy': float(accuracy),
            'train_size': len(train),
            'test_size': len(test),
            'n_categories': len(self.categories),
            'n_features': train_features.shape[1]
        }
    
    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Make predictions on new data.
        
        Args:
            df: DataFrame with columns ['vendor_name', 'description', 'amount']
        
        Returns:
            DataFrame with predictions and confidence scores
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        df = df.copy()
        df = df.fillna({'description': '', 'vendor_name': ''})
        
        # Build TF-IDF features
        tfidf_features = self.tfidf.transform(df['description'])
        tfidf_cols = [f'tfidf_{i}' for i in range(tfidf_features.shape[1])]
        features = pd.DataFrame(tfidf_features.toarray(), columns=tfidf_cols, index=df.index)
        
        # Add amount feature
        features['amount'] = df['amount'].values
        
        # Apply VI features
        vi_confidence = []
        vi_has_match = []
        for idx, row in df.iterrows():
            result = self.vendor_intelligence.classify(
                vendor_name=row['vendor_name'],
                description=row['description'],
                amount=row['amount']
            )
            vi_confidence.append(result.confidence)
            vi_has_match.append(1 if result.match_level != 'none' else 0)
        
        features['vi_confidence'] = vi_confidence
        features['vi_has_match'] = vi_has_match
        
        # Single model prediction
        predictions = self.model.predict(features)
        probabilities = self.model.predict_proba(features).max(axis=1)
        
        # Decode labels
        reverse_encoder = {v: k for k, v in self.label_encoder.items()}
        categories = [reverse_encoder.get(int(p), 'unknown') for p in predictions]
        
        # Assign review tiers
        def assign_tier(confidence):
            if confidence >= 0.9:
                return 'GREEN'
            elif confidence >= 0.7:
                return 'YELLOW'
            else:
                return 'RED'
        
        tiers = [assign_tier(p) for p in probabilities]
        
        results = pd.DataFrame({
            'vendor_name': df['vendor_name'].values,
            'description': df['description'].values,
            'amount': df['amount'].values,
            'predicted_category': categories,
            'confidence': probabilities,
            'review_tier': tiers
        })
        
        return results
    
    def save(self, path: str):
        """Save model to disk."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        
        # Save single model
        with open(path / 'model.pkl', 'wb') as f:
            pickle.dump(self.model, f)
        
        # Save TF-IDF
        with open(path / 'tfidf.pkl', 'wb') as f:
            pickle.dump(self.tfidf, f)
        
        # Save VI
        with open(path / 'vendor_intelligence.pkl', 'wb') as f:
            pickle.dump(self.vendor_intelligence, f)
        
        # Save metadata
        metadata = {
            'categories': self.categories,
            'label_encoder': self.label_encoder,
            'is_trained': self.is_trained,
            'saved_at': datetime.now().isoformat()
        }
        
        with open(path / 'metadata.pkl', 'wb') as f:
            pickle.dump(metadata, f)
        
        logger.info(f"Model saved to {path}")
    
    def load(self, path: str):
        """Load model from disk."""
        path = Path(path)
        
        with open(path / 'model.pkl', 'rb') as f:
            self.model = pickle.load(f)
        
        with open(path / 'tfidf.pkl', 'rb') as f:
            self.tfidf = pickle.load(f)
        
        with open(path / 'vendor_intelligence.pkl', 'rb') as f:
            self.vendor_intelligence = pickle.load(f)
        
        with open(path / 'metadata.pkl', 'rb') as f:
            metadata = pickle.load(f)
        
        self.categories = metadata['categories']
        self.label_encoder = metadata['label_encoder']
        self.is_trained = metadata['is_trained']
        
        logger.info(f"Model loaded from {path}")
