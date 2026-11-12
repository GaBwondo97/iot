
import random
import time

from mqtt.publisher import MqttPublisher
from sensors.sensor import Sensor


# ==========================================================
# CITYPULSE SIMULATOR CONFIGURATION
# ==========================================================

CITY_ID = "CITYPULSE_DEMO"
CITY_NAME = "Kuala Lumpur"

# Proposed simulation interval.
# Requires team approval before final integration.
PUBLISH_INTERVAL = 5


# ==========================================================
# SENSOR INITIALIZATION
# ==========================================================

weather = Sensor(
    "WEATHER",
    "Weather Monitoring",
    CITY_NAME,
    CITY_ID
)

air_quality = Sensor(
    "AIR",
    "Air Quality Monitoring",
    CITY_NAME,
    CITY_ID
)

traffic = Sensor(
    "TRAFFIC",
    "Traffic Monitoring",
    CITY_NAME,
    CITY_ID
)

population = Sensor(
    "POPULATION",
    "Population Monitoring",
    CITY_NAME,
    CITY_ID
)


# ==========================================================
# WEATHER DATA GENERATOR
# ==========================================================

def generate_weather_data():

    measurements = {
        "temperature": round(random.uniform(24, 35), 2),
        "humidity": round(random.uniform(50, 90), 2),
        "wind_speed": round(random.uniform(0, 25), 2),
        "rainfall": round(random.uniform(0, 15), 2)
    }

    return weather.create_reading(measurements)


# ==========================================================
# AIR QUALITY DATA GENERATOR
# ==========================================================

def generate_air_quality_data():

    measurements = {
        "pm2_5": round(random.uniform(5, 100), 2),
        "pm10": round(random.uniform(10, 150), 2),
        "co2": round(random.uniform(400, 1500), 2),
        "aqi": random.randint(0, 150)
    }

    return air_quality.create_reading(measurements)


# ==========================================================
# TRAFFIC DATA GENERATOR
# ==========================================================

def generate_traffic_data():

    measurements = {
        "vehicle_count": random.randint(10, 200),
        "average_speed": round(random.uniform(10, 100), 2),
        "traffic_density": round(random.uniform(5, 100), 2),
        "congestion_category": random.choice([
            "Low",
            "Medium",
            "High"
        ])
    }

    return traffic.create_reading(measurements)


# ==========================================================
# POPULATION DATA GENERATOR
# ==========================================================

def generate_population_data():

    measurements = {
        "estimated_population": random.randint(100, 2000),
        "population_density": round(
            random.uniform(100, 10000), 2
        ),
        "crowd_density_category": random.choice([
            "Low",
            "Medium",
            "High"
        ]),
        "population_change": random.randint(-100, 100)
    }

    return population.create_reading(measurements)


# ==========================================================
# GENERATE ALL MONITORING DATA
# ==========================================================

def generate_all_data():

    return [
        generate_weather_data(),
        generate_air_quality_data(),
        generate_traffic_data(),
        generate_population_data()
    ]


# ==========================================================
# MAIN SIMULATOR
# ==========================================================

def main():

    publisher = MqttPublisher()
    connected = False

    try:

        print("========================================")
        print("       CITYPULSE AI IOT SIMULATOR")
        print("========================================")
        print(f"City: {CITY_NAME}")
        print(f"City ID: {CITY_ID}")
        print(f"Publish interval: {PUBLISH_INTERVAL} seconds")
        print("----------------------------------------")

        # Connect to MQTT broker once.
        publisher.connect()
        connected = True

        print("CityPulse simulator started!")

        while True:

            readings = generate_all_data()

            print("\nGenerating monitoring data...")

            for reading in readings:

                print("\nGenerated reading:")
                print(reading)

                publisher.publish_sensor_data(reading)

            print("\nAll monitoring data sent successfully!")

            time.sleep(PUBLISH_INTERVAL)

    except KeyboardInterrupt:

        print("\nSimulator stopped by user.")

    except Exception as error:

        print(f"\nSimulator error: {error}")

    finally:

        if connected:
            publisher.disconnect()

        print("CityPulse simulator shutdown complete.")


# ==========================================================
# APPLICATION ENTRY POINT
# ==========================================================

if __name__ == "__main__":
    main()
