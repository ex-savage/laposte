import concurrent
import logging
from concurrent.futures import ThreadPoolExecutor

from app.laposte.laposte import client
from app.models.shipment import Shipment

log = logging.getLogger(__name__)
WORKERS = 10


def get_shipments(batches):
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        future_to_url = {executor.submit(client.get_shipments, batch) for batch in batches}
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                data = future.result()
                Shipment.update_multiple_rows(data)
            except Exception:
                log.exception("Error in get_shipments subtask")
