import os
import sys
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps

# Setup path to import config, api, services, etc.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import Config
from services.database_service import init_db, get_transactions, get_stats
from api.routes import api_bp
from iot.simulator import generate_transaction_payload

app = Flask(
    __name__,
    template_folder=os.path.join("..", "templates"),
    static_folder=os.path.join("..", "static"),
    static_url_path="/static"
)
app.config.from_object(Config)

# 1. Logging Configuration
os.makedirs(os.path.dirname(Config.LOG_FILE_PATH), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(Config.LOG_FILE_PATH),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("fraud_detector")
logger.info("Initializing Security Fraud Detection server...")

# 2. Database Initialization
try:
    init_db()
    logger.info("SQLite database initialized successfully.")
except Exception as e:
    logger.error(f"Error initializing SQLite database: {e}", exc_info=True)

# 3. Mount REST API Blueprint
app.register_blueprint(api_bp)
logger.info(f"API version {Config.API_VERSION} routes registered.")

# 4. Authentication Middleware
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "role" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# Context Processor to expose config variables to Jinja2 templates
@app.context_processor
def inject_config():
    return {
        "config_app_name": Config.APP_NAME,
        "config_api_version": Config.API_VERSION
    }

# 5. Page Navigation Routes

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role")
        password = request.form.get("password")
        
        # Simple local credential check
        if role == "Admin" and password == "admin":
            session["role"] = "Admin"
            logger.info("System Admin authorized session.")
            return redirect(url_for("dashboard"))
        elif role == "Analyst" and password == "analyst":
            session["role"] = "Analyst"
            logger.info("Analyst authorized session.")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid access password. Please try again.", "error")
            logger.warning(f"Unauthorized login attempt for role: {role}")
            
    return render_template("login.html")

@app.route("/logout")
def logout():
    role = session.pop("role", None)
    if role:
        logger.info(f"Session closed for role: {role}")
    return redirect(url_for("login"))

@app.route("/")
@login_required
def dashboard():
    """Renders main dashboard displaying metrics, trends, and recent transaction feeds."""
    try:
        stats = get_stats()
        recent_txs = get_transactions(limit=10, offset=0)
    except Exception as e:
        logger.error(f"Dashboard statistics retrieval failed: {e}", exc_info=True)
        stats = {
            "total_transactions": 0, "today_transactions": 0, "total_fraud": 0,
            "today_fraud": 0, "total_genuine": 0, "today_genuine": 0,
            "avg_risk_score": 0.0, "fraud_percentage": 0.0,
            "hourly_transactions": {}, "fraud_trend": {}, "genuine_trend": {},
            "top_merchants": [], "risk_distribution": {}, "fraud_by_amount": {}
        }
        recent_txs = []
        
    db_status = "Connected"
    model_status = "Loaded" if os.path.exists(Config.MODEL_PATH) else "Not Trained"
    
    return render_template(
        "dashboard.html",
        stats=stats,
        recent_transactions=recent_txs,
        db_status=db_status,
        model_status=model_status
    )

@app.route("/analytics")
@login_required
def analytics():
    """Renders deeper analytical charts and models evaluations."""
    try:
        stats = get_stats()
    except Exception as e:
        logger.error(f"Analytics stats retrieval failed: {e}", exc_info=True)
        stats = {}
    return render_template("analytics.html", stats=stats)

@app.route("/transaction-monitor")
@login_required
def transaction_monitor():
    """Renders live transaction log monitor and manual log simulation form."""
    try:
        txs = get_transactions(limit=50, offset=0)
    except Exception as e:
        logger.error(f"Transaction monitor logs retrieval failed: {e}", exc_info=True)
        txs = []
    return render_template("transaction_monitor.html", transactions=txs)

@app.route("/esp32-simulation")
@login_required
def esp32_simulation():
    """Renders ESP32 simulation console for generating client payloads."""
    return render_template("simulator.html")

@app.route("/esp32-status")
@login_required
def esp32_status():
    """Renders connection logs and status monitor metrics for external micro-controllers."""
    # Get last transaction details to show live connection logs
    try:
        recent_txs = get_transactions(limit=1, offset=0)
        last_tx = recent_txs[0] if recent_txs else None
    except Exception:
        last_tx = None
        
    db_status = "Connected"
    model_status = "Loaded" if os.path.exists(Config.MODEL_PATH) else "Not Trained"
    
    return render_template(
        "device_status.html",
        last_tx=last_tx,
        db_status=db_status,
        model_status=model_status
    )

@app.route("/docs")
@login_required
def docs():
    """Renders REST API endpoint schema documentation page."""
    return render_template("docs.html")

# Helper endpoint used by frontend javascript to fetch a random mock transaction payload
@app.route("/get-mock-payload")
@login_required
def get_mock_payload():
    tx_type = request.args.get("type", default="Genuine")
    payload = generate_transaction_payload(tx_type)
    return jsonify(payload)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
