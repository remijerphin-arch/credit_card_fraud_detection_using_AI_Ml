import os
import logging
from flask import Blueprint, request, jsonify
from config import Config
from services.prediction_service import predict_transaction
from services.database_service import save_transaction, get_transactions, get_stats, get_db_connection

# Define API blueprint
api_bp = Blueprint("api", __name__, url_prefix=f"/api/{Config.API_VERSION}")

# Logger setup
logger = logging.getLogger("fraud_detector")

def email_alert_placeholder(payload, prediction, risk_score):
    """Placeholder service for sending email alerts when fraud is detected."""
    logger.warning(
        f"[EMAIL ALERT PREPARED] Alerting system for fraudulent transaction! "
        f"Card ID: {payload.get('card_id')}, Amount: ${payload.get('amount')}, "
        f"Merchant: {payload.get('merchant')}, Risk Score: {risk_score}"
    )

@api_bp.route("/predict", methods=["POST"])
def api_predict():
    """Endpoint for ESP32 and simulation triggers to run inference."""
    try:
        # Validate request is JSON
        if not request.is_json:
            logger.error("Predict API request did not contain valid JSON")
            return jsonify({"error": "Content-Type must be application/json"}), 400
            
        payload = request.get_json()
        
        # Run prediction through inference pipeline (validates and maps features)
        result = predict_transaction(payload)
        
        # Log prediction result in database
        save_transaction(
            card_id=payload["card_id"],
            amount=float(payload["amount"]),
            merchant=payload["merchant"],
            location=payload["location"],
            device_id=payload["device_id"],
            transaction_time=payload["transaction_time"],
            prediction=result["prediction"],
            risk_score=result["risk_score"]
        )
        
        # If prediction is Fraud, log warning and fire placeholder email notification
        if result["prediction"] == "Fraud":
            email_alert_placeholder(payload, result["prediction"], result["risk_score"])
            
        return jsonify(result), 200
        
    except ValueError as val_err:
        # Input validation failed
        logger.warning(f"Predict API validation error: {val_err}")
        return jsonify({"error": str(val_err)}), 400
        
    except FileNotFoundError as fnf_err:
        # Model not trained
        logger.error(f"Predict API model missing: {fnf_err}")
        return jsonify({"error": str(fnf_err)}), 503
        
    except Exception as e:
        # Catch-all exception handling for runtime issues
        logger.error(f"Predict API server error: {e}", exc_info=True)
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@api_bp.route("/transactions", methods=["GET"])
def api_get_transactions():
    """Endpoint to fetch transaction history logs."""
    try:
        limit = request.args.get("limit", default=100, type=int)
        offset = request.args.get("offset", default=0, type=int)
        
        # Enforce positive values
        limit = max(1, limit)
        offset = max(0, offset)
        
        transactions = get_transactions(limit=limit, offset=offset)
        return jsonify(transactions), 200
    except Exception as e:
        logger.error(f"Transactions API error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@api_bp.route("/stats", methods=["GET"])
def api_get_stats():
    """Endpoint to fetch summary dashboard data."""
    try:
        stats = get_stats()
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Stats API error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@api_bp.route("/health", methods=["GET"])
def api_health():
    """Endpoint verifying service health (server, database, model)."""
    health = {
        "server": "Running",
        "database": "Disconnected",
        "model": "Not Trained"
    }
    
    # 1. Verify database connection
    try:
        conn = get_db_connection()
        conn.cursor().execute("SELECT 1")
        conn.close()
        health["database"] = "Connected"
    except Exception as e:
        logger.error(f"Health check database verification failed: {e}")
        
    # 2. Verify model file existence
    if os.path.exists(Config.MODEL_PATH):
        health["model"] = "Loaded"
        
    return jsonify(health), 200
