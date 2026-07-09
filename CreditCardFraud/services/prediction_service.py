import os
import joblib
import logging
from config import Config
from models.iot_feature_mapper import map_iot_to_features, validate_payload

# Initialize logger
logger = logging.getLogger("fraud_detector")

# Global reference for the loaded model
_model = None

def load_model():
    """Loads the RandomForest model from disk if not already loaded."""
    global _model
    if _model is not None:
        return _model
        
    if not os.path.exists(Config.MODEL_PATH):
        logger.error(f"RandomForest model file not found at: {Config.MODEL_PATH}")
        raise FileNotFoundError("Model not trained. Please train the model before making predictions.")
        
    try:
        _model = joblib.load(Config.MODEL_PATH)
        logger.info("RandomForest fraud detection model successfully loaded.")
        return _model
    except Exception as e:
        logger.error(f"Error loading RandomForest model file: {e}")
        raise RuntimeError(f"Failed to load model file: {e}")

def predict_transaction(payload):
    """Executes the prediction workflow for a transaction.
    
    1. Validates the JSON payload
    2. Maps to 30 numerical features
    3. Infers via RandomForest model
    4. Returns prediction label and risk score (probability)
    """
    # Validate payload format
    is_valid, err_msg = validate_payload(payload)
    if not is_valid:
        logger.warning(f"Payload validation failed: {err_msg}")
        raise ValueError(err_msg)
        
    # Ensure model is loaded (will raise FileNotFoundError if missing)
    model = load_model()
    
    # Map IoT payload to numerical ML features
    features = map_iot_to_features(payload)
    
    # Run model prediction
    # model.predict returns array of class labels (e.g. [0] or [1])
    # model.predict_proba returns probability for both classes [[prob_genuine, prob_fraud]]
    prediction_class = int(model.predict(features)[0])
    probabilities = model.predict_proba(features)[0]
    
    # Extract risk score (probability of class 1 / Fraud)
    risk_score = float(probabilities[1])
    
    # Map label to friendly output
    prediction_label = "Fraud" if prediction_class == 1 else "Genuine"
    
    logger.info(f"Transaction processed. CardID: {payload.get('card_id')}, Prediction: {prediction_label}, Risk Score: {risk_score:.4f}")
    
    return {
        "prediction": prediction_label,
        "risk_score": round(risk_score, 2)
    }
