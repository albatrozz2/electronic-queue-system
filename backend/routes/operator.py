from flask import Blueprint, request, jsonify
from backend.models.database import get_db
from datetime import datetime

operator_bp = Blueprint("operator", __name__)

def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _op(conn, op_id):
    return conn.execute("SELECT * FROM operators WHERE id=?", (op_id,)).fetchone()


@operator_bp.post("/login")
def login():
    d = request.get_json(force=True)
    conn = get_db()
    op = conn.execute("SELECT * FROM operators WHERE window_number=? AND password_hash=?",
                      (d.get("window_number"), d.get("password"))).fetchone()
    conn.close()
    if not op:
        return jsonify({"error": "Invalid credentials"}), 401
    return jsonify({"operator_id": op["id"], "full_name": op["full_name"],
                    "window_number": op["window_number"], "token": op["password_hash"]})


@operator_bp.get("/<int:op_id>/status")
def get_status(op_id):
    conn = get_db()
    op = _op(conn, op_id); conn.close()
    if not op: return jsonify({"error": "Not found"}), 404
    return jsonify({"status": op["status"], "current_ticket_id": op["current_ticket_id"]})


@operator_bp.post("/<int:op_id>/next")
def call_next(op_id):
    conn = get_db()
    try:
        op = _op(conn, op_id)
        if not op: return jsonify({"error": "Not found"}), 404
        ticket = conn.execute(
            "SELECT t.*,s.name AS service_name FROM tickets t JOIN services s ON t.service_id=s.id "
            "WHERE t.status='waiting' ORDER BY s.priority,t.id LIMIT 1"
        ).fetchone()
        if not ticket: return jsonify({"message": "Queue is empty"}), 200
        conn.execute("UPDATE tickets SET status='called',operator_id=?,called_at=? WHERE id=?",
                     (op_id, _now(), ticket["id"]))
        conn.execute("UPDATE operators SET status='busy',current_ticket_id=? WHERE id=?",
                     (ticket["id"], op_id))
        conn.commit()
        return jsonify({"ticket_id": ticket["id"], "ticket_number": ticket["ticket_number"],
                        "service": ticket["service_name"], "window": op["window_number"]})
    finally:
        conn.close()


@operator_bp.post("/<int:op_id>/recall")
def recall(op_id):
    conn = get_db()
    op = _op(conn, op_id)
    if not op or not op["current_ticket_id"]:
        conn.close(); return jsonify({"error": "No active ticket"}), 400
    ticket = conn.execute("SELECT * FROM tickets WHERE id=?", (op["current_ticket_id"],)).fetchone()
    conn.close()
    return jsonify({"ticket_number": ticket["ticket_number"] if ticket else None,
                    "window": op["window_number"], "action": "recall"})


@operator_bp.post("/<int:op_id>/complete")
def complete(op_id):
    conn = get_db()
    try:
        op = _op(conn, op_id)
        if not op or not op["current_ticket_id"]:
            return jsonify({"error": "No active ticket"}), 400
        conn.execute("UPDATE tickets SET status='completed',completed_at=? WHERE id=?",
                     (_now(), op["current_ticket_id"]))
        conn.execute("UPDATE operators SET status='available',current_ticket_id=NULL WHERE id=?", (op_id,))
        conn.commit()
        return jsonify({"ok": True})
    finally:
        conn.close()


@operator_bp.post("/<int:op_id>/absent")
def absent(op_id):
    conn = get_db()
    try:
        op = _op(conn, op_id)
        if not op or not op["current_ticket_id"]:
            return jsonify({"error": "No active ticket"}), 400
        conn.execute("UPDATE tickets SET status='cancelled',completed_at=? WHERE id=?",
                     (_now(), op["current_ticket_id"]))
        conn.execute("UPDATE operators SET status='available',current_ticket_id=NULL WHERE id=?", (op_id,))
        conn.commit()
        return jsonify({"ok": True})
    finally:
        conn.close()


@operator_bp.post("/<int:op_id>/break")
def set_break(op_id):
    conn = get_db()
    conn.execute("UPDATE operators SET status='break' WHERE id=?", (op_id,))
    conn.commit(); conn.close()
    return jsonify({"ok": True, "status": "break"})


@operator_bp.post("/<int:op_id>/available")
def set_available(op_id):
    conn = get_db()
    conn.execute("UPDATE operators SET status='available' WHERE id=?", (op_id,))
    conn.commit(); conn.close()
    return jsonify({"ok": True, "status": "available"})


@operator_bp.post("/<int:op_id>/transfer")
def transfer(op_id):
    d = request.get_json(force=True)
    conn = get_db()
    try:
        op = _op(conn, op_id)
        if not op or not op["current_ticket_id"]:
            return jsonify({"error": "No active ticket"}), 400
        conn.execute("UPDATE tickets SET status='waiting',operator_id=NULL,called_at=NULL WHERE id=?",
                     (op["current_ticket_id"],))
        conn.execute("UPDATE operators SET status='available',current_ticket_id=NULL WHERE id=?", (op_id,))
        conn.commit()
        return jsonify({"ok": True})
    finally:
        conn.close()


@operator_bp.get("/<int:op_id>/history")
def history(op_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT t.ticket_number,t.status,t.created_at,t.completed_at,s.name AS service_name "
        "FROM tickets t JOIN services s ON t.service_id=s.id "
        "WHERE t.operator_id=? AND date(t.created_at)=date('now','localtime') ORDER BY t.id DESC",
        (op_id,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])
