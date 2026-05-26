from flask import Blueprint, request, jsonify
from backend.models.ticket import create_ticket, get_queue, get_ticket_status
from backend.models.database import get_db

queue_bp = Blueprint("queue", __name__)
display_bp = Blueprint("display", __name__)


@queue_bp.get("/services")
def services():
    conn = get_db()
    rows = conn.execute(
        "SELECT id,name,code,priority,avg_time FROM services WHERE is_active=1 ORDER BY priority"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@queue_bp.post("/tickets")
def new_ticket():
    d = request.get_json(force=True)
    result = create_ticket(d.get("service_id"))
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result), 201


@queue_bp.get("/tickets/queue")
def queue():
    service_id = request.args.get("service_id", type=int)
    return jsonify(get_queue(service_id))


@queue_bp.get("/tickets/<ticket_number>")
def ticket_status(ticket_number):
    result = get_ticket_status(ticket_number)
    if "error" in result:
        return jsonify(result), 404
    return jsonify(result)


@display_bp.get("/data")
def display_data():
    conn = get_db()
    called = conn.execute(
        "SELECT t.ticket_number,o.window_number,s.name AS service_name "
        "FROM tickets t JOIN operators o ON t.operator_id=o.id JOIN services s ON t.service_id=s.id "
        "WHERE t.status='called' ORDER BY t.called_at"
    ).fetchall()
    waiting = conn.execute(
        "SELECT t.ticket_number,s.name AS service_name "
        "FROM tickets t JOIN services s ON t.service_id=s.id "
        "WHERE t.status='waiting' ORDER BY s.priority,t.id LIMIT 10"
    ).fetchall()
    settings = conn.execute("SELECT key,value FROM settings").fetchall()
    conn.close()
    return jsonify({
        "called":   [dict(r) for r in called],
        "waiting":  [dict(r) for r in waiting],
        "settings": {r["key"]: r["value"] for r in settings},
    })
