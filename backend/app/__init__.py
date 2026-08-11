from flask import Flask
from flask_cors import CORS

from .config import Config
from .routes import api
from .crypto import warmup_crypto
from .security import init_security


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, resources={r"/api/*": {"origins": Config.CORS_ORIGINS}})

    # Rate limiting + security headers + request-size guard.
    # Must run before the blueprint is registered isn't required by
    # Flask, but keep it early for readability.
    init_security(app)

    app.register_blueprint(api, url_prefix="/api")

    warmup_crypto()

    return app
