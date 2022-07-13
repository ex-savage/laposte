from dataclasses import dataclass
from typing import Dict, List

from sqlalchemy.ext.hybrid import hybrid_property

from app.laposte.laposte import LaposteEvent, LaposteShipment
from app.models import Base, db
from app.models.tools import insert


@dataclass
class ShipmentItem:
    sid: int
    tracking_number: str


class ShipmentEvent(Base):
    __tablename__ = "shipment_delivery_history"

    shipment_event_id = db.Column(db.Integer, primary_key=True)
    shipment_id = db.Column(db.ForeignKey("shipment.shipment_id", ondelete="CASCADE"), index=True)
    status = db.Column(db.String(256))
    code = db.Column(db.String(3))
    date = db.Column(db.DateTime(timezone=True), index=True)

    @classmethod
    def prepare_events_to_insert_by_shipment(cls, shipment_id: int, shipment: LaposteShipment):
        values = []
        event: LaposteEvent
        for event in shipment.timeline:
            values.append(
                {
                    "shipment_id": shipment_id,
                    "status": event.status,
                    "code": event.code,
                    "date": event.date,
                }
            )
        return values

    @classmethod
    def prepare_events_to_insert(cls, shipment: LaposteShipment):
        values = []
        event: LaposteEvent
        for event in shipment.timeline:
            values.append({"status": event.status, "code": event.code, "date": event.date})
        return values

    @classmethod
    def insert_events(cls, values: List[Dict]):
        from sqlalchemy.dialects.sqlite import insert

        stmt = insert(ShipmentEvent).values(values).on_conflict_do_nothing()
        db.session.execute(stmt)

    @classmethod
    def update_events_by_shipment(cls, shipment_id: int, shipment: LaposteShipment):
        values = cls.prepare_events_to_insert_by_shipment(shipment_id, shipment)
        cls.insert_events(values)


class Shipment(Base):
    __tablename__ = "shipment"

    shipment_id = db.Column(db.Integer, primary_key=True)
    tracking_number = db.Column(db.String(256), unique=True)
    delivered = db.Column(db.Boolean, default=False)

    @classmethod
    def query_status(cls):
        return (
            ShipmentEvent.query.filter(ShipmentEvent.shipment_id == cls.shipment_id)
            .order_by(ShipmentEvent.date.desc())
            .limit(1)
        )

    @hybrid_property
    def status(self):
        row = self.query_status().one_or_none()
        if row:
            return row.status
        else:
            return "Unknown"

    @status.expression
    def status(cls):
        return cls.query_status().label("status")

    @classmethod
    def get_or_create(cls, tracking_number):
        shipment = Shipment.query.filter(cls.tracking_number == tracking_number).one_or_none()
        if not shipment:
            shipment = Shipment(tracking_number=tracking_number)
            db.session.add(shipment)
        return shipment

    def update(self, shipment: LaposteShipment):
        self.delivered = shipment.delivered
        db.session.flush()
        ShipmentEvent.update_events_by_shipment(self.shipment_id, shipment)
        db.session.commit()

    @classmethod
    def update_multiple_rows(cls, shipments: List[LaposteShipment]):
        data = []
        event_values = {}
        # gather all shipments and events all together to bulk update
        for item in shipments:
            data.append({"tracking_number": item.shipment_id, "delivered": item.delivered})
            event_values[item.shipment_id] = ShipmentEvent.prepare_events_to_insert(item)
        stmt = insert(cls).values(data)
        stmt = stmt.on_conflict_do_update(
            index_elements=["tracking_number"],
            set_={
                "tracking_number": stmt.excluded.tracking_number,
                "delivered": stmt.excluded.delivered,
            },
        ).returning(Shipment.shipment_id, Shipment.tracking_number)
        result = db.session.execute(stmt)
        event_values_to_insert = []
        for i in result:
            item = ShipmentItem(*i)
            for event in event_values[item.tracking_number]:
                event_values_to_insert.append({"shipment_id": item.sid, **event})
        ShipmentEvent.insert_events(event_values_to_insert)
        db.session.commit()

    @classmethod
    def get_undelivered_shipments(cls):
        return cls.query.filter(~cls.delivered)
