
import json
import threading
import uuid

import paho.mqtt.client as mqtt


def test_mqtt_receives_all_categories():

    broker = "localhost"
    port = 1883
    keepalive = 60

    test_id = str(uuid.uuid4())

    categories = [
        "weather",
        "air_quality",
        "traffic",
        "population"
    ]

    topics = [
        f"citypulse/integration_test/{test_id}/{category}"
        for category in categories
    ]

    received_messages = {}

    subscribed_event = threading.Event()
    received_event = threading.Event()
    connected_event = threading.Event()

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2
    )

    # ======================================================
    # MQTT CALLBACKS
    # ======================================================

    def on_connect(client, userdata, flags, reason_code, properties):

        if reason_code == 0:
            connected_event.set()

            # Paho requires a list of (topic, QoS) tuples.
            subscriptions = [
                (topic, 0)
                for topic in topics
            ]

            client.subscribe(subscriptions)

    def on_subscribe(
        client,
        userdata,
        mid,
        reason_code_list,
        properties
    ):

        # Confirm that the broker accepted every subscription.
        if all(reason_code < 128 for reason_code in reason_code_list):
            subscribed_event.set()

    def on_message(client, userdata, message):

        try:
            payload = json.loads(
                message.payload.decode("utf-8")
            )

            received_messages[message.topic] = payload

            if len(received_messages) == len(topics):
                received_event.set()

        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_message = on_message

    # ======================================================
    # CONNECT TO MQTT BROKER
    # ======================================================

    try:

        client.connect(
            broker,
            port,
            keepalive
        )

        client.loop_start()

        assert connected_event.wait(timeout=10), (
            "MQTT client could not connect to the broker."
        )

        # Wait for subscription acknowledgement.
        assert subscribed_event.wait(timeout=10), (
            "MQTT subscription was not acknowledged."
        )

        # ==================================================
        # PUBLISH ONE MESSAGE FOR EACH CATEGORY
        # ==================================================

        for category, topic in zip(categories, topics):

            payload = {
                "record_id": str(uuid.uuid4()),
                "category_id": category.upper(),
                "source_type": "simulation",
                "test": True
            }

            result = client.publish(
                topic,
                json.dumps(payload),
                qos=0
            )

            assert result.rc == mqtt.MQTT_ERR_SUCCESS, (
                f"Failed to publish message to {topic}"
            )

        # ==================================================
        # VERIFY RECEIVED MESSAGES
        # ==================================================

        assert received_event.wait(timeout=10), (
            "Not all monitoring category messages were received."
        )

        assert set(received_messages.keys()) == set(topics)

        for category, topic in zip(categories, topics):

            assert received_messages[topic]["category_id"] == (
                category.upper()
            )

            assert received_messages[topic]["source_type"] == (
                "simulation"
            )

    finally:

        client.disconnect()
        client.loop_stop()
