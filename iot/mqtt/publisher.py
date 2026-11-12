
import json
import time

from paho.mqtt import client as mqtt_client

from config.config import get_mqtt_config
from sensors.validator import validate_sensor_data


class MqttPublisher:
    """
    Handles MQTT connections and publishes validated
    CityPulse simulated sensor readings.
    """

    CONNECTION_TIMEOUT = 10
    PUBLISH_TIMEOUT = 10

    CATEGORY_MAPPING = {
        "weather": "weather",
        "air": "air_quality",
        "air_quality": "air_quality",
        "traffic": "traffic",
        "population": "population"
    }

    def __init__(self):

        self.config = get_mqtt_config()

        self._validate_config()

        self.client = mqtt_client.Client(
            mqtt_client.CallbackAPIVersion.VERSION2,
            client_id=self.config["client_id"]
        )

        self.client.reconnect_delay_set(
            min_delay=1,
            max_delay=30
        )

        # Provisional QoS default.
        # Final QoS requires team approval.
        self.qos = self.config.get("qos", 0)

        if not isinstance(self.qos, int) or self.qos not in (0, 1, 2):
            raise ValueError("MQTT QoS must be 0, 1, or 2.")

    def _validate_config(self):
        """Check required MQTT configuration values."""

        required_fields = [
            "broker",
            "port",
            "keepalive",
            "client_id",
            "topics"
        ]

        for field in required_fields:

            if field not in self.config:
                raise ValueError(
                    f"Missing MQTT configuration: {field}"
                )

        if not isinstance(self.config["broker"], str) or not self.config["broker"].strip():
            raise ValueError("MQTT broker address is invalid.")

        if not isinstance(self.config["port"], int) or not 1 <= self.config["port"] <= 65535:
            raise ValueError("MQTT broker port is invalid.")

        if not isinstance(self.config["keepalive"], int) or self.config["keepalive"] <= 0:
            raise ValueError("MQTT keepalive value is invalid.")

        if not isinstance(self.config["client_id"], str) or not self.config["client_id"].strip():
            raise ValueError("MQTT client ID is invalid.")

        if not isinstance(self.config["topics"], dict):
            raise ValueError("MQTT topics configuration must be a dictionary.")

        for topic_key in (
            "weather",
            "air_quality",
            "traffic",
            "population"
        ):

            topic = self.config["topics"].get(topic_key)

            if not isinstance(topic, str) or not topic.strip():
                raise ValueError(
                    f"Missing or invalid MQTT topic: {topic_key}"
                )

    def connect(self):
        """Connect to the configured MQTT broker."""

        if self.client.is_connected():
            print("Already connected to MQTT broker.")
            return

        print("Connecting to MQTT broker...")

        try:

            self.client.connect(
                self.config["broker"],
                self.config["port"],
                self.config["keepalive"]
            )

            self.client.loop_start()

            timeout = time.monotonic() + self.CONNECTION_TIMEOUT

            while not self.client.is_connected():

                if time.monotonic() >= timeout:
                    raise TimeoutError(
                        "Could not connect to MQTT broker."
                    )

                time.sleep(0.1)

            print("Successfully connected to MQTT broker!")

        except Exception:

            self.client.loop_stop()
            raise

    def publish_sensor_data(self, data):
        """Validate and publish one sensor reading."""

        # STEP 1: Validate sensor data

        if not validate_sensor_data(data):

            raise ValueError(
                "Invalid sensor data. Publishing rejected."
            )

        # STEP 2: Check MQTT connection

        if not self.client.is_connected():

            raise ConnectionError(
                "Cannot publish sensor data: MQTT client is not connected."
            )

        # STEP 3: Identify monitoring category

        category = data["category_id"].lower()

        topic_key = self.CATEGORY_MAPPING.get(category)

        if topic_key is None:

            raise ValueError(
                f"Unknown monitoring category: {category}"
            )

        # STEP 4: Get configured MQTT topic

        topic = self.config["topics"].get(topic_key)

        if not topic:

            raise ValueError(
                f"MQTT topic not configured: {topic_key}"
            )

        # STEP 5: Convert sensor data into JSON

        try:

            payload = json.dumps(
                data,
                allow_nan=False
            )

        except (TypeError, ValueError) as error:

            raise ValueError(
                f"Could not convert sensor data into JSON: {error}"
            ) from error

        # STEP 6: Publish sensor data

        try:

            result = self.client.publish(
                topic,
                payload,
                qos=self.qos
            )

            if result.rc != mqtt_client.MQTT_ERR_SUCCESS:

                raise RuntimeError(
                    f"Failed to publish sensor data to {topic}. "
                    f"MQTT error code: {result.rc}"
                )

            result.wait_for_publish(
                timeout=self.PUBLISH_TIMEOUT
            )

            if not result.is_published():

                raise TimeoutError(
                    f"Publishing timed out: {topic}"
                )

        except (RuntimeError, TimeoutError):
            raise

        except Exception as error:

            raise RuntimeError(
                f"MQTT publishing error on {topic}: {error}"
            ) from error

        print(f"Published successfully: {topic}")

    def disconnect(self):
        """Disconnect from the MQTT broker safely."""

        print("Disconnecting from MQTT broker...")

        try:

            if self.client.is_connected():
                self.client.disconnect()

        finally:

            self.client.loop_stop()

        print("MQTT connection closed.")
