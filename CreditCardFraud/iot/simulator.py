import random
import datetime

# Mock list of cardholders
CARD_IDS = [
    "card_8921_3920_4812", "card_1029_3847_5910", "card_4829_1028_3948", 
    "card_5829_3019_4820", "card_9381_1029_4829", "card_2048_3920_1928",
    "card_3948_5829_1029", "card_5829_4829_1039", "card_4920_1928_3847"
]

# Mock list of merchants
MERCHANTS = [
    "Starbucks Retail", "Amazon.com Gateway", "Shell Petroleum", "Target Store #102",
    "Walmart Grocery", "BestBuy Electronics", "Uber Technologies", "Netflix.com Subscription",
    "Apple Store Online", "Steam Games Inc", "Luxury Watches Outlet", "Electronic Wholesalers"
]

# Mock locations with coordinates
LOCATIONS = [
    {"name": "New York, USA", "lat": 40.7128, "lon": -74.0060},
    {"name": "London, UK", "lat": 51.5074, "lon": -0.1278},
    {"name": "Paris, France", "lat": 48.8566, "lon": 2.3522},
    {"name": "Tokyo, Japan", "lat": 35.6762, "lon": 139.6503},
    {"name": "Berlin, Germany", "lat": 52.5200, "lon": 13.4050},
    {"name": "Sydney, Australia", "lat": -33.8688, "lon": 151.2093},
    {"name": "Dubai, UAE", "lat": 25.2048, "lon": 55.2708},
    {"name": "Abu Dhabi, UAE", "lat": 24.4539, "lon": 54.3773}
]

# Mock devices
DEVICES = [
    "esp32_terminal_01", "esp32_terminal_02", "esp32_terminal_03",
    "esp32_terminal_04", "esp32_terminal_05", "esp32_terminal_06"
]

def generate_transaction_payload(transaction_type="Genuine"):
    """Generates a realistic transaction JSON payload representing an ESP32 event.
    
    * For 'Genuine': amount is typically low to moderate, location is regional, device is standard.
    * For 'Fraud': amount is typically higher, location may be foreign, device is often anomalous.
    """
    card_id = random.choice(CARD_IDS)
    merchant = random.choice(MERCHANTS)
    location_obj = random.choice(LOCATIONS)
    device_id = random.choice(DEVICES)
    
    # Capture current timestamp in HH:MM:SS format
    now = datetime.datetime.now()
    transaction_time = now.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Establish lat/lon
    lat = location_obj["lat"] + random.uniform(-0.01, 0.01)
    lon = location_obj["lon"] + random.uniform(-0.01, 0.01)
    
    # Establish transaction parameters based on simulated type
    if transaction_type == "Fraud":
        # Fraud often features high transaction amount
        amount = round(random.uniform(500.0, 5000.0), 2)
        # Select merchant likely to be associated with luxury fraud
        merchant = random.choice(["Luxury Watches Outlet", "Electronic Wholesalers", "Amazon.com Gateway"])
    else:
        # Genuine transactions are usually small to moderate
        amount = round(random.uniform(5.0, 150.0), 2)
        
    return {
        "card_id": card_id,
        "amount": amount,
        "merchant": merchant,
        "transaction_time": transaction_time,
        "location": location_obj["name"],
        "device_id": device_id,
        "transaction_type": transaction_type,
        "latitude": lat,
        "longitude": lon
    }
