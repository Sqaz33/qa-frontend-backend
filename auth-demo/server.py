"""Loopback-only authentication exercise; independent of the applications demo."""
import argparse
import hashlib
import hmac
import json
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from uuid import uuid4

BUILD = "auth-demo-1.0"


def password_hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)


class AuthState:
    def __init__(self, token_ttl=900, clock=time.monotonic):
        self.token_ttl = token_ttl
        self.clock = clock
        self.lock = threading.Lock()
        self.tokens = {}
        self.users = {}
        for user_id, (username, role) in enumerate(
            [("qa_user", "user"), ("qa_admin", "admin")], start=1
        ):
            salt = secrets.token_bytes(16)
            self.users[username] = {
                "public": {"id": user_id, "username": username, "role": role},
                "salt": salt,
                "hash": password_hash("Study123!", salt),
            }
        self.dummy_salt = secrets.token_bytes(16)
        self.dummy_hash = password_hash("unused", self.dummy_salt)

    def login(self, username, password):
        user = self.users.get(username)
        salt = user["salt"] if user else self.dummy_salt
        expected = user["hash"] if user else self.dummy_hash
        matches = hmac.compare_digest(password_hash(password, salt), expected)
        if not matches or user is None:
            return None
        token = secrets.token_urlsafe(32)
        with self.lock:
            self.tokens[token] = (user["public"], self.clock() + self.token_ttl)
        return {"access_token": token, "token_type": "Bearer",
                "expires_in": self.token_ttl, "user": user["public"]}

    def authenticate(self, token):
        with self.lock:
            session = self.tokens.get(token)
            if session is None:
                return None
            if self.clock() >= session[1]:
                del self.tokens[token]
                return None
            return session[0]

    def logout(self, token):
        with self.lock:
            self.tokens.pop(token, None)


class AuthServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, state):
        self.state = state
        super().__init__(address, Handler)


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, value=None):
        body = b"" if status == 204 else json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        if status != 204:
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Build-Version", BUILD)
        self.send_header("X-Request-Id", str(uuid4()))
        if status == 401:
            self.send_header("WWW-Authenticate", 'Bearer realm="qa-auth"')
        self.end_headers()
        self.wfile.write(body)

    def identity(self):
        authorization = self.headers.get("Authorization")
        if authorization is None:
            self.respond(401, {"error": "unauthorized"})
            return None
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            self.respond(401, {"error": "invalid_token"})
            return None
        user = self.server.state.authenticate(parts[1])
        if user is None:
            self.respond(401, {"error": "invalid_token"})
            return None
        return user, parts[1]

    def do_GET(self):
        route = self.path.split("?", 1)[0]
        if route == "/health":
            return self.respond(200, {"status": "ok", "build": BUILD})
        if route not in ("/api/me", "/api/admin/report"):
            return self.respond(404, {"error": "not_found"})
        identity = self.identity()
        if identity is None:
            return
        user, _ = identity
        if route == "/api/me":
            return self.respond(200, user)
        if user["role"] != "admin":
            return self.respond(403, {"error": "forbidden"})
        return self.respond(200, {"report": "Учебный отчёт", "total": 2})

    def do_POST(self):
        route = self.path.split("?", 1)[0]
        if route == "/auth/logout":
            identity = self.identity()
            if identity is not None:
                self.server.state.logout(identity[1])
                self.respond(204)
            return
        if route != "/auth/login":
            return self.respond(404, {"error": "not_found"})
        media_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if media_type != "application/json":
            return self.respond(415, {"error": "unsupported_media_type"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 1 <= length <= 65536:
                raise ValueError("invalid body length")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("expected an object")
        except (ValueError, UnicodeDecodeError):
            return self.respond(400, {"error": "invalid_json"})
        if any(not isinstance(payload.get(key), str) or not payload[key].strip()
               for key in ("username", "password")):
            return self.respond(422, {"error": "validation_error"})
        result = self.server.state.login(payload["username"], payload["password"])
        if result is None:
            return self.respond(401, {"error": "invalid_credentials"})
        return self.respond(200, result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--token-ttl", type=int, default=900)
    args = parser.parse_args()
    if args.token_ttl < 1:
        parser.error("--token-ttl must be positive")
    server = AuthServer(("127.0.0.1", args.port), AuthState(args.token_ttl))
    print(f"QA auth {BUILD}: http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
