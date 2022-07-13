import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent.resolve()
ENV_FILE = ROOT_DIR / ".env"
if os.path.exists(ENV_FILE):
    load_dotenv(ENV_FILE)

LAPOSTE_KEY = os.getenv("LAPOSTE_KEY")


class Config:
    SQLALCHEMY_DATABASE_URI = "sqlite:///app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CELERY_BROKER_URL = "sqla+sqlite:///celery.db"
    CELERY_RESULT_URL = "db+sqlite:///celery.db"


class TestingConfig(Config):
    ENV_TYPE = "testing"
    SQLALCHEMY_DATABASE_URI = "sqlite:///tests/test.db"
    CELERY_ALWAYS_EAGER = True


class DevelopmentConfig(Config):
    ENV_TYPE = "development"


class ProductionConfig(Config):
    ENV_TYPE = "production"


config = {
    "testing": TestingConfig,
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
