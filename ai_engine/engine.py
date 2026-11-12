from typing import List
from datetime import datetime
from data_engineering.schemas.observation import Observation
from data_engineering.schemas.assessment import Assessment
from ai_engine.risk_scoring.scorer import calculate_risk
from ai_engine.recommendations.recommender import generate_recommendations
from ai_engine.anomaly_detection.detector import detect_anomalies

def assess(city_id: str, observations: List[Observation], current_time: datetime) -> Assessment:
    # 1. Detect Anomalies
    anomalies = detect_anomalies(observations)
    
    # 2. Score Risk
    overall_risk, category_scores = calculate_risk(observations)
    
    # 3. Generate Recommendations
    recs = generate_recommendations(category_scores, anomalies)
    
    return Assessment(
        city_id=city_id,
        timestamp=current_time,
        overall_risk_score=overall_risk,
        category_scores=category_scores,
        anomalies_detected=anomalies,
        recommendations=recs
    )
