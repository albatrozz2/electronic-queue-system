from .database import get_db
from datetime import datetime


def _next_number(conn, code):
    today = datetime.now().strftime("%Y-%m-%d")
    cur = conn.execute(
        "SELECT COUNT(*) FROM tickets WHERE ticket_number LIKE ? AND date(created_at)=?",
        (f"{code}%", today),
    )
    return f"{code}{(cur.fetchone()[0]+1):03d}"


def create_ticket(service_id):
    conn = get_db()
    try:
        service = conn.execute(
            "SELECT * FROM services WHERE id=? AND is_active=1", (service_id,)
        ).fetchone()
        if not service:
            return {"error": "Service not found"}

        number = _next_number(conn, service["code"])
        waiting = conn.execute(
            "SELECT COUNT(*) FROM tickets WHERE service_id=? AND status='waiting'",
            (service_id,),
        ).fetchone()[0]

        conn.execute(
            "INSERT INTO tickets (ticket_number, service_id) VALUES (?,?)",
            (number, service_id),
        )
        conn.commit()
        return {
            "id": conn.execute("SELECT last_insert_rowid()").fetchone()[0],
            "ticket_number": number,
            "service": service["name"],
            "waiting_ahead": waiting,
            "estimated_min": waiting * service["avg_time"],
        }
    finally:
        conn.close()


def get_queue(service_id=None):
    conn = get_db()
    try:
        if service_id:
            rows = conn.execute(
                "SELECT t.*,s.name AS service_name FROM tickets t JOIN services s ON t.service_id=s.id "
                "WHERE t.status='waiting' AND t.service_id=? ORDER BY t.id", (service_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT t.*,s.name AS service_name FROM tickets t JOIN services s ON t.service_id=s.id "
                "WHERE t.status='waiting' ORDER BY s.priority,t.id"
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_ticket_status(ticket_number):
    conn = get_db()
    try:
        ticket = conn.execute(
            "SELECT t.*,s.name AS service_name FROM tickets t JOIN services s ON t.service_id=s.id "
            "WHERE t.ticket_number=?", (ticket_number,)
        ).fetchone()
        if not ticket:
            return {"error": "Not found"}
        position = 0
        if ticket["status"] == "waiting":
            position = conn.execute(
                "SELECT COUNT(*) FROM tickets WHERE status='waiting' AND id<?", (ticket["id"],)
            ).fetchone()[0] + 1
        return {**dict(ticket), "position": position}
    finally:
        conn.close()
