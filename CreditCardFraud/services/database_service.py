import sqlite3
import os
import datetime
from config import Config

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    # Ensure parent directory exists
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database and creates the transactions table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id TEXT NOT NULL,
            amount REAL NOT NULL,
            merchant TEXT,
            location TEXT,
            device_id TEXT,
            transaction_time TEXT,
            prediction TEXT NOT NULL,
            risk_score REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_transaction(card_id, amount, merchant, location, device_id, transaction_time, prediction, risk_score):
    """Saves a transaction record to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (card_id, amount, merchant, location, device_id, transaction_time, prediction, risk_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (card_id, amount, merchant, location, device_id, transaction_time, prediction, risk_score))
    conn.commit()
    conn.close()

def get_transactions(limit=100, offset=0):
    """Retrieves transaction history, ordered by newest first."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM transactions
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
    """, (limit, offset))
    rows = cursor.fetchall()
    conn.close()
    
    # Convert to list of dictionaries
    transactions = []
    for r in rows:
        transactions.append({
            "id": r["id"],
            "card_id": r["card_id"],
            "amount": r["amount"],
            "merchant": r["merchant"],
            "location": r["location"],
            "device_id": r["device_id"],
            "transaction_time": r["transaction_time"],
            "prediction": r["prediction"],
            "risk_score": r["risk_score"],
            "timestamp": r["timestamp"]
        })
    return transactions

def get_stats():
    """Computes and returns summary statistics for the dashboard and analytics pages."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    # 1. KPI Counts
    cursor.execute("SELECT COUNT(*) FROM transactions")
    total_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM transactions WHERE timestamp LIKE ?", (f"{today_str}%",))
    today_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM transactions WHERE prediction = 'Fraud'")
    total_fraud = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM transactions WHERE prediction = 'Fraud' AND timestamp LIKE ?", (f"{today_str}%",))
    today_fraud = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM transactions WHERE prediction = 'Genuine'")
    total_genuine = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM transactions WHERE prediction = 'Genuine' AND timestamp LIKE ?", (f"{today_str}%",))
    today_genuine = cursor.fetchone()[0]
    
    cursor.execute("SELECT AVG(risk_score) FROM transactions")
    avg_risk_score = cursor.fetchone()[0] or 0.0
    
    fraud_percentage = (total_fraud / total_count * 100) if total_count > 0 else 0.0
    
    # 2. Hourly Transactions (last 24 hours)
    cursor.execute("""
        SELECT strftime('%H', timestamp) as hr, COUNT(*) as cnt 
        FROM transactions 
        GROUP BY hr 
        ORDER BY hr
    """)
    hourly_rows = cursor.fetchall()
    hourly_transactions = {f"{i:02d}": 0 for i in range(24)}
    for r in hourly_rows:
        if r["hr"] is not None:
            hourly_transactions[r["hr"]] = r["cnt"]
            
    # 3. Daily Fraud Trend (last 7 days)
    cursor.execute("""
        SELECT date(timestamp) as dt, COUNT(*) as cnt 
        FROM transactions 
        WHERE prediction = 'Fraud'
        GROUP BY dt 
        ORDER BY dt DESC
        LIMIT 7
    """)
    fraud_trend_rows = cursor.fetchall()
    fraud_trend = {r["dt"]: r["cnt"] for r in fraud_trend_rows}
    
    # 4. Daily Genuine Trend (last 7 days)
    cursor.execute("""
        SELECT date(timestamp) as dt, COUNT(*) as cnt 
        FROM transactions 
        WHERE prediction = 'Genuine'
        GROUP BY dt 
        ORDER BY dt DESC
        LIMIT 7
    """)
    genuine_trend_rows = cursor.fetchall()
    genuine_trend = {r["dt"]: r["cnt"] for r in genuine_trend_rows}
    
    # 5. Top Merchants
    cursor.execute("""
        SELECT merchant, COUNT(*) as cnt 
        FROM transactions 
        GROUP BY merchant 
        ORDER BY cnt DESC 
        LIMIT 5
    """)
    merchant_rows = cursor.fetchall()
    top_merchants = [{"merchant": r["merchant"] or "Unknown", "count": r["cnt"]} for r in merchant_rows]
    
    # 6. Risk Score Distribution
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN risk_score < 0.2 THEN 1 ELSE 0 END) as low,
            SUM(CASE WHEN risk_score >= 0.2 AND risk_score < 0.5 THEN 1 ELSE 0 END) as med_low,
            SUM(CASE WHEN risk_score >= 0.5 AND risk_score < 0.8 THEN 1 ELSE 0 END) as med_high,
            SUM(CASE WHEN risk_score >= 0.8 THEN 1 ELSE 0 END) as high
        FROM transactions
    """)
    risk_dist_row = cursor.fetchone()
    risk_distribution = {
        "0.0-0.2": risk_dist_row[0] or 0,
        "0.2-0.5": risk_dist_row[1] or 0,
        "0.5-0.8": risk_dist_row[2] or 0,
        "0.8-1.0": risk_dist_row[3] or 0
    }
    
    # 7. Fraud by Amount Ranges
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN amount < 50 AND prediction = 'Fraud' THEN 1 ELSE 0 END) as range1,
            SUM(CASE WHEN amount >= 50 AND amount < 200 AND prediction = 'Fraud' THEN 1 ELSE 0 END) as range2,
            SUM(CASE WHEN amount >= 200 AND amount < 1000 AND prediction = 'Fraud' THEN 1 ELSE 0 END) as range3,
            SUM(CASE WHEN amount >= 1000 AND prediction = 'Fraud' THEN 1 ELSE 0 END) as range4
        FROM transactions
    """)
    amt_fraud_row = cursor.fetchone()
    fraud_by_amount = {
        "< $50": amt_fraud_row[0] or 0,
        "$50 - $200": amt_fraud_row[1] or 0,
        "$200 - $1000": amt_fraud_row[2] or 0,
        "> $1000": amt_fraud_row[3] or 0
    }
    
    conn.close()
    
    return {
        "total_transactions": total_count,
        "today_transactions": today_count,
        "total_fraud": total_fraud,
        "today_fraud": today_fraud,
        "total_genuine": total_genuine,
        "today_genuine": today_genuine,
        "avg_risk_score": round(avg_risk_score, 2),
        "fraud_percentage": round(fraud_percentage, 2),
        "hourly_transactions": hourly_transactions,
        "fraud_trend": fraud_trend,
        "genuine_trend": genuine_trend,
        "top_merchants": top_merchants,
        "risk_distribution": risk_distribution,
        "fraud_by_amount": fraud_by_amount
    }
