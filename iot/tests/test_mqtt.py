
import json
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest

from mqtt.publisher import MqttPublisher


@pytest.fixture
def publisher():

    with patch("mqtt.publisher.get_mqtt_config") as mock_config:

        mock_config.return_value = {
            "broker": "localhost",
            "port": 1883,
            "keepalive": 60,
            "client_id": "test_client",
            "topics": {
                "weather": "citypulse/weather",
                "air_quality": "citypulse/air_quality",
                "traffic": "citypulse/traffic",
                "population": "citypulse/population"
            }
        }

        mqtt_publisher = MqttPublisher()
        mqtt_publisher.client = MagicMock()

        yield mqtt_publisher


def create_valid_data(category, measurements):

    return {
        "record_id": "test-record-001",
        "city_id": "CITYPULSE_DEMO",
        "category_id": category,
        "category_name": f"{category} Monitoring",
        "location": "Kuala Lumpur",
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat().replace("+00:00", "Z"),
        "source_type": "simulation",
        "measurements": measurements
    }


def configure_successful_publish(publisher):

    mock_result = MagicMock()
    mock_result.rc = 0
    mock_result.is_published.return_value = True

    publisher.client.publish.return_value = mock_result

    return mock_result


# ==========================================================
# WEATHER MQTT TEST
# ==========================================================

def test_weather_mqtt_topic(publisher):

    data = create_valid_data("WEATHER", {
        "temperature": 30,
        "humidity": 75,
        "wind_speed": 12,
        "rainfall": 2
    })

    configure_successful_publish(publisher)

    publisher.publish_sensor_data(data)

    args = publisher.client.publish.call_args

    assert args[0][0] == "citypulse/weather"


# ==========================================================
# AIR QUALITY MQTT TEST
# ==========================================================

def test_air_quality_mqtt_topic(publisher):

    data = create_valid_data("AIR", {
        "pm2_5": 25,
        "pm10": 40,
        "co2": 650,
        "aqi": 50
    })

    configure_successful_publish(publisher)

    publisher.publish_sensor_data(data)

    args = publisher.client.publish.call_args

    assert args[0][0] == "citypulse/air_quality"


# ==========================================================
# TRAFFIC MQTT TEST
# ==========================================================

def test_traffic_mqtt_topic(publisher):

    data = create_valid_data("TRAFFIC", {
        "vehicle_count": 120,
        "average_speed": 45,
        "traffic_density": 20,
        "congestion_category": "Medium"
    })

    configure_successful_publish(publisher)

    publisher.publish_sensor_data(data)

    args = publisher.client.publish.call_args

    assert args[0][0] == "citypulse/traffic"


# ==========================================================
# POPULATION MQTT TEST
# ==========================================================

def test_population_mqtt_topic(publisher):

    data = create_valid_data("POPULATION", {
        "estimated_population": 850,
        "population_density": 2500,
        "crowd_density_category": "High",
        "population_change": -15
    })

    configure_successful_publish(publisher)

    publisher.publish_sensor_data(data)

    args = publisher.client.publish.call_args

    assert args[0][0] == "citypulse/population"


# ==========================================================
# INVALID CATEGORY TEST
# ==========================================================

def test_invalid_category(publisher):

    data = create_valid_data("UNKNOWN", {})

    with pytest.raises(ValueError):
        publisher.publish_sensor_data(data)

    publisher.client.publish.assert_not_called()


# ==========================================================
# INVALID SENSOR DATA TEST
# ==========================================================

def test_invalid_sensor_data(publisher):

    data = create_valid_data("WEATHER", {
        "temperature": 30,
        "humidity": 150,
        "wind_speed": 12,
        "rainfall": 2
    })

    with pytest.raises(ValueError):
        publisher.publish_sensor_data(data)

    publisher.client.publish.assert_not_called()


# ==========================================================
# MQTT PUBLISH FAILURE TEST
# ==========================================================

def test_mqtt_publish_failure(publisher):

    data = create_valid_data("WEATHER", {
        "temperature": 30,
        "humidity": 75,
        "wind_speed": 12,
        "rainfall": 2
    })

    mock_result = MagicMock()
    mock_result.rc = 1

    publisher.client.publish.return_value = mock_result

    with pytest.raises(RuntimeError):
        publisher.publish_sensor_data(data)


# ==========================================================
# MQTT PUBLISH TIMEOUT TEST
# ==========================================================

def test_mqtt_publish_timeout(publisher):

    data = create_valid_data("WEATHER", {
        "temperature": 30,
        "humidity": 75,
        "wind_speed": 12,
        "rainfall": 2
    })

    mock_result = MagicMock()
    mock_result.rc = 0
    mock_result.is_published.return_value = False

    publisher.client.publish.return_value = mock_result

    with pytest.raises(TimeoutError):
        publisher.publish_sensor_data(data)


# ==========================================================
# JSON PAYLOAD TEST
# ==========================================================

def test_mqtt_payload_is_valid_json(publisher):

    data = create_valid_data("WEATHER", {
        "temperature": 30,
        "humidity": 75,
        "wind_speed": 12,
        "rainfall": 2
    })

    configure_successful_publish(publisher)

    publisher.publish_sensor_data(data)

    args = publisher.client.publish.call_args

    decoded_payload = json.loads(args[0][1])

    assert decoded_payload == data


# ==========================================================
# PUBLISH CALL TEST
# ==========================================================

def test_mqtt_publish_called_once(publisher):

    data = create_valid_data("WEATHER", {
        "temperature": 30,
        "humidity": 75,
        "wind_speed": 12,
        "rainfall": 2
    })

    configure_successful_publish(publisher)

    publisher.publish_sensor_data(data)

    publisher.client.publish.assert_called_once()


# ==========================================================
# PUBLISH CONFIRMATION TEST
# ==========================================================

def test_mqtt_publish_waits_for_confirmation(publisher):

    data = create_valid_data("WEATHER", {
        "temperature": 30,
        "humidity": 75,
        "wind_speed": 12,
        "rainfall": 2
    })

    mock_result = configure_successful_publish(publisher)

    publisher.publish_sensor_data(data)

    mock_result.wait_for_publish.assert_called_once_with(
        timeout=10
    )
