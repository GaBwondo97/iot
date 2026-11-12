
import math
from datetime import datetime, timezone


REQUIRED_FIELDS = {
    "WEATHER": [
        "temperature",
        "humidity",
        "wind_speed",
        "rainfall"
    ],
    "AIR": [
        "pm2_5",
        "pm10",
        "co2",
        "aqi"
    ],
    "TRAFFIC": [
        "vehicle_count",
        "average_speed",
        "traffic_density",
        "congestion_category"
    ],
    "POPULATION": [
        "estimated_population",
        "population_density",
        "crowd_density_category",
        "population_change"
    ]
}

CATEGORICAL_FIELDS = {
    "TRAFFIC": {
        "congestion_category": ["low", "medium", "high"]
    },
    "POPULATION": {
        "crowd_density_category": ["low", "medium", "high"]
    }
}

NUMERIC_FIELDS = {
    category: [
        field for field in fields
        if field not in CATEGORICAL_FIELDS.get(category, {})
    ]
    for category, fields in REQUIRED_FIELDS.items()
}


def _is_valid_number(value):
    """Check that a value is a finite number, excluding booleans."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _is_valid_utc_timestamp(timestamp):
    """Check that the timestamp is a valid UTC ISO 8601 string."""
    if not isinstance(timestamp, str):
        return False

    try:
        parsed = datetime.fromisoformat(
            timestamp.replace("Z", "+00:00")
        )

        return (
            parsed.tzinfo is not None
            and parsed.utcoffset() == timezone.utc.utcoffset(parsed)
        )

    except (ValueError, TypeError):
        return False


def validate_sensor_data(data):
    """
    Perform basic IoT-side validation before MQTT publishing.

    Full canonical validation, normalization and deduplication
    remain the responsibility of the Data Engineering pipeline.
    """

    if not isinstance(data, dict):
        return False

    # Validate category
    category = data.get("category_id")

    if not isinstance(category, str):
        return False

    category = category.upper()

    if category not in REQUIRED_FIELDS:
        return False

    # Validate required metadata
    if not isinstance(data.get("record_id"), str):
        return False

    if not data["record_id"].strip():
        return False

    if not isinstance(data.get("city_id"), str):
        return False

    if not data["city_id"].strip():
        return False

    if not _is_valid_utc_timestamp(data.get("timestamp")):
        return False

    # This IoT simulator must identify its data as simulated.
    if data.get("source_type") != "simulation":
        return False

    # Validate measurements
    measurements = data.get("measurements")

    if not isinstance(measurements, dict):
        return False

    # Check all required fields
    for field in REQUIRED_FIELDS[category]:
        if field not in measurements:
            return False

    # Check numeric measurements
    for field in NUMERIC_FIELDS[category]:
        value = measurements[field]

        if not _is_valid_number(value):
            return False

        # Population change may be negative or positive.
        if category == "POPULATION" and field == "population_change":
            continue

        if value < 0:
            return False

    # Check categorical measurements
    for field, allowed_values in CATEGORICAL_FIELDS.get(
        category, {}
    ).items():

        value = measurements[field]

        if not isinstance(value, str):
            return False

        if value.lower() not in allowed_values:
            return False

    # Weather-specific checks
    if category == "WEATHER":

        if not -90 <= measurements["temperature"] <= 60:
            return False

        if not 0 <= measurements["humidity"] <= 100:
            return False

    # Traffic-specific checks
    elif category == "TRAFFIC":

        if measurements["average_speed"] > 300:
            return False

    return True
