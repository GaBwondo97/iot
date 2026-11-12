from typing import List, Dict, Any
from data_engineering.schemas.observation import Observation
from data_engineering.schemas.process_result import ProcessResult
from data_engineering.adapters.iot import parse_iot_payload
from data_engineering.validation.validator import validate_observation
from data_engineering.normalization.normalizer import normalize_observation
from data_engineering.deduplication.deduplicator import Deduplicator

deduplicator = Deduplicator()

def process_iot_message(payload: Dict[str, Any]) -> ProcessResult:
    """End-to-end processing of a single IoT message."""
    result = ProcessResult(accepted=[], rejected=[])
    
    # 1. Adapt/Parse
    parsed_records, parsing_errors = parse_iot_payload(payload)
    for err in parsing_errors:
        result.add_rejection(err.raw_data, err.reason)
        
    # 2. Validate, Normalize, Deduplicate
    for obs in parsed_records:
        if not deduplicator.is_unique(obs):
            result.add_rejection(obs.model_dump(), "Duplicate record")
            continue
            
        is_valid, reason = validate_observation(obs)
        if not is_valid:
            result.add_rejection(obs.model_dump(), reason)
            continue
            
        normalized_obs = normalize_observation(obs)
        result.accepted.append(normalized_obs)
        
    return result
