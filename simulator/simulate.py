# simulator/simulate.py
import requests, random, time, uuid
from datetime import datetime, timedelta

API = "http://localhost:5000"

def create_crew(crew_id, name):
    r = requests.post(f"{API}/crew", json={"crew_id": crew_id, "name": name})
    print("create_crew", r.json())

def log_sleep(crew_id, start, end):
    r = requests.post(f"{API}/sleep", json={
        "crew_id": crew_id,
        "sleep_start": start.isoformat(),
        "sleep_end": end.isoformat()
    })
    print("sleep log", r.json())

def send_event(crew_id, duty_start_iso):
    # simulate HR, perclos, yawns
    hr = random.gauss(75, 8)
    # perclos higher in fatigue: random 0..0.4 typical; make occasional spikes
    perclos = max(0, min(1, random.random() * 0.35 + (0.2 if random.random() < 0.05 else 0)))
    yawns = random.choices([0,1,2,3], weights=[80,12,6,2])[0]
    # actual sleep last 24h — for demo use a randomish value
    actual_sleep = random.choice([4.0, 5.5, 7.0, 8.0])
    payload = {
        "crew_id": crew_id,
        "event_time": datetime.utcnow().isoformat(),
        "duty_start": duty_start_iso,
        "hr": round(hr,1),
        "perclos": round(perclos,3),
        "yawns": yawns,
        "actual_sleep_last_24h": actual_sleep
    }
    r = requests.post(f"{API}/event", json=payload)
    print("event->", payload, "=>", r.json())

if __name__ == '__main__':
    crew_id = "P001"
    create_crew(crew_id, "Captain Test")
    # log a short sleep last night
    now = datetime.utcnow()
    sleep_start = now - timedelta(hours=30)
    sleep_end = sleep_start + timedelta(hours=4.0)  # short sleep
    log_sleep(crew_id, sleep_start, sleep_end)

    duty_start = (now - timedelta(hours=4)).isoformat()
    # send a stream of events
    for i in range(10):
        send_event(crew_id, duty_start)
        time.sleep(1)
