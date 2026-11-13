import json
from unittest.mock import Mock

from stream import dispatcher
from stream import driver


def test_regular_payload_has_required_fields():
    payload = dispatcher.build_payload(7)
    assert set(["id", "city", "zone", "type", "ts"]).issubset(payload.keys())
    assert payload["city"] in {"bangalore", "chennai"}
    assert payload["zone"] in {
        "koramangala",
        "indiranagar",
        "whitefield",
        "tnagar",
    }
    assert payload["type"] in {"ride", "food"}


def test_every_tenth_payload_is_malformed_and_reaches_control_binding():
    payload = dispatcher.build_payload(10)
    assert "zone" not in payload
    assert payload["city"] == "bangalore"
    assert dispatcher.build_routing_key(payload).startswith("bangalore.")


def test_build_routing_key_uses_city_zone_type_format():
    payload = {"city": "bangalore", "zone": "koramangala", "type": "food"}
    assert dispatcher.build_routing_key(payload) == "bangalore.koramangala.food"


def test_sanitize_url_removes_userinfo_and_query():
    url = "amqps://user:secret@example.com:5671/vhost?token=hidden"
    expected = "amqps://example.com:5671"
    assert dispatcher.sanitize_url(url) == expected
    assert driver.sanitize_url(url) == expected


def test_process_message_rejects_missing_zone():
    ch = Mock()
    method = Mock(delivery_tag=42, routing_key="bangalore.koramangala.food")
    payload = {"id": "ORD-0001", "city": "bangalore", "type": "food", "ts": "2026-08-02T00:00:00Z"}
    result = driver.process_message(ch, method, payload, "Ravi")
    assert result is False
    ch.basic_nack.assert_called_once_with(delivery_tag=42, requeue=False)


def test_handle_delivery_rejects_malformed_json():
    ch = Mock()
    method = Mock(delivery_tag=43, routing_key="bangalore.koramangala.food")
    result = driver.handle_delivery(ch, method, b"{not-json", "Ravi")
    assert result is False
    ch.basic_nack.assert_called_once_with(delivery_tag=43, requeue=False)


def test_handle_delivery_rejects_non_object_json():
    ch = Mock()
    method = Mock(delivery_tag=44, routing_key="bangalore.koramangala.food")
    result = driver.handle_delivery(ch, method, b"[]", "Ravi")
    assert result is False
    ch.basic_nack.assert_called_once_with(delivery_tag=44, requeue=False)


def test_handle_delivery_acknowledges_valid_message():
    ch = Mock()
    method = Mock(delivery_tag=88, routing_key="bangalore.indiranagar.ride")
    payload = {
        "id": "ORD-0002",
        "city": "bangalore",
        "zone": "indiranagar",
        "type": "ride",
        "ts": "2026-08-02T00:00:00Z",
    }
    result = driver.handle_delivery(
        ch,
        method,
        json.dumps(payload).encode("utf-8"),
        "Priya",
    )
    assert result is True
    ch.basic_ack.assert_called_once_with(delivery_tag=88)