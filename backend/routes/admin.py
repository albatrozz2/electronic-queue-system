from flask import Blueprint, request, jsonify
from backend.models.database import get_db

admin_bp = Blueprint("admin", __name__)


def auth(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("X-Admin-Token", "")
        conn = get_db()
        ok = conn.execute("SELECT 1 FROM admins WHERE password=?", (token,)).fetchone()
        conn.close()
        if not ok:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


@admin_bp.post("/login")
def login():
    d = request.get_json(force=True)
    conn = get_db()
    row = conn.execute("SELECT * FROM admins WHERE username=? AND password=?",
                       (d.get("username"), d.get("password"))).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Invalid credentials"}), 401
    return jsonify({"token": row["password"], "username": row["username"]})


@admin_bp.get("/services")
@auth
def list_services():
    conn = get_db()
    rows = conn.execute("SELECT * FROM services ORDER BY priority").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@admin_bp.post("/services")
@auth
def create_service():
    d = request.get_json(force=True)
    conn = get_db()
    try:
        conn.execute("INSERT INTO services (name,code,priority,avg_time) VALUES (?,?,?,?)",
                     (d["name"], d["code"].upper(), d.get("priority",1), d.get("avg_time",5)))
        conn.commit()
        return jsonify({"ok": True}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()


@admin_bp.put("/services/<int:sid>")
@auth
def update_service(sid):
    d = request.get_json(force=True)
    conn = get_db()
    conn.execute("UPDATE services SET name=?,priority=?,avg_time=?,is_active=? WHERE id=?",
                 (d["name"], d["priority"], d["avg_time"], d.get("is_active",1), sid))
    conn.commit(); conn.close()
    return jsonify({"ok": True})


@admin_bp.delete("/services/<int:sid>")
@auth
def delete_service(sid):
    conn = get_db()
    conn.execute("UPDATE services SET is_active=0 WHERE id=?", (sid,))
    conn.commit(); conn.close()
    return jsonify({"ok": True})


@admin_bp.get("/operators")
@auth
def list_operators():
    conn = get_db()
    rows = conn.execute("SELECT id,full_name,window_number,status,current_ticket_id FROM operators ORDER BY window_number").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@admin_bp.post("/operators")
@auth
def create_operator():
    d = request.get_json(force=True)
    conn = get_db()
    try:
        conn.execute("INSERT INTO operators (full_name,window_number,password_hash) VALUES (?,?,?)",
                     (d["full_name"], d["window_number"], d.get("password","operator123")))
        conn.commit()
        return jsonify({"ok": True}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()


@admin_bp.put("/operators/<int:oid>")
@auth
def update_operator(oid):
    d = request.get_json(force=True)
    conn = get_db()
    conn.execute("UPDATE operators SET full_name=?,window_number=? WHERE id=?",
                 (d["full_name"], d["window_number"], oid))
    conn.commit(); conn.close()
    return jsonify({"ok": True})


@admin_bp.delete("/operators/<int:oid>")
@auth
def delete_operator(oid):
    conn = get_db()
    conn.execute("DELETE FROM operators WHERE id=?", (oid,))
    conn.commit(); conn.close()
    return jsonify({"ok": True})


@admin_bp.get("/stats")
@auth
def stats():
    conn = get_db()
    served = conn.execute("SELECT COUNT(*) FROM tickets WHERE date(created_at)=date('now','localtime')").fetchone()[0]
    waiting = conn.execute("SELECT COUNT(*) FROM tickets WHERE status='waiting'").fetchone()[0]
    serving = conn.execute("SELECT COUNT(*) FROM tickets WHERE status='called'").fetchone()[0]
    avg = conn.execute(
        "SELECT AVG((strftime('%s',completed_at)-strftime('%s',created_at))/60.0) FROM tickets "
        "WHERE status='completed' AND date(created_at)=date('now','localtime')"
    ).fetchone()[0]
    online = conn.execute("SELECT COUNT(*) FROM operators WHERE status!='unavailable'").fetchone()[0]
    conn.close()
    return jsonify({"served_today": served, "waiting": waiting, "serving": serving,
                    "avg_time_min": round(avg,1) if avg else 0, "operators_online": online})


@admin_bp.get("/settings")
@auth
def get_settings():
    conn = get_db()
    rows = conn.execute("SELECT * FROM settings").fetchall()
    conn.close()
    return jsonify({r["key"]: r["value"] for r in rows})


@admin_bp.put("/settings")
@auth
def update_settings():
    d = request.get_json(force=True)
    conn = get_db()
    for k,v in d.items():
        conn.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k,v))
    conn.commit(); conn.close()
    return jsonify({"ok": True})
