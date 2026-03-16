#!/usr/bin/env python3
"""Quick confidence check"""
import pandas as pd
import numpy as np
from ml_pipeline_qb import MLPipeline
import sys

try:
    print('Loading training data...', flush=True)
    train_df = pd.read_csv('../CSV_data/by_year_edits/General_ledger_2024_edited.csv')
    print(f'Training rows: {len(train_df)}', flush=True)

    if 'Account' in train_df.columns:
        categories = train_df['Account'].value_counts()
        print(f'Unique categories: {len(categories)}', flush=True)
        print(f'Top 5: {list(categories.head(5).index[:50])}', flush=True)

    print('Training model...', flush=True)
    pipeline = MLPipeline()
    results = pipeline.train(train_df)
    print(f'Train Acc: {results.get("train_accuracy", 0):.1%}', flush=True)

    print('Making predictions...', flush=True)
    pred_df = pd.read_csv('../CSV_data/by_year_edits/General_ledger_2026_edited.csv')
    predictions = pipeline.predict(pred_df)

    confidences = np.array([p['Confidence Score'] for p in predictions])
    green = (confidences >= 0.9).sum()
    yellow = ((confidences >= 0.7) & (confidences < 0.9)).sum()
    red = (confidences < 0.7).sum()
    total = len(confidences)

    print('\n' + '='*60, flush=True)
    print('CONFIDENCE DISTRIBUTION RESULTS', flush=True)
    print('='*60, flush=True)
    print(f'GREEN  (>=90%): {green:4d} ({100*green/total:5.1f}%)', flush=True)
    print(f'YELLOW (70-90%): {yellow:4d} ({100*yellow/total:5.1f}%)', flush=True)
    print(f'RED    (<70%): {red:4d} ({100*red/total:5.1f}%)', flush=True)
    print(f'Mean confidence: {confidences.mean():.3f}', flush=True)
    print(f'Median confidence: {np.median(confidences):.3f}', flush=True)
    print('='*60, flush=True)

except Exception as e:
    print(f'ERROR: {e}', flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)
