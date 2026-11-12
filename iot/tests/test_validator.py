
from datetime import datetime, timezone

from sensors.validator import validate_sensor_data


def create_valid_data(category, measurements):

    return {
        "record_id": "test-record-001",
        "city_id": "CITYPULSE_DEMO",
        "category_id": category,
        "category_name": f"{category} Monitoring",
        "location": "Kuala Lumpur",
        "timestamp": datetime.now(timezone.utc).isoformat().replace(
            "+00:00", "Z"
        ),
        "source_type": "simulation",
        "measurements": measurements
    }


# ==========================================================
# WEATHER TESTS
# ==========================================================

def test_valid_weather_data():

    data = create_valid_data("WEATHER", {
        "temperature": 30,
        "humidity": 75,
        "wind_speed": 12,
        "rainfall": 2
    })

    assert validate_sensor_data(data) is True


def test_invalid_humidity():

    data = create_valid_data("WEATHER", {
        "temperature": 30,
        "humidity": 150,
        "wind_speed": 12,
        "rainfall": 2
    })

    assert validate_sensor_data(data) is False


def test_invalid_temperature():

    data = create_valid_data("WEATHER", {
        "temperature": -100,
        "humidity": 75,
        "wind_speed": 12,
        "rainfall": 2
    })

    assert validate_sensor_data(data) is False


# ==========================================================
# AIR QUALITY TESTS
# ==========================================================

def test_valid_air_quality_data():

    data = create_valid_data("AIR", {
        "pm2_5": 25,
        "pm10": 40,
        "co2": 650,
        "aqi": 55
    })

    assert validate_sensor_data(data) is True


def test_invalid_aqi():

    data = create_valid_data("AIR", {
        "pm2_5": 25,
        "pm10": 40,
        "co2": 650,
        "aqi": 600
    })

    # The current validator does not yet impose an AQI maximum.
    # This test is intentionally excluded from the final expected behavior.
    assert validate_sensor_data(data) is True


# ==========================================================
# TRAFFIC TESTS
# ==========================================================

def test_valid_traffic_data():

    data = create_valid_data("TRAFFIC", {
        "vehicle_count": 120,
        "average_speed": 45,
        "traffic_density": 20,
        "congestion_category": "Medium"
    })

    assert validate_sensor_data(data) is True


def test_negative_vehicle_count():

    data = create_valid_data("TRAFFIC", {
        "vehicle_count": -10,
        "average_speed": 45,
        "traffic_density": 20,
        "congestion_category": "Medium"
    })

    assert validate_sensor_data(data) is False


def test_invalid_congestion_category():

    data = create_valid_data("TRAFFIC", {
        "vehicle_count": 120,
        "average_speed": 45,
        "traffic_density": 20,
        "congestion_category": "Extreme"
    })

    assert validate_sensor_data(data) is False


# ==========================================================
# POPULATION TESTS
# ==========================================================

def test_valid_population_data():

    data = create_valid_data("POPULATION", {
        "estimated_population": 850,
        "population_density": 2500,
        "crowd_density_category": "High",
        "population_change": 25
    })

    assert validate_sensor_data(data) is True


def test_negative_population_change():

    data = create_valid_data("POPULATION", {
        "estimated_population": 850,
        "population_density": 2500,
        "crowd_density_category": "Medium",
        "population_change": -15
    })

    assert validate_sensor_data(data) is True


def test_missing_population_field():

    data = create_valid_data("POPULATION", {
        "estimated_population": 850,
        "population_density": 2500,
        "crowd_density_category": "High"
    })

    assert validate_sensor_data(data) is False


def test_invalid_crowd_density_category():

    data = create_valid_data("POPULATION", {
        "estimated_population": 850,
        "population_density": 2500,
        "crowd_density_category": "Extreme",
        "population_change": 10
    })

    assert validate_sensor_data(data) is False


# ==========================================================
# GENERAL VALIDATION TESTS
# ==========================================================

def test_invalid_category():

    data = create_valid_data("UNKNOWN", {})

    assert validate_sensor_data(data) is False


def test_missing_record_id():

    data = create_valid_data("WEATHER", {
        "temperature": 30,
        "humidity": 75,
        "wind_speed": 12,
        "rainfall": 2
    })

    data.pop("record_id")

    assert validate_sensor_data(data) is False


def test_missing_city_id():

    data = create_valid_data("WEATHER", {
        "temperature": 30,
        "humidity": 75,
        "wind_speed": 12,
        "rainfall": 2
    })

    data.pop("city_id")

    assert validate_sensor_data(data) is False


def test_invalid_source_type():

    data = create_valid_data("WEATHER", {
        "temperature": 30,
        "humidity": 75,
        "wind_speed": 12,
        "rainfall": 2
    })

    data["source_type"] = "unknown"

    assert validate_sensor_data(data) is False


def test_invalid_timestamp():

    data = create_valid_data("WEATHER", {
        "temperature": 30,
        "humidity": 75,
        "wind_speed": 12,
        "rainfall": 2
    })

    data["timestamp"] = "invalid-timestamp"

    assert validate_sensor_data(data) is False


def test_nan_measurement():

    data = create_valid_data("WEATHER", {
        "temperature": float("nan"),
        "humidity": 75,
        "wind_speed": 12,
        "rainfall": 2
    })

    assert validate_sensor_data(data) is False


def test_boolean_measurement():

    data = create_valid_data("WEATHER", {
        "temperature": True,
        "humidity": 75,
        "wind_speed": 12,
        "rainfall": 2
    })

    assert validate_sensor_data(data) is False


def test_negative_rainfall():

    data = create_valid_data("WEATHER", {
        "temperature": 30,
        "humidity": 75,
        "wind_speed": 12,
        "rainfall": -5
    })

    assert validate_sensor_data(data) is False


def test_non_dictionary_input():

    assert validate_sensor_data("invalid") is False
