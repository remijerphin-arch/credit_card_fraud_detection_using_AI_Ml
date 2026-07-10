import os
import pandas as pd
from config import Config

# Global cache
DATASET_STATS = None

def get_dataset_stats():
    """Reads datasets/creditcard.csv dynamically and returns summary statistics & metadata with in-memory caching."""
    global DATASET_STATS
    if DATASET_STATS is not None:
        return DATASET_STATS
        
    csv_path = Config.DATASET_PATH
    if not os.path.exists(csv_path):
        return {
            "loaded": False,
            "error_msg": "Dataset not found. Please place creditcard.csv inside the datasets folder."
        }
        
    try:
        # Get file size in MB
        file_size_mb = os.path.getsize(csv_path) / (1024 * 1024)
        
        # Load dataset efficiently (we only compute stats once and cache it)
        df = pd.read_csv(csv_path)
        
        num_rows = len(df)
        num_cols = len(df.columns)
        
        class_counts = df['Class'].value_counts()
        genuine_count = int(class_counts.get(0, 0))
        fraud_count = int(class_counts.get(1, 0))
        
        fraud_percent = (fraud_count / num_rows) * 100 if num_rows > 0 else 0.0
        missing_values = int(df.isnull().sum().sum())
        
        # Extract first 10 rows for sample table
        sample_rows = df.head(10).to_dict(orient='records')
        
        # Amount distribution bins (for histogram visualization)
        amount_bins = {
            "0-10": int(((df['Amount'] >= 0) & (df['Amount'] < 10)).sum()),
            "10-50": int(((df['Amount'] >= 10) & (df['Amount'] < 50)).sum()),
            "50-100": int(((df['Amount'] >= 50) & (df['Amount'] < 100)).sum()),
            "100-500": int(((df['Amount'] >= 100) & (df['Amount'] < 500)).sum()),
            "500+": int((df['Amount'] >= 500).sum())
        }
        
        # Correlation Matrix (Time, Amount, V1, V2, V3, Class)
        corr_cols = ['Time', 'Amount', 'V1', 'V2', 'V3', 'Class']
        corr_matrix = df[corr_cols].corr().round(3).to_dict()
        
        DATASET_STATS = {
            "loaded": True,
            "num_rows": f"{num_rows:,}",
            "num_columns": num_cols,
            "genuine_count": f"{genuine_count:,}",
            "fraud_count": f"{fraud_count:,}",
            "fraud_percent": f"{fraud_percent:.4f}%",
            "missing_values": missing_values,
            "file_size_mb": f"{file_size_mb:.2f} MB",
            "sample_rows": sample_rows,
            "amount_bins": amount_bins,
            "correlation_matrix": corr_matrix,
            "raw_genuine_count": genuine_count,
            "raw_fraud_count": fraud_count
        }
        return DATASET_STATS
    except Exception as e:
        return {
            "loaded": False,
            "error_msg": f"Failed to parse dataset file: {str(e)}"
        }
