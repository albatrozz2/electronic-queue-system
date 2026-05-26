from flask import Flask
from backend.models.database import init_db
from backend.routes.admin import admin_bp
from backend.routes.operator import operator_bp
from backend.routes.queue import queue_bp, display_bp

app = Flask(__name__)
app.secret_key = "queue-secret-2026"

app.register_blueprint(admin_bp,    url_prefix="/api/admin")
app.register_blueprint(operator_bp, url_prefix="/api/operator")
app.register_blueprint(queue_bp,    url_prefix="/api")
app.register_blueprint(display_bp,  url_prefix="/api/display")

@app.route("/")
def index():
    return {"status": "ok", "system": "Electronic Queue System", "version": "1.0"}

def create_app():
    init_db()
    return app

if __name__ == "__main__":
    create_app()
    app.run(debug=True, port=5000)
