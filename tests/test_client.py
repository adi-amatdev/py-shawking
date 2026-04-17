import json
import os
from datetime import datetime, timezone
from urllib import error

import pytest

from shawking import ShawkingClient, ShawkingClientError

CONNECTION_REFUSED = "connection refused"


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_parse_uses_defaults_and_allows_overrides(monkeypatch):
    captured = {}

    def fake_urlopen(http_request, timeout):
        captured["url"] = http_request.full_url
        captured["timeout"] = timeout
        captured["headers"] = dict(http_request.header_items())
        captured["body"] = json.loads(http_request.data.decode("utf-8"))
        return DummyResponse({"dates": []})

    monkeypatch.setattr("shawking.client.request.urlopen", fake_urlopen)

    client = ShawkingClient(ip="192.168.1.50", port=9090).config(
        time_zone="Asia/Kolkata",
        reference_time=1748736000000,
        lang="eng",
    )
    response = client.parse(
        "Call me tomorrow at 9 AM",
        time_zone="UTC",
        maxParseDate=3,
    )

    assert response == {"dates": []}
    assert captured["url"] == "http://192.168.1.50:9090/parse"
    assert captured["timeout"] == 30.0
    assert captured["headers"]["Content-type"] == "application/json"
    assert captured["body"] == {
        "text": "Call me tomorrow at 9 AM",
        "timeZone": "UTC",
        "referenceTime": 1748736000000,
        "lang": "eng",
        "maxParseDate": 3,
    }


def test_parse_accepts_datetime_reference_time(monkeypatch):
    captured = {}

    def fake_urlopen(http_request, timeout):
        del timeout
        captured["body"] = json.loads(http_request.data.decode("utf-8"))
        return DummyResponse([{"text": "15 Jan 2026"}])

    monkeypatch.setattr("shawking.client.request.urlopen", fake_urlopen)

    client = ShawkingClient()
    reference_time = datetime(2026, 1, 15, 12, 30, tzinfo=timezone.utc)
    client.parse("Book a flight on 15 Jan 2026", reference_time=reference_time)

    assert captured["body"]["referenceTime"] == 1768480200000


def test_parse_can_remove_configured_defaults_for_a_single_call(monkeypatch):
    captured = {}

    def fake_urlopen(http_request, timeout):
        del timeout
        captured["body"] = json.loads(http_request.data.decode("utf-8"))
        return DummyResponse({"dates": []})

    monkeypatch.setattr("shawking.client.request.urlopen", fake_urlopen)

    client = ShawkingClient().config(time_zone="Asia/Kolkata", lang="eng")
    client.parse("next week", time_zone=None, lang=None)

    assert captured["body"] == {"text": "next week"}


def test_parse_rejects_empty_text():
    client = ShawkingClient()

    with pytest.raises(ValueError, match="non-empty string"):
        client.parse("   ")


def test_parse_raises_client_error_when_service_is_unreachable(monkeypatch):
    def fake_urlopen(http_request, timeout):
        del http_request, timeout
        raise error.URLError(CONNECTION_REFUSED)

    monkeypatch.setattr("shawking.client.request.urlopen", fake_urlopen)

    with pytest.raises(ShawkingClientError, match="Could not reach Shawking service"):
        ShawkingClient().parse("tomorrow")


@pytest.mark.integration
def test_parse_against_running_shawking_server():
    if os.getenv("SHAWKING_RUN_INTEGRATION") != "1":
        pytest.skip("Set SHAWKING_RUN_INTEGRATION=1 to run integration tests.")

    host = os.getenv("SHAWKING_HOST", "localhost")
    port = int(os.getenv("SHAWKING_PORT", "8080"))
    scheme = os.getenv("SHAWKING_SCHEME", "http")

    client = ShawkingClient(ip=host, port=port, scheme=scheme, timeout=10.0)
    response = client.parse(
        "Book a flight on 15 Jan 2026",
        time_zone="Asia/Kolkata",
        reference_time=1748736000000,
    )

    assert isinstance(response, (dict, list))
    assert response
