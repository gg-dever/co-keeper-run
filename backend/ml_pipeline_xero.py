"""
ML Pipeline for Xero GL Data
Adapted from ml_pipeline.py to handle Xero export format (Jimmy_Before.csv structure)
"""

import pandas as pd
import numpy as np
import pickle
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Add parent directory to path to import src module
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))
from src.features.vendor_intelligence import VendorIntelligence
from confidence_calibration import ConfidenceCalibrator

logger = logging.getLogger(__name__)

# Model storage directory
MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)


class MLPipelineXero:
    """
    Wrapper class for the CoKeeper ML pipeline adapted for Xero GL exports
    Handles training and prediction with the Naive Bayes model
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the ML pipeline

        Args:
            model_path: Optional path to load pre-trained model
        """
        self.model = None
        self.tfidf_vectorizer = None
        self.vendor_intelligence = None
        self.feature_selector = None
        self.confidence_calibrator = ConfidenceCalibrator()
        self.categories = None
        self.account_name_to_code: Dict[str, str] = {}

        if model_path:
            self.load_model(model_path)

    def is_model_loaded(self) -> bool:
        """Check if a trained model is loaded"""
        return self.model is not None

    @staticmethod
    def _parse_xero_csv(file_or_df) -> pd.DataFrame:
        """
        Parse Xero CSV by dynamically finding the header row and data start.

        Xero CSVs have metadata rows before the actual data. We need to:
        1. Find the row that contains 'Date' (first column) and 'Related account' (last column)
        2. Use that row as column headers
        3. Read data starting from the next row
        4. Filter out empty rows or rows without valid dates

        Args:
            file_or_df: File path, file-like object, or DataFrame

        Returns:
            Clean DataFrame with proper columns
        """
        # If it's already a DataFrame (from testing), check if it's already parsed
        if isinstance(file_or_df, pd.DataFrame):
            if 'Date' in file_or_df.columns and 'Related account' in file_or_df.columns:
                # Already parsed correctly
                return file_or_df
            # Otherwise, need to re-parse (shouldn't happen in normal flow)
            logger.warning("DataFrame passed but doesn't have expected columns, treating as raw data")
            return file_or_df

        # Read file to find header row
        lines = []
        if hasattr(file_or_df, 'read'):
            # File-like object
            file_or_df.seek(0)
            for line in file_or_df:
                if isinstance(line, bytes):
                    lines.append(line.decode('utf-8'))
                else:
                    lines.append(line)
        else:
            # File path
            with open(file_or_df, 'r', encoding='utf-8') as f:
                lines = f.readlines()

        # Find the header row (contains 'Date' at start and 'Related account' at end)
        header_row_idx = None
        for i, line in enumerate(lines):
            # Check if this line starts with 'Date' and contains 'Related account'
            if line.strip().startswith('Date') and 'Related account' in line:
                header_row_idx = i
                logger.info(f"Found Xero header row at index {i}")
                break

        if header_row_idx is None:
            raise ValueError(
                "Could not find Xero CSV header row. Expected a row starting with 'Date' "
                "and ending with 'Related account'. Please verify this is a Xero export file."
            )

        # Read CSV starting from header row with explicit parameters for better CSV handling
        if hasattr(file_or_df, 'read'):
            file_or_df.seek(0)
            df = pd.read_csv(file_or_df, skiprows=header_row_idx, encoding='utf-8',
                           quoting=1, na_values=['', 'NA', 'N/A', 'null'])
        else:
            df = pd.read_csv(file_or_df, skiprows=header_row_idx, encoding='utf-8',
                           quoting=1, na_values=['', 'NA', 'N/A', 'null'])

        # Filter out empty rows or rows without a valid Date
        df = df[df['Date'].notna()].copy()

        # Enhanced filtering: only keep rows where Date looks like an actual date
        # Valid formats: "27 Jan 2025", "2025-01-27", "01/27/2025"
        # Must start with a digit (not spaces or dashes)
        # This filters out metadata rows like " - CORP Account - Business Adv Un" or "Opening Balance"
        date_series = df['Date'].astype(str).str.strip()
        df = df[date_series.str.match(r'^\d', na=False)].copy()

        # Filter out rows where we don't have meaningful transaction data
        # Keep rows that have either:
        # 1. Contact OR Description (for normal Xero exports), OR
        # 2. Related account (for edited CSVs where Contact/Description are empty)
        # This filters out metadata rows while allowing edited CSVs with empty Contact/Description
        if 'Related account' in df.columns:
            has_related_account = df['Related account'].notna() & (df['Related account'].astype(str).str.strip() != '')

            if 'Contact' in df.columns and 'Description' in df.columns:
                has_contact_or_desc = ((df['Contact'].notna() & (df['Contact'].astype(str).str.strip() != '')) |
                                      (df['Description'].notna() & (df['Description'].astype(str).str.strip() != '')))
                # Keep rows with either Contact/Description OR Related account
                df = df[has_contact_or_desc | has_related_account].copy()
            else:
                # If Contact/Description columns don't exist, just require Related account
                df = df[has_related_account].copy()

        logger.info(f"Parsed Xero CSV: {len(df)} data rows, columns: {df.columns.tolist()}")

        return df

    def train(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Train the Naive Bayes model on provided Xero transaction data

        Args:
            df: DataFrame with Xero General Ledger format (4 header rows already skipped)
            Expected columns: Date, Source, Contact, Description, Reference, Gross,
                            Debit, Credit, Running Balance, Account Code, Account,
                            Account Type, Related account

        Returns:
            Dictionary with training results (accuracy, categories, etc.)
        """
        logger.info("Training Naive Bayes model for Xero data...")
        logger.info(f"Xero CSV columns: {df.columns.tolist()}")
        logger.info(f"Xero CSV shape: {df.shape}")

        # Step 1: Classify accounts using the Account Type column from the CSV
        # Each user's CSV has different account codes, so we read the type directly
        # rather than guessing from hardcoded code ranges.
        if 'Account Type' not in df.columns:
            raise ValueError(
                "Missing 'Account Type' column. Each Xero export should include "
                "an Account Type column that tells us the account category."
            )

        df['account_type'] = df['Account Type'].apply(self._map_xero_account_type)

        # Parse account code and name from the Related account / Account column
        acct_col = 'Related account' if 'Related account' in df.columns else (
            'Account' if 'Account' in df.columns else None
        )
        if acct_col:
            df[['account_code', 'account_name']] = df[acct_col].apply(
                lambda x: pd.Series(self._parse_account_string(x))
            )
        else:
            df['account_code'] = ''
            df['account_name'] = ''

        # Step 2: Filter to P&L category accounts (Revenue, Direct Costs, Expenses for Xero)
        CATEGORY_TYPES = ['REVENUE', 'DIRECT_COSTS', 'EXPENSE', 'OTHER_INCOME', 'OTHER_EXPENSE']
        clean = df[df['account_type'].isin(CATEGORY_TYPES)].copy()
        logger.info(f"Filtered to {len(clean)} P&L transactions from {len(df)} total")
        logger.info(f"Account type distribution: {clean['account_type'].value_counts().to_dict()}")

        if len(clean) == 0:
            raise ValueError("No P&L transactions found. Check that your Xero export contains revenue and expense accounts.")

        # Step 3: Build description field
        # Xero has 'Contact' for vendor and 'Description' for transaction details
        clean['vendor_name'] = clean['Contact'].fillna('').str.strip()
        clean['memo'] = clean['Description'].fillna('').str.strip()
        clean['description'] = clean.apply(
            lambda row: ' '.join(filter(None, [row['vendor_name'], row['memo']])).strip(),
            axis=1
        )

        # Step 4: Extract amount and category
        # Xero has separate Debit and Credit columns - convert to numeric
        clean['Debit'] = pd.to_numeric(clean['Debit'], errors='coerce').fillna(0)
        clean['Credit'] = pd.to_numeric(clean['Credit'], errors='coerce').fillna(0)
        clean['amount'] = clean['Debit'] + clean['Credit']

        # Use Account column as the prediction target (the GL expense/revenue category)
        # NOT Related account (which is the bank/contra account in Xero)
        clean['category_true'] = clean['Account']

        # Build Account name → Account Code mapping from training data
        if 'Account Code' in clean.columns and 'Account' in clean.columns:
            code_map = clean.dropna(subset=['Account Code', 'Account'])
            for _, row in code_map[['Account', 'Account Code']].drop_duplicates().iterrows():
                name = str(row['Account']).strip()
                code = str(row['Account Code']).strip()
                if name and code:
                    self.account_name_to_code[name] = code
            logger.info(f"Built account name→code mapping: {len(self.account_name_to_code)} entries")

        clean['date'] = pd.to_datetime(clean['Date'], errors='coerce')

        # Step 5: Select and clean data
        training_data = clean[[
            'date', 'description', 'vendor_name', 'amount',
            'category_true', 'account_code'
        ]].copy()

        # Remove zeros and empty descriptions
        training_data = training_data[training_data['amount'] > 0]
        training_data = training_data[training_data['description'].str.strip().str.len() > 0]

        logger.info(f"Training dataset: {len(training_data)} transactions, {training_data['category_true'].nunique()} categories")

        if len(training_data) == 0:
            raise ValueError("No training data remaining after filtering. Check your CSV format and account types.")

        # Step 6: Train/Val/Test split (70/15/15)
        # Fall back to non-stratified split if any category is too small
        min_cat_count = int(training_data['category_true'].value_counts().min())
        use_stratify = min_cat_count >= 7

        if use_stratify:
            train, temp = train_test_split(
                training_data,
                test_size=0.30,
                stratify=training_data['category_true'],
                random_state=42
            )
            val, test = train_test_split(
                temp,
                test_size=0.50,
                stratify=temp['category_true'],
                random_state=42
            )
        else:
            logger.info(
                f"Using non-stratified split (min category count={min_cat_count}) "
                f"to preserve all {training_data['category_true'].nunique()} categories"
            )
            train, temp = train_test_split(training_data, test_size=0.30, random_state=42)
            val, test = train_test_split(temp, test_size=0.50, random_state=42)

        # Step 7: Build TF-IDF features
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            min_df=1,
            stop_words='english'
        )

        train_tfidf = self.tfidf_vectorizer.fit_transform(train['description'].fillna(''))
        val_tfidf = self.tfidf_vectorizer.transform(val['description'].fillna(''))
        test_tfidf = self.tfidf_vectorizer.transform(test['description'].fillna(''))

        # Convert to DataFrames and add amount (ensure numeric arrays)
        train_features = pd.DataFrame(train_tfidf.toarray())
        val_features = pd.DataFrame(val_tfidf.toarray())
        test_features = pd.DataFrame(test_tfidf.toarray())

        train_features['amount_log'] = np.log1p(np.array(train['amount'].values, dtype=np.float64))
        val_features['amount_log'] = np.log1p(np.array(val['amount'].values, dtype=np.float64))
        test_features['amount_log'] = np.log1p(np.array(test['amount'].values, dtype=np.float64))

        # Step 8: Train Vendor Intelligence
        self.vendor_intelligence = VendorIntelligence(
            exact_min_consistency=0.80,
            exact_min_occurrences=2,
            use_merchant_normalization=True
        )

        train_vi_data = train[['vendor_name', 'description', 'amount', 'category_true']].copy()
        self.vendor_intelligence.fit(train_vi_data)

        # Step 9: Apply VI features
        train_vi = self._apply_vi(train)
        val_vi = self._apply_vi(val)
        test_vi = self._apply_vi(test)

        # Step 10: Combine all features
        train_combined = pd.concat([train_features, train_vi], axis=1)
        val_combined = pd.concat([val_features, val_vi], axis=1)
        test_combined = pd.concat([test_features, test_vi], axis=1)

        # Convert all column names to strings to avoid sklearn error
        train_combined.columns = train_combined.columns.astype(str)
        val_combined.columns = val_combined.columns.astype(str)
        test_combined.columns = test_combined.columns.astype(str)

        train_labels = train['category_true'].astype(str).to_numpy()
        val_labels = val['category_true'].astype(str).to_numpy()
        test_labels = test['category_true'].astype(str).to_numpy()

        # Step 11: Feature selection (K=400 optimal from experiments)
        best_k = 400
        if best_k < train_combined.shape[1]:
            self.feature_selector = SelectKBest(chi2, k=best_k)
            train_final = self.feature_selector.fit_transform(train_combined, train_labels)
            val_final = self.feature_selector.transform(val_combined)
            test_final = self.feature_selector.transform(test_combined)
        else:
            self.feature_selector = None
            train_final = train_combined.values
            val_final = val_combined.values
            test_final = test_combined.values

        # Step 12: Train optimized MultinomialNB (alpha=0.01 from experiments)
        self.model = MultinomialNB(alpha=0.01)
        self.model.fit(train_final, train_labels)

        # Step 13: Evaluate
        train_pred = self.model.predict(train_final)
        val_pred = self.model.predict(val_final)
        val_pred_proba = self.model.predict_proba(val_final)
        test_pred = self.model.predict(test_final)

        train_acc = accuracy_score(train_labels, train_pred)
        val_acc = accuracy_score(val_labels, val_pred)
        test_acc = accuracy_score(test_labels, test_pred)

        # Store categories
        self.categories = list(self.model.classes_)

        # Step 13b: Fit confidence calibrator on validation set
        logger.info("Fitting confidence calibrator on validation set...")
        self.confidence_calibrator.fit(
            val_pred, val_labels, val_pred_proba,
            training_df=training_data
        )
        calibration_report = self.confidence_calibrator.get_category_reliability_report()
        logger.info(f"Calibrator fitted. Category reliability report:\n{calibration_report.to_string()}")

        # Step 13c: Learn vendor history from training data
        logger.info("Learning vendor→category patterns from training data...")
        self.confidence_calibrator.fit_vendor_history(
            training_df=training_data,
            vendor_col='vendor_name',
            category_col='category_true'
        )

        # Save model
        model_path = MODELS_DIR / "naive_bayes_xero_model.pkl"
        self.save_model(str(model_path))

        result = {
            "accuracy": float(test_acc * 100),
            "test_accuracy": float(test_acc * 100),
            "validation_accuracy": float(val_acc * 100),
            "train_accuracy": float(train_acc * 100),
            "categories": len(self.categories),
            "transactions": len(training_data),
            "train_transactions": len(train),
            "val_transactions": len(val),
            "test_transactions": len(test),
            "features": best_k if self.feature_selector else train_combined.shape[1],
            "model_path": str(model_path),
            "model_type": "MultinomialNB (Xero)",
            "message": "Naive Bayes model trained successfully for Xero data"
        }

        logger.info(f"Xero training complete: Test={result['test_accuracy']:.1f}%, Val={result['validation_accuracy']:.1f}%")
        return result

    def predict(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Make predictions on new Xero transaction data

        Args:
            df: DataFrame with Xero transaction data (4 header rows already skipped)

        Returns:
            List of dictionaries with predictions for each transaction
        """
        logger.info(f"Making predictions for {len(df)} Xero transactions...")
        logger.info(f"Prediction CSV columns: {df.columns.tolist()}")

        if not self.is_model_loaded():
            raise ValueError("No model loaded. Train a model first or load existing model.")

        # Validate required columns
        required_columns = ['Contact', 'Description', 'Debit', 'Credit']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(
                f"Missing required Xero columns: {', '.join(missing_columns)}. "
                f"Available columns: {', '.join(df.columns.tolist())}. "
                f"Make sure you uploaded a Xero export CSV (with 4 header rows)."
            )

        # Step 0: Filter to only real transactions (exclude Opening Balance, Totals, etc.)
        # For prediction, we can't filter by account type if Related account is empty (that's what we're predicting!)
        # Instead, filter by whether the row has valid transaction data (Contact OR Description)
        df = df.copy()

        # Filter based on whether we have vendor/transaction info
        # Keep rows that have Contact OR Description (actual transactions with vendor info)
        # Exclude metadata rows that have neither
        has_contact = df['Contact'].notna() & (df['Contact'].astype(str).str.strip() != '')
        has_description = df['Description'].notna() & (df['Description'].astype(str).str.strip() != '')

        total_rows = len(df)
        df = df[has_contact | has_description].copy()
        filtered_rows = len(df)
        logger.info(f"Filtered to {filtered_rows} transactions with vendor data from {total_rows} total (removed {total_rows - filtered_rows} metadata rows)")

        if len(df) == 0:
            logger.warning("No transactions with vendor data found after filtering. Returning empty predictions.")
            return []

        # Step 1: Prepare data (same as training)
        df['vendor_name'] = df['Contact'].fillna('').str.strip()
        df['memo'] = df['Description'].fillna('').str.strip()
        df['description'] = df.apply(
            lambda row: ' '.join(filter(None, [row['vendor_name'], row['memo']])).strip(),
            axis=1
        )

        # Convert Debit and Credit to numeric, handling any non-numeric values
        df['Debit'] = pd.to_numeric(df['Debit'], errors='coerce').fillna(0)
        df['Credit'] = pd.to_numeric(df['Credit'], errors='coerce').fillna(0)
        df['amount'] = df['Debit'] + df['Credit']

        # Step 2: Extract TF-IDF features
        tfidf_features = self.tfidf_vectorizer.transform(df['description'].fillna(''))
        features_df = pd.DataFrame(tfidf_features.toarray())

        # Ensure amount is a numpy array and apply log1p
        amount_array = np.array(df['amount'].values, dtype=np.float64)
        features_df['amount_log'] = np.log1p(amount_array)

        # Step 3: Apply VI features
        vi_features = self._apply_vi(df)

        # Step 4: Combine features
        combined_features = pd.concat([features_df, vi_features], axis=1)

        # Convert all column names to strings to avoid sklearn error
        combined_features.columns = combined_features.columns.astype(str)

        # Step 5: Apply feature selection if used
        if self.feature_selector:
            features_final = self.feature_selector.transform(combined_features)
        else:
            features_final = combined_features.values

        # Step 6: Make predictions
        predictions = self.model.predict(features_final)
        probabilities = self.model.predict_proba(features_final)

        # Step 7: Format results - preserve original structure, add predictions w/ calibrated confidence
        results = []
        for idx, pred in enumerate(predictions):
            # Get original row data - preserve everything from input CSV
            orig_row = df.iloc[idx]

            # Start with all original columns as a dict
            result_dict = orig_row.to_dict()

            # Replace NaN values with appropriate defaults for JSON serialization
            for key, value in result_dict.items():
                if pd.isna(value):
                    result_dict[key] = None
                elif isinstance(value, (np.integer, np.floating)):
                    result_dict[key] = float(value)

            # Put prediction in the Account and Account Code columns
            result_dict['Account'] = pred
            result_dict['Account Code'] = self.account_name_to_code.get(pred, '')

            # Get predicted category index for calibration
            pred_idx = np.where(self.model.classes_ == pred)[0][0]
            prob_dist = probabilities[idx]

            # Extract VI features for this transaction
            vi_conf = float(vi_features.iloc[idx]['vi_confidence']) if idx < len(vi_features) else 0.0
            vi_match = int(vi_features.iloc[idx]['has_match']) if idx < len(vi_features) else 0

            # Get vendor name for vendor history boost
            vendor_name = orig_row.get('vendor_name', '')

            # Check if category is rare (< 10 training examples)
            # NOTE: Only mark as rare if category WAS in training data;
            # if pred_idx not in category_frequency, don't penalize it
            category_frequency = self.confidence_calibrator.category_frequency.get(pred_idx, None)
            is_rare = (category_frequency is not None) and (category_frequency < 10)

            # Calibrate confidence using calibrator (now with vendor history)
            calibrated_conf, reason = self.confidence_calibrator.calibrate(
                prob_dist, pred_idx, vi_conf, bool(vi_match),
                vendor_name=vendor_name, predicted_category=pred
            )

            # Assign tier using calibrated confidence
            tier = self.confidence_calibrator.assign_tier(calibrated_conf, pred_idx, is_rare)

            # Add confidence and tier as new columns with descriptive names
            result_dict['Confidence Score'] = float(calibrated_conf)
            result_dict['Confidence Tier'] = tier

            results.append(result_dict)

        logger.info(f"Predictions complete for {len(df)} Xero transactions")
        return results

    def save_model(self, path: str) -> None:
        """
        Save trained model to disk

        Args:
            path: File path to save the model
        """
        if not self.is_model_loaded():
            raise ValueError("No model to save")

        model_data = {
            "model": self.model,
            "tfidf_vectorizer": self.tfidf_vectorizer,
            "vendor_intelligence": self.vendor_intelligence,
            "feature_selector": self.feature_selector,
            "confidence_calibrator": self.confidence_calibrator,
            "categories": self.categories,
            "account_name_to_code": self.account_name_to_code
        }

        with open(path, 'wb') as f:
            pickle.dump(model_data, f)

        logger.info(f"Xero model saved to {path}")

    def load_model(self, path: str) -> None:
        """
        Load trained model from disk

        Args:
            path: File path to load the model from
        """
        with open(path, 'rb') as f:
            model_data = pickle.load(f)

        self.model = model_data["model"]
        self.tfidf_vectorizer = model_data["tfidf_vectorizer"]
        self.vendor_intelligence = model_data["vendor_intelligence"]
        self.feature_selector = model_data.get("feature_selector")
        self.confidence_calibrator = model_data.get("confidence_calibrator", ConfidenceCalibrator())
        self.categories = model_data.get("categories")
        self.account_name_to_code = model_data.get("account_name_to_code", {})

        logger.info(f"Xero model loaded from {path}")

    @staticmethod
    def _get_tier(confidence: float) -> str:
        """
        Assign confidence tier based on threshold

        Args:
            confidence: Prediction confidence (0-1)

        Returns:
            Tier label: GREEN (high), YELLOW (medium), RED (low)
        """
        if confidence >= 0.9:
            return "GREEN"
        elif confidence >= 0.7:
            return "YELLOW"
        else:
            return "RED"

    @staticmethod
    def _map_xero_account_type(account_type_str) -> str:
        """
        Map the Account Type column value from any Xero CSV to an internal category.

        This reads the type directly from the CSV rather than guessing from
        account code ranges, so it works for every client's chart of accounts.
        """
        if pd.isna(account_type_str):
            return 'UNKNOWN'

        type_lower = str(account_type_str).strip().lower()

        if type_lower in ('revenue', 'sales'):
            return 'REVENUE'
        elif type_lower in ('direct costs', 'cost of sales', 'direct cost'):
            return 'DIRECT_COSTS'
        elif type_lower in ('expense', 'overhead', 'operating expense'):
            return 'EXPENSE'
        elif type_lower in ('other income',):
            return 'OTHER_INCOME'
        elif type_lower in ('other expense', 'depreciation'):
            return 'OTHER_EXPENSE'
        elif 'asset' in type_lower:
            return 'ASSET'
        elif 'liability' in type_lower:
            return 'LIABILITY'
        elif type_lower == 'equity':
            return 'EQUITY'
        else:
            return 'UNKNOWN'

    @staticmethod
    def _parse_account_string(account_str):
        """
        Parse an account string like "4101 - Credit Card Cash Back" into
        (account_code, account_name).  No type classification — that comes
        from the Account Type column in the CSV.
        """
        if pd.isna(account_str):
            return '', ''

        account_str = str(account_str).strip()
        if not account_str:
            return '', ''

        if ' - ' in account_str:
            parts = account_str.split(' - ', 1)
            return parts[0].strip(), parts[1].strip()

        return account_str, account_str

    def _apply_vi(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply Vendor Intelligence and return VI features

        Args:
            df: DataFrame with vendor_name, description, amount columns

        Returns:
            DataFrame with VI features (vi_confidence, has_match)
        """
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


if __name__ == "__main__":
    import os
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    TRAIN_CSV = os.path.expanduser(
        "~/Downloads/TrueFocus_Strategic_Consulting_LLC_-_Account_Transactions.xlsx - Account Transactions.csv"
    )
    TEST_CSV = os.path.expanduser("~/Downloads/Jimmy_Post_edit.csv")
    OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "..", "output", "pipeline_predictions.csv")

    # --- TRAIN ---
    if not os.path.exists(TRAIN_CSV):
        print(f"Training CSV not found: {TRAIN_CSV}")
        sys.exit(1)

    pipeline = MLPipelineXero()
    train_df = pipeline._parse_xero_csv(TRAIN_CSV)
    print(f"Parsed {len(train_df)} training rows")

    result = pipeline.train(train_df)
    print("\n=== Training Results ===")
    for k, v in result.items():
        print(f"  {k}: {v}")

    # --- PREDICT ---
    if not os.path.exists(TEST_CSV):
        print(f"\nTest CSV not found: {TEST_CSV}")
        sys.exit(1)

    test_df = pipeline._parse_xero_csv(TEST_CSV)
    print(f"\nParsed {len(test_df)} test rows")

    # Disable fuzzy matching for speed on large prediction sets
    from src.features.vendor_intelligence import FuzzyVendorMatcher
    pipeline.vendor_intelligence.fuzzy_matcher = FuzzyVendorMatcher()

    predictions = pipeline.predict(test_df)
    pred_df = pd.DataFrame(predictions)

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    pred_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nPredictions saved to {OUTPUT_CSV}")

    # --- SUMMARY ---
    print(f"\n=== Prediction Summary ===")
    print(f"  Total predictions: {len(pred_df)}")
    print(f"  Unique accounts predicted: {pred_df['Account'].nunique()}")
    print(f"\n  Confidence Tier Distribution:")
    for tier, count in pred_df['Confidence Tier'].value_counts().items():
        pct = 100 * count / len(pred_df)
        print(f"    {tier}: {count} ({pct:.1f}%)")
    print(f"\n  Confidence Score Stats:")
    print(f"    Mean:   {pred_df['Confidence Score'].mean():.4f}")
    print(f"    Median: {pred_df['Confidence Score'].median():.4f}")
    print(f"    Min:    {pred_df['Confidence Score'].min():.4f}")
    print(f"    Max:    {pred_df['Confidence Score'].max():.4f}")
    print(f"\n  Sample Predictions (first 10):")
    cols = ['Contact', 'Description', 'Account', 'Account Code', 'Confidence Score', 'Confidence Tier']
    cols = [c for c in cols if c in pred_df.columns]
    print(pred_df[cols].head(10).to_string(index=False))
