from data_engineering.pipeline import process_iot_message

def test_process_valid_message():
    msg = {
        "device_id": "test_01",
        "timestamp": "2026-11-12T15:00:00Z",
        "metrics": {
            "temperature": {"value": 25.0, "unit": "C"}
        }
    }
    result = process_iot_message(msg)
    assert len(result.accepted) == 1
    assert len(result.rejected) == 0
