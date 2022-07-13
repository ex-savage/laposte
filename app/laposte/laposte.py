from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import List

from apiclient import APIClient, HeaderAuthentication, JsonResponseHandler
from apiclient.exceptions import APIRequestError
from apiclient.request_formatters import NoOpRequestFormatter

from app import config
from app.laposte.exceptions import (
    CorruptedData,
    InvalidTrackingNumber,
    LaposteError,
    UnauthorizedError,
)


@contextmanager
def handle_laposte_errors():
    try:
        yield
    except APIRequestError as exc:
        if exc.status_code == 400:
            raise InvalidTrackingNumber()
        if exc.status_code == 401:
            raise UnauthorizedError()
        else:
            raise LaposteError()


@dataclass
class LaposteEvent:
    status: str
    code: str
    date: datetime

    @classmethod
    def from_dict(cls, event):
        return cls(
            status=event["label"],
            code=event["code"],
            date=datetime.strptime(event["date"], "%Y-%m-%dT%H:%M:%S%z"),
        )


@dataclass
class LaposteShipment:
    shipment_id: str
    delivered: bool
    timeline: List[LaposteEvent]


class LaposteRequestFormatter(NoOpRequestFormatter):
    @classmethod
    def get_headers(cls):
        return {"Accept": "application/json"}


class LaposteClient(APIClient):
    URL = "https://api.laposte.fr/suivi/v2/idships/"

    def base_get(self, param):
        return self.get(f"{self.URL}{param}", params={"lang": "en_GB"})

    def get_shipment_data(self, shipment_id: str):
        return self.base_get(shipment_id)

    def get_shipments_data(self, shipment_ids: List[str]):
        return self.base_get(",".join(shipment_ids))

    @staticmethod
    def parse_shipment(data):
        try:
            return LaposteShipment(
                shipment_id=data["shipment"]["idShip"],
                delivered=data["shipment"]["isFinal"],
                timeline=[LaposteEvent.from_dict(item) for item in data["shipment"]["event"]],
            )
        except (KeyError, TypeError):
            raise CorruptedData(data)

    @classmethod
    def get_shipment(cls, shipment_id):
        with handle_laposte_errors():
            data = client.get_shipment_data(shipment_id)
        return cls.parse_shipment(data)

    @classmethod
    def get_shipments(cls, shipment_ids: List[str]):
        if len(shipment_ids) == 1:
            return [cls.get_shipment(shipment_ids[0])]
        shipments = []
        with handle_laposte_errors():
            data = client.get_shipments_data(shipment_ids)
        for item in data:
            shipments.append(cls.parse_shipment(item))
        return shipments


client = LaposteClient(
    authentication_method=HeaderAuthentication(token=config.LAPOSTE_KEY, parameter="X-Okapi-Key", scheme=None),
    request_formatter=LaposteRequestFormatter,
    response_handler=JsonResponseHandler,
)
