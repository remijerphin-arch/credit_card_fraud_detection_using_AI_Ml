import os
import sys
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

# Add parent directory to path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import Config

def train():
    # Construct path to dataset
    dataset_path = os.path.join(os.path.dirname(__file__), "..", "datasets", "creditcard.csv")
    dataset_path = os.path.abspath(dataset_path)
    
    # 1. Check if dataset exists
    if not os.path.exists(dataset_path):
        print("\n" + "="*50)
        print("Dataset not found. Please place creditcard.csv inside the datasets folder.")
        print("="*50 + "\n")
        return
        
    print(f"Dataset found at: {dataset_path}")
    print("Loading dataset...")
    
    try:
        df = pd.read_csv(dataset_path)
    except Exception as e:
        print(f"Error reading dataset: {e}")
        return
        
    print(f"Dataset loaded. Total rows: {len(df)}, columns: {list(df.columns)}")
    
    # 2. Preprocess data
    X = df.drop(columns=["Class"], errors="ignore")
    y = df["Class"]
    
    print("Splitting dataset into train and test sets (stratified)...")
    # Stratified split because dataset is heavily imbalanced
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    
    print("Training RandomForest model (n_estimators=100)...")
    # Use n_jobs=-1 for fast parallel processing
    model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    # 3. Evaluate model
    print("Evaluating model...")
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    print(f"Model Accuracy on Test Data: {accuracy * 100:.4f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, predictions))
    
    # 4. Save serialized model
    model_dir = os.path.dirname(Config.MODEL_PATH)
    os.makedirs(model_dir, exist_ok=True)
    
    print(f"Saving serialized model to: {Config.MODEL_PATH}...")
    joblib.dump(model, Config.MODEL_PATH)
    print("Model training and saving complete!")

if __name__ == "__main__":
    train()
