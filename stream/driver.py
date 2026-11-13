import json
import os
import sys
from typing import Any, Mapping
from urllib.parse import urlsplit, urlunsplit

import pika

EXCHANGE = "rapido-dispatch"


def sanitize_url(url: str) -> str:
    parts = urlsplit(url)
    netloc = parts.hostname or "unknown-host"
    if parts.port:
        netloc = f"{netloc}:{parts.port}"
    return urlunsplit((parts.scheme, netloc, "", "", ""))


def process_message(
    channel: Any,
    method: Any,
    payload: Mapping[str, Any],
    driver_name: str,
) -> bool:
    print(f"[{driver_name}] Received message on {method.routing_key}: {payload}")
    if "zone" not in payload:
        print(f"[{driver_name}] Invalid message: missing zone; NACK without requeue")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return False
    channel.basic_ack(delivery_tag=method.delivery_tag)
    return True


def handle_delivery(channel: Any, method: Any, body: bytes, driver_name: str) -> bool:
    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"[{driver_name}] Invalid JSON message ({type(exc).__name__}); NACK without requeue")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return False

    if not isinstance(payload, dict):
        print(f"[{driver_name}] Invalid message: expected a JSON object; NACK without requeue")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return False
    return process_message(channel, method, payload, driver_name)


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python driver.py NAME PATTERN", file=sys.stderr)
        raise SystemExit(1)

    driver_name, binding_pattern = sys.argv[1], sys.argv[2]
    url = os.getenv("RABBITMQ_URL", "amqp://localhost:5672/")
    print(f"[{driver_name}] connecting to {sanitize_url(url)}")
    try:
        connection = pika.BlockingConnection(pika.URLParameters(url))
    except Exception as exc:
        print(
            f"[{driver_name}] failed to connect ({type(exc).__name__}); "
            "check RABBITMQ_URL and broker availability",
            file=sys.stderr,
        )
        raise SystemExit(1)

    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)

    result = channel.queue_declare(queue="", exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange=EXCHANGE, queue=queue_name, routing_key=binding_pattern)

    def callback(ch, method, properties, body):
        handle_delivery(ch, method, body, driver_name)

    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    print(f"[{driver_name}] waiting for messages with pattern {binding_pattern}")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()


if __name__ == "__main__":
    main()