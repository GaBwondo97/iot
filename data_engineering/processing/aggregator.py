from typing import List, Dict
from data_engineering.schemas.observation import Observation

def aggregate_hourly(observations: List[Observation]) -> Dict[str, float]:
    aggs = {}
    counts = {}
    for obs in observations:
        if obs.metric not in aggs:
            aggs[obs.metric] = 0.0
            counts[obs.metric] = 0
        aggs[obs.metric] += obs.value
        counts[obs.metric] += 1
        
    return {k: v / counts[k] for k, v in aggs.items()}
