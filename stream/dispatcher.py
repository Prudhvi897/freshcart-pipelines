import json
import logging
import os
import random
import sys
import time
from typing import Any, Dict
from urllib.parse import urlsplit, urlunsplit

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
    if counter % 10 == 0:
        city = "bangalore"
    payload = {
        "id": f"ORD-{counter:04d}",
        "city": city,
        "zone": zone,
        "type": msg_type,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    if counter % 10 == 0:
        payload.pop("zone")
    return payload


def build_routing_key(payload: Dict[str, Any]) -> str:
    return f"{payload.get('city', 'unknown')}.{payload.get('zone', 'unknown')}.{payload.get('type', 'unknown')}"


def sanitize_url(url: str) -> str:
    parts = urlsplit(url)
    netloc = parts.hostname or "unknown-host"
    if parts.port:
        netloc = f"{netloc}:{parts.port}"
    return urlunsplit((parts.scheme, netloc, "", "", ""))


def main() -> None:
    url = os.getenv("RABBITMQ_URL", "amqp://localhost:5672/")
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.info("Connecting to %s", sanitize_url(url))
    params = pika.URLParameters(url)
    try:
        connection = pika.BlockingConnection(params)
    except Exception as exc:
        logging.error(
            "Dispatcher failed to connect (%s). Check RABBITMQ_URL and broker availability.",
            type(exc).__name__,
        )
        raise SystemExit(1)

    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    counter = 0
    try:
        while True:
            counter += 1
            payload = build_payload(counter)
            logging.info("Publishing message %s %s", counter, json.dumps(payload, separators=(",", ":")))
            routing_key = build_routing_key(payload)
            channel.basic_publish(
                exchange=EXCHANGE,
                routing_key=routing_key,
                body=json.dumps(payload),
                properties=pika.BasicProperties(content_type="application/json"),
            )
            time.sleep(2)
    except KeyboardInterrupt:
        logging.info("Stopping dispatcher.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()