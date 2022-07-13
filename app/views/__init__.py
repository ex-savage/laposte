from flask import render_template

from app.laposte.exceptions import LaposteError
from app.laposte.laposte import LaposteShipment, client
from app.main import app, celery
from app.models.shipment import Shipment, ShipmentEvent
from app.tasks import update_shipments


@app.route("/ping", methods=["GET"])
def ping():
    return "pong", 200


@app.route("/shipments/", methods=["GET"])
def update_shipments_statuses():
    task = update_shipments.delay()
    return task.task_id, 200


@app.route("/tasks/<task_id>", methods=["GET"])
def get_task_result(task_id):
    status = celery.AsyncResult(task_id).state
    return status, 200


@app.route("/shipments/<tracking_number>", methods=["GET"])
def get_shipment_status(tracking_number):
    shipment = Shipment.get_or_create(tracking_number)
    # since shipment delivered it doesn't make sense to go to Laposte API, we already have that info
    if shipment.delivered:
        return f"{shipment.status}", 200
    try:
        shipment_data: LaposteShipment = client.get_shipment(tracking_number)
    except LaposteError as exc:
        return f"Error: {exc.message}", 200
    shipment.update(shipment_data)
    return f"{shipment.status}", 200


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", shipments=Shipment.query.all())


@app.route("/shipments/history/<int:shipment_id>", methods=["GET"])
def get_shipment_history(shipment_id):
    return render_template(
        "history.html",
        events=ShipmentEvent.query.filter(ShipmentEvent.shipment_id == shipment_id)
        .order_by(ShipmentEvent.date.asc())
        .all(),
    )
