import json
import os
import random
import sys
import time
from typing import Any, Dict

import pika

EXCHANGE = "rapido-dispatch"
CITY_OPTIONS = ["bangalore", "chennai"]
ZONE_OPTIONS = {
    "bangalore": ["koramangala", "indiranagar", "whitefield"],
    "chennai": ["tnagar", "whitefield"],
}
TYPE_OPTIONS = ["ride", "food"]


def build_payload(counter: int) -> Dict[str, Any]:
    city = random.choice(CITY_OPTIONS)
    zone = random.choice(ZONE_OPTIONS[city])
    msg_type = random.choice(TYPE_OPTIONS)
    payload = {
        "id": f"ORD-{counter:04d}",
        "city": city,
        "zone": zone,
        "type": msg_type,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    return payload


def main() -> None:
    url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    print(f"Connecting to {url}")
    params = pika.URLParameters(url)
    try:
        connection = pika.BlockingConnection(params)
    except Exception as exc:
        print(f"Dispatcher failed to connect: {exc}", file=sys.stderr)
        raise SystemExit(1)

    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    counter = 0
    try:
        while True:
            counter += 1
            payload = build_payload(counter)
            if counter % 10 == 0:
                payload.pop("zone", None)
                print(f"Publishing invalid message #{counter}: {json.dumps(payload)}")
            else:
                print(f"Publishing valid message #{counter}: {json.dumps(payload)}")
            routing_key = f"{payload.get('city', 'unknown')}.{payload.get('zone', 'unknown')}.{payload.get('type', 'unknown')}"
            channel.basic_publish(
                exchange=EXCHANGE,
                routing_key=routing_key,
                body=json.dumps(payload),
            )
            time.sleep(2)
    except KeyboardInterrupt:
        print("Stopping dispatcher.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
