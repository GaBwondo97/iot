from data_engineering.schemas.observation import Observation
from datetime import datetime, timezone

def validate_observation(obs: Observation) -> tuple[bool, str]:
    # Freshness check
    now = datetime.now(timezone.utc)
    if obs.timestamp.tzinfo is None:
        obs.timestamp = obs.timestamp.replace(tzinfo=timezone.utc)
        
    age_seconds = (now - obs.timestamp).total_seconds()
    if age_seconds > 86400: # Older than 24h
        return False, "Data too old (stale)"
        
    # Hard rules based on metric
    if obs.metric == "temperature" and not (-50 <= obs.value <= 60):
        return False, f"Temperature {obs.value} out of bounds"
    if obs.metric == "humidity" and not (0 <= obs.value <= 100):
        return False, f"Humidity {obs.value} out of bounds"
        
    return True, "Valid"
