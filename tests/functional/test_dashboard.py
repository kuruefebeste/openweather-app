from flask import Flask
import website.views as views


def create_test_app(monkeypatch):
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(views.main_blueprint)

    # Avoid TemplateNotFound in tests (we're testing route behavior, not Jinja)
    def fake_render_template(_name, **ctx):
        # return something that includes the message so we can assert on it
        msg = ctx.get("error_message") or ""
        return f"OK|{msg}"

    monkeypatch.setattr(views, "render_template", fake_render_template)
    return app


def test_dashboard_get_status_code(monkeypatch):
    monkeypatch.setattr(views.os, "getenv", lambda _k: None)

    app = create_test_app(monkeypatch)
    client = app.test_client()

    resp = client.get("/")
    assert resp.status_code == 200
    assert b"API key not configured." in resp.data


def test_dashboard_post_invalid_location(monkeypatch):
    monkeypatch.setattr(views.os, "getenv", lambda _k: "fake-key")

    app = create_test_app(monkeypatch)
    client = app.test_client()

    resp = client.post("/", data={"location": "Waterville,ME,"})
    assert resp.status_code == 200
    assert b"City and Country are required." in resp.data
