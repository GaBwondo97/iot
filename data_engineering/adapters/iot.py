from typing import Dict, Any, Tuple, List
from datetime import datetime
from data_engineering.schemas.observation import Observation, RejectRecord

def parse_iot_payload(payload: Dict[str, Any]) -> Tuple[List[Observation], List[RejectRecord]]:
    observations = []
    errors = []
    
    try:
        device_id = payload.get("device_id")
        city_id = payload.get("city_id", "default_city")
        timestamp_str = payload.get("timestamp")
        
        if not device_id or not timestamp_str:
            errors.append(RejectRecord(raw_data=payload, reason="Missing device_id or timestamp"))
            return observations, errors
            
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        
        # Handle metrics dictionary
        metrics = payload.get("metrics", {})
        for metric, data in metrics.items():
            if isinstance(data, dict) and "value" in data and "unit" in data:
                try:
                    obs = Observation(
                        sensor_id=f"{device_id}_{metric}",
                        metric=metric,
                        value=float(data["value"]),
                        unit=data["unit"],
                        timestamp=timestamp,
                        city_id=city_id
                    )
                    observations.append(obs)
                except Exception as e:
                    errors.append(RejectRecord(raw_data=data, reason=f"Invalid metric data for {metric}: {str(e)}"))
            else:
                errors.append(RejectRecord(raw_data=data, reason=f"Malformed metric payload for {metric}"))
                
    except Exception as e:
        errors.append(RejectRecord(raw_data=payload, reason=f"Fatal parsing error: {str(e)}"))
        
    return observations, errors
