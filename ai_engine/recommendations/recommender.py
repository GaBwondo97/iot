from typing import Dict, List

def generate_recommendations(category_scores: Dict[str, float], anomalies: List[str]) -> List[str]:
    recs = []
    if category_scores.get("environmental", 0) > 60:
        recs.append("Issue health advisory for sensitive groups due to air quality.")
    if category_scores.get("mobility", 0) > 70:
        recs.append("Deploy traffic wardens to congestion hotspots and reroute public transit.")
    if not recs:
        recs.append("Systems normal. Continue baseline monitoring.")
    return recs
