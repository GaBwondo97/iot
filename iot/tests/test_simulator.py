
from datetime import datetime

from simulator.simulator import generate_all_data
from sensors.validator import validate_sensor_data


EXPECTED_FIELDS = {
    "WEATHER": {
        "temperature",
        "humidity",
        "wind_speed",
        "rainfall"
    },
    "AIR": {
        "pm2_5",
        "pm10",
        "co2",
        "aqi"
    },
    "TRAFFIC": {
        "vehicle_count",
        "average_speed",
        "traffic_density",
        "congestion_category"
    },
    "POPULATION": {
        "estimated_population",
        "population_density",
        "crowd_density_category",
        "population_change"
    }
}


# ==========================================================
# MONITORING CATEGORY TESTS
# ==========================================================

def test_all_monitoring_categories():

    readings = generate_all_data()

    assert len(readings) == 4

    categories = {
        reading["category_id"]
        for reading in readings
    }

    assert categories == {
        "WEATHER",
        "AIR",
        "TRAFFIC",
        "POPULATION"
    }


# ==========================================================
# READING METADATA TESTS
# ==========================================================

def test_readings_have_required_fields():

    readings = generate_all_data()

    required_fields = {
        "record_id",
        "city_id",
        "category_id",
        "category_name",
        "location",
        "timestamp",
        "source_type",
        "measurements"
    }

    for reading in readings:

        assert required_fields.issubset(reading.keys())


def test_readings_have_unique_record_ids():

    readings = generate_all_data()

    record_ids = [
        reading["record_id"]
        for reading in readings
    ]

    assert len(record_ids) == len(set(record_ids))


def test_readings_use_simulation_source():

    readings = generate_all_data()

    for reading in readings:

        assert reading["source_type"] == "simulation"


def test_readings_have_city_id():

    readings = generate_all_data()

    for reading in readings:

        assert isinstance(reading["city_id"], str)
        assert reading["city_id"].strip()


# ==========================================================
# TIMESTAMP TESTS
# ==========================================================

def test_readings_have_valid_utc_timestamps():

    readings = generate_all_data()

    for reading in readings:

        timestamp = datetime.fromisoformat(
            reading["timestamp"].replace("Z", "+00:00")
        )

        assert timestamp.tzinfo is not None
        assert timestamp.utcoffset().total_seconds() == 0


# ==========================================================
# MEASUREMENT TESTS
# ==========================================================

def test_measurements_are_not_empty():

    readings = generate_all_data()

    for reading in readings:

        assert isinstance(reading["measurements"], dict)
        assert len(reading["measurements"]) > 0


def test_each_category_has_correct_measurement_fields():

    readings = generate_all_data()

    for reading in readings:

        category = reading["category_id"]

        actual_fields = set(
            reading["measurements"].keys()
        )

        assert category in EXPECTED_FIELDS

        assert actual_fields == EXPECTED_FIELDS[category]


# ==========================================================
# VALIDATION TESTS
# ==========================================================

def test_all_generated_readings_pass_validation():

    readings = generate_all_data()

    for reading in readings:

        assert validate_sensor_data(reading) is True, (
            f"Generated {reading['category_id']} reading "
            "failed validation."
        )
