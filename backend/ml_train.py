import sqlite3
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from joblib import dump
from datetime import datetime

DB = "fatigue.db"

# Load data from SQLite
conn = sqlite3.connect(DB)
df = pd.read_sql_query("""
SELECT
    time_on_duty_hours,
    hr,
    perclos,
    yawns,
    fatigue_score,
    event_time
FROM events
WHERE hr IS NOT NULL
""", conn)
conn.close()

# Add circadian feature
df["event_hour"] = pd.to_datetime(
    df["event_time"],
    format="mixed",
    utc=True,
    errors="coerce"
).dt.hour
df = df.dropna()


# Feature matrix (X) and target (y)
X = df[[
    "time_on_duty_hours",
    "hr",
    "perclos",
    "yawns",
    "event_hour"
]]
y = df["fatigue_score"]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
model = RandomForestRegressor(
    n_estimators=100,
    random_state=42
)
model.fit(X_train, y_train)

# Save model
dump(model, "fatigue_model.pkl")

print("ML model trained and saved as fatigue_model.pkl")
print("Training R² score:", model.score(X_test, y_test))
