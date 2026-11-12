from typing import List
from data_engineering.schemas.observation import Observation

def detect_anomalies(observations: List[Observation]) -> List[str]:
    anomalies = []
    for obs in observations:
        if obs.metric == "pm25" and obs.value > 100:
            anomalies.append(f"High PM2.5 detected: {obs.value} ug/m3 from {obs.sensor_id}")
        if obs.metric == "traffic_speed" and obs.value < 15:
            anomalies.append(f"Severe congestion detected: {obs.value} km/h at {obs.sensor_id}")
    return anomalies
