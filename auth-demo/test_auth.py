"""HTTP contract checks with a controlled clock; no sleep needed for expiry."""
import http.client
import json
import threading
import unittest
from unittest.mock import patch

from server import AuthServer, AuthState, Handler


class AuthContractTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.state = AuthState(token_ttl=10, clock=lambda: self.now)
        self.server = AuthServer(("127.0.0.1", 0), self.state)
        self.quiet = patch.object(Handler, "log_message", lambda *args: None)
        self.quiet.start()
        self.thread = threading.Thread(
            target=self.server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
        )
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.quiet.stop()

    def request(self, method, path, body=None, token=None, headers=None):
        actual_headers = dict(headers or {})
        if isinstance(body, dict):
            body = json.dumps(body)
            actual_headers.setdefault("Content-Type", "application/json")
        if token is not None:
            actual_headers["Authorization"] = "Bearer " + token
        connection = http.client.HTTPConnection(*self.server.server_address, timeout=5)
        try:
            connection.request(method, path, body=body, headers=actual_headers)
            response = connection.getresponse()
            raw = response.read()
            result = json.loads(raw) if raw else None
            return response.status, dict(response.getheaders()), result
        finally:
            connection.close()

    def login(self, username="qa_user", **extra):
        status, _, data = self.request("POST", "/auth/login", {
            "username": username, "password": "Study123!", **extra
        })
        self.assertEqual(status, 200)
        self.assertEqual(data["token_type"], "Bearer")
        self.assertEqual(data["expires_in"], 10)
        self.assertIsInstance(data["access_token"], str)
        self.assertTrue(data["access_token"])
        return data["access_token"]

    def test_health_contract(self):
        status, headers, data = self.request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(data, {"status": "ok", "build": "auth-demo-1.0"})
        self.assertIn("application/json", headers["Content-Type"])
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(headers["X-Build-Version"], "auth-demo-1.0")
        self.assertTrue(headers["X-Request-Id"])

    def test_all_protected_routes_need_token(self):
        for method, path in (("GET", "/api/me"), ("GET", "/api/admin/report"),
                             ("POST", "/auth/logout")):
            with self.subTest(path=path):
                status, headers, data = self.request(method, path)
                self.assertEqual(status, 401)
                self.assertEqual(data["error"], "unauthorized")
                self.assertEqual(headers["WWW-Authenticate"], 'Bearer realm="qa-auth"')

    def test_invalid_authorization(self):
        for value in ("Bearer unknown", "Basic unknown", "Bearer", "Bearer x y"):
            with self.subTest(value=value):
                status, _, data = self.request("GET", "/api/me", headers={"Authorization": value})
                self.assertEqual(status, 401)
                self.assertEqual(data["error"], "invalid_token")

    def test_login_and_profile(self):
        token = self.login()
        status, _, data = self.request("GET", "/api/me", token=token)
        self.assertEqual(status, 200)
        self.assertEqual(data, {"id": 1, "username": "qa_user", "role": "user"})

    def test_wrong_password_and_unknown_user_same_error(self):
        for username, password in (("qa_user", "wrong"), ("nobody", "Study123!")):
            status, _, data = self.request("POST", "/auth/login", {
                "username": username, "password": password
            })
            self.assertEqual(status, 401)
            self.assertEqual(data, {"error": "invalid_credentials"})

    def test_login_input_errors(self):
        cases = [("{", {"Content-Type": "application/json"}, 400, "invalid_json"),
                 ("[]", {"Content-Type": "application/json"}, 400, "invalid_json"),
                 ("{}", {"Content-Type": "text/plain"}, 415, "unsupported_media_type"),
                 ({}, {}, 422, "validation_error"),
                 ({"username": True, "password": "x"}, {}, 422, "validation_error"),
                 ({"username": "qa_user", "password": " "}, {}, 422, "validation_error")]
        for body, headers, expected, error in cases:
            with self.subTest(body=body):
                status, _, data = self.request("POST", "/auth/login", body, headers=headers)
                self.assertEqual(status, expected)
                self.assertEqual(data["error"], error)

    def test_user_cannot_read_admin_report(self):
        token = self.login()
        status, _, data = self.request("GET", "/api/admin/report", token=token)
        self.assertEqual(status, 403)
        self.assertEqual(data, {"error": "forbidden"})

    def test_admin_can_read_report(self):
        token = self.login("qa_admin")
        status, _, data = self.request("GET", "/api/admin/report", token=token)
        self.assertEqual(status, 200)
        self.assertEqual(data, {"report": "Учебный отчёт", "total": 2})

    def test_client_cannot_choose_own_role(self):
        token = self.login(role="admin", id=2)
        status, _, data = self.request("GET", "/api/me", token=token)
        self.assertEqual(status, 200)
        self.assertEqual(data["role"], "user")
        self.assertEqual(data["id"], 1)
        status, _, _ = self.request("GET", "/api/admin/report", token=token)
        self.assertEqual(status, 403)

    def test_logout_revokes_only_current_token(self):
        first, second = self.login(), self.login()
        self.assertNotEqual(first, second)
        status, _, data = self.request("POST", "/auth/logout", token=first)
        self.assertEqual(status, 204)
        self.assertIsNone(data)
        status, _, data = self.request("GET", "/api/me", token=first)
        self.assertEqual(status, 401)
        self.assertEqual(data["error"], "invalid_token")
        status, _, _ = self.request("GET", "/api/me", token=second)
        self.assertEqual(status, 200)

    def test_expiry_boundary_and_no_sliding_extension(self):
        token = self.login()
        self.now = 109.99
        self.assertEqual(self.request("GET", "/api/me", token=token)[0], 200)
        self.now = 110.0
        status, _, data = self.request("GET", "/api/me", token=token)
        self.assertEqual(status, 401)
        self.assertEqual(data["error"], "invalid_token")

    def test_unknown_route(self):
        status, _, data = self.request("GET", "/api/missing")
        self.assertEqual(status, 404)
        self.assertEqual(data["error"], "not_found")


if __name__ == "__main__":
    unittest.main()
