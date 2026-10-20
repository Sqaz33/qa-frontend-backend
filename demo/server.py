"""Local QA demo: Python standard library only."""
import argparse
import json
import sqlite3
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "runtime"
BUILD = "demo-1.0"

def connect():
    db = sqlite3.connect(DATA_DIR / "applications.sqlite")
    db.row_factory = sqlite3.Row
    return db

def init_db():
    DATA_DIR.mkdir(exist_ok=True)
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, amount INTEGER NOT NULL,
            consent INTEGER NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL
        )""")

def application(row):
    return {**dict(row), "consent": bool(row["consent"])}

class Handler(BaseHTTPRequestHandler):
    def json_response(self, status, value, location=None):
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Build-Version", BUILD)
        self.send_header("X-Request-Id", str(uuid4()))
        if location:
            self.send_header("Location", location)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        route = self.path.split("?", 1)[0]
        if route == "/health":
            return self.json_response(200, {"status": "ok", "build": BUILD})
        if route == "/api/applications":
            with connect() as db:
                rows = db.execute("SELECT * FROM applications ORDER BY id DESC").fetchall()
            return self.json_response(200, {"items": [application(row) for row in rows]})
        if route.startswith("/api/applications/"):
            key = route.removeprefix("/api/applications/")
            if not key.isascii() or not key.isdigit():
                return self.json_response(404, {"error": "not_found", "message": "Заявка не найдена"})
            with connect() as db:
                row = db.execute("SELECT * FROM applications WHERE id = ?", (key,)).fetchone()
            if row is None:
                return self.json_response(404, {"error": "not_found", "message": "Заявка не найдена"})
            return self.json_response(200, application(row))
        static = {"/": ("index.html", "text/html"), "/style.css": ("style.css", "text/css"),
                  "/app.js": ("app.js", "text/javascript")}
        if route not in static:
            return self.json_response(404, {"error": "not_found", "message": "Ресурс не найден"})
        filename, mime = static[route]
        body = (ROOT / "dist" / filename).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/api/applications":
            return self.json_response(404, {"error": "not_found", "message": "Ресурс не найден"})
        if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
            return self.json_response(415, {"error": "unsupported_media_type", "message": "Нужен application/json"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self.json_response(400, {"error": "invalid_length", "message": "Некорректная длина запроса"})
        if length < 1 or length > 65536:
            return self.json_response(400, {"error": "invalid_body", "message": "Некорректный размер тела"})
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return self.json_response(400, {"error": "invalid_json", "message": "Некорректный JSON"})
        if not isinstance(payload, dict):
            return self.json_response(400, {"error": "invalid_body", "message": "Ожидается объект JSON"})
        errors = {}
        name = payload.get("name")
        if not isinstance(name, str) or not 2 <= len(name.strip()) <= 50:
            errors["name"] = "Укажите имя: от 2 до 50 символов"
        amount = payload.get("amount")
        if type(amount) is not int or not 1000 <= amount <= 100000:
            errors["amount"] = "Сумма: целое число от 1 000 до 100 000 рублей"
        if payload.get("consent") is not True:
            errors["consent"] = "Нужно согласие"
        if errors:
            return self.json_response(422, {"error": "validation_error", "fields": errors})
        created_at = datetime.now(timezone.utc).isoformat()
        with connect() as db:
            cursor = db.execute(
                "INSERT INTO applications (name, amount, consent, status, created_at) VALUES (?, ?, 1, 'new', ?)",
                (name.strip(), amount, created_at))
            row = db.execute("SELECT * FROM applications WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return self.json_response(201, application(row), f"/api/applications/{row['id']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    init_db()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"QA demo {BUILD}: http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
