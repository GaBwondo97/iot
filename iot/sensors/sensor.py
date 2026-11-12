
import uuid
from datetime import datetime, timezone


class Sensor:
    """
    Represents a simulated CityPulse monitoring sensor.

    Each reading includes metadata required for MQTT publishing
    and downstream Data Engineering processing.
    """

    def __init__(
        self,
        category_id,
        category_name,
        location,
        city_id="CITYPULSE_DEMO"
    ):
        self.category_id = category_id.upper()
        self.category_name = category_name
        self.location = location
        self.city_id = city_id

    def create_reading(self, measurements):
        """
        Generate a standardized simulated sensor reading.
        """

        if not isinstance(measurements, dict):
            raise TypeError("Measurements must be provided as a dictionary.")

        return {
            "record_id": str(uuid.uuid4()),
            "city_id": self.city_id,
            "category_id": self.category_id,
            "category_name": self.category_name,
            "location": self.location,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat().replace("+00:00", "Z"),
            "source_type": "simulation",
            "measurements": measurements
        }
