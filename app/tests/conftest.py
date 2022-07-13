import os

import pytest
from flask.testing import FlaskClient
from sqlalchemy.orm import sessionmaker

Session = sessionmaker()


@pytest.fixture(scope="session")
def app():
    """Create test's application."""

    os.environ["FLASK_CONFIG"] = "testing"
    from app.main import app

    app.test_client_class = FlaskClient

    return app


@pytest.fixture(scope="session")
def db(app):
    from app.models import Base, db

    with app.test_request_context():
        connection = db.engine.connect()
        Base.metadata.create_all(connection)
        db.session.commit()
        yield db
        db.session.rollback()
        db.session.close_all()
        Base.metadata.drop_all(bind=db.engine)


@pytest.fixture
def web(app):
    from app.views import ping, get_shipment_status, update_shipments_statuses  # noqa

    return app.test_client()


# Use to rewrite cassettes stubs: pytest --record-mode=rewrite tests/
