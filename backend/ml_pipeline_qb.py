"""
CoKeeper Production Pipeline - QuickBooks Categorization v2

MultinomialNB Classifier with Triple TF-IDF + 5-Layer Validation
- Test Accuracy: 92.5%
- Features: 863 (TF-IDF: 851, VI: 2, Transport: 8, Rules: 2)
- Model: MultinomialNB (alpha=1.0, K=100)

Author: CoKeeper AI
Date: March 2026
"""

import pandas as pd
import numpy as np
import pickle
import os
from typing import Dict, Tuple, Optional, List, Any
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_selection import SelectKBest, chi2
import warnings
warnings.filterwarnings('ignore')

# Import CoKeeper modules
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.features.vendor_intelligence import VendorIntelligence
from src.features.rule_based_classifier import RuleBasedClassifier
from src.features.post_prediction_validator import PostPredictionValidator
from src.features.transportation_keywords import detect_transportation_type


class QuickBooksPipeline:
    """
    Production pipeline for QuickBooks transaction categorization.

    Features:
    - Triple TF-IDF (word + char + trigram)
    - Vendor Intelligence matching
    - Transportation keyword detection
    - Rule-based classification
    - 5-layer post-prediction validation

    Usage:
        # Training
        pipeline = QuickBooksPipeline()
        pipeline.train(training_csv_path)
        pipeline.save_model('models/qb_pipeline_v2.pkl')

        # Prediction
        pipeline = QuickBooksPipeline.load_model('models/qb_pipeline_v2.pkl')
        predictions = pipeline.predict(new_csv_path)
    """

    def __init__(self, alpha: float = 1.0, k_best: int = 100, min_examples: int = 10):
        """
        Initialize pipeline with hyperparameters.

        Args:
            alpha: Laplace smoothing for MultinomialNB
            k_best: Number of features to select with SelectKBest
            min_examples: Minimum category examples for training
        """
        self.alpha = alpha
        self.k_best = k_best
        self.min_examples = min_examples

        # Model components (initialized during training)
        self.model = None
        self.selector = None
        self.tfidf_word = None
        self.tfidf_char = None
        self.tfidf_trigram = None
        self.vendor_intelligence = None
        self.rule_classifier = None
        self.validator = None

        # Feature names for consistent ordering
        self.tfidf_cols = None
        self.tfidf_char_cols = None
        self.tfidf_trigram_cols = None

        # Training metadata
        self.training_categories = None
        self.category_types = ['EXPENSE', 'COGS', 'INCOME', 'OTHER_INCOME', 'OTHER_EXPENSE']
        self.test_accuracy = None

    @staticmethod
    def classify_account(account_str: str) -> Tuple[str, str, str]:
        """
        Classify QuickBooks account by code into type.

        Args:
            account_str: Account string from QuickBooks (e.g., "50000.1 Advertising")

        Returns:
            Tuple of (account_type, account_code, account_name)
        """
        if pd.isna(account_str):
            return 'UNKNOWN', '', ''

        account_str = str(account_str).strip()
        parts = account_str.split(' ', 1)
        code_str = parts[0]
        name = parts[1] if len(parts) > 1 else account_str

        try:
            code_num = float(code_str.split('.')[0])
        except ValueError:
            return 'UNKNOWN', code_str, name

        # QuickBooks Chart of Accounts structure
        if code_num < 20000:
            acct_type = 'ASSET'
        elif code_num < 30000:
            acct_type = 'LIABILITY'
        elif code_num < 40000:
            acct_type = 'EQUITY'
        elif code_num < 50000:
            acct_type = 'INCOME'
        elif code_num < 60000:
            acct_type = 'COGS'
        elif code_num < 80000:
            acct_type = 'EXPENSE'
        elif code_num < 90000:
            acct_type = 'OTHER_INCOME'
        elif code_num < 100000:
            acct_type = 'OTHER_EXPENSE'
        else:
            acct_type = 'UNKNOWN'

        return acct_type, code_str, name

    def prepare_training_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare and clean training data.

        Args:
            df: Raw QuickBooks general ledger DataFrame

        Returns:
            Cleaned training DataFrame
        """
        # Classify accounts
        df[['account_type', 'account_code', 'account_name']] = df['Account'].apply(
            lambda x: pd.Series(self.classify_account(x))
        )

        # Filter to trained account types only
        clean = df[df['account_type'].isin(self.category_types)].copy()

        # Extract vendor name and description
        memo_cols = [c for c in df.columns if 'memo' in c.lower() or 'description' in c.lower()]
        memo_col = memo_cols[0] if memo_cols else None

        clean['vendor_name'] = clean['Name'].fillna('').str.strip()
        clean['memo'] = clean[memo_col].fillna('').str.strip() if memo_col else ''
        clean['description'] = clean.apply(
            lambda row: ' '.join(filter(None, [row['vendor_name'], row['memo']])).strip(),
            axis=1
        )

        # Calculate amount and extract ground truth
        clean['amount'] = clean['Debit'].fillna(0) + clean['Credit'].fillna(0)
        clean['category_true'] = clean['Transaction Type']
        clean['date'] = pd.to_datetime(clean['Date'], errors='coerce')

        # Filter valid transactions
        training_data = clean[['date', 'description', 'vendor_name', 'amount', 'category_true', 'account_code']].copy()
        training_data = training_data[training_data['amount'] > 0]
        training_data = training_data[training_data['description'].str.strip().str.len() > 0]

        # Remove categories with too few examples
        cat_counts = training_data['category_true'].value_counts()
        small_cats = cat_counts[cat_counts < self.min_examples].index
        if len(small_cats) > 0:
            training_data = training_data[~training_data['category_true'].isin(small_cats)]

        self.training_categories = training_data['category_true'].unique().tolist()

        return training_data

    def extract_tfidf_features(self, train_df: pd.DataFrame, val_df: pd.DataFrame,
                               test_df: pd.DataFrame) -> Tuple:
        """
        Extract triple TF-IDF features (word + char + trigram).

        Args:
            train_df, val_df, test_df: Split DataFrames

        Returns:
            Tuple of (train_features, val_features, test_features)
        """
        # Layer 1: Word-level TF-IDF (1-2 grams)
        self.tfidf_word = TfidfVectorizer(
            max_features=500,
            ngram_range=(1, 2),
            min_df=2,
            stop_words='english'
        )
        train_tfidf = self.tfidf_word.fit_transform(train_df['description'].fillna(''))
        val_tfidf = self.tfidf_word.transform(val_df['description'].fillna(''))
        test_tfidf = self.tfidf_word.transform(test_df['description'].fillna(''))

        self.tfidf_cols = [f'tfidf_{i}' for i in range(train_tfidf.shape[1])]
        train_features = pd.DataFrame(train_tfidf.toarray(), columns=self.tfidf_cols)
        val_features = pd.DataFrame(val_tfidf.toarray(), columns=self.tfidf_cols)
        test_features = pd.DataFrame(test_tfidf.toarray(), columns=self.tfidf_cols)

        # Add amount feature
        train_features['amount_log'] = np.log1p(train_df['amount'].values)
        val_features['amount_log'] = np.log1p(val_df['amount'].values)
        test_features['amount_log'] = np.log1p(test_df['amount'].values)

        # Layer 2: Character-level TF-IDF (3-5 grams)
        self.tfidf_char = TfidfVectorizer(
            max_features=200,
            analyzer='char',
            ngram_range=(3, 5),
            min_df=2,
            max_df=0.8
        )
        train_char = self.tfidf_char.fit_transform(train_df['description'].fillna(''))
        val_char = self.tfidf_char.transform(val_df['description'].fillna(''))
        test_char = self.tfidf_char.transform(test_df['description'].fillna(''))

        self.tfidf_char_cols = [f'char_tfidf_{i}' for i in range(train_char.shape[1])]
        train_char_features = pd.DataFrame(train_char.toarray(), columns=self.tfidf_char_cols)
        val_char_features = pd.DataFrame(val_char.toarray(), columns=self.tfidf_char_cols)
        test_char_features = pd.DataFrame(test_char.toarray(), columns=self.tfidf_char_cols)

        train_features = pd.concat([train_features, train_char_features], axis=1)
        val_features = pd.concat([val_features, val_char_features], axis=1)
        test_features = pd.concat([test_features, test_char_features], axis=1)

        # Layer 3: Word trigrams (2-3 grams)
        self.tfidf_trigram = TfidfVectorizer(
            max_features=150,
            analyzer='word',
            ngram_range=(2, 3),
            min_df=2,
            max_df=0.8,
            stop_words=None
        )
        train_trigram = self.tfidf_trigram.fit_transform(train_df['description'].fillna(''))
        val_trigram = self.tfidf_trigram.transform(val_df['description'].fillna(''))
        test_trigram = self.tfidf_trigram.transform(test_df['description'].fillna(''))

        self.tfidf_trigram_cols = [f'trigram_tfidf_{i}' for i in range(train_trigram.shape[1])]
        train_trigram_features = pd.DataFrame(train_trigram.toarray(), columns=self.tfidf_trigram_cols)
        val_trigram_features = pd.DataFrame(val_trigram.toarray(), columns=self.tfidf_trigram_cols)
        test_trigram_features = pd.DataFrame(test_trigram.toarray(), columns=self.tfidf_trigram_cols)

        train_features = pd.concat([train_features, train_trigram_features], axis=1)
        val_features = pd.concat([val_features, val_trigram_features], axis=1)
        test_features = pd.concat([test_features, test_trigram_features], axis=1)

        return train_features, val_features, test_features

    def apply_vendor_intelligence(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract vendor intelligence features."""
        vi_results = []
        for _, row in df.iterrows():
            result = self.vendor_intelligence.classify(
                vendor_name=row['vendor_name'],
                description=row['description'],
                amount=row['amount']
            )
            vi_results.append({
                'vi_confidence': result.confidence,
                'has_match': 1 if result.match_level != 'none' else 0
            })
        return pd.DataFrame(vi_results)

    def apply_transportation_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract transportation keyword features."""
        transport_features = pd.DataFrame(index=df.index)
        categories = ['airline', 'rideshare', 'gas_station', 'parking',
                     'public_transit', 'toll', 'car_rental', 'auto_service']

        for cat in categories:
            transport_features[f'is_{cat}'] = 0

        for idx, row in df.iterrows():
            transport_type = detect_transportation_type(
                description=row['description'],
                vendor_name=row['vendor_name']
            )
            if transport_type:
                transport_features.loc[idx, f'is_{transport_type}'] = 1

        return transport_features

    def apply_rule_classifier(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply rule-based classification."""
        rb_results = []
        for _, row in df.iterrows():
            result = self.rule_classifier.classify(
                description=row['description'],
                vendor_name=row['vendor_name'],
                amount=row['amount'],
                vendor_type=None
            )
            rb_results.append({
                'rule_prediction': result.transaction_type if result.transaction_type else '',
                'rule_confidence': result.confidence,
                'has_rule_match': 1 if result.transaction_type else 0
            })
        return pd.DataFrame(rb_results)

    def is_model_loaded(self) -> bool:
        """
        Check if a trained model is ready for predictions.

        Returns:
            bool: True if model is loaded and ready, False otherwise
        """
        return self.model is not None

    def train(self, df: pd.DataFrame, test_size: float = 0.30) -> Dict[str, Any]:
        """
        Train the pipeline on historical QuickBooks data.

        Args:
            df: DataFrame with QuickBooks general ledger data
            test_size: Fraction of data for validation+test (default 0.30)

        Returns:
            Training metrics dictionary with keys required by FRONTBACK API:
            - test_accuracy: float (0-100 scale)
            - validation_accuracy: float (0-100 scale)
            - train_accuracy: float (0-100 scale)
            - categories: int (number of unique categories)
            - transactions: int (total training samples)
            - model_path: str (where model was saved)
            - message: str (human-readable status)
        """
        print(f"Training on {len(df)} transactions...")

        # Prepare data
        training_data = self.prepare_training_data(df)
        print(f"Training: {len(training_data)} transactions, {len(self.training_categories)} categories")

        # Split data (70/15/15)
        train, temp = train_test_split(
            training_data,
            test_size=test_size,
            stratify=training_data['category_true'],
            random_state=42
        )
        val, test = train_test_split(
            temp,
            test_size=0.50,
            stratify=temp['category_true'],
            random_state=42
        )
        train = train.reset_index(drop=True)
        val = val.reset_index(drop=True)
        test = test.reset_index(drop=True)

        print(f"Split: Train {len(train)}, Val {len(val)}, Test {len(test)}")

        # Extract TF-IDF features
        print("Extracting TF-IDF features...")
        train_features, val_features, test_features = self.extract_tfidf_features(train, val, test)
        print(f"TF-IDF features: {train_features.shape[1]} (word: 501, char: 200, trigram: 150)")

        # Initialize and train Vendor Intelligence
        print("Training Vendor Intelligence...")
        self.vendor_intelligence = VendorIntelligence(
            exact_min_consistency=0.80,
            exact_min_occurrences=2,
            use_merchant_normalization=True
        )
        train_vi_data = train[['vendor_name', 'description', 'amount', 'category_true']].copy()
        self.vendor_intelligence.fit(train_vi_data)

        train_vi = self.apply_vendor_intelligence(train)
        val_vi = self.apply_vendor_intelligence(val)
        test_vi = self.apply_vendor_intelligence(test)
        print(f"VI coverage: {train_vi['has_match'].mean()*100:.1f}%")

        # Extract transportation features
        print("Extracting transportation features...")
        train_transport = self.apply_transportation_features(train)
        val_transport = self.apply_transportation_features(val)
        test_transport = self.apply_transportation_features(test)

        # Initialize rule classifier
        print("Applying rule-based classifier...")
        self.rule_classifier = RuleBasedClassifier()
        train_rules = self.apply_rule_classifier(train)
        val_rules = self.apply_rule_classifier(val)
        test_rules = self.apply_rule_classifier(test)
        print(f"Rule coverage: {train_rules['has_rule_match'].mean()*100:.1f}%")

        # Combine all features
        train_rules_numeric = train_rules[['rule_confidence', 'has_rule_match']]
        val_rules_numeric = val_rules[['rule_confidence', 'has_rule_match']]
        test_rules_numeric = test_rules[['rule_confidence', 'has_rule_match']]

        train_combined = pd.concat([train_features, train_vi, train_transport, train_rules_numeric], axis=1)
        val_combined = pd.concat([val_features, val_vi, val_transport, val_rules_numeric], axis=1)
        test_combined = pd.concat([test_features, test_vi, test_transport, test_rules_numeric], axis=1)

        train_labels = train['category_true'].astype(str).to_numpy()
        val_labels = val['category_true'].astype(str).to_numpy()
        test_labels = test['category_true'].astype(str).to_numpy()

        print(f"Combined: {train_combined.shape[1]} features (TF-IDF: {train_features.shape[1]}, VI: 2, Transport: 8, Rules: 2)")

        # Feature selection with SelectKBest
        print(f"Selecting top {self.k_best} features...")
        self.selector = SelectKBest(chi2, k=self.k_best)
        train_final = self.selector.fit_transform(train_combined, train_labels)
        val_final = self.selector.transform(val_combined)
        test_final = self.selector.transform(test_combined)

        # Train MultinomialNB
        print(f"Training MultinomialNB (alpha={self.alpha})...")
        self.model = MultinomialNB(alpha=self.alpha)
        self.model.fit(train_final, train_labels)

        # Evaluate on all splits
        train_pred = self.model.predict(train_final)
        val_pred = self.model.predict(val_final)
        test_pred = self.model.predict(test_final)

        train_accuracy = accuracy_score(train_labels, train_pred) * 100
        val_accuracy = accuracy_score(val_labels, val_pred) * 100
        test_accuracy = accuracy_score(test_labels, test_pred) * 100
        self.test_accuracy = test_accuracy / 100  # Store as 0-1 scale internally

        # Initialize confidence calibrator and fit on validation data
        from confidence_calibration import ConfidenceCalibrator
        self.confidence_calibrator = ConfidenceCalibrator()
        
        # Get validation probabilities for calibration
        val_proba = self.model.predict_proba(val_final)
        
        # Convert string labels to indices for the calibrator
        unique_categories = np.array(sorted(set(val_labels)))
        val_labels_idx = np.array([np.where(unique_categories == label)[0][0] for label in val_labels])
        val_pred_idx = np.array([np.where(unique_categories == label)[0][0] for label in val_pred])
        
        # Fit calibrator on validation data
        self.confidence_calibrator.fit(val_pred_idx, val_labels_idx, val_proba)
        
        # Learn vendor history from training data
        if 'vendor_name' in train.columns and 'category_true' in train.columns:
            self.confidence_calibrator.fit_vendor_history(train, 'vendor_name', 'category_true')

        # Initialize validator
        self.validator = PostPredictionValidator()

        # Save model automatically
        default_model_path = "models/naive_bayes_model.pkl"
        os.makedirs("models", exist_ok=True)
        self.save_model(default_model_path)

        # Return metrics in FRONTBACK.md format
        metrics = {
            'test_accuracy': test_accuracy,  # 0-100 scale
            'validation_accuracy': val_accuracy,  # 0-100 scale
            'train_accuracy': train_accuracy,  # 0-100 scale
            'categories': len(self.training_categories),
            'transactions': len(training_data),
            'train_transactions': len(train),
            'val_transactions': len(val),
            'test_transactions': len(test),
            'features': self.k_best,
            'model_path': default_model_path,
            'model_type': 'MultinomialNB',
            'message': 'QuickBooks pipeline trained successfully'
        }

        print(f"\n{'='*70}")
        print(f"Training Complete!")
        print(f"{'='*70}")
        print(f"Test Accuracy: {test_accuracy:.1f}%")
        print(f"Validation Accuracy: {val_accuracy:.1f}%")
        print(f"Train Accuracy: {train_accuracy:.1f}%")
        print(f"Categories: {len(self.training_categories)}")
        print(f"Features: {train_combined.shape[1]} → {self.k_best} (selected)")
        print(f"Model saved to: {default_model_path}")
        print(f"{'='*70}\n")

        return metrics

    def predict(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Predict transaction categories for new data.

        Args:
            df: DataFrame with QuickBooks general ledger data

        Returns:
            List of dicts, one per transaction, with all original columns plus:
            - "Transaction Type (New)": str (predicted category)
            - "Confidence Score": float (0.0-1.0)
            - "Confidence Tier": str ("GREEN", "YELLOW", or "RED")
        """
        if not self.is_model_loaded():
            raise ValueError("No model loaded. Train a model first or load existing model.")

        print(f"Predicting for {len(df)} transactions...")

        # Prepare features
        memo_cols = [c for c in df.columns if 'memo' in c.lower() or 'description' in c.lower()]
        memo_col = memo_cols[0] if memo_cols else None

        df['vendor_name'] = df['Name'].fillna('').str.strip()
        memo_text = df[memo_col].fillna('').str.strip() if memo_col else ''
        df['description'] = (df['vendor_name'] + ' ' + memo_text).str.strip()
        df['amount'] = df['Debit'].fillna(0) + df['Credit'].fillna(0)
        df[['account_type', 'account_code', 'account_name']] = df['Account'].apply(
            lambda x: pd.Series(self.classify_account(x))
        )

        # Rule-based pre-processing
        rules = self.apply_rule_classifier(df)
        rule_matches = rules['has_rule_match'] == 1
        rule_high_conf = rules['rule_confidence'] >= 0.85

        # Extract TF-IDF features
        tfidf_word = self.tfidf_word.transform(df['description'])
        features = pd.DataFrame(tfidf_word.toarray(), columns=self.tfidf_cols)
        features['amount_log'] = np.log1p(df['amount'])

        tfidf_char = self.tfidf_char.transform(df['description'])
        char_features = pd.DataFrame(tfidf_char.toarray(), columns=self.tfidf_char_cols)

        tfidf_trigram = self.tfidf_trigram.transform(df['description'])
        trigram_features = pd.DataFrame(tfidf_trigram.toarray(), columns=self.tfidf_trigram_cols)

        features = pd.concat([features, char_features, trigram_features], axis=1)

        # Apply other feature extractors
        vi_features = self.apply_vendor_intelligence(df)
        transport_features = self.apply_transportation_features(df)
        rules_numeric = rules[['rule_confidence', 'has_rule_match']]

        # Combine and select features
        combined = pd.concat([features, vi_features, transport_features, rules_numeric], axis=1)
        final_features = self.selector.transform(combined)

        # ML predictions
        ml_predictions = self.model.predict(final_features)
        ml_probabilities = self.model.predict_proba(final_features)
        ml_confidence = ml_probabilities.max(axis=1)

        # Hybrid: Use rule predictions if high confidence, otherwise ML + apply calibration
        final_predictions = []
        final_confidence = []
        prediction_source = []

        for idx in range(len(df)):
            if rule_matches.iloc[idx] and rule_high_conf.iloc[idx]:
                final_predictions.append(rules.iloc[idx]['rule_prediction'])
                # Use raw rule confidence (no calibration needed for rules)
                final_confidence.append(rules.iloc[idx]['rule_confidence'])
                prediction_source.append('rule')
            else:
                pred = ml_predictions[idx]
                final_predictions.append(pred)
                
                # Apply calibration to ML predictions
                pred_prob = ml_probabilities[idx]
                
                # Get predicted category index for calibrator
                try:
                    pred_idx = int(np.where(self.model.classes_ == pred)[0][0]) if hasattr(self.model, 'classes_') else idx
                except:
                    pred_idx = 0
                
                # Extract vendor intelligence info for calibration boosts
                vi_conf = float(vi_features.iloc[idx]['vi_confidence']) if idx < len(vi_features) else 0.0
                vi_match = int(vi_features.iloc[idx]['has_match']) if idx < len(vi_features) else 0
                vendor_name = df.iloc[idx].get('vendor_name', '')
                
                # Calibrate confidence using the calibrator
                if hasattr(self, 'confidence_calibrator') and self.confidence_calibrator:
                    calibrated_conf, _ = self.confidence_calibrator.calibrate(
                        pred_prob, pred_idx, vi_conf, bool(vi_match),
                        vendor_name=vendor_name, predicted_category=pred
                    )
                    final_confidence.append(calibrated_conf)
                else:
                    # Fallback to raw confidence if calibrator not available
                    final_confidence.append(float(ml_confidence[idx]))
                
                prediction_source.append('ml')

        # Add predictions to DataFrame (use FRONTBACK.md column names)
        df['Transaction Type (New)'] = final_predictions
        df['Account Code (New)'] = df['account_code']  # Include parsed account code like Xero does
        df['Confidence Score'] = final_confidence
        df['Confidence Tier'] = pd.cut(
            final_confidence,
            bins=[0, 0.4, 0.7, 1.01],
            labels=['RED', 'YELLOW', 'GREEN']
        )
        df['Prediction Source'] = prediction_source

        # Apply 5-layer validation
        print("Applying 5-layer validation...")
        validated_df = self.validator.validate_batch(
            df,
            prediction_col='Transaction Type (New)',
            confidence_col='Confidence Score',
            amount_col='amount',
            description_col='description',
            vendor_col='vendor_name',
            account_type_col='account_type'
        )

        # Update confidence tier with validated tier (overwrite for UI consistency)
        # Convert categorical columns to string first to avoid categorical assignment issues
        validated_df['Confidence Tier'] = validated_df['Validated Tier'].astype(str)
        validated_df['Transaction Type (New)'] = validated_df['Validated Transaction Type'].astype(str)

        # Print summary
        tiers = validated_df['Confidence Tier'].value_counts()
        print(f"\n{'='*70}")
        print(f"Predictions Complete: {len(validated_df)} transactions")
        print(f"{'='*70}")
        for tier in ['GREEN', 'YELLOW', 'RED']:
            count = tiers.get(tier, 0)
            pct = count / len(validated_df) * 100
            print(f"{tier:7s}: {count:4d} ({pct:5.1f}%)")
        print(f"{'='*70}\n")

        # Handle NaN values before JSON serialization
        # Convert any categorical columns to object type first
        for col in validated_df.columns:
            if pd.api.types.is_categorical_dtype(validated_df[col]):
                validated_df[col] = validated_df[col].astype(str)

        # Replace NaN values based on column type
        for col in validated_df.columns:
            if validated_df[col].dtype in ['float64', 'float32', 'int64', 'int32']:
                validated_df[col] = validated_df[col].fillna(0)
            else:
                validated_df[col] = validated_df[col].fillna('')

        # Ensure critical columns have no empty values
        if 'Transaction Type (New)' in validated_df.columns:
            validated_df['Transaction Type (New)'] = validated_df['Transaction Type (New)'].replace('', 'Unknown')
        if 'Confidence Tier' in validated_df.columns:
            validated_df['Confidence Tier'] = validated_df['Confidence Tier'].replace('', 'RED')

        # Convert to list of dicts for FRONTBACK API compatibility
        result_list = validated_df.to_dict('records')
        return result_list

    def save_model(self, filepath: str):
        """
        Save trained model to disk.

        Args:
            filepath: Path to save pickle file
        """
        if self.model is None:
            raise ValueError("No model to save. Train the model first.")

        # Create directory if needed
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        model_data = {
            'model': self.model,
            'selector': self.selector,
            'tfidf_word': self.tfidf_word,
            'tfidf_char': self.tfidf_char,
            'tfidf_trigram': self.tfidf_trigram,
            'vendor_intelligence': self.vendor_intelligence,
            'rule_classifier': self.rule_classifier,
            'validator': self.validator,
            'tfidf_cols': self.tfidf_cols,
            'tfidf_char_cols': self.tfidf_char_cols,
            'tfidf_trigram_cols': self.tfidf_trigram_cols,
            'training_categories': self.training_categories,
            'category_types': self.category_types,
            'test_accuracy': self.test_accuracy,
            'alpha': self.alpha,
            'k_best': self.k_best
        }

        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)

        print(f"Model saved to {filepath}")
        print(f"Size: {os.path.getsize(filepath) / 1024 / 1024:.2f} MB")

    @classmethod
    def load_model(cls, filepath: str) -> 'QuickBooksPipeline':
        """
        Load trained model from disk.

        Args:
            filepath: Path to pickle file

        Returns:
            Initialized QuickBooksPipeline instance
        """
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)

        pipeline = cls(
            alpha=model_data['alpha'],
            k_best=model_data['k_best']
        )

        pipeline.model = model_data['model']
        pipeline.selector = model_data['selector']
        pipeline.tfidf_word = model_data['tfidf_word']
        pipeline.tfidf_char = model_data['tfidf_char']
        pipeline.tfidf_trigram = model_data['tfidf_trigram']
        pipeline.vendor_intelligence = model_data['vendor_intelligence']
        pipeline.rule_classifier = model_data['rule_classifier']
        pipeline.validator = model_data['validator']
        pipeline.tfidf_cols = model_data['tfidf_cols']
        pipeline.tfidf_char_cols = model_data['tfidf_char_cols']
        pipeline.tfidf_trigram_cols = model_data['tfidf_trigram_cols']
        pipeline.training_categories = model_data['training_categories']
        pipeline.category_types = model_data['category_types']
        pipeline.test_accuracy = model_data['test_accuracy']

        print(f"Model loaded from {filepath}")
        print(f"Test Accuracy: {pipeline.test_accuracy:.1%}")
        print(f"Categories: {len(pipeline.training_categories)}")

        return pipeline


def main():
    """Example usage of the pipeline."""

    # Example 1: Training a new model
    print("="*70)
    print("TRAINING NEW MODEL")
    print("="*70)

    pipeline = QuickBooksPipeline(alpha=1.0, k_best=100)

    training_path = '../CSV_data/by_year/General_ledger_2023.csv'
    metrics = pipeline.train(training_path)

    # Save model
    model_path = 'models/qb_pipeline_v2.pkl'
    pipeline.save_model(model_path)

    print("\n" + "="*70)
    print("MAKING PREDICTIONS")
    print("="*70)

    # Example 2: Loading model and making predictions
    pipeline = QuickBooksPipeline.load_model(model_path)

    prediction_path = '../CSV_data/by_year_edits/General_ledger_2025_edited.csv'
    predictions = pipeline.predict(prediction_path)

    # Save predictions
    output_path = 'output/predictions_2025.csv'
    predictions.to_csv(output_path, index=False)
    print(f"\nPredictions saved to {output_path}")


if __name__ == '__main__':
    main()
