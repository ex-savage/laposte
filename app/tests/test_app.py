from uuid import UUID

import pytest

from app.laposte.laposte import client
from app.models.shipment import Shipment, ShipmentEvent


def test_get_ping(web):
    response = web.get("/ping")
    assert response.status_code == 200
    assert response.get_data(as_text=True) == "pong"


@pytest.mark.vcr
def test_get_shipment_status_invalid_number(web, db):
    response = web.get("/shipments/1")
    assert response.status_code == 200
    assert response.get_data(as_text=True) == "Error: Invalid tracking number"
    db.session.rollback()  # to check that shipments with invalid tracking numbers not committed
    assert not Shipment.query.count()


@pytest.mark.vcr
def test_get_shipment_status_delivered(web, db):
    assert not Shipment.query.count()
    response = web.get("/shipments/6A21757464334")
    assert response.status_code == 200
    assert response.get_data(as_text=True) == "Your parcel has been delivered in your letter box."
    shipment = Shipment.query.one_or_none()
    assert shipment.status == "Your parcel has been delivered in your letter box."
    assert shipment.delivered
    ShipmentEvent.query.delete()
    db.session.commit()
    assert Shipment.query.filter(Shipment.tracking_number == "6A21757464334").one_or_none().status == "Unknown"


@pytest.mark.vcr
def test_update_shipments_status_basic_logic(web, db):
    web.get("/shipments/6A21757464334")
    web.get("/shipments/6A22658410765")
    assert Shipment.query.count() == 2
    batch = []
    for shipment in Shipment.query.all():
        assert shipment.delivered
        shipment.delivered = False
        batch.append(shipment.tracking_number)
    ShipmentEvent.query.delete()
    db.session.commit()
    for shipment in Shipment.query:
        assert shipment.status == "Unknown"
    data = client.get_shipments(batch)
    Shipment.update_multiple_rows(data)
    for shipment in Shipment.query:
        assert shipment.delivered
    assert ShipmentEvent.query.count()


@pytest.mark.vcr
def test_update_shipments_task(web, db):
    # we need some data in db to run batch update
    web.get("/shipments/6A21757464334")
    web.get("/shipments/6A22658410765")
    assert Shipment.query.count() == 2
    ShipmentEvent.query.delete()
    db.session.commit()
    for shipment in Shipment.query:
        assert shipment.status == "Unknown"
    response = web.get("/shipments/")
    assert UUID(response.get_data(as_text=True), version=4)  # check that we get back task_id
    assert response.status_code == 200
    # check that our task updated data in db
    for shipment in Shipment.query:
        assert shipment.delivered
