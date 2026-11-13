import json
import os
import sys

import pika

EXCHANGE = "rapido-dispatch"


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python driver.py NAME PATTERN", file=sys.stderr)
        raise SystemExit(1)

    driver_name, binding_pattern = sys.argv[1], sys.argv[2]
    url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    connection = pika.BlockingConnection(pika.URLParameters(url))
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)

    result = channel.queue_declare(queue="", exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange=EXCHANGE, queue=queue_name, routing_key=binding_pattern)

    def callback(ch, method, properties, body):
        payload = json.loads(body)
        print(f"[{driver_name}] Received message on {method.routing_key}: {payload}")
        if "zone" not in payload:
            print(f"[{driver_name}] Invalid message: missing zone; NACK without requeue")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return
        ch.basic_ack(delivery_tag=method.delivery_tag)

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
