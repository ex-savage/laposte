from datetime import datetime
from unittest import mock

import pytest

from app.laposte import exceptions
from app.laposte.laposte import client


@pytest.mark.vcr
def test_laposte_client_ok():
    tracking_number = "6A21757464334"
    shipment = client.get_shipment(tracking_number)
    assert shipment.shipment_id == tracking_number
    assert shipment.delivered
    assert len(shipment.timeline) == 4
    assert shipment.timeline[0].status == "Your parcel has been delivered in your letter box."
    assert shipment.timeline[0].code == "DI1"
    assert shipment.timeline[0].date == datetime.strptime("2022-01-25T12:56:54+01:00", "%Y-%m-%dT%H:%M:%S%z")


@pytest.mark.vcr
def test_laposte_client_multiple_ok():
    tracking_numbers = ["6A21757464334", "6A22658410765"]
    shipments = client.get_shipments(tracking_numbers)
    assert len(shipments) == 2
    assert shipments[0].shipment_id in tracking_numbers
    assert shipments[0].shipment_id in tracking_numbers
    assert shipments[0].delivered
    assert shipments[1].delivered
    assert shipments[0].timeline
    assert shipments[1].timeline


@pytest.mark.vcr
def test_laposte_client_invalid_number():
    tracking_number = "WRONG"
    with pytest.raises(exceptions.InvalidTrackingNumber):
        client.get_shipment(tracking_number)


@pytest.mark.vcr
def test_laposte_client_wrong_api_key():
    with mock.patch.object(client._authentication_method, "_token", "WRONG_KEY"):
        with pytest.raises(exceptions.UnauthorizedError):
            client.get_shipment("1")


def test_laposte_client_corrupted_data():
    with mock.patch.object(client, "get_shipment_data", mock.Mock(return_value=[])):
        with pytest.raises(exceptions.CorruptedData):
            client.get_shipment("1")
