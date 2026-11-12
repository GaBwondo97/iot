import json
import os
import sys
from datetime import datetime, timezone

# Ensure the root package is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_engineering.pipeline import process_iot_message
from ai_engine.engine import assess

def main():
    print("--- Starting CityPulse AI Demo ---")
    
    # Load Fixtures
    fixture_path = os.path.join(
        os.path.dirname(__file__), 
        '../data_engineering/fixtures/sample_iot_messages.json'
    )
    with open(fixture_path, 'r') as f:
        messages = json.load(f)
        
    all_accepted_observations = []
    
    print("\n[1] Processing IoT Messages through Data Engineering Pipeline...")
    for i, msg in enumerate(messages):
        res = process_iot_message(msg)
        all_accepted_observations.extend(res.accepted)
        print(f"Message {i+1}: {len(res.accepted)} accepted, {len(res.rejected)} rejected.")
        for rej in res.rejected:
            print(f"  -> Rejected: {rej.reason}")
            
    print("\n[2] Running AI Engine Risk Fusion & Assessment...")
    now = datetime.now(timezone.utc)
    assessment = assess(city_id="kuala_lumpur_cheras", observations=all_accepted_observations, current_time=now)
    
    print("\n--- Final Assessment Report ---")
    print(f"City ID: {assessment.city_id}")
    print(f"Overall Risk Score: {assessment.overall_risk_score:.2f} / 100.0")
    print("Category Scores:")
    for cat, score in assessment.category_scores.items():
        print(f"  - {cat.capitalize()}: {score:.2f}")
        
    print("Anomalies Detected:")
    for a in assessment.anomalies_detected:
        print(f"  - [ALERT] {a}")
        
    print("Recommendations:")
    for r in assessment.recommendations:
        print(f"  - {r}")

if __name__ == "__main__":
    main()
