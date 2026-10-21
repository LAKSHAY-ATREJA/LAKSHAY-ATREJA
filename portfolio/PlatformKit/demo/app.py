"""A tiny standard-library HTTP service for the local platform demo."""

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HEALTH = {"status": "ok", "service": "PlatformKit"}
METRICS = (
    b"# HELP platformkit_demo_info Static information about the demo service.\n"
    b"# TYPE platformkit_demo_info gauge\n"
    b'platformkit_demo_info{version="1.0.0"} 1\n'
)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            self._send(HTTPStatus.OK, json.dumps(HEALTH).encode(), "application/json")
        elif self.path == "/metrics":
            self._send(HTTPStatus.OK, METRICS, "text/plain; version=0.0.4")
        else:
            self._send(
                HTTPStatus.NOT_FOUND,
                json.dumps({"detail": "not found"}).encode(),
                "application/json",
            )

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    ThreadingHTTPServer((host, port), Handler).serve_forever()
