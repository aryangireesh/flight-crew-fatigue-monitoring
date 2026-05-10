import requests, random, time
from datetime import datetime, timedelta

API = "http://127.0.0.1:5000"

def create_crew(crew_id, name):
    r = requests.post(f"{API}/crew", json={"crew_id": crew_id, "name": name})
    print("create_crew", crew_id, r.json())

def send_event(crew_id, duty_hours, sleep_hours, base_hr, base_perclos, yawns_range):
    now = datetime.utcnow()
    duty_start = now - timedelta(hours=duty_hours)
    payload = {
        "crew_id": crew_id,
        "event_time": now.isoformat(),
        "duty_start": duty_start.isoformat(),
        "hr": round(base_hr + random.uniform(-5,5),1),
        "perclos": round(base_perclos + random.uniform(-0.05,0.05),3),
        "yawns": random.randint(*yawns_range),
        "actual_sleep_last_24h": sleep_hours
    }
    r = requests.post(f"{API}/event", json=payload)
    print("event", crew_id, "=>", r.json().get("fatigue_score"))

if __name__ == '__main__':
    # make sure backend app.py is running first!
    pilots = [
        ("P001","Captain Rested", 2, 8.0, 72, 0.12, (0,1)),
        ("P002","Captain Medium", 5, 6.0, 80, 0.25, (1,3)),
        ("P003","Captain Tired", 9, 3.5, 90, 0.40, (2,4)),
        ("P004","FO Longhaul", 7, 5.0, 78, 0.30, (1,3)),
        ("P005","FO Night", 10, 4.0, 82, 0.35, (2,4)),
    ]

    for crew_id, name, duty, sleep, hr, perclos, yawns_rng in pilots:
        create_crew(crew_id, name)
        for i in range(10):   # 10 events each -> 50 total
            send_event(crew_id, duty, sleep, hr, perclos, yawns_rng)
            time.sleep(0.2)
