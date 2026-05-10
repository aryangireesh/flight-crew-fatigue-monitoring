from joblib import load
import numpy as np
from datetime import datetime

model = load("fatigue_model.pkl")

def predict_fatigue_ml(
    time_on_duty,
    hr,
    perclos,
    yawns,
    event_time_iso
):
    hour = datetime.fromisoformat(event_time_iso).hour

    X = np.array([[
        time_on_duty,
        hr,
        perclos,
        yawns,
        hour
    ]])

    prediction = model.predict(X)[0]
    return max(0, min(100, prediction))
