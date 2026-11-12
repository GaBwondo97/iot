
from datetime import datetime, timezone

import pytest

from sensors.sensor import Sensor


CITY_ID = "CITYPULSE_DEMO"
LOCATION = "Kuala Lumpur"


def create_sensor(category_id, category_name):
    return Sensor(
        category_id,
        category_name,
        LOCATION,
        CITY_ID
    )


def test_weather_sensor():

    sensor = create_sensor(
        "WEATHER",
        "Weather Monitoring"
    )

    reading = sensor.create_reading({
        "temperature": 30.5,
        "humidity": 75,
        "wind_speed": 12,
        "rainfall": 2.5
    })

    assert reading["category_id"] == "WEATHER"
    assert reading["category_name"] == "Weather Monitoring"
    assert reading["location"] == LOCATION
    assert reading["city_id"] == CITY_ID
    assert reading["source_type"] == "simulation"

    assert reading["measurements"]["temperature"] == 30.5
    assert reading["measurements"]["humidity"] == 75
    assert reading["measurements"]["wind_speed"] == 12
    assert reading["measurements"]["rainfall"] == 2.5


def test_air_quality_sensor():

    sensor = create_sensor(
        "AIR",
        "Air Quality Monitoring"
    )

    reading = sensor.create_reading({
        "pm2_5": 25,
        "pm10": 40,
        "co2": 650,
        "aqi": 55
    })

    assert reading["category_id"] == "AIR"
    assert reading["measurements"]["pm2_5"] == 25
    assert reading["measurements"]["pm10"] == 40
    assert reading["measurements"]["co2"] == 650
    assert reading["measurements"]["aqi"] == 55


def test_traffic_sensor():

    sensor = create_sensor(
        "TRAFFIC",
        "Traffic Monitoring"
    )

    reading = sensor.create_reading({
        "vehicle_count": 120,
        "average_speed": 45,
        "traffic_density": 60,
        "congestion_category": "Medium"
    })

    assert reading["category_id"] == "TRAFFIC"
    assert reading["measurements"]["vehicle_count"] == 120
    assert reading["measurements"]["average_speed"] == 45
    assert reading["measurements"]["traffic_density"] == 60
    assert reading["measurements"]["congestion_category"] == "Medium"


def test_population_sensor():

    sensor = create_sensor(
        "POPULATION",
        "Population Monitoring"
    )

    reading = sensor.create_reading({
        "estimated_population": 850,
        "population_density": 2500,
        "crowd_density_category": "High",
        "population_change": -15
    })

    assert reading["category_id"] == "POPULATION"
    assert reading["measurements"]["estimated_population"] == 850
    assert reading["measurements"]["population_density"] == 2500
    assert reading["measurements"]["crowd_density_category"] == "High"
    assert reading["measurements"]["population_change"] == -15


def test_reading_contains_required_metadata():

    sensor = create_sensor(
        "WEATHER",
        "Weather Monitoring"
    )

    reading = sensor.create_reading({
        "temperature": 30,
        "humidity": 75,
        "wind_speed": 10,
        "rainfall": 0
    })

    assert reading["record_id"]
    assert reading["city_id"] == CITY_ID
    assert reading["source_type"] == "simulation"
    assert reading["category_id"] == "WEATHER"

    assert "timestamp" in reading


def test_record_ids_are_unique():

    sensor = create_sensor(
        "WEATHER",
        "Weather Monitoring"
    )

    measurements = {
        "temperature": 30,
        "humidity": 75,
        "wind_speed": 10,
        "rainfall": 0
    }

    reading_one = sensor.create_reading(measurements)
    reading_two = sensor.create_reading(measurements)

    assert reading_one["record_id"] != reading_two["record_id"]


def test_timestamp_is_utc():

    sensor = create_sensor(
        "WEATHER",
        "Weather Monitoring"
    )

    reading = sensor.create_reading({
        "temperature": 30,
        "humidity": 75,
        "wind_speed": 10,
        "rainfall": 0
    })

    timestamp = datetime.fromisoformat(
        reading["timestamp"].replace("Z", "+00:00")
    )

    assert timestamp.tzinfo is not None
    assert timestamp.utcoffset() == timezone.utc.utcoffset(timestamp)


def test_invalid_measurements_type():

    sensor = create_sensor(
        "WEATHER",
        "Weather Monitoring"
    )

    with pytest.raises(TypeError):
        sensor.create_reading("invalid measurements")


def test_sensor_category_is_uppercase():

    sensor = Sensor(
        "weather",
        "Weather Monitoring",
        LOCATION,
        CITY_ID
    )

    assert sensor.category_id == "WEATHER"
