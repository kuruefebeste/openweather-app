import importlib

import dotenv
from flask import Flask


def test_load_dotenv_called_on_import(monkeypatch):
    """
    website/__init__.py calls load_dotenv() at import time.
    We patch dotenv.load_dotenv, reload the package, and assert it was called.
    """
    calls = {"n": 0}

    def fake_load_dotenv(*args, **kwargs):
        calls["n"] += 1
        return True

    monkeypatch.setattr(dotenv, "load_dotenv", fake_load_dotenv)

    import website  # noqa: F401
    importlib.reload(website)

    assert calls["n"] >= 1


def test_create_app_sets_secret_key_and_registers_blueprint():
    from website import create_app

    app = create_app()

    assert isinstance(app, Flask)
    assert app.config["SECRET_KEY"] == "dev-secret-key"

    # Blueprint registration should create 
    # the "/" rule and endpoint "main.dashboard"
    rules = [r.rule for r in app.url_map.iter_rules()]
    endpoints = [r.endpoint for r in app.url_map.iter_rules()]

    assert "/" in rules
    assert "main.dashboard" in endpoints


def test_create_app_returns_new_app_each_time():
    from website import create_app

    app1 = create_app()
    app2 = create_app()

    assert app1 is not app2
