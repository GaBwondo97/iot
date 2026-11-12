from data_engineering.schemas.observation import Observation

def normalize_observation(obs: Observation) -> Observation:
    # Convert Fahrenheit to Celsius
    if obs.metric == "temperature" and obs.unit == "F":
        obs.value = (obs.value - 32) * 5.0/9.0
        obs.unit = "C"
        
    # Standardize string formats
    obs.metric = obs.metric.lower().strip()
    return obs
