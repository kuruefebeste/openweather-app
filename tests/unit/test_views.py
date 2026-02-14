import requests
from flask import Flask


import website.views as views


class FakeResp:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text

    def json(self):
        return self._json_data


def _capture_template_context(monkeypatch):
    """
    Patch render_template to return the context dict directly,
    so we can assert on values without needing real templates.
    """
    def fake_render_template(_template_name, **context):
        return context

    monkeypatch.setattr(views, "render_template", fake_render_template)


def test_get_default_location_missing_api_key(monkeypatch):
    _capture_template_context(monkeypatch)

    monkeypatch.setattr(views.os, "getenv", lambda _k: None)

    app = Flask(__name__)
    app.register_blueprint(views.main_blueprint)

    with app.test_request_context("/", method="GET"):
        ctx = views.dashboard()

    assert ctx["error_message"] == "API key not configured."
    assert ctx["selected_location"] == "Waterville,ME,US"
    assert ctx["weather_data"] is None


def test_post_missing_country(monkeypatch):
    _capture_template_context(monkeypatch)

    monkeypatch.setattr(views.os, "getenv", lambda _k: "fake-key")

    app = Flask(__name__)
    app.register_blueprint(views.main_blueprint)

    with app.test_request_context(
        "/",
        method="POST",
        data={"location": "Waterville,ME,"},
    ):
        ctx = views.dashboard()

    assert ctx["error_message"] == "City and Country are required."
    assert ctx["weather_data"] is None


def test_weather_api_non_200(monkeypatch):
    _capture_template_context(monkeypatch)
    monkeypatch.setattr(views.os, "getenv", lambda _k: "fake-key")

    def fake_get(url, timeout=8):
        assert "data/2.5/weather" in url
        return FakeResp(status_code=404, text="nope")

    monkeypatch.setattr(views.requests, "get", fake_get)

    app = Flask(__name__)
    app.register_blueprint(views.main_blueprint)

    with app.test_request_context("/", method="GET"):
        ctx = views.dashboard()

    assert ctx["error_message"] == "Unable to fetch weather data."
    assert ctx["weather_data"] is None


def test_weather_network_exception(monkeypatch):
    _capture_template_context(monkeypatch)
    monkeypatch.setattr(views.os, "getenv", lambda _k: "fake-key")

    def fake_get(url, timeout=8):
        raise requests.RequestException("boom")

    monkeypatch.setattr(views.requests, "get", fake_get)

    app = Flask(__name__)
    app.register_blueprint(views.main_blueprint)

    with app.test_request_context("/", method="GET"):
        ctx = views.dashboard()

    assert ctx["error_message"] == "Network error. Please try again."
    assert ctx["weather_data"] is None


def test_success_dewpoint_from_onecall(monkeypatch):
    _capture_template_context(monkeypatch)
    monkeypatch.setattr(views.os, "getenv", lambda _k: "fake-key")

    weather_json = {
        "weather":
        [{"main": "Clouds", "description": "broken clouds", "icon": "03d"}],
        "main":
        {"temp": 10.4, "feels_like": 8.9, "humidity": 80, "pressure": 1000},
        "visibility": 9000,
        "wind": {"speed": 5.0},  # m/s => 18 km/h
        "dt": 1700000000,
        "timezone": 0,
        "coord": {"lat": 44.55, "lon": -69.63},
    }

    onecall_json = {"daily": [{"dew_point": 6.2}]}

    def fake_get(url, timeout=8):
        if "data/2.5/weather" in url:
            return FakeResp(200, weather_json)
        if "data/3.0/onecall" in url:
            return FakeResp(200, onecall_json)
        raise AssertionError("Unexpected URL")

    monkeypatch.setattr(views.requests, "get", fake_get)

    app = Flask(__name__)
    app.register_blueprint(views.main_blueprint)

    with app.test_request_context("/", method="GET"):
        ctx = views.dashboard()

    assert ctx["error_message"] is None
    assert ctx["current_icon_url"].endswith("03d@2x.png")
    assert ctx["current_desc"] == "Clouds"
    assert ctx["current_temp"] == "10°C"
    assert ctx["feels_like"] == "9°"
    assert ctx["humidity"] == "80%"
    assert ctx["pressure"] == "1000 mb"
    assert ctx["visibility"] == "9 km"
    assert ctx["wind_speed"] == "18 km/h"
    assert ctx["dew_point"] == "6°"
    assert ctx["current_summary"] == "It is broken clouds."


def test_success_dewpoint_fallback_when_onecall_fails(monkeypatch):
    _capture_template_context(monkeypatch)
    monkeypatch.setattr(views.os, "getenv", lambda _k: "fake-key")

    weather_json = {
        "weather":
        [{"main": "Rain", "description": "light rain", "icon": "10d"}],
        "main":
        {"temp": 20.0, "feels_like": 20.0, "humidity": 50, "pressure": 1012},
        "coord": {"lat": 1.0, "lon": 2.0},
    }

    def fake_get(url, timeout=8):
        if "data/2.5/weather" in url:
            return FakeResp(200, weather_json)
        if "data/3.0/onecall" in url:
            # simulate OneCall not accessible (e.g., 401)
            # -> should fallback formula
            return FakeResp(401, {}, text="unauthorized")
        raise AssertionError("Unexpected URL")

    monkeypatch.setattr(views.requests, "get", fake_get)

    app = Flask(__name__)
    app.register_blueprint(views.main_blueprint)

    with app.test_request_context("/", method="GET"):
        ctx = views.dashboard()

    assert ctx["error_message"] is None
    assert ctx["dew_point"] is not None
    assert ctx["dew_point"].endswith("°")
