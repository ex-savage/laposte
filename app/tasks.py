from app.laposte.batch import get_shipments
from app.main import celery
from app.models.shipment import Shipment


@celery.task()
def update_shipments():
    batches = []
    counter = 0
    batch = []
    for item in Shipment.get_undelivered_shipments().yield_per(10):
        if counter > 9:
            batches.append(batch)
            counter = 0
            batch = []
        batch.append(item.tracking_number)
        counter += 1
    if batch:
        batches.append(batch)
    if batches:
        get_shipments(batches)
