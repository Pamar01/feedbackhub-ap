"""FeedbackHub application factory."""
import os

from flask import Flask

from . import db
from .routes import bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=os.environ.get("FEEDBACKHUB_DB", os.path.join(app.instance_path, "feedbackhub.sqlite")),
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(os.path.dirname(app.config["DATABASE"]) or ".", exist_ok=True)

    db.init_app(app)
    app.register_blueprint(bp)

    with app.app_context():
        db.init_db()

    return app
