import requests
import sqlite3
import time
import threading

from datetime import datetime
from flask import Flask, jsonify, render_template, redirect, url_for

app = Flask(__name__)

# Configuration
API_URL = "http://127.0.0.1:5000/api"
CHECK_INTERVAL = 10
TIMEOUT = 5
DB_NAME = "health.db"
MAX_RECORDS = 100
RANDOM_API_URL = "http://127.0.0.1:5002/"

# Initialize database
def init_db():
    with sqlite3.connect(DB_NAME) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS health_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_time TEXT,
                status TEXT,
                http_code INTEGER
            )
        """)


# Check Notepad API health
def check_api():
    check_time = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    try:
        response = requests.get(API_URL, timeout=TIMEOUT)

        http_code = response.status_code

        if 200 <= http_code < 300:
            status = "HEALTHY"
        else:
            status = "UNHEALTHY"

    except requests.RequestException:
        status = "UNHEALTHY"
        http_code = None

    # Save result to the database
    with sqlite3.connect(DB_NAME) as db:
        db.execute("""
            INSERT INTO health_checks
            (check_time, status, http_code)
            VALUES (?, ?, ?)
        """, (check_time, status, http_code))
        # Keep only the latest 100 records
        db.execute("""
            DELETE FROM health_checks
            WHERE id NOT IN (
                SELECT id
                FROM health_checks
                ORDER BY id DESC
                LIMIT ?
            )
        """, (MAX_RECORDS,))

    print(f"{check_time} | {status} | HTTP: {http_code}")


# Background monitoring loop
def monitor_loop():
    while True:
        check_api()
        time.sleep(CHECK_INTERVAL)


# API endpoint to retrieve history
@app.get('/')
def index():
    return redirect(url_for('history_page'))

@app.get("/history")
def history_page():
    return render_template("history.html")

@app.get("/api/history")
def get_history_data():
    with sqlite3.connect(DB_NAME) as db:
        db.row_factory = sqlite3.Row

        rows = db.execute("""
            SELECT id, check_time, status, http_code
            FROM health_checks
            ORDER BY id DESC
        """).fetchall()

    return jsonify({
        "history": [dict(row) for row in rows]
    }), 200

@app.get("/api/status")
def get_status():
    try:
        response = requests.get(API_URL, timeout=TIMEOUT)

        return (
            response.content,
            response.status_code,
            {"Content-Type": response.headers.get(
                "Content-Type", "application/octet-stream"
            )}
        )

    except requests.RequestException:
        return jsonify({
            "error": "Notepad API is unreachable"
        }), 503

@app.get("/num")
def get_numbers():
    try:
        response = requests.get(RANDOM_API_URL, timeout=TIMEOUT)
        response.raise_for_status()

        data = response.json()

        num1 = data["number1"]
        num2 = data["number2"]
        total = num1 + num2

        return f"Got two numbers, {num1} and {num2}, the total is {total}", 200

    except requests.RequestException:
        return jsonify({"error": "Random Number API unavailable"}), 503

    except (ValueError, KeyError, TypeError):
        return jsonify({"error": "Invalid response from Random Number API"}), 502
    

if __name__ == "__main__":
    init_db()

    # Start monitoring in a background thread
    monitor_thread = threading.Thread(
        target=monitor_loop,
        daemon=True
    )
    monitor_thread.start()

    # Start Flask API server
    app.run(
    host="127.0.0.1",
    port=5001,
    debug=True
    )