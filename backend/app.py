from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from datetime import datetime
import os

# ==============================
# Flask App Setup
# ==============================
app = Flask(
    __name__,
    static_folder="static",
    static_url_path="/static"
)
DB = "fatigue.db"

# ==============================
# ML Import (SAFE)
# ==============================
USE_ML = False
try:
    from ml_predict import predict_fatigue_ml
    USE_ML = True
    print("✅ ML model loaded successfully")
except Exception as e:
    print("⚠️ ML disabled:", e)

# ==============================
# Database Helpers
# ==============================
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS crew (
        crew_id TEXT PRIMARY KEY,
        name TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        crew_id TEXT,
        event_time TEXT,
        duty_start TEXT,
        time_on_duty_hours REAL,
        hr REAL,
        perclos REAL,
        yawns INTEGER,
        fatigue_score REAL
    )
    """)

    conn.commit()
    conn.close()

# ==============================
# Rule-Based Fatigue Algorithm
# ==============================
def compute_rule_fatigue(actual_sleep, duty_hours, hr, perclos, yawns):
    sleep_factor = max(0, (8 - actual_sleep) / 8)
    duty_factor = min(1, duty_hours / 12)
    behavior_factor = min(1, perclos + yawns / 5)

    hr_penalty = 0.2 if (hr < 50 or hr > 110) else 0

    score = (
        0.35 * sleep_factor +
        0.25 * duty_factor +
        0.30 * behavior_factor +
        hr_penalty
    ) * 100

    return round(min(score, 100), 2)

# ==============================
# Serve Frontend
# ==============================
FRONTEND_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "frontend"
)

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")

# ==============================
# API: Add Crew
# ==============================
@app.route("/crew", methods=["POST"])
def add_crew():
    data = request.json
    crew_id = data["crew_id"]
    name = data.get("name", "")

    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO crew (crew_id, name) VALUES (?, ?)",
        (crew_id, name)
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

# ==============================
# API: Add Fatigue Event (ML HERE ✅)
# ==============================
@app.route("/event", methods=["POST"])
def add_event():
    data = request.json

    crew_id = data["crew_id"]
    event_time = data["event_time"]
    duty_start = data["duty_start"]
    hr = float(data["hr"])
    perclos = float(data["perclos"])
    yawns = int(data["yawns"])
    actual_sleep = float(data["actual_sleep_last_24h"])

    # Convert timestamps
    event_dt = datetime.fromisoformat(event_time.replace("Z", ""))
    duty_dt = datetime.fromisoformat(duty_start.replace("Z", ""))

    duty_hours = (event_dt - duty_dt).total_seconds() / 3600

    # ---- RULE-BASED FATIGUE ----
    rule_score = compute_rule_fatigue(
        actual_sleep, duty_hours, hr, perclos, yawns
    )

    # ---- ML FATIGUE PREDICTION ----
    if USE_ML:
        try:
            ml_score = predict_fatigue_ml(
                duty_hours,
                hr,
                perclos,
                yawns,
                event_time.replace("Z", "")
            )
            final_score = round(0.6 * rule_score + 0.4 * ml_score, 2)
        except Exception as e:
            print("⚠️ ML prediction failed:", e)
            final_score = rule_score
    else:
        final_score = rule_score

    # Store in DB
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO events
        (crew_id, event_time, duty_start, time_on_duty_hours,
         hr, perclos, yawns, fatigue_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        crew_id, event_time, duty_start, duty_hours,
        hr, perclos, yawns, final_score
    ))
    conn.commit()
    conn.close()

    return jsonify({
        "status": "ok",
        "rule_score": rule_score,
        "final_fatigue_score": final_score
    })

# ==============================
# API: Latest Event
# ==============================
@app.route("/latest/<crew_id>")
def latest(crew_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM events
        WHERE crew_id = ?
        ORDER BY event_time DESC
        LIMIT 1
    """, (crew_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "no events"})

    return jsonify(dict(row))

# ==============================
# API: Event History
# ==============================
@app.route("/events/<crew_id>")
def history(crew_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM events
        WHERE crew_id = ?
        ORDER BY event_time DESC
        LIMIT 50
    """, (crew_id,))
    rows = c.fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])

# ==============================
# Start Server
# ==============================
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
