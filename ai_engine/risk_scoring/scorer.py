from typing import List, Tuple, Dict
from data_engineering.schemas.observation import Observation

def calculate_risk(observations: List[Observation]) -> Tuple[float, Dict[str, float]]:
    env_score = 0.0
    mob_score = 0.0
    
    # Simplified mock scoring based on raw values for demo
    for obs in observations:
        if obs.metric == "pm25":
            env_score += min(obs.value / 2.0, 100.0) # PM25 over 200 = 100% risk
        elif obs.metric == "traffic_speed":
            mob_score += max(100.0 - obs.value, 0.0) # Speed 0 = 100% risk
            
    # Normalize (naive)
    env_risk = min(env_score, 100.0)
    mob_risk = min(mob_score, 100.0)
    
    overall = (env_risk * 0.6) + (mob_risk * 0.4)
    
    return overall, {"environmental": env_risk, "mobility": mob_risk}
