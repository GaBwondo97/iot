from ai_engine.anomaly_detection.detector import detect_anomalies
from data_engineering.schemas.observation import Observation
from datetime import datetime, timezone

def test_detect_anomalies():
    obs = Observation(
        sensor_id="s1",
        metric="pm25",
        value=150.0,
        unit="ug/m3",
        timestamp=datetime.now(timezone.utc),
        city_id="city1"
    )
    anomalies = detect_anomalies([obs])
    assert len(anomalies) == 1
