import os
from pathlib import Path

from celery import Celery
from flask import Flask
from flask_cors import CORS

from app.config import config
from app.models import db


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config["CELERY_RESULT_URL"],
        broker=app.config["CELERY_BROKER_URL"],
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


app = Flask(__name__)
CORS(app, origins="*", supports_credentials=True)

config_name = os.getenv("FLASK_CONFIG") or "default"
app.config.from_object(config[config_name])

db.init_app(app)

celery = make_celery(app)


def init_db():
    from app.models.shipment import Shipment, ShipmentEvent  # noqa
    with app.app_context():
        db.create_all()
        db.session.commit()


ROOT_DIR = Path(__file__).parent.resolve()
DB_FILE = ROOT_DIR / 'app.db'
if not os.path.exists(DB_FILE):
    init_db()

from .views import *  # noqa
