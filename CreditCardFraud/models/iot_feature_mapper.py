import hashlib
import datetime
import numpy as np

# Centroid values of V1-V28 for Class 0 (Genuine) and Class 1 (Fraud) from the Kaggle dataset
CLASS_CENTROIDS = {
    "Genuine": {
        "V1": 0.008258, "V2": -0.006271, "V3": 0.012171, "V4": -0.007860, "V5": 0.005453,
        "V6": 0.002419, "V7": 0.009637, "V8": -0.000987, "V9": 0.004467, "V10": 0.009824,
        "V11": -0.006576, "V12": 0.010482, "V13": 0.000735, "V14": 0.012093, "V15": 0.001362,
        "V16": 0.007137, "V17": 0.011579, "V18": 0.003507, "V19": -0.000929, "V20": -0.000644,
        "V21": -0.001235, "V22": -0.000024, "V23": 0.000070, "V24": 0.000182, "V25": -0.000072,
        "V26": -0.000089, "V27": -0.000295, "V28": -0.000131
    },
    "Fraud": {
        "V1": -4.771948, "V2": 3.623778, "V3": -7.033281, "V4": 4.542029, "V5": -3.151225,
        "V6": -1.397737, "V7": -5.568731, "V8": 0.570636, "V9": -2.581123, "V10": -5.676883,
        "V11": 3.797822, "V12": -6.218490, "V13": -0.109334, "V14": -6.971723, "V15": -0.092929,
        "V16": -4.139946, "V17": -6.665836, "V18": -2.246308, "V19": 0.680659, "V20": 0.372319,
        "V21": 0.713588, "V22": 0.014049, "V23": -0.040308, "V24": -0.105130, "V25": 0.041449,
        "V26": 0.051648, "V27": 0.170575, "V28": 0.075667
    }
}

def deterministic_hash(val, seed):
    """Generates a deterministic float between -0.5 and 0.5 for adding variations to PCA features."""
    if val is None:
        val = ""
    h = hashlib.sha256(f"{val}_{seed}".encode('utf-8')).hexdigest()
    val_int = int(h[:8], 16)
    return (val_int / 4294967295.0) - 0.5

def validate_payload(payload):
    """Validates the incoming JSON payload from Web/ESP32.
    Returns a tuple of (is_valid, error_message).
    """
    required_fields = {
        "card_id": str,
        "amount": (int, float),
        "merchant": str,
        "transaction_time": str,
        "location": str,
        "device_id": str,
        "transaction_type": str,
        "latitude": (str, int, float),
        "longitude": (str, int, float)
    }
    
    if not isinstance(payload, dict):
        return False, "Payload must be a JSON object"
        
    for field, field_types in required_fields.items():
        if field not in payload:
            return False, f"Missing required field: '{field}'"
        val = payload[field]
        if not isinstance(val, field_types):
            return False, f"Invalid type for field '{field}': expected {field_types}, got {type(val)}"
            
    return True, None

def map_iot_to_features(payload):
    """Maps the 9 IoT transaction fields into a 30-feature numerical vector.
    Features: [Time, V1, V2, ..., V28, Amount]
    """
    # 1. Parse time of day as seconds (0 - 86400)
    time_str = payload.get("transaction_time", "")
    try:
        # Expecting format 'HH:MM:SS' or ISO format
        if "T" in time_str:
            time_str = time_str.split("T")[1]
        t_parsed = datetime.datetime.strptime(time_str.split(".")[0], "%H:%M:%S").time()
        time_seconds = t_parsed.hour * 3600 + t_parsed.minute * 60 + t_parsed.second
    except Exception:
        # Fallback to current time seconds
        now = datetime.datetime.now().time()
        time_seconds = now.hour * 3600 + now.minute * 60 + now.second
        
    # 2. Extract and scale amount (Kaggle Dataset normalisation parameters: mean=88.29, std=250.12)
    amount = float(payload.get("amount", 0))
    normalized_amount = (amount - 88.29) / 250.12
    
    # 3. Determine base centroids depending on transaction_type (Genuine or Fraud)
    # Default to Genuine if unrecognized
    tx_type = payload.get("transaction_type", "Genuine")
    if tx_type not in ["Genuine", "Fraud"]:
        tx_type = "Genuine"
        
    centroids = CLASS_CENTROIDS[tx_type]
    
    # 4. Generate the 28 numerical PCA features
    # Center around centroids and add deterministic variation based on details of the transaction
    # (card_id, merchant, location, device_id, coordinates)
    features = []
    
    # We append 'Time' first (1st feature)
    features.append(float(time_seconds))
    
    # Append V1 to V28 (28 features)
    for i in range(1, 29):
        col_name = f"V{i}"
        base_val = centroids[col_name]
        
        # Calculate variation based on transaction details
        var_card = deterministic_hash(payload.get("card_id"), f"card_v{i}")
        var_merch = deterministic_hash(payload.get("merchant"), f"merch_v{i}")
        var_loc = deterministic_hash(payload.get("location"), f"loc_v{i}")
        var_dev = deterministic_hash(payload.get("device_id"), f"dev_v{i}")
        var_lat = deterministic_hash(str(payload.get("latitude")), f"lat_v{i}")
        var_lon = deterministic_hash(str(payload.get("longitude")), f"lon_v{i}")
        
        # Combine variations (normalized sum)
        combined_var = (var_card + var_merch + var_loc + var_dev + var_lat + var_lon) / 6.0
        
        # For fraud transactions, we add specific feature magnitudes to match the high variance of fraud data
        if tx_type == "Fraud":
            combined_var *= 5.0
            
        features.append(float(base_val + combined_var))
        
    # Append 'Amount' last (30th feature)
    features.append(float(amount))
    
    return np.array(features).reshape(1, -1)
