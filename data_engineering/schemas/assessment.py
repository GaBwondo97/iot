from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime

class Assessment(BaseModel):
    city_id: str
    timestamp: datetime
    overall_risk_score: float
    category_scores: Dict[str, float]
    anomalies_detected: List[str]
    recommendations: List[str]
