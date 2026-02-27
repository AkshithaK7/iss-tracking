import time
import json
import requests
from confluent_kafka import Producer

KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "iss_location"
ISS_API_URL = "https://api.wheretheiss.at/v1/satellites/25544"
POLL_INTERVAL = 6  # seconds


def delivery_callback(err, msg):
    if err:
        print(f"[ERROR] Message delivery failed: {err}")
    else:
        print(f"[OK] Delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")


def fetch_iss_location():
    response = requests.get(ISS_API_URL, timeout=10)
    response.raise_for_status()
    data = response.json()
    return {
        "timestamp": int(data["timestamp"]),
        "latitude": float(data["latitude"]),
        "longitude": float(data["longitude"]),
        "altitude_km": float(data["altitude"]),
        "velocity_kmh": float(data["velocity"])
    }


def main():
    producer = Producer({"bootstrap.servers": KAFKA_BROKER})
    print(f"Starting ISS producer. Publishing to topic '{KAFKA_TOPIC}' every {POLL_INTERVAL}s...")

    try:
        while True:
            try:
                payload = fetch_iss_location()
            except Exception as e:
                print(f"[WARN] API error: {e}. Retrying in {POLL_INTERVAL}s...")
                time.sleep(POLL_INTERVAL)
                continue
            message = json.dumps(payload)
            producer.produce(KAFKA_TOPIC, value=message, callback=delivery_callback)
            producer.poll(0)
            print(f"[SENT] {message}")
            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopping producer...")
    finally:
        producer.flush()
        print("Producer shut down cleanly.")


if __name__ == "__main__":
    main()
