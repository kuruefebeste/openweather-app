from flask import Flask
from dotenv import load_dotenv

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-secret-key"

    from .views import main_blueprint
    app.register_blueprint(main_blueprint)

    return app
