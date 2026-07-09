import os

# Base directory of the project
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Application settings
    APP_NAME = "IoT-Ready AI-Driven Credit Card Fraud Detection System"
    API_VERSION = "v1"
    SECRET_KEY = os.environ.get("SECRET_KEY", "banking-glassmorphism-secret-token-93812")
    
    # Database configuration
    DATABASE_PATH = os.path.join(BASE_DIR, "database", "transactions.db")
    
    # Model configuration
    MODEL_PATH = os.path.join(BASE_DIR, "models", "fraud_model.pkl")
    
    # Logging configuration
    LOG_FILE_PATH = os.path.join(BASE_DIR, "logs", "application.log")
